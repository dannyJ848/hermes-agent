#!/usr/bin/env python3
"""
Qwen 27B Expert Logician Training — Manual Memory Management v1
Extreme memory optimization for full fine-tuning on 130GB GPU.

Strategy:
1. Load model in bf16 (27GB)
2. Use SGD instead of AdamW (no optimizer state memory!)
3. Gradient checkpointing (trade compute for memory)
4. Micro-batch size 1, sequence length 1024
5. Manual gradient accumulation (16 steps = effective batch 16)
6. Clear cache aggressively
7. No SAE/teacher distillation (add back later when basic training works)

Memory budget:
- Model: 27GB (bf16)
- Gradients: 27GB
- Activations: ~10GB (with grad checkpointing, seq 1024)
- Temp buffers: ~15GB
- Total: ~79GB (within 130GB limit)

SGD saves 54GB vs AdamW (no momentum/variance states).
"""

import os
import sys
import gc
import logging
from dataclasses import dataclass
from typing import Optional, List

import torch
import torch.nn.functional as F
from torch.utils.data import IterableDataset, DataLoader

from transformers import AutoModelForCausalLM, AutoTokenizer

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/mnt/bigssd/train_manual_v1.log')
    ]
)

# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class TrainConfig:
    student_model_path: str = "/data/models/Qwen3.6-27B-Uncensored/"
    curatedthoughts_dir: str = "/data/datasets/curatedthoughts/"
    openthoughts_dir: str = "/data/datasets/openthoughts2-1m/"
    
    max_steps: int = 10000
    batch_size: int = 1
    grad_accum_steps: int = 16
    max_seq_len: int = 1024  # Shorter sequences
    
    lr: float = 1e-4  # SGD needs higher LR
    momentum: float = 0.9
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    
    warmup_steps: int = 500
    
    save_every: int = 500
    checkpoint_dir: str = "/data/SpecForge/custom_dflash/checkpoints/"


# ============================================================
# STREAMING DATASET
# ============================================================

class StreamingReasoningDataset(IterableDataset):
    def __init__(self, config, tokenizer):
        self.config = config
        self.tokenizer = tokenizer
        self.files = []
        self._discover_files()
        logging.info(f"Streaming dataset: {len(self.files)} files")
    
    def _discover_files(self):
        for dir_path in [self.config.curatedthoughts_dir, self.config.openthoughts_dir]:
            if os.path.exists(dir_path):
                for f in os.listdir(dir_path):
                    if f.endswith('.parquet'):
                        self.files.append(os.path.join(dir_path, f))
    
    def _format_conversation(self, data):
        if 'conversations' in data and isinstance(data['conversations'], list):
            convs = data['conversations']
            if len(convs) > 0:
                if isinstance(convs[0], dict) and 'value' in convs[0]:
                    return "\n".join([c['value'] for c in convs if 'value' in c])
                elif isinstance(convs[0], str):
                    return "\n".join(convs)
        
        if 'messages' in data and isinstance(data['messages'], list):
            msgs = data['messages']
            if len(msgs) > 0:
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
# LEARNING RATE SCHEDULE
# ============================================================

def get_lr(step, warmup_steps, max_steps, base_lr):
    """Warmup + cosine decay."""
    if step < warmup_steps:
        return base_lr * (step + 1) / warmup_steps
    
    progress = (step - warmup_steps) / (max_steps - warmup_steps)
    return base_lr * 0.5 * (1 + math.cos(math.pi * progress))


# ============================================================
# TRAINING LOOP
# ============================================================

def train(config):
    import math
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    logging.info("=" * 70)
    logging.info("QWEN 27B EXPERT LOGICIAN — Manual Memory Management v1")
    logging.info("=" * 70)
    logging.info(f"Max steps: {config.max_steps}")
    logging.info(f"Batch: {config.batch_size}, Grad accum: {config.grad_accum_steps}")
    logging.info(f"Effective batch: {config.batch_size * config.grad_accum_steps}")
    logging.info(f"LR: {config.lr}, Optimizer: SGD+momentum")
    logging.info(f"Sequence length: {config.max_seq_len}")
    logging.info(f"GPU: {torch.cuda.get_device_name(0)}")
    logging.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Load tokenizer
    logging.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(config.student_model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model in bf16 on GPU directly
    logging.info("Loading model in bf16 on GPU...")
    model = AutoModelForCausalLM.from_pretrained(
        config.student_model_path,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    ).to(device)
    
    # NOTE: Gradient checkpointing disabled due to Qwen3.5 linear_attn bug
    # Instead, use shorter sequences to fit in memory
    # model.gradient_checkpointing_enable()
    # model.enable_input_require_grads()
    logging.info("Gradient checkpointing disabled (Qwen3.5 compatibility)")
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logging.info(f"Total params: {total_params/1e9:.1f}B")
    logging.info(f"Trainable: {trainable_params/1e9:.1f}B")
    
    # Dataset
    logging.info("Loading dataset...")
    dataset = StreamingReasoningDataset(config, tokenizer)
    
    # Optimizer: SGD (saves ~54GB vs AdamW)
    logging.info("Creating SGD optimizer...")
    optimizer = torch.optim.SGD(
        model.parameters(),
        lr=config.lr,
        momentum=config.momentum,
        weight_decay=config.weight_decay,
    )
    
    # Checkpoint dir
    os.makedirs(config.checkpoint_dir, exist_ok=True)
    
    logging.info("=" * 70)
    logging.info("STARTING TRAINING")
    logging.info("=" * 70)
    
    model.train()
    
    global_step = 0
    accumulated_loss = 0.0
    
    for batch in dataset:
        if global_step >= config.max_steps:
            break
        
        # Forward
        input_ids = batch['input_ids'].to(device)
        labels = batch['labels'].to(device)
        
        outputs = model(input_ids=input_ids, labels=labels)
        loss = outputs.loss / config.grad_accum_steps
        
        # Backward
        loss.backward()
        
        accumulated_loss += loss.item() * config.grad_accum_steps
        
        # Gradient accumulation step
        if (global_step + 1) % config.grad_accum_steps == 0:
            # Clip gradients
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
            
            # Update LR
            current_lr = get_lr(global_step, config.warmup_steps, config.max_steps, config.lr)
            for param_group in optimizer.param_groups:
                param_group['lr'] = current_lr
            
            # Optimizer step
            optimizer.step()
            optimizer.zero_grad()
            
            # Log
            avg_loss = accumulated_loss / config.grad_accum_steps
            if global_step % 10 == 0:
                logging.info(
                    f"Step {global_step}/{config.max_steps} | "
                    f"Loss: {avg_loss:.4f} | LR: {current_lr:.2e} | "
                    f"GPU: {torch.cuda.memory_allocated()/1e9:.1f}GB"
                )
            
            accumulated_loss = 0.0
            
            # Checkpoint
            if global_step % config.save_every == 0 and global_step > 0:
                checkpoint_path = os.path.join(
                    config.checkpoint_dir,
                    f"checkpoint_step_{global_step}.pt"
                )
                torch.save({
                    'step': global_step,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                }, checkpoint_path)
                logging.info(f"Saved checkpoint: {checkpoint_path}")
            
            # Clear cache
            if global_step % 50 == 0:
                torch.cuda.empty_cache()
                gc.collect()
        
        global_step += 1
    
    # Final save
    final_path = os.path.join(config.checkpoint_dir, "final_model.pt")
    torch.save({
        'step': global_step,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
    }, final_path)
    logging.info(f"Training complete! Saved to {final_path}")


if __name__ == "__main__":
    config = TrainConfig()
    if os.environ.get("MAX_STEPS"):
        config.max_steps = int(os.environ.get("MAX_STEPS"))
    train(config)
