# DGX GPU Memory Reconciliation — Training Log vs nvidia-smi vs Dashboard

**Date:** May 8, 2026  
**System:** DGX Spark (NVIDIA GB10, 130GB GPU, 128GB RAM)  
**Context:** Qwen 27B LoRA training, rank 256, step 2040

## The Discrepancy

User reported DGX dashboard showing "near max usage" while training log showed only 62.6GB GPU. Investigation revealed three different metrics:

| Source | Value | What It Actually Measures |
|--------|-------|---------------------------|
| Training log `GPU: 62.6GB` | 62.6 GB | Active tensors + optimizer state (explicitly tracked by script) |
| nvidia-smi process memory | ~93 GB | Total GPU allocation including CUDA context, PyTorch cache, SAE buffers, teacher forward passes |
| DGX dashboard system RAM | 116.5 GB / 128 GB | **Host system memory**, not GPU VRAM |

## Why They Differ

### Training Log Under-Reports
The training script only tracks what it explicitly measures:
```python
# This tracks model + optimizer only
gpu_allocated = torch.cuda.memory_allocated() / 1e9  # ~62GB
```

It does NOT include:
- CUDA context overhead (~2-3GB)
- PyTorch caching allocator reserved memory (~15-20GB)
- SAE feature extraction temporary buffers (~5-8GB)
- Teacher model forward pass activations (~8-12GB)
- Data loader pinned memory in host RAM (shows as system RAM, not GPU)

### nvidia-smi on GB10 Reports N/A for Totals
The GB10 driver doesn't expose total VRAM via standard nvidia-smi queries:
```bash
nvidia-smi --query-gpu=memory.total,memory.used --format=csv
# Returns: [N/A], [N/A]
```

Use this instead for per-process allocation:
```bash
nvidia-smi -q | grep "Used GPU Memory"
# Shows: 95227 MiB (~93GB) for the training process
```

### Dashboard "System Memory" is Host RAM
The DGX dashboard's top gauge showing 116.51 GB / 128 GB is **system RAM** (CPU memory), not GPU VRAM. The bottom gauge showing 93% is **GPU compute utilization** (how busy the cores are), not memory usage.

## Reconciliation Pattern

When checking training status, pull ALL three metrics:

```bash
# 1. Training progress (log)
grep 'Step [0-9]' /mnt/bigssd/train_r256_final.log | tail -1

# 2. GPU compute + temp (nvidia-smi basic)
nvidia-smi --query-gpu=utilization.gpu,temperature.gpu --format=csv,noheader,nounits

# 3. Per-process GPU memory (nvidia-smi detailed)
nvidia-smi -q | grep -A 2 "Used GPU Memory"

# 4. System RAM (free)
free -h

# 5. Process status
pgrep -f train_lora | xargs ps -o pid,%cpu,%mem,etime
```

## Key Lesson

**Never trust a single metric.** The training log's GPU number is the most optimistic. The dashboard's "system memory" is completely different hardware. Only `nvidia-smi -q` process memory shows true GPU allocation. On GB10, always use the verbose query form — the compact format returns N/A.

## SSH Connection Detail

DGX Spark uses NVIDIA Sync SSH config:
```
Host spark-85e8.local
  Hostname spark-85e8.local
  User djg6228
  IdentityFile "~/Library/Application Support/NVIDIA/Sync/config/nvsync.key"
```

Always check this config before asking user for credentials.
