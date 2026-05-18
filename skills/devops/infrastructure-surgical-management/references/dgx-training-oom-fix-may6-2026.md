# DGX Training Checkpoint OOM Fix — May 6, 2026

## Problem

Qwen 27B LoRA training (r=1024) on DGX Spark (130GB GPU) died at step 500 during checkpoint save.

**Root cause:** `model.save_pretrained()` at 85.3GB/130GB GPU utilization triggered OOM because:
- Training uses 85.3GB continuously
- save_pretrained needs additional memory to serialize LoRA weights
- Combined usage exceeds 130GB → OOM killer terminates process
- Checkpoint directory is created but weights never written → empty checkpoint

## Solution: Four-Phase CPU Offload Save

```python
# Phase 1: Free all possible GPU memory before save
torch.cuda.empty_cache()
import gc; gc.collect()
torch.cuda.synchronize()  # Wait for all streams

# Phase 2: Move to CPU for zero-GPU-overhead serialization
model = model.to('cpu')
torch.cuda.empty_cache()
gc.collect()

# Phase 3: Save on CPU (no GPU memory pressure)
try:
    model.save_pretrained(checkpoint_path)
    torch.save({
        'step': global_step,
        'optimizer_state_dict': optimizer.state_dict(),
        'config': config,
    }, os.path.join(checkpoint_path, "optimizer.pt"))
    logging.info(f"Saved checkpoint: {checkpoint_path}")
except Exception as e:
    logging.error(f"Checkpoint save failed: {e}")
finally:
    # Phase 4: Always return to GPU, even if save failed
    model = model.to('cuda')
    torch.cuda.empty_cache()
    gc.collect()
```

## Config Corrections Applied

| Parameter | Before | After | Reason |
|-----------|--------|-------|--------|
| max_steps | 10000 | 4000 | User wants 4K only |
| save_every | 1000 | 500 | More frequent saves with OOM fix |
| warmup_steps | 500 | 400 | Match 4K target |

## Verification

The fix is implemented but untested at 85GB GPU occupancy. A watcher script monitors for step 1000 checkpoint:

```bash
# Watcher PID 778063 on DGX
python3 /tmp/checkpoint_watcher.py
# Exits 0 on success, 1 on OOM
```

## Recovery Plan

If checkpoint save crashes training:

```bash
# /tmp/recovery_plan.sh on DGX
LATEST=$(ls -td /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_* 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    echo "Resume: cd /data/SpecForge/custom_dflash && python3 -u train_lora_sae_teacher_v1.py --resume $LATEST"
fi
```

## Key Insight

At GPU memory edge (>65% utilization), treat checkpoint saves as hazards not routine ops. CPU offload is the only safe serialization path when training occupies 85GB+.
