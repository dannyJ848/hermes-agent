# DGX Training Process Management — May 3-4, 2026 Sessions

## Context
Training Qwen3.6-27B-Uncensored (27B params, bf16) on DGX Spark with NVIDIA GB10 (130.7GB GPU, 128GB RAM, 8TB SSD).

## Critical Pitfalls Discovered

### 1. Dataset Paths ≠ Expected Names
**Expected:** `/data/datasets/slimorca/`, `/data/datasets/openhermes/`  
**Actual:** `/data/datasets/curatedthoughts/`, `/data/datasets/openthoughts2-1m/`  
**Fix:** Always `ls` the directory before assuming paths. Parquet format, not JSONL.

### 2. Parquet `conversations` Column = numpy arrays
Loading Parquet `conversations` gives numpy arrays, which fail Python truthiness checks (`ValueError: ambiguous truth value`).  
**Fix:** `.tolist()` before iterating.

### 3. Qwen3.5 Gradient Checkpointing — FIXED May 4, 2026

**OLD understanding (May 3):** Gradient checkpointing broken in Qwen3.5 `linear_attn` layer. `ValueError: not enough values to unpack (expected 3, got 2)`.

**NEW understanding (May 4):** The bug was specifically with `use_reentrant=True` (the default). With `use_reentrant=False`, gradient checkpointing works stably on Qwen3.5 custom attention kernels.

**The fix:**
```python
# OLD (broken — causes deadlock):
model.gradient_checkpointing_enable()  # defaults to use_reentrant=True

# NEW (stable — validated 5+ steps, 58.3GB peak):
model.gradient_checkpointing_enable({"use_reentrant": False})
```

**Impact:** This unlocks ~30-40GB memory savings, making advanced LoRA + SAE + teacher distillation viable on 130GB GPU. Without it, training OOMs at 110GB+ with no stack trace (Linux OOM killer SIGKILL).

**Validation:**
- Before fix: batch=4, no checkpointing → 110.85GB peak → OOM kill at step 0
- After fix: batch=1, checkpointing+use_reentrant=False → 58.3GB peak → stable training

### 4. DeepSpeed NCCL Bootstrap OOM
**Error:** `ncclUnhandledCudaError: Cuda failure 'out of memory'` during `torch.distributed.init_process_group()`  
**Root cause:** NCCL allocates communication buffers BEFORE DeepSpeed can partition the model. With 27B model loaded, no room for NCCL.  
**Fix:** None on single GPU. Need multi-GPU or `deepspeed.zero.Init()` with meta-device model creation (still failed in our tests).

### 5. AdamW Optimizer State Memory
AdamW on 27B model = 108GB optimizer states (fp32 params + momentum + variance).  
**Options:**
- CPU offload: saves GPU but needs 108GB RAM (we have 128GB, barely fits)
- 8-bit AdamW (`bitsandbytes`): saves ~54GB, validated working
- SGD: saves all 108GB but needs higher LR, less stable

### 6. Streaming Dataset Required
Loading 46k tokenized samples into RAM = OOM killer (SIGKILL, exit 137).  
**Fix:** Stream Parquet files on-the-fly. Never load entire dataset into memory.

### 7. SSH Unresponsive During Training
DGX Spark SSH times out under heavy GPU load.  
**Rule:** Do NOT panic-kill processes. System prioritizes training over network I/O. Use `process_poll` or check log files instead of SSH.

### 8. Silent OOM Kill Pattern (May 4)
When training OOMs on DGX, there is NO Python stack trace. Linux OOM killer sends SIGKILL, which terminates the process instantly.

**Symptoms:**
- Log ends abruptly at "STARTING TRAINING" or mid-step
- No error message, no traceback
- `nvidia-smi` shows 0% util, N/A memory (process dead, GPU freed)
- `dmesg | grep -i 'killed process'` shows: `Killed process <pid> (python3)`

**Fix path (validated):**
1. Enable gradient checkpointing with `use_reentrant=False`
2. Reduce batch_size to 1 (keep grad_accum=4 for effective batch=16)
3. Combined result: 110.85GB → 58.3GB peak VRAM

See `references/oom-gradient-checkpointing-fix.md` in the qwen27b-training-pipeline skill for full reproduction.

## Memory Budget Math (27B Full Fine-Tuning)

| Component | Size | Notes |
|-----------|------|-------|
| Model weights (bf16) | 54GB | 27B × 2 bytes |
| Gradients (bf16) | 54GB | Same as weights |
| Activations (no ckpt) | ~40GB | seq 1024, batch 1 |
| Temp buffers | ~15GB | Backward temporaries |
| **Total forward+backward** | **~163GB** | **> 130GB GPU = OOM** |
| AdamW optimizer states | 108GB | fp32 copy + momentum + variance |
| **Total with AdamW** | **~271GB** | **Impossible on single GPU** |

With gradient checkpointing (use_reentrant=False): saves ~30-40GB activations → ~123-133GB (barely fits, need batch=1).

## What Actually Works on This Hardware

1. **LoRA** (rank 64-256): ~500M-1.27B trainable params, fits comfortably
2. **QLoRA** (4-bit + LoRA): Even smaller footprint
3. **SAE-guided LoRA**: Add Qwen-Scope feature alignment for quality boost
4. **Teacher distillation + LoRA**: Franken V8 hidden-state distillation
5. **8-bit AdamW**: Reduces optimizer state memory by ~50%
6. **Gradient checkpointing + use_reentrant=False**: Essential for 27B on 130GB GPU

## Log File Locations
- `/mnt/bigssd/train_expert_logician_v4.log` — AdamW attempt
- `/mnt/bigssd/train_deepspeed_zero3_v1.log` — DeepSpeed attempt
- `/mnt/bigssd/train_manual_v1.log` — SGD manual attempt
- `/mnt/bigssd/train_lora_sae_teacher_v1.log` — LoRA+SAE+teacher distillation (current)

## Scripts in Branch
- `training/qwen27b-sae-only/train_expert_logician_v4.py` — Full FT with streaming dataset, AdamW CPU offload
- `training/qwen27b-deepspeed/train_deepspeed_zero3_v1.py` — DeepSpeed ZeRO-3 Offload
- `training/qwen27b-manual/train_manual_v1.py` — SGD, no grad checkpointing
- `training/qwen27b-lora-sae-teacher/train_lora_sae_teacher_v1.py` — LoRA+SAE+teacher (current, validated)
