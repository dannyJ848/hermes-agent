#!/usr/bin/env python3
"""
Qwen 27B Full FT - Standard Training (no teacher)
Proven working configuration from minimal_v2.
"""
import os
import sys
import time
import glob
import torch
from torch.utils.data import Dataset, DataLoader

MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored/"
HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states/"
CHECKPOINT_DIR = "/data/SpecForge/custom_dflash/checkpoints/"
LOG_FILE = "/mnt/bigssd/train_standard.log"

MAX_SEQ_LEN = 256
BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4
MAX_STEPS = 1000
LEARNING_RATE = 1e-5
SAVE_EVERY = 50  # Save checkpoint every 50 steps

os.makedirs(CHECKPOINT_DIR, exist_ok=True)

log_f = open(LOG_FILE, "w")
def log(msg):
    print(msg, flush=True)
    log_f.write(msg + "\n")
    log_f.flush()

log("=" * 60)
log("QWEN 27B STANDARD TRAINING")
log("=" * 60)

if not torch.cuda.is_available():
    log("ERROR: No CUDA")
    sys.exit(1)

device = torch.device("cuda:0")
log("GPU: " + str(torch.cuda.get_device_name(0)))
log("GPU Memory: %.1f GB" % (torch.cuda.get_device_properties(0).total_memory / 1e9))

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

log("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
log("Tokenizer vocab size: %d" % len(tokenizer))

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

load_time = time.time() - start
log("Model loaded in %.1fs" % load_time)
log("Model device: " + str(next(model.parameters()).device))

total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
log("Total params: %.1fB" % (total_params/1e9))
log("Trainable: %.1fB" % (trainable_params/1e9))

log("Enabling gradient checkpointing...")
model.gradient_checkpointing_enable()
model.enable_input_require_grads()

log("Creating SGD optimizer...")
optimizer = torch.optim.SGD(model.parameters(), lr=LEARNING_RATE)
log("Optimizer: SGD, lr=%e" % LEARNING_RATE)

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
    log("ERROR: No data files!")
    sys.exit(1)

log("Dataset size: %d" % len(dataset))

def collate_fn(batch):
    return {
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "labels": torch.stack([b["labels"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
    }

dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)

log("\n" + "=" * 60)
log("STARTING TRAINING")
log("=" * 60)
log("Steps: %d, batch=%d, accum=%d" % (MAX_STEPS, BATCH_SIZE, GRAD_ACCUM_STEPS))

model.train()
global_step = 0
accumulated_loss = 0
start_time = time.time()

for epoch in range(1000):
    for batch_idx, batch in enumerate(dataloader):
        if global_step >= MAX_STEPS:
            break
        
        step_start = time.time()
        
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
        )
        loss = outputs.loss / GRAD_ACCUM_STEPS
        loss.backward()
        
        accumulated_loss += loss.item()
        
        if (batch_idx + 1) % GRAD_ACCUM_STEPS == 0:
            optimizer.step()
            optimizer.zero_grad()
            
            step_time = time.time() - step_start
            global_step += 1
            
            mem_allocated = torch.cuda.memory_allocated(device) / 1e9
            mem_reserved = torch.cuda.memory_reserved(device) / 1e9
            
            log("[Step %d/%d] Loss: %.4f | Time: %.1fs | GPU: %.1fGB/%.1fGB" % (
                global_step, MAX_STEPS, accumulated_loss, step_time,
                mem_allocated, mem_reserved))
            
            accumulated_loss = 0
            
            # Save checkpoint every SAVE_EVERY steps
            if global_step % SAVE_EVERY == 0:
                ckpt_path = os.path.join(CHECKPOINT_DIR, "standard_step_%d.pt" % global_step)
                log("  Saving checkpoint...")
                torch.save({
                    "step": global_step,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                }, ckpt_path)
                log("  Checkpoint saved: %s" % ckpt_path)
            
            if global_step >= MAX_STEPS:
                break
    
    if global_step >= MAX_STEPS:
        break

total_time = time.time() - start_time
log("\n" + "=" * 60)
log("TRAINING COMPLETE")
log("=" * 60)
log("Total time: %.1f minutes" % (total_time / 60))
log("Average time per step: %.1fs" % (total_time / global_step))

# Final checkpoint
ckpt_path = os.path.join(CHECKPOINT_DIR, "standard_final_step_%d.pt" % global_step)
log("Saving final checkpoint to %s..." % ckpt_path)
torch.save({
    "step": global_step,
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
}, ckpt_path)
log("Final checkpoint saved!")

log("\nSUCCESS!")
log_f.close()
