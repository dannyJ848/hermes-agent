#!/usr/bin/env python3
"""
Stage 1: Pre-compute Franken V8 teacher outputs on CPU
No GPU needed - runs entirely on CPU
"""
import os
import sys
import time
import glob
import torch
from torch.utils.data import Dataset, DataLoader

MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored/"
TEACHER_PATH = "/data/models/FrankenV8-Final/final_model.pt"
HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states/"
TEACHER_OUTPUTS_DIR = "/data/SpecForge/custom_dflash/teacher_outputs/"
LOG_FILE = "/mnt/bigssd/precompute_teacher.log"

MAX_SEQ_LEN = 256
BATCH_SIZE = 1

os.makedirs(TEACHER_OUTPUTS_DIR, exist_ok=True)

log_f = open(LOG_FILE, "w")
def log(msg):
    print(msg, flush=True)
    log_f.write(msg + "\n")
    log_f.flush()

log("=" * 60)
log("PRE-COMPUTING TEACHER OUTPUTS (CPU ONLY)")
log("=" * 60)

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

log("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
log("Tokenizer vocab size: %d" % len(tokenizer))

log("\nLoading TEACHER model (Franken V8) on CPU...")
start = time.time()

config = AutoConfig.from_pretrained(MODEL_PATH, trust_remote_code=True)
config.vocab_size = len(tokenizer)
config.use_cache = False

# Force CPU-only - no GPU memory used
teacher = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    config=config,
    torch_dtype=torch.float32,  # Use float32 on CPU for stability
    device_map=None,
    trust_remote_code=True,
).to("cpu")

# Load Franken V8 weights
teacher_state = torch.load(TEACHER_PATH, map_location="cpu", weights_only=False)
if "model_state_dict" in teacher_state:
    teacher.load_state_dict(teacher_state["model_state_dict"], strict=False)
    log("Loaded teacher weights from checkpoint")
else:
    teacher.load_state_dict(teacher_state, strict=False)
    log("Loaded teacher weights directly")

# Freeze and eval
for param in teacher.parameters():
    param.requires_grad = False
teacher.eval()

log("Teacher loaded in %.1fs" % (time.time() - start))
log("Teacher on CPU, frozen")

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
            "file_idx": idx,
        }

dataset = SimpleDataset(HIDDEN_STATES_DIR, MAX_SEQ_LEN)

def collate_fn(batch):
    return {
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "labels": torch.stack([b["labels"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
        "file_idx": [b["file_idx"] for b in batch],
    }

dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)

# Pre-compute and save teacher logits
log("\n" + "=" * 60)
log("PRE-COMPUTING TEACHER LOGITS")
log("=" * 60)

total_start = time.time()
with torch.no_grad():
    for batch_idx, batch in enumerate(dataloader):
        input_ids = batch["input_ids"]
        attention_mask = batch["attention_mask"]
        file_idx = batch["file_idx"][0]
        
        # Teacher forward on CPU
        outputs = teacher(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        
        # Save logits (as float16 to save disk space)
        logits = outputs.logits.to(torch.float16)
        save_path = os.path.join(TEACHER_OUTPUTS_DIR, "teacher_logits_%04d.pt" % file_idx)
        torch.save({"logits": logits, "file_idx": file_idx}, save_path)
        
        if (batch_idx + 1) % 5 == 0 or batch_idx == 0:
            elapsed = time.time() - total_start
            rate = (batch_idx + 1) / elapsed
            remaining = (len(dataset) - batch_idx - 1) / rate if rate > 0 else 0
            log("  [%d/%d] Saved: %s | Elapsed: %.1fs | ETA: %.1fs" % (
                batch_idx + 1, len(dataset), save_path, elapsed, remaining))

total_time = time.time() - total_start
log("\n" + "=" * 60)
log("PRE-COMPUTATION COMPLETE")
log("=" * 60)
log("Total time: %.1f minutes" % (total_time / 60))
log("Average per sample: %.1fs" % (total_time / len(dataset)))
log("Output dir: %s" % TEACHER_OUTPUTS_DIR)
log("Files saved: %d" % len(os.listdir(TEACHER_OUTPUTS_DIR)))

log("\nSUCCESS! Teacher outputs cached.")
log_f.close()
