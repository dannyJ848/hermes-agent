# Qwen 27B Expert Logician Training — Master Document
## Session: May 3, 2026 | Branch: qwen27b-training-artifacts-may3-2026

---

## Mission
Train Qwen3.6-27B-Uncensored to be a Claude-level expert logician with strong reasoning, coding, tool calling, and iterative ability.

## Hardware
- DGX Spark with NVIDIA GB10 (130.7GB GPU, 128GB RAM, 8TB SSD)

## Datasets
- curatedthoughts: /data/datasets/curatedthoughts/ (~16.5k samples)
- openthoughts2-1m: /data/datasets/openthoughts2-1m/ (~30k samples)
- Total: ~46k samples (Parquet format)

## What We Tried (15+ attempts, all failed)

### 1. Full Fine-Tuning v4 (AdamW, WSD-S schedule, SAE-guided)
- Script: `training/qwen27b-sae-only/train_expert_logician_v4.py`
- Optimizer: AdamW with CPU offloading for optimizer states
- Batch: 1, grad accum 16, effective 16
- Sequence: 4096
- **Failure**: GPU OOM during backward pass. 27B model + gradients + temp buffers > 130GB even with optimizer states on CPU.

### 2. Streaming Dataset Fix
- Rewrote dataset to stream Parquet files on-the-fly instead of loading all into RAM
- **Fixed RAM OOM** (was loading 46k tokenized tensors into 128GB RAM)
- **Still GPU OOM**: Backward pass needs ~27GB gradients + ~30GB temp buffers on top of ~27GB model

### 3. DeepSpeed ZeRO-3 Offload
- Script: `training/qwen27b-deepspeed/train_deepspeed_zero3_v1.py`
- Config: `ds_config_zero3_offload.json`
- **Failure**: NCCL CUDA OOM during process group initialization. NCCL allocates communication buffers before DeepSpeed can partition model. 27B model leaves no room for NCCL.

### 4. Manual Memory Management (SGD, no gradient checkpointing)
- Script: `training/qwen27b-manual/train_manual_v1.py`
- Strategy: SGD (saves 54GB vs AdamW), bf16, seq 1024, no grad checkpointing
- **Failure**: Qwen3.5 `linear_attn` layer has gradient checkpointing incompatibility bug — expects 3D input `(batch, seq, hidden)` but gets 2D during backward. Even with grad checkpointing disabled, the model's own internal checkpointing triggers the same bug.

### 5. LoRA (abandoned — user wants full fine-tune)
- Script: `training/qwen27b-lora/train_lora_v1.py` (never ran)

---

## Root Causes

1. **GPU Memory Wall**: 27B model in bf16 = 54GB (bf16 weights + bf16 gradients). Add temp buffers for backward = ~30GB. Total ~84GB minimum just for forward+backward. AdamW optimizer states = another 108GB (fp32 copy of params + momentum + variance). Total: 192GB minimum for full AdamW fine-tuning. We have 130GB.

2. **Qwen3.5 Architecture Bug**: `modeling_qwen3_5.py` line 431 — `linear_attn` layer unpacks `hidden_states.shape` as `(batch_size, seq_len, _)` but gradient checkpointing passes 2D tensor. This is a bug in the model code, not our training code.

3. **DeepSpeed/NCCL Bootstrap**: Even ZeRO-3 Offload needs NCCL to initialize, and NCCL allocates GPU buffers before model partitioning happens.

---

## Key Files in Branch

| File | Purpose |
|------|---------|
| `franken_v8_bridge_v3.py` | Complete Franken V8 bridge |
| `train_ultimate_v3_trainonly.py` | Previous training script (reference) |
| `precompute_teacher_v2.py` | Teacher hidden state precomputation |
| `evaluate_checkpoints.py` | Checkpoint evaluation |
| `training/qwen27b-sae-only/train_expert_logician_v4.py` | Full fine-tuning attempt (streaming dataset, AdamW CPU offload) |
| `training/qwen27b-deepspeed/train_deepspeed_zero3_v1.py` | DeepSpeed ZeRO-3 attempt |
| `training/qwen27b-deepspeed/ds_config_zero3_offload.json` | DeepSpeed config |
| `training/qwen27b-manual/train_manual_v1.py` | SGD manual memory attempt |
| `training/qwen27b-lora/train_lora_v1.py` | LoRA script (unused) |

---

## What Would Work

1. **More GPU Memory**: 192GB+ GPU (H100 80GB x 3, or A100 80GB x 3 with DeepSpeed)
2. **Fix Qwen3.5 Bug**: Patch `modeling_qwen3_5.py` line 431 to handle 2D input in `linear_attn`
3. **8-bit Optimizer**: Use `bitsandbytes` 8-bit AdamW (saves ~54GB optimizer state memory)
4. **Gradient Checkpointing Fix**: Fix the Qwen model's `linear_attn` to be compatible with `torch.utils.checkpoint`
5. **Pipeline Parallelism**: Split model across 2+ GPUs (not available on single DGX Spark)

---

## Next Steps for New CLI

1. **Decide approach**: Full fine-tune requires either more hardware or fixing the Qwen bug
2. **If continuing**: Try 8-bit AdamW (`pip install bitsandbytes`, use `bnb.optim.Adam8bit`) + fix Qwen `linear_attn` shape handling
3. **If scaling up**: Need multi-GPU setup (2x H100 80GB minimum for comfortable training)
4. **If abandoning full-FT**: LoRA works on 130GB GPU (trainable params ~500M instead of 27B)

---

## Contact
- Danny (dannyJ848) — repo owner, custom loop guard modifications
- Hermes Agent — this session's operator
