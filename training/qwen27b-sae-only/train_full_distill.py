#!/usr/bin/env python3
"""
Qwen 27B Full FT + Franken V8 Teacher Distillation
Working configuration based on minimal_v2 success.
"""
import os
import sys
import time
import glob
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# Paths
MODEL_PATH = "/data/models/Qwen3.6-27B-Uncensored/"
TEACHER_PATH = "/data/models/FrankenV8-Final/final_model.pt"
HIDDEN_STATES_DIR = "/data/SpecForge/custom_dflash/hidden_states/"
CHECKPOINT_DIR = "/data/SpecForge/custom_dflash/checkpoints/"
LOG_FILE = "/mnt/bigssd/train_full_distill.log"

# Training config
MAX_SEQ_LEN = 256
BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4
MAX_STEPS = 100  # 100 steps for this test
LEARNING_RATE = 1e-5
TEMPERATURE = 2.0  # For distillation
ALPHA = 0.5  # Weight for distillation loss (0.5 = equal mix)

os.makedirs(CHECKPOINT_DIR, exist_ok=True)

log_f = open(LOG_FILE, "w")
def log(msg):
    print(msg, flush=True)
    log_f.write(msg + "\n")
    log_f.flush()

log("=" * 60)
log("QWEN 27B + FRANKEN V8 DISTILLATION")
log("=" * 60)

if not torch.cuda.is_available():
    log("ERROR: No CUDA")
    sys.exit(1)

device = torch.device("cuda:0")
log("GPU: " + str(torch.cuda.get_device_name(0)))
log("GPU Memory: %.1f GB" % (torch.cuda.get_device_properties(0).total_memory / 1e9))

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

# Load tokenizer
log("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
log("Tokenizer vocab size: %d" % len(tokenizer))

# Load student model
log("Loading STUDENT model...")
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

load_time = time.time() - start
log("Student loaded in %.1fs" % load_time)
log("Student device: " + str(next(student.parameters()).device))

# Count parameters
total_params = sum(p.numel() for p in student.parameters())
log("Student params: %.1fB" % (total_params/1e9))

# Enable gradient checkpointing
log("Enabling gradient checkpointing...")
student.gradient_checkpointing_enable()
student.enable_input_require_grads()

# Load teacher model (Franken V8)
log("\nLoading TEACHER (Franken V8)...")
start = time.time()

# Teacher uses same architecture but loaded from checkpoint
teacher = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    config=config,
    torch_dtype=torch.bfloat16,
    device_map="cpu",  # Teacher on CPU to save GPU memory
    trust_remote_code=True,
)

# Load Franken weights
teacher_state = torch.load(TEACHER_PATH, map_location="cpu", weights_only=False)
if "model_state_dict" in teacher_state:
    teacher.load_state_dict(teacher_state["model_state_dict"], strict=False)
    log("Loaded Franken weights from checkpoint")
else:
    teacher.load_state_dict(teacher_state, strict=False)
    log("Loaded Franken weights directly")

teacher.eval()
for param in teacher.parameters():
    param.requires_grad = False

log("Teacher loaded in %.1fs" % (time.time() - start))
log("Teacher on CPU (frozen)")

# Optimizer
log("\nCreating SGD optimizer...")
optimizer = torch.optim.SGD(student.parameters(), lr=LEARNING_RATE)
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

log("\nCreating dataset...")
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

# Training loop
log("\n" + "=" * 60)
log("STARTING TRAINING")
log("=" * 60)
log("Steps: %d, batch=%d, accum=%d" % (MAX_STEPS, BATCH_SIZE, GRAD_ACCUM_STEPS))
log("Distillation: alpha=%.2f, temp=%.1f" % (ALPHA, TEMPERATURE))

student.train()
global_step = 0
accumulated_loss = 0

for epoch in range(1000):
    for batch_idx, batch in enumerate(dataloader):
        if global_step >= MAX_STEPS:
            break
        
        step_start = time.time()
        
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        
        # Student forward
        outputs = student(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
        )
        
        # Standard cross-entropy loss
        ce_loss = outputs.loss / GRAD_ACCUM_STEPS
        
        # Distillation loss (teacher on CPU)
        if ALPHA > 0:
            with torch.no_grad():
                teacher_outputs = teacher(
                    input_ids=input_ids.cpu(),
                    attention_mask=attention_mask.cpu(),
                )
                teacher_logits = teacher_outputs.logits.to(device)
            
            student_logits = outputs.logits
            
            # KL divergence for distillation
            teacher_probs = F.softmax(teacher_logits / TEMPERATURE, dim=-1)
            student_log_probs = F.log_softmax(student_logits / TEMPERATURE, dim=-1)
            
            # Only compute on non-padding tokens
            mask = attention_mask.unsqueeze(-1).expand_as(student_logits)
            kl_loss = F.kl_div(
                student_log_probs.view(-1, student_logits.size(-1)),
                teacher_probs.view(-1, teacher_logits.size(-1)),
                reduction="batchmean"
            ) * (TEMPERATURE ** 2) / GRAD_ACCUM_STEPS
            
            loss = (1 - ALPHA) * ce_loss + ALPHA * kl_loss
        else:
            loss = ce_loss
            kl_loss = torch.tensor(0.0)
        
        loss.backward()
        
        accumulated_loss += loss.item()
        
        if (batch_idx + 1) % GRAD_ACCUM_STEPS == 0:
            optimizer.step()
            optimizer.zero_grad()
            
            step_time = time.time() - step_start
            log("[Step %d/%d] CE: %.4f | KL: %.4f | Total: %.4f | Time: %.1fs" % (
                global_step + 1, MAX_STEPS, 
                ce_loss.item() * GRAD_ACCUM_STEPS,
                kl_loss.item() * GRAD_ACCUM_STEPS,
                accumulated_loss, step_time))
            
            global_step += 1
            accumulated_loss = 0
            
            mem_allocated = torch.cuda.memory_allocated(device) / 1e9
            mem_reserved = torch.cuda.memory_reserved(device) / 1e9
            log("  GPU: %.1fGB allocated, %.1fGB reserved" % (mem_allocated, mem_reserved))
            
            # Save checkpoint every 10 steps
            if global_step % 10 == 0:
                ckpt_path = os.path.join(CHECKPOINT_DIR, "distill_step_%d.pt" % global_step)
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

log("\n" + "=" * 60)
log("TRAINING COMPLETE")
log("=" * 60)

# Final checkpoint
ckpt_path = os.path.join(CHECKPOINT_DIR, "distill_final_step_%d.pt" % global_step)
log("Saving final checkpoint to %s..." % ckpt_path)
torch.save({
    "step": global_step,
    "model_state_dict": student.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
}, ckpt_path)
log("Final checkpoint saved!")

log("\nSUCCESS: Distillation training complete!")
log_f.close()
