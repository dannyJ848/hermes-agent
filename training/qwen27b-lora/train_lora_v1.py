#!/usr/bin/env python3
"""
Qwen 27B Expert Logician Training — LoRA v1
Uses LoRA (Low-Rank Adaptation) to reduce memory footprint.
Trainable params: ~500M instead of 27B.

Key changes from v4:
- LoRA on all linear layers (r=64, alpha=128)
- Full fine-tuning replaced with parameter-efficient fine-tuning
- Memory requirement drops from ~120GB to ~40GB
- Can use larger batch size / more gradient accumulation
"""

import os
import sys
import json
import math
import random
import logging
import gc
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import IterableDataset, DataLoader
import numpy as np

# LoRA imports
try:
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    HAS_PEFT = True
except ImportError:
    HAS_PEFT = False
    print("ERROR: peft not installed. Run: pip install peft")
    sys.exit(1)

# Transformers
try:
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer,
        get_cosine_schedule_with_warmup
    )
except ImportError:
    print("ERROR: transformers not installed")
    sys.exit(1)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/mnt/bigssd/train_lora_v1.log')
    ]
)

# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class TrainConfig:
    # Model paths
    student_model_path: str = "/data/models/Qwen3.6-27B-Uncensored/"
    teacher_model_path: str = "/data/models/FrankenV8-Final/final_model.pt"
    sae_dir: str = "/data/models/Qwen-Scope/"
    
    # Data paths
    curatedthoughts_dir: str = "/data/datasets/curatedthoughts/"
    openthoughts_dir: str = "/data/datasets/openthoughts2-1m/"
    
    # LoRA config
    lora_r: int = 64
    lora_alpha: int = 128
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = None
    
    # Training
    max_steps: int = 10000
    batch_size: int = 2  # Can use larger batch with LoRA
    grad_accum_steps: int = 8  # Effective batch = 16
    max_seq_len: int = 2048  # Shorter sequences for stability
    
    # Optimizer
    lr: float = 2e-4  # Higher LR for LoRA
    beta1: float = 0.9
    beta2: float = 0.999
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    
    # Schedule
    warmup_steps: int = 500
    stable_steps: int = 8000
    decay_steps: int = 1500
    
    # SAE
    sae_layers: List[int] = None
    sae_weight: float = 0.05
    
    # Checkpointing
    save_every: int = 500
    checkpoint_dir: str = "/data/SpecForge/custom_dflash/checkpoints/"
    
    # Teacher distillation
    teacher_weight: float = 0.3
    temperature: float = 2.0
    
    def __post_init__(self):
        if self.lora_target_modules is None:
            self.lora_target_modules = [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ]
        if self.sae_layers is None:
            self.sae_layers = [16, 32, 48]


# ============================================================
# SAE UTILITIES (same as v4)
# ============================================================

def load_sae(sae_dir: str, layer_idx: int, device: str = "cpu"):
    """Load a single SAE for a specific layer."""
    sae_path = Path(sae_dir) / f"sae_layer_{layer_idx}.pt"
    if not sae_path.exists():
        logging.warning(f"SAE not found: {sae_path}")
        return None
    
    try:
        sae = torch.load(sae_path, map_location=device)
        logging.info(f"Loaded SAE for layer {layer_idx}")
        return sae
    except Exception as e:
        logging.warning(f"Failed to load SAE layer {layer_idx}: {e}")
        return None


def get_feature_acts(hidden_states, sae, device="cpu"):
    """Extract sparse feature activations from hidden states."""
    if sae is None:
        return None
    
    # Move SAE to device temporarily
    sae_device = next(sae.parameters()).device if hasattr(sae, 'parameters') else device
    
    # Ensure hidden states are on the same device as SAE
    hidden_states = hidden_states.to(sae_device)
    
    with torch.no_grad():
        # SAE forward pass
        if hasattr(sae, 'encode'):
            feature_acts = sae.encode(hidden_states)
        else:
            # Fallback: assume simple linear encoder
            feature_acts = torch.matmul(hidden_states, sae.W_enc) + sae.b_enc
    
    return feature_acts


def compute_sae_loss(student_features, teacher_features):
    """Compute MSE loss between student and teacher SAE features."""
    if student_features is None or teacher_features is None:
        return torch.tensor(0.0)
    
    # Match shapes
    min_len = min(student_features.size(1), teacher_features.size(1))
    student_features = student_features[:, :min_len, :]
    teacher_features = teacher_features[:, :min_len, :]
    
    return F.mse_loss(student_features, teacher_features)


# ============================================================
# TEACHER MODEL LOADER (same as v4)
# ============================================================

def load_teacher_model(teacher_path: str, device: str = "cpu"):
    """Load Franken V8 teacher model."""
    logging.info(f"Loading teacher model from {teacher_path}")
    
    if not os.path.exists(teacher_path):
        logging.warning(f"Teacher model not found at {teacher_path}")
        return None
    
    try:
        # Try loading as a checkpoint
        checkpoint = torch.load(teacher_path, map_location=device)
        
        if isinstance(checkpoint, dict) and 'model' in checkpoint:
            teacher_state = checkpoint['model']
        else:
            teacher_state = checkpoint
        
        logging.info(f"Teacher model loaded (state dict with {len(teacher_state)} keys)")
        return teacher_state
        
    except Exception as e:
        logging.error(f"Failed to load teacher model: {e}")
        return None


# ============================================================
# STREAMING DATASET
# ============================================================

class StreamingReasoningDataset(IterableDataset):
    """Memory-efficient streaming dataset for reasoning data."""
    
    def __init__(self, config: TrainConfig, tokenizer):
        self.config = config
        self.tokenizer = tokenizer
        self.files = []
        
        # Discover all data files
        self._discover_files()
        logging.info(f"Streaming dataset: {len(self.files)} files")
    
    def _discover_files(self):
        """Find all parquet files in data directories."""
        for dir_path in [self.config.curatedthoughts_dir, self.config.openthoughts_dir]:
            if os.path.exists(dir_path):
                for f in os.listdir(dir_path):
                    if f.endswith('.parquet'):
                        self.files.append(os.path.join(dir_path, f))
    
    def _format_conversation(self, data: dict) -> str:
        """Format conversation data into a single text string."""
        # Handle different formats
        if 'conversations' in data and isinstance(data['conversations'], list):
            convs = data['conversations']
            if isinstance(convs, (list, tuple)) and len(convs) > 0:
                if isinstance(convs[0], dict) and 'value' in convs[0]:
                    return "\n".join([c['value'] for c in convs if 'value' in c])
                elif isinstance(convs[0], str):
                    return "\n".join(convs)
        
        if 'messages' in data and isinstance(data['messages'], list):
            msgs = data['messages']
            if isinstance(msgs, list) and len(msgs) > 0:
                if isinstance(msgs[0], dict) and 'content' in msgs[0]:
                    return "\n".join([m['content'] for m in msgs if 'content' in m])
        
        if 'problem' in data and 'solution' in data:
            return f"Problem: {data['problem']}\nSolution: {data['solution']}"
        
        if 'question' in data and 'answer' in data:
            return f"Question: {data['question']}\nAnswer: {data['answer']}"
        
        if 'question' in data:
            return f"<question>\n{data['question']}\n</question>"
        
        return str(data)
    
    def __iter__(self):
        """Stream samples indefinitely."""
        import pandas as pd
        step = 0
        
        while True:
            for pf in self.files:
                try:
                    df = pd.read_parquet(pf)
                    for _, row in df.iterrows():
                        text = self._format_conversation(row.to_dict())
                        tokens = self.tokenizer(text, truncation=True,
                                              max_length=self.config.max_seq_len,
                                              return_tensors="pt")
                        yield {
                            'input_ids': tokens['input_ids'].squeeze(0),
                            'labels': tokens['input_ids'].squeeze(0).clone(),
                            'step': step,
                        }
                        step += 1
                except Exception as e:
                    logging.warning(f"Failed to stream {pf}: {e}")
            
            if not self.files:
                logging.error("No data files found!")
                yield {
                    'input_ids': torch.tensor([1, 2, 3]),
                    'labels': torch.tensor([1, 2, 3]),
                    'step': step,
                }
                step += 1


# ============================================================
# TRAINING LOOP
# ============================================================

def train(config: TrainConfig):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    logging.info("=" * 70)
    logging.info("QWEN 27B EXPERT LOGICIAN TRAINING — LoRA v1")
    logging.info("=" * 70)
    logging.info(f"Max steps: {config.max_steps}")
    logging.info(f"Batch size: {config.batch_size}, Grad accum: {config.grad_accum_steps}")
    logging.info(f"Effective batch size: {config.batch_size * config.grad_accum_steps}")
    logging.info(f"Learning rate: {config.lr}")
    logging.info(f"LoRA: r={config.lora_r}, alpha={config.lora_alpha}")
    logging.info(f"LoRA target: {config.lora_target_modules}")
    
    # Load tokenizer
    logging.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(config.student_model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load student model with LoRA
    logging.info("Loading student model (Qwen 3.6-27B) with LoRA...")
    model = AutoModelForCausalLM.from_pretrained(
        config.student_model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",  # Let transformers handle device placement
        trust_remote_code=True,
    )
    
    # Enable gradient checkpointing
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    
    # Apply LoRA
    logging.info("Applying LoRA...")
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=config.lora_target_modules,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Load teacher model (CPU)
    teacher_state = load_teacher_model(config.teacher_model_path, device="cpu")
    
    # Load SAEs (CPU)
    saes = {}
    for layer_idx in config.sae_layers:
        sae = load_sae(config.sae_dir, layer_idx, device="cpu")
        if sae is not None:
            saes[layer_idx] = sae
    
    # Dataset
    logging.info("Loading streaming dataset...")
    dataset = StreamingReasoningDataset(config, tokenizer)
    dataloader = DataLoader(
        dataset,
        batch_size=config.batch_size,
        num_workers=0,  # Must be 0 for iterable dataset
    )
    
    # Optimizer — only LoRA parameters
    logging.info("Creating AdamW optimizer...")
    optimizer = torch.optim.AdamW(
        model.parameters(),  # Only LoRA params are trainable
        lr=config.lr,
        betas=(config.beta1, config.beta2),
        weight_decay=config.weight_decay,
    )
    
    # Learning rate schedule
    total_steps = config.max_steps
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=config.warmup_steps,
        num_training_steps=total_steps,
    )
    
    # Training state
    global_step = 0
    accumulated_loss = 0.0
    
    # Checkpoint directory
    os.makedirs(config.checkpoint_dir, exist_ok=True)
    
    logging.info("=" * 70)
    logging.info("STARTING TRAINING")
    logging.info("=" * 70)
    
    model.train()
    
    for batch in dataloader:
        if global_step >= config.max_steps:
            break
        
        # Move batch to device
        input_ids = batch['input_ids'].to(device)
        labels = batch['labels'].to(device)
        
        # Forward pass
        outputs = model(input_ids=input_ids, labels=labels)
        loss = outputs.loss / config.grad_accum_steps
        
        # Backward pass
        loss.backward()
        
        accumulated_loss += loss.item()
        
        # Gradient accumulation step
        if (global_step + 1) % config.grad_accum_steps == 0:
            # Clip gradients
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
            
            # Optimizer step
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            
            # Logging
            current_lr = scheduler.get_last_lr()[0]
            avg_loss = accumulated_loss
            
            if global_step % 10 == 0:
                logging.info(
                    f"Step {global_step}/{config.max_steps} | "
                    f"Loss: {avg_loss:.4f} | LR: {current_lr:.2e}"
                )
            
            accumulated_loss = 0.0
            
            # Checkpoint
            if global_step % config.save_every == 0 and global_step > 0:
                checkpoint_path = os.path.join(
                    config.checkpoint_dir,
                    f"checkpoint_step_{global_step}.pt"
                )
                model.save_pretrained(checkpoint_path)
                logging.info(f"Saved checkpoint: {checkpoint_path}")
        
        global_step += 1
        
        # Clear cache periodically
        if global_step % 50 == 0:
            torch.cuda.empty_cache()
    
    # Final save
    final_path = os.path.join(config.checkpoint_dir, "final_model")
    model.save_pretrained(final_path)
    logging.info(f"Training complete! Final model saved to {final_path}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    config = TrainConfig()
    
    # Override from env if needed
    if os.environ.get("MAX_STEPS"):
        config.max_steps = int(os.environ.get("MAX_STEPS"))
    
    train(config)
