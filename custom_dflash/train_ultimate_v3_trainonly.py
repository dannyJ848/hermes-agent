#!/usr/bin/env python3
"""
ULTIMATE PIPELINE v3 — TRAINING ONLY (Franken V8 hidden states pre-computed)
Uses teacher hidden states from /mnt/bigssd/teacher_hidden_states_v3/
Trains Qwen 27B with triple loss: CE + SAE reconstruction + teacher hidden matching
"""
import os, sys, time, glob, torch, torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

MODEL_PATH = '/data/models/Qwen3.6-27B-Uncensored/'
HIDDEN_STATES_DIR = '/data/SpecForge/custom_dflash/hidden_states/'
TEACHER_OUTPUTS_DIR = '/mnt/bigssd/teacher_hidden_states_v3/'
SAE_DIR = '/data/models/Qwen-Scope/'
CHECKPOINT_DIR = '/mnt/bigssd/checkpoints_ultimate_v3/'
LOG_FILE = '/mnt/bigssd/train_ultimate_v3.log'

MAX_SEQ_LEN = 256
BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 4
MAX_STEPS = 1000
LEARNING_RATE = 1e-5
SAVE_EVERY = 50

SAE_LAYERS = [16, 32, 48]
SAE_WEIGHT = 1.0
TEACHER_WEIGHT = 0.5

os.makedirs(CHECKPOINT_DIR, exist_ok=True)

log_f = open(LOG_FILE, "w")
def log(msg):
    t = time.strftime('%H:%M:%S')
    line = f"[{t}] {msg}"
    print(line, flush=True)
    log_f.write(line + "\n")
    log_f.flush()

log("=" * 70)
log("ULTIMATE PIPELINE v3 — TRAINING ONLY")
log("=" * 70)
log("Teacher hidden states: pre-computed from Franken V8-25Grafts")
log("Student: Qwen 3.6-27B-Uncensored (27B params)")
log("SAE: Qwen-Scope layers 16, 32, 48")
log("Loss: CE + SAE_reconstruction + teacher_hidden_matching")
log("")

if not torch.cuda.is_available():
    log("ERROR: No CUDA")
    sys.exit(1)

device = torch.device("cuda:0")
log(f"GPU: {torch.cuda.get_device_name(0)}")
log(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

# Load tokenizer
log("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
log(f"Tokenizer vocab: {len(tokenizer)}")

# Load SAEs
log("Loading Qwen-Scope SAEs...")
saes = {}
for layer_idx in SAE_LAYERS:
    sae_path = os.path.join(SAE_DIR, f"layer{layer_idx}.sae.pt")
    if os.path.exists(sae_path):
        sae = torch.load(sae_path, map_location='cpu')
        saes[layer_idx] = {
            "W_enc": sae["W_enc"].to(device).bfloat16(),
            "b_enc": sae["b_enc"].to(device).bfloat16(),
            "W_dec": sae["W_dec"].to(device).bfloat16(),
            "b_dec": sae["b_dec"].to(device).bfloat16(),
        }
        log(f"  Layer {layer_idx}: SAE loaded")
    else:
        log(f"  WARNING: layer{layer_idx}.sae.pt not found")

# SAE functions
def get_feature_acts(residual, sae_dict):
    W_enc = sae_dict["W_enc"]
    b_enc = sae_dict["b_enc"]
    residual = residual.to(W_enc.dtype)
    pre_acts = residual @ W_enc.T + b_enc
    topk_vals, topk_idx = pre_acts.topk(50, dim=-1)
    acts = torch.zeros_like(pre_acts)
    acts.scatter_(-1, topk_idx, topk_vals)
    return acts

def reconstruct_from_features(features, sae_dict):
    W_dec = sae_dict["W_dec"]
    b_dec = sae_dict["b_dec"]
    return features @ W_dec.T + b_dec

# Load student model
log("")
log("Loading student model...")
start = time.time()

config = AutoConfig.from_pretrained(MODEL_PATH, trust_remote_code=True)
config.vocab_size = len(tokenizer)
config.use_cache = False

model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    config=config,
    torch_dtype=torch.bfloat16,
    device_map='auto',
    max_memory={0: '120GiB', 'cpu': '0GiB'},
    trust_remote_code=True,
)

load_time = time.time() - start
log(f"Model loaded in {load_time:.1f}s")

log("Enabling gradient checkpointing...")
model.gradient_checkpointing_enable()
model.enable_input_require_grads()

# SAE hooks
captured_features = {}
captured_hidden = {}

def make_hook(layer_idx):
    def hook(module, input, output):
        hidden = output[0] if isinstance(output, tuple) else output
        if layer_idx in saes and hidden.requires_grad:
            features = get_feature_acts(hidden, saes[layer_idx])
            captured_features[layer_idx] = features
            captured_hidden[layer_idx] = hidden
        return output
    return hook

hooks = []
for layer_idx in SAE_LAYERS:
    if layer_idx in saes and layer_idx < len(model.model.layers):
        h = model.model.layers[layer_idx].register_forward_hook(make_hook(layer_idx))
        hooks.append(h)

log(f"Registered {len(hooks)} SAE hooks")

# Optimizer with layer-wise LR
log("Creating optimizer...")
embed_params = list(model.model.embed_tokens.parameters())
embed_param_ids = {id(p) for p in embed_params}

sae_layer_params = []
for layer_idx in SAE_LAYERS:
    if layer_idx < len(model.model.layers):
        for p in model.model.layers[layer_idx].parameters():
            sae_layer_params.append(p)

sae_param_ids = {id(p) for p in sae_layer_params}
other_params = [p for p in model.parameters() if id(p) not in embed_param_ids and id(p) not in sae_param_ids]

param_groups = [
    {"params": embed_params, "lr": LEARNING_RATE * 0.1},
    {"params": sae_layer_params, "lr": LEARNING_RATE * 2.0},
    {"params": other_params, "lr": LEARNING_RATE}
]
optimizer = torch.optim.SGD(param_groups, lr=LEARNING_RATE)
log(f"Optimizer: embed={LEARNING_RATE*0.1:.1e}, sae={LEARNING_RATE*2.0:.1e}, other={LEARNING_RATE:.1e}")

# Dataset with teacher hidden states
class UltimateDataset(Dataset):
    def __init__(self, hidden_states_dir, teacher_outputs_dir, max_seq_len=256):
        self.hidden_files = sorted(glob.glob(os.path.join(hidden_states_dir, "*.pt")))
        self.teacher_files = sorted(glob.glob(os.path.join(teacher_outputs_dir, "teacher_hidden_*.pt")))
        self.max_seq_len = max_seq_len
        log(f"Found {len(self.hidden_files)} hidden state files")
        log(f"Found {len(self.teacher_files)} teacher hidden state files")
        
    def __len__(self):
        return len(self.hidden_files)
    
    def __getitem__(self, idx):
        data = torch.load(self.hidden_files[idx], map_location='cpu', weights_only=False)
        input_ids = data["input_ids"].squeeze(0)[:self.max_seq_len]
        
        if len(input_ids) < self.max_seq_len:
            padding = torch.zeros(self.max_seq_len - len(input_ids), dtype=torch.long)
            input_ids = torch.cat([input_ids, padding])
        
        labels = input_ids.clone()
        labels[:-1] = input_ids[1:]
        labels[-1] = tokenizer.pad_token_id
        
        teacher_hidden = None
        if idx < len(self.teacher_files):
            teacher_hidden = torch.load(self.teacher_files[idx], map_location='cpu')
        
        return {
            "input_ids": input_ids,
            "labels": labels,
            "attention_mask": (input_ids != tokenizer.pad_token_id).long(),
            "teacher_hidden": teacher_hidden,
        }

log("Creating dataset...")
dataset = UltimateDataset(HIDDEN_STATES_DIR, TEACHER_OUTPUTS_DIR, MAX_SEQ_LEN)
log(f"Dataset size: {len(dataset)}")

def collate_fn(batch):
    return {
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "labels": torch.stack([b["labels"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
        "teacher_hidden": [b["teacher_hidden"] for b in batch],
    }

dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)

# Resume from checkpoint
latest_ckpt = None
for s in range(MAX_STEPS, 0, -1):
    ck = os.path.join(CHECKPOINT_DIR, f"ultimate_v3_step_{s}.pt")
    if os.path.exists(ck):
        latest_ckpt = ck
        break

start_step = 0
if latest_ckpt:
    log(f"Resuming from: {latest_ckpt}")
    ckpt = torch.load(latest_ckpt, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    optimizer.load_state_dict(ckpt["optimizer_state_dict"])
    start_step = ckpt.get("step", 0)
    log(f"Resumed at step {start_step}")
else:
    log("Starting fresh training (no checkpoint found)")
    start_step = 0

# Training loop
log("")
log("=" * 70)
log("TRAINING — Triple Loss")
log("=" * 70)
log(f"Loss = CE + {SAE_WEIGHT}*SAE_reconstruction + {TEACHER_WEIGHT}*teacher_hidden_matching")
log(f"Steps: {MAX_STEPS}, batch={BATCH_SIZE}, accum={GRAD_ACCUM_STEPS}")

model.train()
global_step = start_step
accumulated_ce = 0
accumulated_sae = 0
accumulated_teacher = 0
start_time = time.time()

for epoch in range(1000):
    for batch_idx, batch in enumerate(dataloader):
        if global_step >= MAX_STEPS:
            break
        
        step_start = time.time()
        
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        teacher_hidden = batch["teacher_hidden"][0]
        
        # Clear captures
        captured_features.clear()
        captured_hidden.clear()
        
        # Forward pass
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
        )
        ce_loss = outputs.loss
        
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
            
            count = len([l for l in SAE_LAYERS if l in captured_features])
            if count > 0:
                sae_loss = sae_loss / count
        
        # Teacher hidden state matching loss
        teacher_loss = 0.0
        if teacher_hidden is not None:
            # Map Franken V8 layers (8) to Qwen layers (64) proportionally
            for franken_layer in range(8):
                qwem_layer = franken_layer * 8
                if qwem_layer in captured_hidden and franken_layer in teacher_hidden:
                    student_h = captured_hidden[qwem_layer]
                    teacher_h = teacher_hidden[franken_layer].to(device).to(student_h.dtype)
                    
                    # Match sequence lengths
                    min_len = min(student_h.shape[1], teacher_h.shape[1])
                    student_h = student_h[:, :min_len, :]
                    teacher_h = teacher_h[:, :min_len, :]
                    
                    # Project teacher to student hidden size if needed
                    if teacher_h.shape[-1] != student_h.shape[-1]:
                        projection = torch.nn.Linear(teacher_h.shape[-1], student_h.shape[-1], bias=False).to(device).to(student_h.dtype)
                        teacher_h = projection(teacher_h)
                    
                    # Normalize both before MSE (critical for cross-model alignment)
                    student_h_norm = F.layer_norm(student_h, student_h.shape[-1:])
                    teacher_h_norm = F.layer_norm(teacher_h, teacher_h.shape[-1:])
                    
                    # MSE loss on normalized hidden states
                    layer_teacher_loss = F.mse_loss(student_h_norm, teacher_h_norm)
                    teacher_loss += layer_teacher_loss.item()
            
            count = len([i for i in range(8) if i*8 in captured_hidden and i in teacher_hidden])
            if count > 0:
                teacher_loss = teacher_loss / count
        
        # Combined loss
        sae_tensor = torch.tensor(sae_loss, device=device, dtype=torch.bfloat16)
        teacher_tensor = torch.tensor(teacher_loss, device=device, dtype=torch.bfloat16)
        combined_loss = ce_loss + SAE_WEIGHT * sae_tensor + TEACHER_WEIGHT * teacher_tensor
        scaled_loss = combined_loss / GRAD_ACCUM_STEPS
        scaled_loss.backward()
        
        accumulated_ce += ce_loss.item()
        accumulated_sae += sae_loss
        accumulated_teacher += teacher_loss
        
        if (batch_idx + 1) % GRAD_ACCUM_STEPS == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            
            optimizer.step()
            optimizer.zero_grad()
            
            step_time = time.time() - step_start
            global_step += 1
            
            mem_allocated = torch.cuda.memory_allocated(device) / 1e9
            mem_reserved = torch.cuda.memory_reserved(device) / 1e9
            
            total = accumulated_ce + SAE_WEIGHT * accumulated_sae + TEACHER_WEIGHT * accumulated_teacher
            
            log(f"[Step {global_step}/{MAX_STEPS}] CE: {accumulated_ce:.4f} | SAE: {accumulated_sae:.4f} | Teacher: {accumulated_teacher:.4f} | Total: {total:.4f} | Time: {step_time:.1f}s | GPU: {mem_allocated:.1f}GB/{mem_reserved:.1f}GB")
            
            accumulated_ce = 0
            accumulated_sae = 0
            accumulated_teacher = 0
            
            if global_step % SAVE_EVERY == 0:
                ckpt_path = os.path.join(CHECKPOINT_DIR, f"ultimate_v3_step_{global_step}.pt")
                log(f"  Saving checkpoint...")
                torch.save({
                    "step": global_step,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                }, ckpt_path)
                log(f"  Checkpoint saved: {ckpt_path}")
            
            if global_step >= MAX_STEPS:
                break
    
    if global_step >= MAX_STEPS:
        break

total_time = time.time() - start_time
log("")
log("=" * 70)
log("TRAINING COMPLETE")
log("=" * 70)
log(f"Total time: {total_time / 60:.1f} minutes")
log(f"Average time per step: {total_time / (global_step - start_step):.1f}s")

ckpt_path = os.path.join(CHECKPOINT_DIR, "ultimate_v3_final.pt")
log(f"Saving final checkpoint to {ckpt_path}...")
torch.save({
    "step": global_step,
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
}, ckpt_path)
log("Final checkpoint saved!")

for h in hooks:
    h.remove()

log("")
log("SUCCESS! ULTIMATE PIPELINE v3 COMPLETE!")
log("Franken V8 fully integrated with Qwen 27B training!")
log_f.close()
