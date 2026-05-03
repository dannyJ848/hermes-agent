#!/usr/bin/env python3
"""
Qwen 27B MAXIMUM QUALITY SAE-Enhanced Training
Addresses: LR schedule, warmup, gradient clipping, mixed precision checks
"""
import os
import sys
import time
import glob
import math
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored/"
SAE_DIR = "/data/models/Qwen-Scope/"
HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states/"
CHECKPOINT_DIR = "/data/SpecForge/custom_dflash/checkpoints/"
LOG_FILE = "/mnt/bigssd/train_max_quality.log"

MAX_SEQ_LEN = 256
BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4
MAX_STEPS = 1000
BASE_LR = 1e-5
WARMUP_STEPS = 50
SAVE_EVERY = 100
GRAD_CLIP = 1.0

# SAE Configuration
SAE_LAYERS = [8, 16, 24, 32, 40, 48, 56]  # More layers for better coverage
SAE_RECON_WEIGHT = 0.03  # Lower weight - don't interfere with next-token
SAE_SPARSITY_WEIGHT = 0.001  # Encourage sparsity

os.makedirs(CHECKPOINT_DIR, exist_ok=True)

log_f = open(LOG_FILE, "w")
def log(msg):
    print(msg, flush=True)
    log_f.write(msg + "\n")
    log_f.flush()

log("=" * 60)
log("QWEN 27B MAXIMUM QUALITY SAE TRAINING")
log("=" * 60)
log("Features: LR schedule, warmup, grad clipping, sparsity penalty")
log("SAE layers: %s" % str(SAE_LAYERS))

if not torch.cuda.is_available():
    log("ERROR: No CUDA")
    sys.exit(1)

device = torch.device("cuda:0")
log("GPU: " + str(torch.cuda.get_device_name(0)))
log("GPU Memory: %.1f GB" % (torch.cuda.get_device_properties(0).total_memory / 1e9))

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

# Load SAEs
log("Loading Qwen-Scope SAEs...")
saes = {}
for layer_idx in SAE_LAYERS:
    sae_path = os.path.join(SAE_DIR, f"layer{layer_idx}.sae.pt")
    if os.path.exists(sae_path):
        sae = torch.load(sae_path, map_location="cpu")
        saes[layer_idx] = {
            "W_enc": sae["W_enc"].to(device).bfloat16(),
            "b_enc": sae["b_enc"].to(device).bfloat16(),
            "W_dec": sae["W_dec"].to(device).bfloat16(),
            "b_dec": sae["b_dec"].to(device).bfloat16(),
        }
        log(f"  Layer {layer_idx}: SAE loaded")

log(f"Loaded {len(saes)} SAEs")

def get_feature_acts(residual, sae_dict):
    """Extract sparse features with TopK=50"""
    W_enc = sae_dict["W_enc"]
    b_enc = sae_dict["b_enc"]
    pre_acts = residual @ W_enc.T + b_enc
    topk_vals, topk_idx = pre_acts.topk(50, dim=-1)
    acts = torch.zeros_like(pre_acts)
    acts.scatter_(-1, topk_idx, topk_vals)
    return acts

def reconstruct_from_features(features, sae_dict):
    """Reconstruct hidden states from sparse features"""
    W_dec = sae_dict["W_dec"]
    b_dec = sae_dict["b_dec"]
    return features @ W_dec.T + b_dec

def compute_sparsity_penalty(features):
    """L1 penalty to encourage sparsity"""
    return features.abs().mean()

# Load tokenizer
log("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
log("Tokenizer vocab size: %d" % len(tokenizer))

# Load model
log("Loading model...")
start = time.time()

config = AutoConfig.from_pretrained(MODEL_PATH, trust_remote_code=True)
config.vocab_size = len(tokenizer)
config.use_cache = False

model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    config=config,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    max_memory={0: "120GiB", "cpu": "0GiB"},
    trust_remote_code=True,
)

log("Model loaded in %.1fs" % (time.time() - start))
log("Total params: %.1fB" % (sum(p.numel() for p in model.parameters())/1e9))

log("Enabling gradient checkpointing...")
model.gradient_checkpointing_enable()
model.enable_input_require_grads()

# SAE hooks
captured_features = {}
captured_hidden = {}

def make_hook(layer_idx):
    def hook(module, input, output):
        hidden = output[0] if isinstance(output, tuple) else output
        if layer_idx in saes:
            captured_features[layer_idx] = get_feature_acts(hidden, saes[layer_idx])
            captured_hidden[layer_idx] = hidden
        return output
    return hook

hooks = []
for layer_idx in SAE_LAYERS:
    if layer_idx in saes:
        h = model.model.layers[layer_idx].register_forward_hook(make_hook(layer_idx))
        hooks.append(h)

log(f"Registered {len(hooks)} SAE hooks")

# Dataset
class HiddenStateDataset(Dataset):
    def __init__(self, hidden_states_dir):
        self.files = sorted(glob.glob(os.path.join(hidden_states_dir, "*.pt")))
        log("Found %d hidden state files" % len(self.files))
    def __len__(self):
        return len(self.files)
    def __getitem__(self, idx):
        data = torch.load(self.files[idx], map_location="cpu")
        input_ids = data["input_ids"].squeeze(0)[:MAX_SEQ_LEN]
        return {"input_ids": input_ids}

dataset = HiddenStateDataset(HIDDEN_STATES_DIR)
dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

# Optimizer: SGD with momentum (better than plain SGD)
log("Creating SGD optimizer with momentum...")
optimizer = torch.optim.SGD(model.parameters(), lr=BASE_LR, momentum=0.9, nesterov=True)
log("Optimizer: SGD+momentum, lr=%e, momentum=0.9" % BASE_LR)

# Learning rate schedule with warmup
def get_lr(step):
    if step < WARMUP_STEPS:
        return BASE_LR * (step + 1) / WARMUP_STEPS
    else:
        # Cosine decay
        progress = (step - WARMUP_STEPS) / (MAX_STEPS - WARMUP_STEPS)
        return BASE_LR * 0.5 * (1 + math.cos(math.pi * progress))

# Training loop
log("")
log("=" * 60)
log("STARTING MAX QUALITY TRAINING")
log("=" * 60)
log("Steps: %d, warmup: %d, grad_clip: %.1f" % (MAX_STEPS, WARMUP_STEPS, GRAD_CLIP))

model.train()
step = 0
accum_count = 0
best_loss = float('inf')

while step < MAX_STEPS:
    for batch in dataloader:
        if step >= MAX_STEPS:
            break
        
        # Update learning rate
        lr = get_lr(step)
        for param_group in optimizer.param_groups:
            param_group['lr'] = lr
        
        input_ids = batch["input_ids"].to(device)
        labels = input_ids.clone()
        
        # Forward pass
        captured_features.clear()
        captured_hidden.clear()
        
        outputs = model(input_ids=input_ids, labels=labels)
        loss = outputs.loss
        
        # SAE losses
        sae_recon_loss = 0.0
        sae_sparsity_loss = 0.0
        
        if captured_features and captured_hidden:
            for layer_idx in SAE_LAYERS:
                if layer_idx in captured_features and layer_idx in captured_hidden:
                    features = captured_features[layer_idx]
                    original = captured_hidden[layer_idx]
                    
                    # Reconstruction loss
                    reconstructed = reconstruct_from_features(features, saes[layer_idx])
                    recon_loss = F.mse_loss(reconstructed, original)
                    sae_recon_loss += recon_loss.item()
                    
                    # Sparsity penalty (encourage sparse features)
                    sparsity = compute_sparsity_penalty(features)
                    sae_sparsity_loss += sparsity.item()
            
            count = len([l for l in SAE_LAYERS if l in captured_features])
            sae_recon_loss = sae_recon_loss / count
            sae_sparsity_loss = sae_sparsity_loss / count
            
            sae_recon_tensor = torch.tensor(sae_recon_loss, device=device, dtype=torch.bfloat16)
            sae_sparsity_tensor = torch.tensor(sae_sparsity_loss, device=device, dtype=torch.bfloat16)
        else:
            sae_recon_tensor = torch.tensor(0.0, device=device, dtype=torch.bfloat16)
            sae_sparsity_tensor = torch.tensor(0.0, device=device, dtype=torch.bfloat16)
        
        # Combined loss
        combined_loss = loss + SAE_RECON_WEIGHT * sae_recon_tensor + SAE_SPARSITY_WEIGHT * sae_sparsity_tensor
        
        # Scale for gradient accumulation
        scaled_loss = combined_loss / GRAD_ACCUM_STEPS
        scaled_loss.backward()
        
        accum_count += 1
        
        if accum_count >= GRAD_ACCUM_STEPS:
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            
            optimizer.step()
            optimizer.zero_grad()
            accum_count = 0
            step += 1
            
            # Track best loss
            if loss.item() < best_loss:
                best_loss = loss.item()
            
            # Log
            gpu_mem = torch.cuda.memory_allocated(device) / 1e9
            gpu_total = torch.cuda.get_device_properties(device).total_memory / 1e9
            log("[Step %d/%d] LR: %.2e | Loss: %.4f | SAERecon: %.4f | Sparsity: %.4f | GPU: %.1fGB/%.1fGB" % 
                (step, MAX_STEPS, lr, loss.item(), sae_recon_loss, sae_sparsity_loss, gpu_mem, gpu_total))
            
            # Save checkpoint
            if step % SAVE_EVERY == 0:
                ckpt_path = os.path.join(CHECKPOINT_DIR, "maxquality_step_%d.pt" % step)
                torch.save({
                    "step": step,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "best_loss": best_loss,
                }, ckpt_path)
                log("Checkpoint saved: %s (best_loss: %.4f)" % (ckpt_path, best_loss))

# Final save
ckpt_path = os.path.join(CHECKPOINT_DIR, "maxquality_final.pt")
torch.save({
    "step": step,
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
    "best_loss": best_loss,
}, ckpt_path)
log("Final checkpoint: %s (best_loss: %.4f)" % (ckpt_path, best_loss))

log("")
log("=" * 60)
log("MAX QUALITY TRAINING COMPLETE")
log("Best loss: %.4f" % best_loss)
log("=" * 60)

for h in hooks:
    h.remove()

log_f.close()
