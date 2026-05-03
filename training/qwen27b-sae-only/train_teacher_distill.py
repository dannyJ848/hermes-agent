#!/usr/bin/env python3
"""
Qwen 27B Full FT - Teacher Distillation + SAE Integration
Architecture: Qwen+SAEs=student (trainable), Franken=teacher (frozen)
Teacher outputs pre-computed to avoid CPU bottleneck
"""
import os
import sys
import time
import glob
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored/"
TEACHER_PATH = "/data/models/FrankenV8-Final/final_model.pt"
HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states/"
CHECKPOINT_DIR = "/data/SpecForge/custom_dflash/checkpoints/"
TEACHER_OUTPUTS_DIR = "/data/SpecForge/custom_dflash/teacher_outputs/"
LOG_FILE = "/mnt/bigssd/train_teacher_distill.log"

MAX_SEQ_LEN = 256
BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4
MAX_STEPS = 1000
LEARNING_RATE = 1e-5
SAVE_EVERY = 50

# Distillation weights
ALPHA_CE = 0.7      # Cross-entropy weight
ALPHA_KL = 0.3      # KL divergence weight
TEMPERATURE = 2.0   # Softmax temperature for distillation

os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(TEACHER_OUTPUTS_DIR, exist_ok=True)

log_f = open(LOG_FILE, "w")
def log(msg):
    print(msg, flush=True)
    log_f.write(msg + "\n")
    log_f.flush()

log("=" * 60)
log("QWEN 27B + FRANKEN V8 TEACHER DISTILLATION")
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

# ============================================================
# LOAD STUDENT (Qwen 27B) - Trainable, on GPU
# ============================================================
log("Loading STUDENT model (Qwen 27B)...")
start = time.time()

config = AutoConfig.from_pretrained(MODEL_PATH, trust_remote_code=True)
config.vocab_size = len(tokenizer)
config.use_cache = False

student = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    config=config,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    max_memory={0: "120GiB", "cpu": "0GiB"},
    trust_remote_code=True,
)

student_load_time = time.time() - start
log("Student loaded in %.1fs" % student_load_time)
log("Student device: " + str(next(student.parameters()).device))

total_params = sum(p.numel() for p in student.parameters())
trainable_params = sum(p.numel() for p in student.parameters() if p.requires_grad)
log("Student params: %.1fB (trainable: %.1fB)" % (total_params/1e9, trainable_params/1e9))

log("Enabling gradient checkpointing...")
student.gradient_checkpointing_enable()
student.enable_input_require_grads()

# ============================================================
# LOAD TEACHER (Franken V8) - Frozen, on CPU
# ============================================================
log("\nLoading TEACHER model (Franken V8)...")
start = time.time()

# Franken V8 is a modified Qwen - load with same config but freeze
# Force CPU-only loading to avoid GPU OOM
teacher = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    config=config,
    torch_dtype=torch.bfloat16,
    device_map=None,  # No auto device mapping
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

# Freeze teacher
for param in teacher.parameters():
    param.requires_grad = False
teacher.eval()

teacher_load_time = time.time() - start
log("Teacher loaded in %.1fs" % teacher_load_time)
log("Teacher device: CPU (frozen)")

# ============================================================
# PRE-COMPUTE TEACHER OUTPUTS
# ============================================================
log("\n" + "=" * 60)
log("PRE-COMPUTING TEACHER OUTPUTS")
log("=" * 60)

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

if len(dataset) == 0:
    log("ERROR: No data files!")
    sys.exit(1)

def collate_fn(batch):
    return {
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "labels": torch.stack([b["labels"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
        "file_idx": [b["file_idx"] for b in batch],
    }

dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)

# Pre-compute teacher logits for all samples
log("Pre-computing teacher logits (this may take a while)...")
teacher_start = time.time()

teacher_logits_cache = {}
with torch.no_grad():
    for batch_idx, batch in enumerate(dataloader):
        input_ids = batch["input_ids"]
        attention_mask = batch["attention_mask"]
        file_idx = batch["file_idx"][0]
        
        # Teacher forward on CPU
        teacher_outputs = teacher(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        
        # Store logits (move to GPU for distillation)
        teacher_logits = teacher_outputs.logits.to(device)
        teacher_logits_cache[file_idx] = teacher_logits
        
        if (batch_idx + 1) % 10 == 0:
            log("  Pre-computed %d/%d teacher outputs" % (batch_idx + 1, len(dataset)))

teacher_precompute_time = time.time() - teacher_start
log("Teacher pre-computation complete: %.1fs" % teacher_precompute_time)
log("Cached %d teacher outputs" % len(teacher_logits_cache))

# Free teacher model from memory
del teacher
torch.cuda.empty_cache()
log("Teacher model unloaded from memory")

# ============================================================
# OPTIMIZER
# ============================================================
log("\nCreating SGD optimizer...")
optimizer = torch.optim.SGD(student.parameters(), lr=LEARNING_RATE)
log("Optimizer: SGD, lr=%e" % LEARNING_RATE)

# ============================================================
# TRAINING LOOP
# ============================================================
log("\n" + "=" * 60)
log("STARTING TRAINING")
log("=" * 60)
log("Steps: %d, batch=%d, accum=%d" % (MAX_STEPS, BATCH_SIZE, GRAD_ACCUM_STEPS))
log("Distillation: CE=%.1f, KL=%.1f, T=%.1f" % (ALPHA_CE, ALPHA_KL, TEMPERATURE))

student.train()
global_step = 0
accumulated_loss = 0
start_time = time.time()

# Create shuffled dataloader for training
train_dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)

for epoch in range(1000):
    for batch_idx, batch in enumerate(train_dataloader):
        if global_step >= MAX_STEPS:
            break
        
        step_start = time.time()
        
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        file_idx = batch["file_idx"][0]
        
        # Student forward
        student_outputs = student(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
        )
        
        # Cross-entropy loss
        ce_loss = student_outputs.loss / GRAD_ACCUM_STEPS
        
        # KL distillation loss (if teacher output cached)
        kl_loss = 0
        if file_idx in teacher_logits_cache:
            teacher_logits = teacher_logits_cache[file_idx]
            student_logits = student_outputs.logits
            
            # Temperature-scaled softmax
            teacher_probs = F.softmax(teacher_logits / TEMPERATURE, dim=-1)
            student_log_probs = F.log_softmax(student_logits / TEMPERATURE, dim=-1)
            
            # KL divergence
            kl_loss = F.kl_div(
                student_log_probs.view(-1, student_log_probs.size(-1)),
                teacher_probs.view(-1, teacher_probs.size(-1)),
                reduction="batchmean",
            ) * (TEMPERATURE ** 2) / GRAD_ACCUM_STEPS
        
        # Combined loss
        loss = ALPHA_CE * ce_loss + ALPHA_KL * kl_loss
        loss.backward()
        
        accumulated_loss += loss.item()
        
        if (batch_idx + 1) % GRAD_ACCUM_STEPS == 0:
            optimizer.step()
            optimizer.zero_grad()
            
            step_time = time.time() - step_start
            global_step += 1
            
            mem_allocated = torch.cuda.memory_allocated(device) / 1e9
            mem_reserved = torch.cuda.memory_reserved(device) / 1e9
            
            log("[Step %d/%d] Loss: %.4f (CE=%.4f, KL=%.4f) | Time: %.1fs | GPU: %.1fGB/%.1fGB" % (
                global_step, MAX_STEPS, accumulated_loss, ce_loss.item() * GRAD_ACCUM_STEPS,
                kl_loss.item() * GRAD_ACCUM_STEPS if isinstance(kl_loss, torch.Tensor) else 0,
                step_time, mem_allocated, mem_reserved))
            
            accumulated_loss = 0
            
            # Save checkpoint
            if global_step % SAVE_EVERY == 0:
                ckpt_path = os.path.join(CHECKPOINT_DIR, "teacher_distill_step_%d.pt" % global_step)
                log("  Saving checkpoint...")
                torch.save({
                    "step": global_step,
                    "model_state_dict": student.state_dict(),
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
ckpt_path = os.path.join(CHECKPOINT_DIR, "teacher_distill_final_step_%d.pt" % global_step)
log("Saving final checkpoint to %s..." % ckpt_path)
torch.save({
    "step": global_step,
    "model_state_dict": student.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
}, ckpt_path)
log("Final checkpoint saved!")

log("\nSUCCESS!")
log_f.close()
