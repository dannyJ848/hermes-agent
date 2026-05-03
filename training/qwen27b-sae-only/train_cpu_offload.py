#!/usr/bin/env python3
"""
Qwen 27B FULL FINE-TUNING - CPU-Offloaded Optimizer Approach

Strategy:
1. Model on GPU in bf16
2. Forward+backward on GPU (compute gradients)
3. Move gradients to CPU
4. Optimizer step on CPU (update fp32 master weights)
5. Copy updated weights back to GPU in bf16

This avoids storing optimizer states on GPU. CPU has 121GB RAM.
Optimizer states for 27B in fp32: ~108GB (fits in CPU RAM)
Model weights in bf16 on GPU: ~54GB
Activations with grad checkpointing: ~20-30GB
Total GPU: ~80GB (fits in 130GB)
Total CPU: ~108GB (fits in 121GB)
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

# ============================================================================
# CONFIGURATION
# ============================================================================
MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored"
SAE_DIR = "/data/models/Qwen-Scope"
HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states"
CHECKPOINT_DIR = "/data/SpecForge/custom_dflash/checkpoints"
LOG_FILE = "/mnt/bigssd/train_cpu_offload.log"

MAX_STEPS = 1000
BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4
LR = 1e-5
SAE_WEIGHT = 0.05
WARMUP_STEPS = 50
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

# ============================================================================
# SETUP
# ============================================================================
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
cpu_device = torch.device("cpu")

log("=" * 70)
log("QWEN 27B FULL FINE-TUNING - CPU-Offloaded Optimizer")
log("=" * 70)
log("GPU: %s | %.1f GB" % (torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory / 1e9))
log("CPU RAM: ~121 GB")

# ============================================================================
# LOAD SAEs
# ============================================================================
log("Loading SAEs...")
saes = {}
for layer_idx in SAE_LAYERS:
    sae_path = os.path.join(SAE_DIR, "layer%d.sae.pt" % layer_idx)
    if os.path.exists(sae_path):
        saes[layer_idx] = torch.load(sae_path, map_location=device)
        log("  Layer %d: loaded" % layer_idx)

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
# LOAD MODEL
# ============================================================================
log("Loading Qwen 27B...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    max_memory={0: "110GiB", "cpu": "0GiB"},
    trust_remote_code=True,
)

model.gradient_checkpointing_enable()
model.enable_input_require_grads()

# ALL parameters trainable
for param in model.parameters():
    param.requires_grad = True

# Register hooks
for layer_idx in SAE_LAYERS:
    if layer_idx < len(model.model.layers):
        model.model.layers[layer_idx].register_forward_hook(make_sae_hook(layer_idx))

log("Model loaded. Trainable params: %.2fB" % (sum(p.numel() for p in model.parameters() if p.requires_grad) / 1e9))

# ============================================================================
# CPU-OFFLOADED OPTIMIZER SETUP
# ============================================================================
log("Setting up CPU-offloaded optimizer...")

# Create fp32 master copies on CPU for all trainable parameters
master_params = {}
for name, param in model.named_parameters():
    if param.requires_grad:
        master_params[name] = param.detach().clone().float().to(cpu_device)
        log("  Master param %s: CPU fp32" % name[:50])

# AdamW optimizer on CPU master params
master_list = list(master_params.values())
optimizer = torch.optim.AdamW(master_list, lr=LR, weight_decay=0.01, betas=(0.9, 0.999), eps=1e-8)
log("AdamW optimizer on %d master params (CPU)" % len(master_list))

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
            # Move gradients to CPU and apply to master params
            grad_norm = 0.0
            for (name, param), master_p in zip(model.named_parameters(), master_params.values()):
                if param.grad is not None:
                    # Move grad to CPU
                    cpu_grad = param.grad.detach().float().to(cpu_device)
                    
                    # Copy grad to master param
                    if master_p.grad is None:
                        master_p.grad = cpu_grad
                    else:
                        master_p.grad.add_(cpu_grad)
                    
                    # Accumulate grad norm for logging
                    grad_norm += cpu_grad.norm(2).item() ** 2
                    
                    # Clear GPU grad
                    param.grad = None
            
            grad_norm = grad_norm ** 0.5
            
            # Clip gradients on CPU
            torch.nn.utils.clip_grad_norm_(master_list, 1.0)
            
            # Optimizer step on CPU
            optimizer.step()
            optimizer.zero_grad()
            
            # Copy updated master params back to GPU model in bf16
            for (name, param), master_p in zip(model.named_parameters(), master_params.values()):
                param.data.copy_(master_p.to(device).bfloat16())
            
            accum_count = 0
            step += 1
            
            # Update LR
            current_lr = get_lr(step, WARMUP_STEPS, MAX_STEPS, LR)
            for param_group in optimizer.param_groups:
                param_group['lr'] = current_lr
            
            # Log
            gpu_mem = torch.cuda.memory_allocated(device) / 1e9
            gpu_total = torch.cuda.get_device_properties(device).total_memory / 1e9
            log("[Step %d/%d] Loss: %.4f | SAELoss: %.4f | GradNorm: %.2f | LR: %.2e | GPU: %.1fGB/%.1fGB" % 
                (step, MAX_STEPS, loss.item(), sae_loss, grad_norm, current_lr, gpu_mem, gpu_total))
            
            # Checkpoint
            if step % SAVE_EVERY == 0:
                ckpt_path = os.path.join(CHECKPOINT_DIR, "cpuoffload_step_%d.pt" % step)
                torch.save({
                    "step": step,
                    "model_state_dict": {k: v.cpu() for k, v in model.state_dict().items()},
                    "optimizer_state_dict": optimizer.state_dict(),
                    "master_params": {k: v.cpu() for k, v in master_params.items()},
                }, ckpt_path)
                log("Checkpoint: %s" % ckpt_path)
            
            if torch.isnan(loss) or torch.isinf(loss):
                log("FATAL: NaN/Inf loss - stopping")
                break
            
            if grad_norm > 1000:
                log("WARNING: GradNorm %.2f - possible explosion" % grad_norm)

# Final save
ckpt_path = os.path.join(CHECKPOINT_DIR, "cpuoffload_final.pt")
torch.save({
    "step": step,
    "model_state_dict": {k: v.cpu() for k, v in model.state_dict().items()},
    "optimizer_state_dict": optimizer.state_dict(),
    "master_params": {k: v.cpu() for k, v in master_params.items()},
}, ckpt_path)
log("Final checkpoint: %s" % ckpt_path)
log("=" * 70)
log("FULL FINE-TUNING COMPLETE")
log("=" * 70)
