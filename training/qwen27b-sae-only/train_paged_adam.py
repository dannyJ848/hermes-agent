#!/usr/bin/env python3
"""
Qwen 27B FULL FINE-TUNING - PagedAdamW8bit

Strategy:
- Model on GPU in bf16 (~54GB)
- PagedAdamW8bit: 8-bit quantized optimizer states (~27GB)
- Total GPU: ~54 + ~27 + ~30GB activations = ~111GB (fits in 130GB)
- No CPU RAM needed for optimizer states
"""

import os
import sys
import time
import glob
import math
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
import bitsandbytes as bnb

# ============================================================================
# CONFIGURATION
# ============================================================================
MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored"
SAE_DIR = "/data/models/Qwen-Scope"
HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states"
CHECKPOINT_DIR = "/data/SpecForge/custom_dflash/checkpoints"
LOG_FILE = "/mnt/bigssd/train_paged_adam.log"

MAX_STEPS = 1000
BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4
LR = 1e-5
SAE_WEIGHT = 0.05
WARMUP_STEPS = 50
SAVE_EVERY = 50
SAE_LAYERS = [16, 32, 48]
GRAD_CLIP = 1.0

# ============================================================================
# LOGGING
# ============================================================================
def log(msg):
    t = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (t, msg)
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ============================================================================
# SETUP
# ============================================================================
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

log("=" * 70)
log("QWEN 27B FULL FINE-TUNING - PagedAdamW8bit")
log("=" * 70)
log("GPU: %s | %.1f GB" % (torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory / 1e9))

# ============================================================================
# LOAD SAEs (bf16)
# ============================================================================
log("Loading SAEs...")
saes = {}
for layer_idx in SAE_LAYERS:
    sae_path = os.path.join(SAE_DIR, "layer%d.sae.pt" % layer_idx)
    if os.path.exists(sae_path):
        saes[layer_idx] = torch.load(sae_path, map_location=device)
        # Convert to bf16
        for k in saes[layer_idx]:
            if isinstance(saes[layer_idx][k], torch.Tensor):
                saes[layer_idx][k] = saes[layer_idx][k].to(torch.bfloat16)
        log("  Layer %d: loaded (bf16)" % layer_idx)

def reconstruct_from_features(features, sae_state):
    W_dec = sae_state["W_dec"]
    b_dec = sae_state["b_dec"]
    return torch.matmul(features, W_dec.t()) + b_dec

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
            topk_vals, topk_idx = torch.topk(features.abs(), k=50, dim=-1)
            sparse_features = torch.zeros_like(features)
            sparse_features.scatter_(-1, topk_idx, features.gather(-1, topk_idx))
            captured_features[layer_idx] = sparse_features
            captured_hidden[layer_idx] = hidden
        return output
    return hook

# ============================================================================
# LOAD MODEL - ALL ON GPU
# ============================================================================
log("Loading Qwen 27B to GPU...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",  # Force all on GPU
    trust_remote_code=True,
)

model.gradient_checkpointing_enable()
model.enable_input_require_grads()

for param in model.parameters():
    param.requires_grad = True

for layer_idx in SAE_LAYERS:
    if layer_idx < len(model.model.layers):
        model.model.layers[layer_idx].register_forward_hook(make_sae_hook(layer_idx))

log("Model loaded. Trainable: %.2fB" % (sum(p.numel() for p in model.parameters() if p.requires_grad) / 1e9))

# ============================================================================
# PagedAdamW8bit OPTIMIZER
# ============================================================================
log("Setting up PagedAdamW8bit optimizer...")
optimizer = bnb.optim.PagedAdamW8bit(
    model.parameters(),
    lr=LR,
    betas=(0.9, 0.999),
    eps=1e-8,
    weight_decay=0.01,
    min_8bit_size=4096,
    block_wise=True,
)
log("Optimizer ready")

# ============================================================================
# DATASET
# ============================================================================
class HiddenStateDataset(Dataset):
    def __init__(self, hidden_states_dir):
        self.files = sorted(glob.glob(os.path.join(hidden_states_dir, "*.pt")))
        log("Dataset: %d samples" % len(self.files))
    def __len__(self): return len(self.files)
    def __getitem__(self, idx):
        data = torch.load(self.files[idx], map_location="cpu")
        return {"input_ids": data["input_ids"].squeeze(0), "labels": data["input_ids"].squeeze(0)}

dataset = HiddenStateDataset(HIDDEN_STATES_DIR)

# ============================================================================
# LR SCHEDULER
# ============================================================================
def get_lr(step, warmup_steps, max_steps, base_lr):
    if step < warmup_steps:
        return base_lr * step / warmup_steps
    progress = (step - warmup_steps) / (max_steps - warmup_steps)
    return base_lr * 0.5 * (1.0 + math.cos(math.pi * progress))

# ============================================================================
# TRAINING LOOP
# ============================================================================
log("")
log("=" * 70)
log("STARTING FULL FINE-TUNING")
log("=" * 70)

step = 0
accum_count = 0
epoch = 0

model.train()

while step < MAX_STEPS:
    epoch += 1
    log("Epoch %d" % epoch)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    for batch in dataloader:
        if step >= MAX_STEPS:
            break
        
        input_ids = batch["input_ids"].to(device)
        labels = input_ids.clone()
        
        captured_features.clear()
        captured_hidden.clear()
        
        # Forward
        outputs = model(input_ids=input_ids, labels=labels)
        loss = outputs.loss
        
        # SAE loss
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
        
        sae_loss_tensor = torch.tensor(sae_loss, device=loss.device, dtype=torch.bfloat16)
        combined_loss = loss + SAE_WEIGHT * sae_loss_tensor
        
        # Scale for grad accum
        scaled_loss = combined_loss / GRAD_ACCUM_STEPS
        scaled_loss.backward()
        
        accum_count += 1
        
        if accum_count >= GRAD_ACCUM_STEPS:
            # Gradient clipping
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            
            # Optimizer step
            current_lr = get_lr(step, WARMUP_STEPS, MAX_STEPS, LR)
            for param_group in optimizer.param_groups:
                param_group['lr'] = current_lr
            
            optimizer.step()
            optimizer.zero_grad()
            
            accum_count = 0
            step += 1
            
            # Log
            gpu_mem = torch.cuda.memory_allocated(device) / 1e9
            gpu_total = torch.cuda.get_device_properties(device).total_memory / 1e9
            log("[Step %d/%d] Loss: %.4f | SAELoss: %.4f | GradNorm: %.2f | LR: %.2e | GPU: %.1fGB/%.1fGB" % 
                (step, MAX_STEPS, loss.item(), sae_loss, grad_norm.item() if isinstance(grad_norm, torch.Tensor) else grad_norm, current_lr, gpu_mem, gpu_total))
            
            # Checkpoint
            if step % SAVE_EVERY == 0:
                ckpt_path = os.path.join(CHECKPOINT_DIR, "pagedadam_step_%d.pt" % step)
                torch.save({
                    "step": step,
                    "model_state_dict": {k: v.cpu() for k, v in model.state_dict().items()},
                    "optimizer_state_dict": optimizer.state_dict(),
                }, ckpt_path)
                log("Checkpoint: %s" % ckpt_path)
            
            if torch.isnan(loss) or torch.isinf(loss):
                log("FATAL: NaN/Inf loss - stopping")
                break

# Final save
ckpt_path = os.path.join(CHECKPOINT_DIR, "pagedadam_final.pt")
torch.save({
    "step": step,
    "model_state_dict": {k: v.cpu() for k, v in model.state_dict().items()},
    "optimizer_state_dict": optimizer.state_dict(),
}, ckpt_path)
log("Final checkpoint: %s" % ckpt_path)
log("=" * 70)
log("FULL FINE-TUNING COMPLETE")
log("=" * 70)
