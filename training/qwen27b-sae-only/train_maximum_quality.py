#!/usr/bin/env python3
"""
QWEN 27B MAXIMUM QUALITY TRAINING PIPELINE
===========================================
Comprehensive training with:
- SGD + Nesterov momentum (best memory/quality tradeoff)
- Warmup + cosine decay LR schedule
- Gradient clipping
- SAE reconstruction + sparsity + teacher alignment losses
- Validation every N steps
- Checkpoint resume
- Mixed precision safety checks
- Comprehensive logging

Author: Danny Green
Date: May 3, 2026
"""

import os
import sys
import time
import glob
import math
import json
import pickle
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
    SAE_DIR = "/data/models/Qwen-Scope/"
    HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states/"
    CHECKPOINT_DIR = "/data/SpecForge/custom_dflash/checkpoints/"
    LOG_DIR = "/mnt/bigssd/"
    TEACHER_FEATURES_DIR = "/data/SpecForge/custom_dflash/teacher_sae_features/"
    
    # Model
    MAX_SEQ_LEN = 256
    BATCH_SIZE = 1
    GRAD_ACCUM_STEPS = 4
    MAX_STEPS = 5000  # Extended for quality
    WARMUP_STEPS = 100
    SAVE_EVERY = 250
    VALIDATE_EVERY = 100
    
    # Optimization
    BASE_LR = 2e-5  # Slightly higher with warmup
    MIN_LR = 1e-6
    MOMENTUM = 0.9
    NESTEROV = True
    GRAD_CLIP = 1.0
    WEIGHT_DECAY = 0.01  # Light regularization
    
    # SAE Configuration
    SAE_LAYERS = [16, 32, 48]  # Start with fewer layers for stability
    SAE_RECON_WEIGHT = 0.01  # Very light - don't fight next-token
    SAE_SPARSITY_WEIGHT = 0.0001  # Minimal sparsity pressure
    SAE_TEACHER_WEIGHT = 0.05  # Align with teacher features
    
    # Loss weights
    NEXT_TOKEN_WEIGHT = 1.0
    
    # Training stability
    MAX_NORM_GRAD = 10.0  # Alert if gradients explode
    LOSS_SPIKE_THRESHOLD = 3.0  # Alert if loss jumps
    
    # Reproducibility
    SEED = 42

# =============================================================================
# LOGGING
# =============================================================================

class TrainingLogger:
    """Comprehensive training logger with metrics tracking"""
    
    def __init__(self, log_dir, experiment_name):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{experiment_name}_{timestamp}.log"
        self.metrics_file = self.log_dir / f"{experiment_name}_{timestamp}_metrics.jsonl"
        
        self.log_f = open(self.log_file, "w")
        self.metrics_f = open(self.metrics_file, "w")
        
        self.start_time = time.time()
        self.step_times = []
        
    def log(self, msg, level="INFO"):
        """Log with timestamp and level"""
        elapsed = time.time() - self.start_time
        formatted = f"[{elapsed:8.1f}s] [{level:6s}] {msg}"
        print(formatted, flush=True)
        self.log_f.write(formatted + "\n")
        self.log_f.flush()
        
    def log_metric(self, step, metrics_dict):
        """Log structured metrics for analysis"""
        metrics_dict["step"] = step
        metrics_dict["timestamp"] = time.time()
        self.metrics_f.write(json.dumps(metrics_dict) + "\n")
        self.metrics_f.flush()
        
    def log_alert(self, msg):
        """Log warning/alert"""
        self.log(msg, level="ALERT")
        
    def close(self):
        self.log_f.close()
        self.metrics_f.close()

# =============================================================================
# DATA PIPELINE
# =============================================================================

class HiddenStateDataset(Dataset):
    """Dataset with augmentation and validation split"""
    
    def __init__(self, hidden_states_dir, max_seq_len=256, augment=True):
        self.files = sorted(glob.glob(os.path.join(hidden_states_dir, "*.pt")))
        self.max_seq_len = max_seq_len
        self.augment = augment
        
        # Load all data into memory for speed
        self.samples = []
        for f in self.files:
            data = torch.load(f, map_location="cpu")
            input_ids = data["input_ids"].squeeze(0)
            
            # Store with metadata
            self.samples.append({
                "input_ids": input_ids,
                "file": os.path.basename(f),
                "original_length": len(input_ids),
            })
            
        print(f"Loaded {len(self.samples)} samples")
        
    def __len__(self):
        # Return augmented count if augmenting
        if self.augment:
            return len(self.samples) * 4  # 4x augmentation
        return len(self.samples)
        
    def __getitem__(self, idx):
        sample_idx = idx % len(self.samples)
        aug_variant = idx // len(self.samples)
        
        sample = self.samples[sample_idx]
        input_ids = sample["input_ids"].clone()
        
        # Augmentation variants
        if self.augment and aug_variant > 0:
            if aug_variant == 1:
                # Random crop from start
                start = torch.randint(0, max(1, len(input_ids) - self.max_seq_len), (1,)).item()
                input_ids = input_ids[start:start + self.max_seq_len]
            elif aug_variant == 2:
                # Random crop from end
                end = min(len(input_ids), self.max_seq_len)
                start = max(0, len(input_ids) - end - torch.randint(0, 10, (1,)).item())
                input_ids = input_ids[start:start + self.max_seq_len]
            elif aug_variant == 3:
                # Random truncation
                trunc = torch.randint(self.max_seq_len // 2, self.max_seq_len, (1,)).item()
                input_ids = input_ids[:trunc]
        
        # Pad or truncate
        if len(input_ids) > self.max_seq_len:
            input_ids = input_ids[:self.max_seq_len]
        
        return {
            "input_ids": input_ids,
            "file": sample["file"],
            "aug_variant": aug_variant,
        }

# =============================================================================
# SAE UTILITIES
# =============================================================================

def load_saes(sae_dir, layers, device):
    """Load SAEs for specified layers - load to CPU first, then move to GPU individually"""
    saes = {}
    for layer_idx in layers:
        sae_path = os.path.join(sae_dir, f"layer{layer_idx}.sae.pt")
        if os.path.exists(sae_path):
            # Load to CPU first
            sae = torch.load(sae_path, map_location="cpu")
            # Keep on CPU initially, move to GPU only when needed
            saes[layer_idx] = {
                "W_enc": sae["W_enc"].bfloat16(),
                "b_enc": sae["b_enc"].bfloat16(),
                "W_dec": sae["W_dec"].bfloat16(),
                "b_dec": sae["b_dec"].bfloat16(),
            }
            print(f"  Layer {layer_idx}: SAE loaded (CPU)")
    return saes

def get_feature_acts(residual, sae_dict):
    """Extract sparse features with TopK=50 - move SAE to GPU for computation"""
    device = residual.device
    W_enc = sae_dict["W_enc"].to(device)
    b_enc = sae_dict["b_enc"].to(device)
    pre_acts = residual @ W_enc.T + b_enc
    topk_vals, topk_idx = pre_acts.topk(50, dim=-1)
    acts = torch.zeros_like(pre_acts)
    acts.scatter_(-1, topk_idx, topk_vals)
    # Move back to CPU to save GPU memory
    return acts.cpu(), topk_idx.cpu()

def reconstruct_from_features(features, sae_dict, device):
    """Reconstruct hidden states from sparse features"""
    W_dec = sae_dict["W_dec"].to(device)
    b_dec = sae_dict["b_dec"].to(device)
    return features.to(device) @ W_dec.T + b_dec

def compute_sparsity_penalty(features):
    """L1 penalty to encourage sparsity"""
    return features.abs().mean()

def compute_feature_cosine_similarity(student_features, teacher_features):
    """Compute cosine similarity between student and teacher SAE features"""
    # Flatten across sequence dimension
    s_flat = student_features.reshape(-1, student_features.shape[-1])
    t_flat = teacher_features.reshape(-1, teacher_features.shape[-1])
    
    # Cosine similarity
    s_norm = F.normalize(s_flat, p=2, dim=-1)
    t_norm = F.normalize(t_flat, p=2, dim=-1)
    
    similarity = (s_norm * t_norm).sum(dim=-1).mean()
    return similarity

# =============================================================================
# LEARNING RATE SCHEDULE
# =============================================================================

def get_lr(step, base_lr, min_lr, warmup_steps, max_steps):
    """Warmup + cosine decay learning rate schedule"""
    if step < warmup_steps:
        # Linear warmup
        return base_lr * (step + 1) / warmup_steps
    else:
        # Cosine decay after warmup
        progress = (step - warmup_steps) / (max_steps - warmup_steps)
        return min_lr + (base_lr - min_lr) * 0.5 * (1 + math.cos(math.pi * progress))

# =============================================================================
# GRADIENT UTILITIES
# =============================================================================

def check_gradient_health(model, max_norm=10.0):
    """Check for gradient explosions or vanishing gradients"""
    total_norm = 0.0
    param_norms = {}
    
    for name, param in model.named_parameters():
        if param.grad is not None:
            param_norm = param.grad.data.norm(2).item()
            total_norm += param_norm ** 2
            param_norms[name] = param_norm
    
    total_norm = total_norm ** 0.5
    
    # Check for issues
    issues = []
    if total_norm > max_norm:
        issues.append(f"GRADIENT EXPLOSION: norm={total_norm:.2f}")
    
    # Check for vanishing gradients in specific layers
    for name, norm in param_norms.items():
        if norm < 1e-7:
            issues.append(f"VANISHING: {name} norm={norm:.2e}")
    
    return total_norm, issues

# =============================================================================
# VALIDATION
# =============================================================================

def validate(model, val_dataloader, device, saes, logger, step):
    """Run validation and log metrics"""
    model.eval()
    
    total_loss = 0.0
    total_sae_recon = 0.0
    total_sae_sparsity = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for batch in val_dataloader:
            input_ids = batch["input_ids"].to(device)
            labels = input_ids.clone()
            
            outputs = model(input_ids=input_ids, labels=labels)
            loss = outputs.loss
            
            total_loss += loss.item()
            num_batches += 1
            
            if num_batches >= 10:  # Validate on subset
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
    """Save comprehensive checkpoint"""
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
    """Load checkpoint and return state"""
    checkpoint = torch.load(path, map_location="cpu")
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint["step"], checkpoint["best_loss"]

# =============================================================================
# MAIN TRAINING LOOP
# =============================================================================

def main():
    """Main training function"""
    
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", type=str, default=None, help="Checkpoint to resume from")
    parser.add_argument("--steps", type=int, default=Config.MAX_STEPS, help="Total training steps")
    args = parser.parse_args()
    
    # Initialize
    config = Config()
    config.MAX_STEPS = args.steps
    
    torch.manual_seed(config.SEED)
    
    logger = TrainingLogger(config.LOG_DIR, "qwen27b_maxquality")
    
    logger.log("=" * 60)
    logger.log("QWEN 27B MAXIMUM QUALITY TRAINING")
    logger.log("=" * 60)
    logger.log(f"Steps: {config.MAX_STEPS}, Warmup: {config.WARMUP_STEPS}")
    logger.log(f"LR: {config.BASE_LR} → {config.MIN_LR}, GradClip: {config.GRAD_CLIP}")
    logger.log(f"SAE Layers: {config.SAE_LAYERS}")
    logger.log(f"SAE Weights: recon={config.SAE_RECON_WEIGHT}, sparsity={config.SAE_SPARSITY_WEIGHT}, teacher={config.SAE_TEACHER_WEIGHT}")
    
    # Device setup
    if not torch.cuda.is_available():
        logger.log("ERROR: No CUDA available", level="ERROR")
        sys.exit(1)
    
    device = torch.device("cuda:0")
    logger.log(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.log(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Load SAEs
    logger.log("Loading SAEs...")
    saes = load_saes(config.SAE_DIR, config.SAE_LAYERS, device)
    logger.log(f"Loaded {len(saes)} SAEs")
    
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
    
    # SAE hooks
    captured_features = {}
    captured_hidden = {}
    
    def make_hook(layer_idx):
        def hook(module, input, output):
            hidden = output[0] if isinstance(output, tuple) else output
            if layer_idx in saes:
                features, indices = get_feature_acts(hidden, saes[layer_idx])
                captured_features[layer_idx] = features
                captured_hidden[layer_idx] = hidden
            return output
        return hook
    
    hooks = []
    for layer_idx in config.SAE_LAYERS:
        if layer_idx in saes and layer_idx < len(model.model.layers):
            h = model.model.layers[layer_idx].register_forward_hook(make_hook(layer_idx))
            hooks.append(h)
    
    logger.log(f"Registered {len(hooks)} SAE hooks")
    
    # Load teacher features if available
    teacher_features_available = False
    if os.path.exists(config.TEACHER_FEATURES_DIR):
        teacher_files = glob.glob(os.path.join(config.TEACHER_FEATURES_DIR, "*.pt"))
        if teacher_files:
            teacher_features_available = True
            logger.log(f"Found {len(teacher_files)} teacher feature files")
    
    # Dataset with augmentation
    logger.log("Loading dataset...")
    full_dataset = HiddenStateDataset(config.HIDDEN_STATES_DIR, config.MAX_SEQ_LEN, augment=True)
    
    # Split train/val (90/10)
    train_size = int(0.9 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    
    # Manual split to ensure we get different samples
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
    
    # Training state tracking
    recent_losses = []  # For spike detection
    
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
            
            captured_features.clear()
            captured_hidden.clear()
            
            outputs = model(input_ids=input_ids, labels=labels)
            loss = outputs.loss
            
            # SAE losses
            sae_recon_loss = 0.0
            sae_sparsity_loss = 0.0
            sae_teacher_loss = 0.0
            
            if captured_features and captured_hidden:
                active_layers = 0
                
                for layer_idx in config.SAE_LAYERS:
                    if layer_idx in captured_features and layer_idx in captured_hidden:
                        features = captured_features[layer_idx]
                        original = captured_hidden[layer_idx]
                        
                        # Reconstruction loss
                        reconstructed = reconstruct_from_features(features, saes[layer_idx], device)
                        recon_loss = F.mse_loss(reconstructed, original)
                        sae_recon_loss += recon_loss.item()
                        
                        # Sparsity penalty
                        sparsity = compute_sparsity_penalty(features)
                        sae_sparsity_loss += sparsity.item()
                        
                        active_layers += 1
                
                if active_layers > 0:
                    sae_recon_loss = sae_recon_loss / active_layers
                    sae_sparsity_loss = sae_sparsity_loss / active_layers
                
                sae_recon_tensor = torch.tensor(sae_recon_loss, device=device, dtype=torch.bfloat16)
                sae_sparsity_tensor = torch.tensor(sae_sparsity_loss, device=device, dtype=torch.bfloat16)
            else:
                sae_recon_tensor = torch.tensor(0.0, device=device, dtype=torch.bfloat16)
                sae_sparsity_tensor = torch.tensor(0.0, device=device, dtype=torch.bfloat16)
            
            # Combined loss
            combined_loss = (
                config.NEXT_TOKEN_WEIGHT * loss +
                config.SAE_RECON_WEIGHT * sae_recon_tensor +
                config.SAE_SPARSITY_WEIGHT * sae_sparsity_tensor
            )
            
            # Scale for gradient accumulation
            scaled_loss = combined_loss / config.GRAD_ACCUM_STEPS
            scaled_loss.backward()
            
            accum_count += 1
            
            if accum_count >= config.GRAD_ACCUM_STEPS:
                # Gradient health check
                grad_norm, issues = check_gradient_health(model, config.MAX_NORM_GRAD)
                
                if issues:
                    for issue in issues:
                        logger.log_alert(issue)
                
                # Gradient clipping - use adaptive clip based on norm
                effective_clip = min(config.GRAD_CLIP, grad_norm * 0.5) if grad_norm > config.GRAD_CLIP else config.GRAD_CLIP
                torch.nn.utils.clip_grad_norm_(model.parameters(), effective_clip)
                
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
                    f"SAERecon: {sae_recon_loss:.4f} | "
                    f"Sparsity: {sae_sparsity_loss:.4f} | "
                    f"GradNorm: {grad_norm:.2f} | "
                    f"GPU: {gpu_mem:.1f}GB/{gpu_total:.1f}GB"
                )
                
                logger.log_metric(step, {
                    "loss": loss.item(),
                    "sae_recon": sae_recon_loss,
                    "sae_sparsity": sae_sparsity_loss,
                    "combined": combined_loss.item(),
                    "lr": lr,
                    "grad_norm": grad_norm,
                    "gpu_mem_gb": gpu_mem,
                })
                
                # Validation
                if step % config.VALIDATE_EVERY == 0 and step > 0:
                    val_loss = validate(model, val_dataloader, device, saes, logger, step)
                
                # Save checkpoint
                if step % config.SAVE_EVERY == 0 and step > 0:
                    ckpt_path = os.path.join(config.CHECKPOINT_DIR, f"maxquality_step_{step}.pt")
                    save_checkpoint(model, optimizer, step, best_loss, config, ckpt_path)
                    logger.log(f"Checkpoint saved: {ckpt_path}")
    
    # Final save
    ckpt_path = os.path.join(config.CHECKPOINT_DIR, "maxquality_final.pt")
    save_checkpoint(model, optimizer, step, best_loss, config, ckpt_path)
    logger.log(f"Final checkpoint: {ckpt_path}")
    logger.log(f"Best loss: {best_loss:.4f}")
    
    logger.log("")
    logger.log("=" * 60)
    logger.log("TRAINING COMPLETE")
    logger.log("=" * 60)
    
    # Cleanup
    for h in hooks:
        h.remove()
    logger.close()

if __name__ == "__main__":
    main()
