# Rank-256 Stable Config — May 7, 2026

## History

Previous ranks all OOM'd on DGX Spark (130GB GPU):
- Rank 1024: OOM immediately
- Rank 768: OOM at model loading
- Rank 640: OOM during first training step
- Rank 512: OOM at step ~50
- Rank 384: OOM at step ~150
- **Rank 256: FIRST stable config with ALL components active**

## Current Config

```python
lora_rank = 256
lora_alpha = 512
batch_size = 1
grad_accum_steps = 4
# CE + distillation (D) + SAE all active
```

## Metrics at Step 600

| Metric | Value |
|--------|-------|
| Loss | 1.9350 |
| GPU memory | 62.6GB / 130GB |
| GPU utilization | 92% |
| Step pace | 0.34 min/step (21 sec/step) |
| ETA to 10K | ~54 hours (~2.3 days) |
| Checkpoints | Every 100 steps |

## Why Rank 256 Works

1. **LoRA params**: ~2.5B trainable (vs ~10B at rank-1024)
2. **Optimizer states**: 8-bit AdamW = ~5GB (vs ~20GB at rank-1024)
3. **Activation memory**: batch=1 keeps activations small
4. **Gradient checkpointing**: `use_reentrant=False` saves ~30GB
5. **Headroom**: 67GB free for spikes, checkpoint saves, fragmentation

## All Components Active

- Cross-entropy loss (CE)
- Teacher distillation (D) — Franken V8 hidden states
- SAE feature alignment — Qwen-Scope layers [16,32,48]
- 8-bit AdamW optimizer
- WSD-S learning rate schedule

## Checkpoint Times

| Checkpoint | Time (May 7) | Interval |
|------------|-------------|----------|
| 100 | 01:08 | — |
| 200 | 17:17 | 16h09m (paused) |
| 300 | 17:51 | 34m |
| 400 | 18:27 | 36m |
| 500 | 22:11 | 3h44m (paused) |
| 600 | 22:45 | 34m |

Normal pace: ~34 min per 100 steps. Pauses are user-initiated (DGX cycling, SSH issues).

## PID

180722 — stable since launch. Monitored every 5 min by both local and remote scripts.

## Commit

f08825c61 on branch `qwen27b-training-artifacts-may3-2026`
