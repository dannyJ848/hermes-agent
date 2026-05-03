#!/usr/bin/env python3
"""
Qwen 27B + Qwen-Scope SAE Training (without live teacher)
Uses SAE reconstruction loss to encourage sparse, interpretable features
"""
import os
import sys
import time
import glob
import itertools
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored/"
SAE_DIR = "/data/models/Qwen-Scope/"
HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states/"
CHECKPOINT_DIR = "/data/SpecForge/custom_dflash/checkpoints/"
LOG_FILE = "/mnt/bigssd/train_sae_only.log"

MAX_SEQ_LEN = 256
BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4
MAX_STEPS = 1000
LEARNING_RATE = 1e-5
SAVE_EVERY = 100
SAE_LAYERS = [16, 32, 48]
SAE_WEIGHT = 0.05  # Reconstruction loss weight

os.makedirs(CHECKPOINT_DIR, exist_ok=True)

log_f = open(LOG_FILE, "w")
def log(msg):
    print(msg, flush=True)
    log_f.write(msg + "\n")
    log_f.flush()

log("=" * 60)
log("QWEN 27B + SAE TRAINING (NO LIVE TEACHER)")
log("=" * 60)

if not torch.cuda.is_available():
    log("ERROR: No CUDA")
    sys.exit(1)

device = torch.device("cuda:0")
log("GPU: " + str(torch.cuda.get_device_name(0)))
log("GPU Memory: %.1f GB" % (torch.cuda.get_device_properties(0).total_memory / 1e9))

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

# Load SAEs (frozen feature extractors)
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
    else:
        log(f"  WARNING: layer{layer_idx}.sae.pt not found")

log(f"Loaded {len(saes)} SAEs")

def get_feature_acts(residual, sae_dict):
    """Extract sparse features from hidden states"""
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

# Load tokenizer
log("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
log("Tokenizer vocab size: %d" % len(tokenizer))

# Load model
log("Loading model (Qwen 3.6-27B)...")
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

load_time = time.time() - start
log("Model loaded in %.1fs" % load_time)

total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
log("Total params: %.1fB" % (total_params/1e9))
log("Trainable: %.1fB" % (trainable_params/1e9))

log("Enabling gradient checkpointing...")
model.gradient_checkpointing_enable()
model.enable_input_require_grads()

# SAE capture hooks
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

# Optimizer
log("Creating SGD optimizer...")
optimizer = torch.optim.SGD(model.parameters(), lr=LEARNING_RATE)
log("Optimizer: SGD, lr=%e" % LEARNING_RATE)

# Training loop
log("")
log("=" * 60)
log("STARTING SAE-ENHANCED TRAINING")
log("=" * 60)
log("Steps: %d, batch=%d, accum=%d" % (MAX_STEPS, BATCH_SIZE, GRAD_ACCUM_STEPS))
log("SAE layers: %s" % str(SAE_LAYERS))
log("SAE weight: %.3f" % SAE_WEIGHT)

# Resume from latest checkpoint if exists
latest_ckpt = None
for s in range(MAX_STEPS, 0, -1):
    ck = os.path.join(CHECKPOINT_DIR, "sae_step_%d.pt" % s)
    if os.path.exists(ck):
        latest_ckpt = ck
        break
if latest_ckpt:
    log("Resuming from: %s" % latest_ckpt)
    ckpt = torch.load(latest_ckpt, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    optimizer.load_state_dict(ckpt["optimizer_state_dict"])
    step = ckpt.get("step", 0)
    log("Resumed at step %d" % step)
else:
    step = 0

model.train()
accum_count = 0

epoch = 0
while step < MAX_STEPS:
    epoch += 1
    log("Starting epoch %d" % epoch)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    for batch in dataloader:
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
                    
                    # Reconstruct hidden states from sparse features
                    reconstructed = reconstruct_from_features(features, saes[layer_idx])
                    
                    # MSE between original and reconstructed
                    layer_loss = F.mse_loss(reconstructed, original)
                    sae_loss += layer_loss.item()
            
            sae_loss = sae_loss / len([l for l in SAE_LAYERS if l in captured_features])
            sae_loss_tensor = torch.tensor(sae_loss, device=device, dtype=torch.bfloat16)
        else:
            sae_loss_tensor = torch.tensor(0.0, device=device, dtype=torch.bfloat16)
        
        # Combined loss
        combined_loss = loss + SAE_WEIGHT * sae_loss_tensor
        
        # Scale for gradient accumulation
        scaled_loss = combined_loss / GRAD_ACCUM_STEPS
        scaled_loss.backward()
        
        accum_count += 1
        
        if accum_count >= GRAD_ACCUM_STEPS:
            optimizer.step()
            optimizer.zero_grad()
            accum_count = 0
            step += 1
            
            # Log
            gpu_mem = torch.cuda.memory_allocated(device) / 1e9
            gpu_total = torch.cuda.get_device_properties(device).total_memory / 1e9
            log("[Step %d/%d] Loss: %.4f | SAELoss: %.4f | Combined: %.4f | GPU: %.1fGB/%.1fGB" % 
                (step, MAX_STEPS, loss.item(), sae_loss, combined_loss.item(), gpu_mem, gpu_total))
            
            # Save checkpoint
            if step % SAVE_EVERY == 0:
                ckpt_path = os.path.join(CHECKPOINT_DIR, "sae_step_%d.pt" % step)
                torch.save({
                    "step": step,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                }, ckpt_path)
                log("Checkpoint saved: %s" % ckpt_path)

# Final save
ckpt_path = os.path.join(CHECKPOINT_DIR, "sae_final.pt")
torch.save({
    "step": step,
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
}, ckpt_path)
log("Final checkpoint: %s" % ckpt_path)

log("")
log("=" * 60)
log("SAE-ENHANCED TRAINING COMPLETE")
log("=" * 60)

# Clean up hooks
for h in hooks:
    h.remove()

log_f.close()
