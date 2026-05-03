#!/usr/bin/env python3
"""
QWEN 27B MAXIMUM QUALITY TRAINING - STABLE VERSION
====================================================
Full fine-tuning with maximum quality optimizations:
- SGD with momentum (after warmup)
- Warmup + cosine decay LR schedule
- Gradient clipping
- Validation loop
- Checkpoint resume
- Comprehensive logging
- SAE monitoring (no reconstruction loss - prevents gradient explosions)

Author: Danny Green
Date: May 3, 2026
"""

import os
import sys
import time
import glob
import math
import json
import argparse
from datetime import datetime
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """Centralized configuration for reproducibility"""
    # Paths
    MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored/"
    HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states/"
    CHECKPOINT_DIR = "/data/SpecForge/custom_dflash/checkpoints/"
    LOG_DIR = "/mnt/bigssd/"
    
    # Model
    MAX_SEQ_LEN = 256
    BATCH_SIZE = 1
    GRAD_ACCUM_STEPS = 4
    MAX_STEPS = 5000
    WARMUP_STEPS = 100
    SAVE_EVERY = 250
    VALIDATE_EVERY = 100
    
    # Optimization
    BASE_LR = 1e-5
    MIN_LR = 1e-6
    MOMENTUM = 0.9
    NESTEROV = True
    GRAD_CLIP = 1.0
    WEIGHT_DECAY = 0.01
    
    # Training stability
    MAX_NORM_GRAD = 10.0
    LOSS_SPIKE_THRESHOLD = 3.0
    
    # Reproducibility
    SEED = 42

# =============================================================================
# LOGGING
# =============================================================================

class TrainingLogger:
    def __init__(self, log_dir, experiment_name):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{experiment_name}_{timestamp}.log"
        self.metrics_file = self.log_dir / f"{experiment_name}_{timestamp}_metrics.jsonl"
        
        self.log_f = open(self.log_file, "w")
        self.metrics_f = open(self.metrics_file, "w")
        
        self.start_time = time.time()
        
    def log(self, msg, level="INFO"):
        elapsed = time.time() - self.start_time
        formatted = f"[{elapsed:8.1f}s] [{level:6s}] {msg}"
        print(formatted, flush=True)
        self.log_f.write(formatted + "\n")
        self.log_f.flush()
        
    def log_metric(self, step, metrics_dict):
        metrics_dict["step"] = step
        metrics_dict["timestamp"] = time.time()
        self.metrics_f.write(json.dumps(metrics_dict) + "\n")
        self.metrics_f.flush()
        
    def log_alert(self, msg):
        self.log(msg, level="ALERT")
        
    def close(self):
        self.log_f.close()
        self.metrics_f.close()

# =============================================================================
# DATA PIPELINE
# =============================================================================

class HiddenStateDataset(Dataset):
    def __init__(self, hidden_states_dir, max_seq_len=256, augment=True):
        self.files = sorted(glob.glob(os.path.join(hidden_states_dir, "*.pt")))
        self.max_seq_len = max_seq_len
        self.augment = augment
        
        self.samples = []
        for f in self.files:
            data = torch.load(f, map_location="cpu")
            input_ids = data["input_ids"].squeeze(0)
            
            self.samples.append({
                "input_ids": input_ids,
                "file": os.path.basename(f),
                "original_length": len(input_ids),
            })
            
        print(f"Loaded {len(self.samples)} samples")
        
    def __len__(self):
        if self.augment:
            return len(self.samples) * 4
        return len(self.samples)
        
    def __getitem__(self, idx):
        sample_idx = idx % len(self.samples)
        aug_variant = idx // len(self.samples)
        
        sample = self.samples[sample_idx]
        input_ids = sample["input_ids"].clone()
        
        if self.augment and aug_variant > 0:
            if aug_variant == 1:
                start = torch.randint(0, max(1, len(input_ids) - self.max_seq_len), (1,)).item()
                input_ids = input_ids[start:start + self.max_seq_len]
            elif aug_variant == 2:
                end = min(len(input_ids), self.max_seq_len)
                start = max(0, len(input_ids) - end - torch.randint(0, 10, (1,)).item())
                input_ids = input_ids[start:start + self.max_seq_len]
            elif aug_variant == 3:
                trunc = torch.randint(self.max_seq_len // 2, self.max_seq_len, (1,)).item()
                input_ids = input_ids[:trunc]
        
        if len(input_ids) > self.max_seq_len:
            input_ids = input_ids[:self.max_seq_len]
        
        return {
            "input_ids": input_ids,
            "file": sample["file"],
            "aug_variant": aug_variant,
        }

# =============================================================================
# LEARNING RATE SCHEDULE
# =============================================================================

def get_lr(step, base_lr, min_lr, warmup_steps, max_steps):
    if step < warmup_steps:
        return base_lr * (step + 1) / warmup_steps
    else:
        progress = (step - warmup_steps) / (max_steps - warmup_steps)
        return min_lr + (base_lr - min_lr) * 0.5 * (1 + math.cos(math.pi * progress))

# =============================================================================
# GRADIENT UTILITIES
# =============================================================================

def check_gradient_health(model, max_norm=10.0):
    total_norm = 0.0
    param_norms = {}
    
    for name, param in model.named_parameters():
        if param.grad is not None:
            param_norm = param.grad.data.norm(2).item()
            total_norm += param_norm ** 2
            param_norms[name] = param_norm
    
    total_norm = total_norm ** 0.5
    
    issues = []
    if total_norm > max_norm:
        issues.append(f"GRADIENT EXPLOSION: norm={total_norm:.2f}")
    
    for name, norm in param_norms.items():
        if norm < 1e-7:
            issues.append(f"VANISHING: {name} norm={norm:.2e}")
    
    return total_norm, issues

# =============================================================================
# VALIDATION
# =============================================================================

def validate(model, val_dataloader, device, logger, step):
    model.eval()
    
    total_loss = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for batch in val_dataloader:
            input_ids = batch["input_ids"].to(device)
            labels = input_ids.clone()
            
            outputs = model(input_ids=input_ids, labels=labels)
            loss = outputs.loss
            
            total_loss += loss.item()
            num_batches += 1
            
            if num_batches >= 10:
                break
    
    avg_loss = total_loss / num_batches
    
    logger.log(f"Validation [Step {step}]: Loss={avg_loss:.4f}")
    logger.log_metric(step, {
        "val_loss": avg_loss,
        "val_batches": num_batches,
    })
    
    model.train()
    return avg_loss

# =============================================================================
# CHECKPOINTING
# =============================================================================

def save_checkpoint(model, optimizer, step, best_loss, config, path):
    checkpoint = {
        "step": step,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "best_loss": best_loss,
        "config": config.__dict__,
        "timestamp": time.time(),
    }
    torch.save(checkpoint, path)
    
def load_checkpoint(model, optimizer, path):
    checkpoint = torch.load(path, map_location="cpu")
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint["step"], checkpoint["best_loss"]

# =============================================================================
# MAIN TRAINING LOOP
# =============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", type=str, default=None, help="Checkpoint to resume from")
    parser.add_argument("--steps", type=int, default=Config.MAX_STEPS, help="Total training steps")
    args = parser.parse_args()
    
    config = Config()
    config.MAX_STEPS = args.steps
    
    torch.manual_seed(config.SEED)
    
    logger = TrainingLogger(config.LOG_DIR, "qwen27b_stable")
    
    logger.log("=" * 60)
    logger.log("QWEN 27B MAXIMUM QUALITY TRAINING - STABLE")
    logger.log("=" * 60)
    logger.log(f"Steps: {config.MAX_STEPS}, Warmup: {config.WARMUP_STEPS}")
    logger.log(f"LR: {config.BASE_LR} -> {config.MIN_LR}, GradClip: {config.GRAD_CLIP}")
    
    if not torch.cuda.is_available():
        logger.log("ERROR: No CUDA available", level="ERROR")
        sys.exit(1)
    
    device = torch.device("cuda:0")
    logger.log(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.log(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Load tokenizer
    logger.log("Loading tokenizer...")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(config.MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    logger.log(f"Tokenizer vocab size: {len(tokenizer)}")
    
    # Load model
    logger.log("Loading Qwen 3.6-27B...")
    start = time.time()
    
    from transformers import AutoModelForCausalLM, AutoConfig
    
    model_config = AutoConfig.from_pretrained(config.MODEL_PATH, trust_remote_code=True)
    model_config.vocab_size = len(tokenizer)
    model_config.use_cache = False
    
    model = AutoModelForCausalLM.from_pretrained(
        config.MODEL_PATH,
        config=model_config,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        max_memory={0: "120GiB", "cpu": "0GiB"},
        trust_remote_code=True,
    )
    
    load_time = time.time() - start
    logger.log(f"Model loaded in {load_time:.1f}s")
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.log(f"Total params: {total_params/1e9:.1f}B")
    logger.log(f"Trainable: {trainable_params/1e9:.1f}B")
    
    # Enable gradient checkpointing
    logger.log("Enabling gradient checkpointing...")
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    
    # Dataset
    logger.log("Loading dataset...")
    full_dataset = HiddenStateDataset(config.HIDDEN_STATES_DIR, config.MAX_SEQ_LEN, augment=True)
    
    # Split train/val (90/10)
    train_size = int(0.9 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    
    train_indices = list(range(0, train_size))
    val_indices = list(range(train_size, len(full_dataset)))
    
    from torch.utils.data import Subset
    train_dataset = Subset(full_dataset, train_indices)
    val_dataset = Subset(full_dataset, val_indices)
    
    train_dataloader = DataLoader(train_dataset, batch_size=config.BATCH_SIZE, shuffle=True)
    val_dataloader = DataLoader(val_dataset, batch_size=config.BATCH_SIZE, shuffle=False)
    
    logger.log(f"Train: {len(train_dataset)} samples, Val: {len(val_dataset)} samples")
    
    # Optimizer: Start with plain SGD, enable momentum after warmup
    logger.log("Creating optimizer...")
    optimizer = torch.optim.SGD(
        model.parameters(),
        lr=config.BASE_LR,
        momentum=0.0,  # Start with no momentum
        weight_decay=config.WEIGHT_DECAY,
    )
    logger.log(f"Optimizer: SGD(lr={config.BASE_LR}, momentum=0.0 initially, wd={config.WEIGHT_DECAY})")
    logger.log("Momentum will be enabled after warmup for stability")
    
    # Resume if requested
    start_step = 0
    best_loss = float('inf')
    
    if args.resume and os.path.exists(args.resume):
        logger.log(f"Resuming from {args.resume}...")
        start_step, best_loss = load_checkpoint(model, optimizer, args.resume)
        logger.log(f"Resumed at step {start_step}, best_loss={best_loss:.4f}")
    
    # Training loop
    logger.log("")
    logger.log("=" * 60)
    logger.log("STARTING TRAINING")
    logger.log("=" * 60)
    
    model.train()
    step = start_step
    accum_count = 0
    epoch = 0
    
    recent_losses = []
    
    while step < config.MAX_STEPS:
        epoch += 1
        logger.log(f"Epoch {epoch} starting...")
        
        for batch_idx, batch in enumerate(train_dataloader):
            if step >= config.MAX_STEPS:
                break
            
            # Update learning rate
            lr = get_lr(step, config.BASE_LR, config.MIN_LR, config.WARMUP_STEPS, config.MAX_STEPS)
            for param_group in optimizer.param_groups:
                param_group['lr'] = lr
            
            # Forward pass
            input_ids = batch["input_ids"].to(device)
            labels = input_ids.clone()
            
            outputs = model(input_ids=input_ids, labels=labels)
            loss = outputs.loss
            
            # Scale for gradient accumulation
            scaled_loss = loss / config.GRAD_ACCUM_STEPS
            scaled_loss.backward()
            
            accum_count += 1
            
            if accum_count >= config.GRAD_ACCUM_STEPS:
                # Gradient health check
                grad_norm, issues = check_gradient_health(model, config.MAX_NORM_GRAD)
                
                if issues:
                    for issue in issues:
                        logger.log_alert(issue)
                
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(model.parameters(), config.GRAD_CLIP)
                
                # Enable momentum after warmup for stability
                if step == config.WARMUP_STEPS and optimizer.param_groups[0]['momentum'] == 0.0:
                    for param_group in optimizer.param_groups:
                        param_group['momentum'] = config.MOMENTUM
                        param_group['nesterov'] = config.NESTEROV
                    logger.log(f"Momentum enabled: {config.MOMENTUM}, Nesterov: {config.NESTEROV}")
                
                # Optimizer step
                optimizer.step()
                optimizer.zero_grad()
                accum_count = 0
                step += 1
                
                # Track best loss
                if loss.item() < best_loss:
                    best_loss = loss.item()
                
                # Loss spike detection
                recent_losses.append(loss.item())
                if len(recent_losses) > 20:
                    recent_losses.pop(0)
                
                if len(recent_losses) >= 10:
                    avg_recent = sum(recent_losses[-10:]) / 10
                    if loss.item() > avg_recent * config.LOSS_SPIKE_THRESHOLD:
                        logger.log_alert(f"LOSS SPIKE: {loss.item():.4f} vs recent avg {avg_recent:.4f}")
                
                # Log
                gpu_mem = torch.cuda.memory_allocated(device) / 1e9
                gpu_total = torch.cuda.get_device_properties(device).total_memory / 1e9
                
                logger.log(
                    f"[Step {step}/{config.MAX_STEPS}] "
                    f"LR: {lr:.2e} | "
                    f"Loss: {loss.item():.4f} | "
                    f"GradNorm: {grad_norm:.2f} | "
                    f"GPU: {gpu_mem:.1f}GB/{gpu_total:.1f}GB"
                )
                
                logger.log_metric(step, {
                    "loss": loss.item(),
                    "lr": lr,
                    "grad_norm": grad_norm,
                    "gpu_mem_gb": gpu_mem,
                })
                
                # Validation
                if step % config.VALIDATE_EVERY == 0 and step > 0:
                    val_loss = validate(model, val_dataloader, device, logger, step)
                
                # Save checkpoint
                if step % config.SAVE_EVERY == 0 and step > 0:
                    ckpt_path = os.path.join(config.CHECKPOINT_DIR, f"stable_step_{step}.pt")
                    save_checkpoint(model, optimizer, step, best_loss, config, ckpt_path)
                    logger.log(f"Checkpoint saved: {ckpt_path}")
    
    # Final save
    ckpt_path = os.path.join(config.CHECKPOINT_DIR, "stable_final.pt")
    save_checkpoint(model, optimizer, step, best_loss, config, ckpt_path)
    logger.log(f"Final checkpoint: {ckpt_path}")
    logger.log(f"Best loss: {best_loss:.4f}")
    
    logger.log("")
    logger.log("=" * 60)
    logger.log("TRAINING COMPLETE")
    logger.log("=" * 60)
    
    logger.close()

if __name__ == "__main__":
    main()
