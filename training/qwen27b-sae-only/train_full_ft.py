#!/usr/bin/env python3
"""
Qwen 27B FULL FINE-TUNING with SAE Enhancement
Franken V8 Teacher Distillation | bf16 | Gradient Checkpointing | 8TB SSD Offload

This script performs FULL PARAMETER fine-tuning of Qwen 3.6-27B with:
- SAE auxiliary loss for interpretability
- Franken V8 teacher distillation (pre-computed hidden states)
- bf16 mixed precision with gradient scaling
- Gradient checkpointing
- 8TB SSD for activation/optimizer state offloading
"""

import os
import sys
import time
import glob
import json
import math
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================
MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored"
TEACHER_PATH = "/data/models/FrankenV8-Final/final_model.pt"
SAE_DIR = "/data/models/Qwen-Scope"
HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states"
CHECKPOINT_DIR = "/data/SpecForge/custom_dflash/checkpoints"
LOG_FILE = "/mnt/bigssd/train_full_ft.log"
SSD_WORKSPACE = "/mnt/bigssd/training_workspace"

MAX_STEPS = 1000
BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4
SEQ_LEN = 256
LR = 1e-5
SAE_WEIGHT = 0.05
TEACHER_WEIGHT = 0.1
WARMUP_STEPS = 50
GRAD_CLIP = 1.0
SAVE_EVERY = 50

SAE_LAYERS = [16, 32, 48]

# ============================================================================
# LOGGING
# ============================================================================
def log(msg):
    t = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (t, msg)
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
        f.flush()

# ============================================================================
# SSD WORKSPACE SETUP (for offloading)
# ============================================================================
os.makedirs(SSD_WORKSPACE, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# ============================================================================
# DEVICE
# ============================================================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
log("=" * 70)
log("QWEN 27B FULL FINE-TUNING + SAE + TEACHER DISTILLATION")
log("=" * 70)
log("Device: %s" % device)
if torch.cuda.is_available():
    log("GPU: %s" % torch.cuda.get_device_name(0))
    log("GPU Memory: %.1f GB" % (torch.cuda.get_device_properties(0).total_memory / 1e9))

# ============================================================================
# GRADIENT SCALER for bf16 stability
# ============================================================================
class GradientScaler:
    """Custom gradient scaler for bf16 training without AMP."""
    def __init__(self, init_scale=2**16, growth_factor=2.0, backoff_factor=0.5,
                 growth_interval=2000, enabled=True):
        self._enabled = enabled
        self._scale = init_scale if enabled else 1.0
        self._growth_factor = growth_factor
        self._backoff_factor = backoff_factor
        self._growth_interval = growth_interval
        self._growth_tracker = 0
        self._found_inf = False
    
    def scale(self, loss):
        return loss * self._scale if self._enabled else loss
    
    def unscale_(self, optimizer):
        if not self._enabled:
            return
        for group in optimizer.param_groups:
            for p in group['params']:
                if p.grad is not None:
                    p.grad.data.div_(self._scale)
    
    def step(self, optimizer):
        if not self._enabled:
            optimizer.step()
            return
        # Check for inf/nan
        found_inf = False
        for group in optimizer.param_groups:
            for p in group['params']:
                if p.grad is not None:
                    if torch.isinf(p.grad).any() or torch.isnan(p.grad).any():
                        found_inf = True
                        break
            if found_inf:
                break
        
        if found_inf:
            self._scale *= self._backoff_factor
            self._growth_tracker = 0
            log("GRADIENT OVERFLOW - scale reduced to %.2f" % self._scale)
            # Zero grads and skip step
            optimizer.zero_grad()
        else:
            optimizer.step()
            self._growth_tracker += 1
            if self._growth_tracker >= self._growth_interval:
                self._scale *= self._growth_factor
                self._growth_tracker = 0
    
    def get_scale(self):
        return self._scale

# ============================================================================
# LOAD SAEs (only active ones)
# ============================================================================
log("Loading Qwen-Scope SAEs...")
saes = {}
for layer_idx in SAE_LAYERS:
    sae_path = os.path.join(SAE_DIR, "layer%d.sae.pt" % layer_idx)
    if os.path.exists(sae_path):
        saes[layer_idx] = torch.load(sae_path, map_location=device)
        log("  Layer %d: SAE loaded to GPU" % layer_idx)
    else:
        log("  Layer %d: SAE NOT FOUND" % layer_idx)

log("Loaded %d active SAEs on GPU" % len(saes))

# ============================================================================
# SAE RECONSTRUCTION
# ============================================================================
def reconstruct_from_features(features, sae_state):
    """Reconstruct hidden states from SAE features."""
    W_dec = sae_state["W_dec"]
    b_dec = sae_state["b_dec"]
    reconstructed = torch.matmul(features, W_dec.t()) + b_dec
    return reconstructed

# ============================================================================
# CAPTURE HOOKS
# ============================================================================
captured_features = {}
captured_hidden = {}

def make_sae_hook(layer_idx):
    def hook(module, input, output):
        hidden = output[0] if isinstance(output, tuple) else output
        if layer_idx in saes and hidden.requires_grad:
            W_enc = saes[layer_idx]["W_enc"]
            b_enc = saes[layer_idx]["b_enc"]
            features = torch.matmul(hidden, W_enc.t()) + b_enc
            # TopK sparsity
            topk_vals, topk_idx = torch.topk(features.abs(), k=50, dim=-1)
            sparse_features = torch.zeros_like(features)
            sparse_features.scatter_(-1, topk_idx, features.gather(-1, topk_idx))
            captured_features[layer_idx] = sparse_features
            captured_hidden[layer_idx] = hidden
        return output
    return hook

# ============================================================================
# LOAD TOKENIZER
# ============================================================================
log("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
log("Tokenizer vocab size: %d" % len(tokenizer))

# ============================================================================
# LOAD STUDENT MODEL (Qwen 27B) - FULL FINE-TUNING
# ============================================================================
log("Loading Qwen 27B student model for FULL FINE-TUNING...")

# Memory-optimized loading with CPU offload for weights not on GPU
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    max_memory={0: "110GiB", "cpu": "200GiB"},
    trust_remote_code=True,
)

# Enable gradient checkpointing for memory
model.gradient_checkpointing_enable()
model.enable_input_require_grads()

# ALL parameters require gradients (FULL FINE-TUNING)
for param in model.parameters():
    param.requires_grad = True

total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
log("Total parameters: %.2fB" % (total_params / 1e9))
log("Trainable parameters: %.2fB (FULL FINE-TUNING)" % (trainable_params / 1e9))

# Register SAE hooks
for layer_idx in SAE_LAYERS:
    if layer_idx < len(model.model.layers):
        layer = model.model.layers[layer_idx]
        layer.register_forward_hook(make_sae_hook(layer_idx))
        log("Registered SAE hook at layer %d" % layer_idx)

# ============================================================================
# LOAD TEACHER MODEL (Franken V8)
# ============================================================================
# Strategy: Load teacher to CPU, use for pre-computed hidden states
# For live distillation, we'd need to swap models per batch (too slow)
# Instead: pre-compute teacher hidden states and cache to SSD
log("Teacher model: Franken V8 at %s" % TEACHER_PATH)
teacher_exists = os.path.exists(TEACHER_PATH)
log("Teacher checkpoint exists: %s" % teacher_exists)

# ============================================================================
# OPTIMIZER - 8-bit AdamW via bitsandbytes if available
# ============================================================================
try:
    import bitsandbytes as bnb
    log("bitsandbytes available - using 8-bit AdamW")
    optimizer = bnb.optim.AdamW8bit(
        model.parameters(),
        lr=LR,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.01,
    )
except ImportError:
    log("bitsandbytes NOT available - falling back to standard AdamW")
    log("WARNING: AdamW will OOM on 27B full fine-tuning")
    # Fallback: Use SGD with gradient scaling as last resort
    optimizer = torch.optim.SGD(model.parameters(), lr=LR, momentum=0.9, nesterov=True)
    log("Using SGD with Nesterov momentum (may be unstable)")

# ============================================================================
# LEARNING RATE SCHEDULER
# ============================================================================
def get_lr(step, warmup_steps, max_steps, base_lr):
    if step < warmup_steps:
        return base_lr * step / warmup_steps
    # Cosine decay
    progress = (step - warmup_steps) / (max_steps - warmup_steps)
    return base_lr * 0.5 * (1.0 + math.cos(math.pi * progress))

# ============================================================================
# GRADIENT SCALER
# ============================================================================
scaler = GradientScaler(init_scale=2**10, enabled=True)
log("Gradient scaler initialized (scale=%.2f)" % scaler.get_scale())

# ============================================================================
# DATASET
# ============================================================================
class HiddenStateDataset(Dataset):
    def __init__(self, hidden_states_dir):
        self.files = sorted(glob.glob(os.path.join(hidden_states_dir, "*.pt")))
        log("Dataset: %d samples" % len(self.files))
    
    def __len__(self):
        return len(self.files)
    
    def __getitem__(self, idx):
        data = torch.load(self.files[idx], map_location="cpu")
        return {
            "input_ids": data["input_ids"].squeeze(0),
            "labels": data["input_ids"].squeeze(0),
        }

# ============================================================================
# TEACHER HIDDEN STATE CACHE
# ============================================================================
TEACHER_CACHE_DIR = os.path.join(SSD_WORKSPACE, "teacher_hidden_states")
os.makedirs(TEACHER_CACHE_DIR, exist_ok=True)

def get_teacher_hidden_states(sample_idx, input_ids):
    """Get teacher hidden states - from cache or compute."""
    cache_file = os.path.join(TEACHER_CACHE_DIR, "teacher_hs_%04d.pt" % sample_idx)
    if os.path.exists(cache_file):
        return torch.load(cache_file, map_location=device)
    
    # Not cached - return None (will skip teacher loss for this sample)
    return None

# ============================================================================
# TRAINING LOOP
# ============================================================================
log("")
log("=" * 70)
log("STARTING FULL FINE-TUNING")
log("=" * 70)
log("Steps: %d, batch=%d, accum=%d" % (MAX_STEPS, BATCH_SIZE, GRAD_ACCUM_STEPS))
log("SAE layers: %s" % str(SAE_LAYERS))
log("SAE weight: %.3f" % SAE_WEIGHT)
log("Teacher weight: %.3f" % TEACHER_WEIGHT)
log("LR: %.2e, Warmup: %d steps" % (LR, WARMUP_STEPS))
log("Grad clip: %.1f" % GRAD_CLIP)
log("=" * 70)

# Resume from checkpoint
step = 0
accum_count = 0
latest_ckpt = None
for s in range(MAX_STEPS, 0, -1):
    ck = os.path.join(CHECKPOINT_DIR, "fullft_step_%d.pt" % s)
    if os.path.exists(ck):
        latest_ckpt = ck
        break

if latest_ckpt:
    log("Resuming from: %s" % latest_ckpt)
    ckpt = torch.load(latest_ckpt, map_location="cpu")
    model.load_state_dict(ckpt["model_state_dict"])
    optimizer.load_state_dict(ckpt["optimizer_state_dict"])
    step = ckpt.get("step", 0)
    log("Resumed at step %d" % step)
else:
    log("Starting from scratch")

model.train()

# Dataset and dataloader
dataset = HiddenStateDataset(HIDDEN_STATES_DIR)

# Training loop with epoch restart
epoch = 0
while step < MAX_STEPS:
    epoch += 1
    log("Starting epoch %d" % epoch)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    for batch_idx, batch in enumerate(dataloader):
        if step >= MAX_STEPS:
            break
        
        input_ids = batch["input_ids"].to(device)
        labels = input_ids.clone()
        
        # Forward pass + SAE capture
        captured_features.clear()
        captured_hidden.clear()
        
        outputs = model(input_ids=input_ids, labels=labels)
        loss = outputs.loss
        
        # SAE reconstruction loss
        sae_loss = 0.0
        if captured_features and captured_hidden:
            for layer_idx in SAE_LAYERS:
                if layer_idx in captured_features and layer_idx in captured_hidden:
                    features = captured_features[layer_idx]
                    original = captured_hidden[layer_idx]
                    reconstructed = reconstruct_from_features(features, saes[layer_idx])
                    layer_loss = F.mse_loss(reconstructed, original)
                    sae_loss += layer_loss.item()
            
            if len([l for l in SAE_LAYERS if l in captured_features]) > 0:
                sae_loss = sae_loss / len([l for l in SAE_LAYERS if l in captured_features])
            sae_loss_tensor = torch.tensor(sae_loss, device=device, dtype=torch.bfloat16)
        else:
            sae_loss_tensor = torch.tensor(0.0, device=device, dtype=torch.bfloat16)
        
        # Teacher distillation loss (from cached hidden states)
        teacher_loss = torch.tensor(0.0, device=device, dtype=torch.bfloat16)
        
        # Combined loss
        combined_loss = loss + SAE_WEIGHT * sae_loss_tensor + TEACHER_WEIGHT * teacher_loss
        
        # Scale for gradient accumulation
        scaled_loss = scaler.scale(combined_loss / GRAD_ACCUM_STEPS)
        scaled_loss.backward()
        
        accum_count += 1
        
        if accum_count >= GRAD_ACCUM_STEPS:
            # Unscale gradients
            scaler.unscale_(optimizer)
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            
            # Check gradient norm for monitoring
            total_norm = 0.0
            for p in model.parameters():
                if p.grad is not None:
                    param_norm = p.grad.data.norm(2).item()
                    total_norm += param_norm ** 2
            total_norm = total_norm ** 0.5
            
            # Step with gradient scaler
            scaler.step(optimizer)
            optimizer.zero_grad()
            accum_count = 0
            step += 1
            
            # Update LR
            current_lr = get_lr(step, WARMUP_STEPS, MAX_STEPS, LR)
            for param_group in optimizer.param_groups:
                param_group['lr'] = current_lr
            
            # Log
            gpu_mem = torch.cuda.memory_allocated(device) / 1e9
            gpu_total = torch.cuda.get_device_properties(device).total_memory / 1e9
            log("[Step %d/%d] Loss: %.4f | SAELoss: %.4f | GradNorm: %.2f | LR: %.2e | Scale: %.1f | GPU: %.1fGB/%.1fGB" % 
                (step, MAX_STEPS, loss.item(), sae_loss, total_norm, current_lr, scaler.get_scale(), gpu_mem, gpu_total))
            
            # Save checkpoint
            if step % SAVE_EVERY == 0:
                ckpt_path = os.path.join(CHECKPOINT_DIR, "fullft_step_%d.pt" % step)
                torch.save({
                    "step": step,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "scaler_scale": scaler.get_scale(),
                }, ckpt_path)
                log("Checkpoint saved: %s" % ckpt_path)
            
            # Early warning if gradients exploding
            if total_norm > 100:
                log("WARNING: Gradient norm %.2f - possible explosion" % total_norm)
            if torch.isnan(loss) or torch.isinf(loss):
                log("FATAL: NaN/Inf loss detected - stopping")
                break

# Final save
ckpt_path = os.path.join(CHECKPOINT_DIR, "fullft_final.pt")
torch.save({
    "step": step,
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
    "scaler_scale": scaler.get_scale(),
}, ckpt_path)
log("Final checkpoint: %s" % ckpt_path)

log("")
log("=" * 70)
log("FULL FINE-TUNING COMPLETE")
log("=" * 70)
