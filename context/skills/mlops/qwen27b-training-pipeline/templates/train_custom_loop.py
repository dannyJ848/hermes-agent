#!/usr/bin/env python3
"""
Custom training loop for Qwen 27B on DGX Spark GB10.
Based on train_lora_sae_teacher_v1.py (May 8, 2026) which achieved ~20s/step.

Key differences from transformers.Trainer:
- 8-bit AdamW (bnb.optim.Adam8bit) instead of standard AdamW
- Custom collator without tensor duplication
- No gradient checkpointing (fits at ~62GB)
- ~25x faster than transformers.Trainer approach

Usage:
    export PYTHONPATH=/data/SpecForge/custom_dflash:$PYTHONPATH
    export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    python train_custom_loop.py
"""

import os
import sys
import json
import time
import logging
from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    get_cosine_schedule_with_warmup,
)
from peft import LoraConfig, get_peft_model, TaskType
import bitsandbytes as bnb

# Configuration
@dataclass
class Config:
    model_path: str = "/data/SpecForge/custom_dflash/checkpoints/final_model_merged"
    output_dir: str = "/data/SpecForge/custom_dflash/checkpoints"
    
    # LoRA
    lora_r: int = 256
    lora_alpha: int = 512
    lora_dropout: float = 0.05
    target_modules: list = None
    
    # Training
    batch_size: int = 1
    grad_accum_steps: int = 4
    max_steps: int = 10000
    learning_rate: float = 2e-4
    warmup_steps: int = 500
    max_length: int = 4096
    
    # Data
    data_paths: list = None  # List of JSONL files
    
    # Logging
    log_interval: int = 10
    save_interval: int = 1000
    
    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", 
                                   "gate_proj", "up_proj", "down_proj"]
        if self.data_paths is None:
            self.data_paths = [
                "/data/SpecForge/custom_dflash/preprocessed/tier1_preprocessed.jsonl",
                "/data/SpecForge/custom_dflash/datasets/tier2-reasoning-chat.jsonl",
                "/data/SpecForge/custom_dflash/datasets/tier3-health-chat.jsonl",
            ]


class LazyPreTokenizedDataset(Dataset):
    """Memory-efficient lazy loading for pre-tokenized JSONL."""
    def __init__(self, file_path, max_length=4096):
        self.file_path = file_path
        self.max_length = max_length
        self.offsets = []
        with open(file_path, 'rb') as f:
            offset = 0
            for line in f:
                self.offsets.append(offset)
                offset += len(line)
        print(f"Indexed {len(self.offsets)} examples from {file_path}")
    
    def __len__(self):
        return len(self.offsets)
    
    def __getitem__(self, idx):
        with open(self.file_path, 'rb') as f:
            f.seek(self.offsets[idx])
            data = json.loads(f.readline().decode('utf-8'))
        return {
            'input_ids': torch.tensor(data['input_ids'], dtype=torch.long),
            'attention_mask': torch.tensor(data['attention_mask'], dtype=torch.long),
            'labels': torch.tensor(data.get('labels', data['input_ids']), dtype=torch.long),
        }


class CausalLMCollator:
    """Custom collator that does NOT duplicate tensors."""
    def __call__(self, features):
        input_ids = torch.stack([f["input_ids"] for f in features])
        attention_mask = torch.stack([f["attention_mask"] for f in features])
        labels = torch.stack([f["labels"] for f in features])
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }


def setup_logging(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(output_dir, "training_custom.log")),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_model(config: Config):
    """Load model with LoRA applied."""
    logging.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(config.model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    logging.info("Loading model in bf16 (~5 min)...")
    model = AutoModelForCausalLM.from_pretrained(
        config.model_path,
        torch_dtype=torch.bfloat16,
        device_map="cuda:0",
        low_cpu_mem_usage=False,  # CRITICAL: prevents meta-device gradient bugs
        trust_remote_code=True,
    )
    
    logging.info("Applying LoRA...")
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=config.target_modules,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model, tokenizer


def create_optimizer(model, config: Config):
    """Create 8-bit AdamW optimizer."""
    logging.info("Creating 8-bit AdamW optimizer...")
    optimizer = bnb.optim.Adam8bit(
        model.parameters(),
        lr=config.learning_rate,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.01,
    )
    return optimizer


def create_scheduler(optimizer, config: Config):
    """Create learning rate scheduler."""
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=config.warmup_steps,
        num_training_steps=config.max_steps,
    )
    return scheduler


def train(config: Config):
    setup_logging(config.output_dir)
    logging.info("=" * 70)
    logging.info("QWEN 27B — Custom Training Loop (GB10 Optimized)")
    logging.info("=" * 70)
    logging.info(f"Max steps: {config.max_steps}")
    logging.info(f"Batch: {config.batch_size}, Grad accum: {config.grad_accum_steps}")
    logging.info(f"Effective batch: {config.batch_size * config.grad_accum_steps}")
    logging.info(f"LoRA: r={config.lora_r}, alpha={config.lora_alpha}")
    logging.info(f"LR: {config.learning_rate}")
    
    # Load model
    model, tokenizer = load_model(config)
    
    # Create optimizer and scheduler
    optimizer = create_optimizer(model, config)
    scheduler = create_scheduler(optimizer, config)
    
    # Load datasets
    logging.info("Loading datasets...")
    datasets = []
    for path in config.data_paths:
        if os.path.exists(path):
            datasets.append(LazyPreTokenizedDataset(path, config.max_length))
        else:
            logging.warning(f"Dataset not found: {path}")
    
    if not datasets:
        raise ValueError("No datasets found!")
    
    # Combine datasets
    from torch.utils.data import ConcatDataset
    if len(datasets) == 1:
        train_dataset = datasets[0]
    else:
        # Repeat smaller datasets for weighting
        # Adjust repetition factors based on your needs
        train_dataset = ConcatDataset(datasets)
    
    logging.info(f"Total examples: {len(train_dataset)}")
    
    # Create dataloader
    collator = CausalLMCollator()
    dataloader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=0,  # CRITICAL: num_workers>0 forks and doubles RAM
        collate_fn=collator,
    )
    
    # Training loop
    logging.info("=" * 70)
    logging.info("STARTING TRAINING")
    logging.info("=" * 70)
    
    model.train()
    global_step = 0
    accumulated_loss = 0
    batch_count = 0
    start_time = time.time()
    
    data_iter = iter(dataloader)
    
    while global_step < config.max_steps:
        try:
            batch = next(data_iter)
        except StopIteration:
            data_iter = iter(dataloader)
            batch = next(data_iter)
        
        # Move to device
        batch = {k: v.cuda() if isinstance(v, torch.Tensor) else v 
                 for k, v in batch.items()}
        
        # Forward pass
        outputs = model(**batch)
        loss = outputs.loss / config.grad_accum_steps
        
        # Backward pass
        loss.backward()
        
        accumulated_loss += loss.item() * config.grad_accum_steps
        batch_count += 1
        
        # Gradient accumulation
        if batch_count % config.grad_accum_steps == 0:
            # Optimizer step
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            
            global_step += 1
            
            # Logging
            if global_step % config.log_interval == 0:
                elapsed = time.time() - start_time
                steps_per_sec = global_step / elapsed
                eta_sec = (config.max_steps - global_step) / steps_per_sec
                
                logging.info(
                    f"Step {global_step}/{config.max_steps} | "
                    f"Loss: {accumulated_loss/config.grad_accum_steps:.4f} | "
                    f"LR: {scheduler.get_last_lr()[0]:.2e} | "
                    f"Speed: {1/steps_per_sec:.1f}s/step | "
                    f"ETA: {eta_sec/3600:.1f}h"
                )
                accumulated_loss = 0
            
            # Save checkpoint
            if global_step % config.save_interval == 0:
                checkpoint_dir = os.path.join(config.output_dir, f"checkpoint_step_{global_step}")
                logging.info(f"Saving checkpoint to {checkpoint_dir}")
                model.save_pretrained(checkpoint_dir)
                torch.save(optimizer.state_dict(), os.path.join(checkpoint_dir, "optimizer.pt"))
    
    # Final save
    final_dir = os.path.join(config.output_dir, "final_model")
    logging.info(f"Saving final model to {final_dir}")
    model.save_pretrained(final_dir)
    
    logging.info("Training complete!")
    logging.info(f"Total time: {(time.time() - start_time)/3600:.1f} hours")


if __name__ == "__main__":
    config = Config()
    train(config)
