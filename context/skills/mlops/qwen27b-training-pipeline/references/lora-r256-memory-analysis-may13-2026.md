# r=256 vs r=128 Memory Analysis — Qwen 27B LoRA on DGX Spark GB10

**Date:** May 13, 2026
**Context:** Determining if LoRA r=256 fits on GB10 with gradient checkpointing enabled

## Memory Calculation

Qwen 27B has ~7 target modules per layer, ~64 layers.
LoRA params scale linearly with rank: `params = 2 * r * (d_in + d_out)` per module.

| Config | Trainable Params | GPU Memory | Step Time |
|--------|-----------------|------------|-----------|
| r=128 | 637M (2.3% of total) | ~58GB | ~38s/step |
| r=256 | 1.27B (4.6% of total) | ~62GB | ~40s/step |
| Difference | +637M params | +4GB | +2s/step |

**Breakdown of extra memory for r=256:**
- Adapter weights (bf16): +1.3GB
- Optimizer states (8-bit AdamW): +0.6GB  
- Gradients: +1.3GB
- **Total extra: ~3.2GB**

## Why r=256 Works Now

Earlier r=256 attempts FAILED because:
1. **Without gradient checkpointing:** Total memory hit 117GB+ (OOM at 121GB limit)
2. **With CPU-only PyTorch in train-venv:** "Deadlock" was actually failed CUDA initialization

r=256 works with:
1. **Gradient checkpointing enabled** (`use_reentrant=False`)
2. **System Python** (`/usr/bin/python3` with CUDA torch 2.11.0+cu130)
3. **8-bit AdamW** optimizer
4. **Custom training loop** (not transformers.Trainer)

## Verification Commands

```bash
# Check current training config
ssh djg6228@10.0.0.171 "grep 'lora_r = \|lora_alpha = ' /data/SpecForge/custom_dflash/train_qwen_all_tiers.py"

# Check GPU memory during training
ssh djg6228@10.0.0.171 "nvidia-smi --query-gpu=memory.used --format=csv,noheader"

# Check training progress
ssh djg6228@10.0.0.171 "tail -5 /data/SpecForge/custom_dflash/logs/train_alltiers_*.log"
```

## Key Lesson

**Never assume a config is impossible based on one failure mode.** The r=256 "failure" was actually an environment bug (CPU-only torch), not a memory limit. Always verify the environment before concluding a config won't fit.
