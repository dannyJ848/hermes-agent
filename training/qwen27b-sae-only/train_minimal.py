#!/usr/bin/env python3
"""
Qwen 27B Full FT - Minimal Working Version
No teacher, no SAEs - just verify the training loop works.
"""
import os
import sys
import time
import glob
import json
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# Paths
MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored/"
HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states/"
CHECKPOINT_DIR = "/data/SpecForge/custom_dflash/checkpoints/"
LOG_FILE = "/mnt/bigssd/train_minimal.log"

# Training config
MAX_SEQ_LEN = 256
BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4
MAX_STEPS = 5
LEARNING_RATE = 1e-5

os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# Logging
log_f = open(LOG_FILE, "w")
def log(msg):
    print(msg, flush=True)
    log_f.write(msg + "\n")
    log_f.flush()

log("=" * 60)
log("QWEN 27B MINIMAL TRAINING LOOP")
log("=" * 60)

# Check GPU
if not torch.cuda.is_available():
    log("ERROR: No CUDA available")
    sys.exit(1)

device = torch.device("cuda:0")
log("GPU: " + str(torch.cuda.get_device_name(0)))
log("GPU Memory: %.1f GB" % (torch.cuda.get_device_properties(0).total_memory / 1e9))

# Import transformers
log("Importing transformers...")
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

# Load tokenizer
log("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
log("Tokenizer vocab size: %d" % len(tokenizer))

# Load model with direct GPU placement
log("Loading model to GPU (this will take ~4 minutes)...")
start = time.time()

config = AutoConfig.from_pretrained(MODEL_PATH, trust_remote_code=True)
config.vocab_size = len(tokenizer)
config.use_cache = False

model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    config=config,
    torch_dtype=torch.bfloat16,
    device_map={"": 0},
    trust_remote_code=True,
)

load_time = time.time() - start
log("Model loaded in %.1fs" % load_time)
log("Model device: " + str(next(model.parameters()).device))
log("Model dtype: " + str(next(model.parameters()).dtype))

# Count parameters
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
log("Total params: %.1fB" % (total_params/1e9))
log("Trainable: %.1fB" % (trainable_params/1e9))

# Enable gradient checkpointing
log("Enabling gradient checkpointing...")
model.gradient_checkpointing_enable()
model.enable_input_require_grads()

# Optimizer
log("Creating SGD optimizer...")
optimizer = torch.optim.SGD(model.parameters(), lr=LEARNING_RATE)
log("Optimizer: SGD, lr=%e" % LEARNING_RATE)

# Dataset
class SimpleDataset(Dataset):
    def __init__(self, hidden_states_dir, max_seq_len=256):
        self.files = sorted(glob.glob(os.path.join(hidden_states_dir, "*.pt")))
        self.max_seq_len = max_seq_len
        log("Found %d hidden state files" % len(self.files))
        
    def __len__(self):
        return len(self.files)
    
    def __getitem__(self, idx):
        data = torch.load(self.files[idx], map_location="cpu", weights_only=False)
        input_ids = data["input_ids"].squeeze(0)[:self.max_seq_len]
        
        if len(input_ids) < self.max_seq_len:
            padding = torch.zeros(self.max_seq_len - len(input_ids), dtype=torch.long)
            input_ids = torch.cat([input_ids, padding])
        
        labels = input_ids.clone()
        labels[:-1] = input_ids[1:]
        labels[-1] = tokenizer.pad_token_id
        
        return {
            "input_ids": input_ids,
            "labels": labels,
            "attention_mask": (input_ids != tokenizer.pad_token_id).long(),
        }

log("Creating dataset...")
dataset = SimpleDataset(HIDDEN_STATES_DIR, MAX_SEQ_LEN)

if len(dataset) == 0:
    log("ERROR: No data files found!")
    sys.exit(1)

log("Dataset size: %d" % len(dataset))

def collate_fn(batch):
    return {
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "labels": torch.stack([b["labels"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
    }

dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)

# Training loop
log("")
log("=" * 60)
log("STARTING TRAINING")
log("=" * 60)
log("Steps: %d, batch=%d, accum=%d" % (MAX_STEPS, BATCH_SIZE, GRAD_ACCUM_STEPS))

model.train()
global_step = 0
accumulated_loss = 0

for epoch in range(100):
    for batch_idx, batch in enumerate(dataloader):
        if global_step >= MAX_STEPS:
            break
        
        step_start = time.time()
        
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        
        log("")
        log("[Step %d/%d] Forward pass..." % (global_step+1, MAX_STEPS))
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
        )
        loss = outputs.loss / GRAD_ACCUM_STEPS
        
        log("[Step %d] Backward pass..." % (global_step+1))
        loss.backward()
        
        accumulated_loss += loss.item()
        
        if (batch_idx + 1) % GRAD_ACCUM_STEPS == 0:
            log("[Step %d] Optimizer step..." % (global_step+1))
            optimizer.step()
            optimizer.zero_grad()
            
            step_time = time.time() - step_start
            log("[Step %d] LOSS: %.4f | Time: %.1fs" % (global_step+1, accumulated_loss, step_time))
            
            global_step += 1
            accumulated_loss = 0
            
            mem_allocated = torch.cuda.memory_allocated(device) / 1e9
            mem_reserved = torch.cuda.memory_reserved(device) / 1e9
            log("[Step %d] GPU: %.1fGB allocated, %.1fGB reserved" % (global_step, mem_allocated, mem_reserved))
            
            if global_step >= MAX_STEPS:
                break
    
    if global_step >= MAX_STEPS:
        break

log("")
log("=" * 60)
log("TRAINING COMPLETE")
log("=" * 60)

ckpt_path = os.path.join(CHECKPOINT_DIR, "minimal_step_5.pt")
log("Saving checkpoint to %s..." % ckpt_path)
torch.save({
    "step": global_step,
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
}, ckpt_path)
log("Checkpoint saved!")

log("")
log("SUCCESS: Training loop verified!")
log_f.close()
