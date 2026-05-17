# dgx-qwen-training-deadlock-analysis

*Researched: 2026-05-13 22:03 CDT*

# DGX Spark GB10 Qwen 27B Training Deadlock Analysis

## Date: May 13, 2026

## Problem
Training Qwen 27B with LoRA on DGX Spark (GB10, 121GB GPU) is blocked by a deadlock when gradient checkpointing is enabled.

## Evidence

### With Gradient Checkpointing
- `model.gradient_checkpointing_enable()` (any use_reentrant setting) causes permanent deadlock
- Process enters D state (uninterruptible sleep) at first forward+backward pass
- GPU memory allocated (~51GB) but 0% utilization
- Must kill with `kill -9`

### Without Gradient Checkpointing
- Forward pass works
- Backward pass OOMs at 117GB even with minimal config:
  - seq_len=1024 (reduced from 4096)
  - r=128 (reduced from 256)
  - batch_size=1
  - grad_accum=4
  - 8-bit AdamW

### Memory Breakdown
- Model weights (bf16): ~51GB
- LoRA adapters: ~1GB
- Activations (seq=1024, batch=1): ~2GB
- Gradients: ~1GB
- Optimizer states (8-bit): ~2GB
- **Expected total: ~57GB**
- **Actual usage: 117GB** (likely due to activation storage for backward pass)

## Root Cause Hypothesis
Qwen3.5 uses mixed attention (3 linear_attention + 1 full_attention layers, repeating). The `linear_attention` implementation may have a bug with PyTorch's gradient checkpointing hooks.

## The May 8 Mystery
Script `train_lora_sae_teacher_v1.py` supposedly trained 10k steps with gradient checkpointing on May 8. Unresolved whether:
1. Different model checkpoint (no linear attention bug)
2. Different PyTorch/CUDA version
3. Intermittent deadlock
4. Script pattern avoids deadlock
5. Log was from run without gradient checkpointing

## Files on DGX
- `/data/SpecForge/custom_dflash/train_lora_sae_teacher_v1.py` - May 8 script (broken log path /mnt/bigssd/)
- `/data/SpecForge/custom_dflash/train_micro.py` - r=128, seq=1024, no GC (OOMs)
- `/data/SpecForge/custom_dflash/train_reentrant.py` - r=256, seq=4096, GC default (deadlocks)
- `/data/SpecForge/custom_dflash/train_nogc_smallbatch.py` - r=256, seq=2048, no GC (OOMs)

## Next Steps
1. Fix May 8 script log path and test
2. If works: copy its pattern
3. If also deadlocks: investigate PyTorch/CUDA compatibility
4. Alternative: install flash-linear-attention package
5. Alternative: QLoRA with proper bitsandbytes setup
6. Alternative: smaller base model (Qwen 7B/14B)

## Commands
```bash
# SSH to DGX
ssh djg6228@10.0.0.171

# Kill deadlocked training
sudo systemctl stop qwen-training
pkill -9 -f 'train_.*\.py'

# Check GPU
nvidia-smi

# Check process state
ps aux | grep train
```
