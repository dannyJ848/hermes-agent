# Checkpoint OOM Fix: CPU-Offload Save Pattern

Session: May 6, 2026 — Qwen 27B LoRA training at 85.3GB/130GB GPU memory.

## Problem

Saving checkpoints at GPU memory edge (85+ GB) triggers OOM during `torch.save()` because the save operation allocates additional GPU memory for serialization buffers.

## Solution: CPU-Offload Save

```python
# Before save: move model to CPU, free GPU memory
try:
    model.to('cpu')
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    
    # Now save from CPU — no GPU memory pressure
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict(),
        'step': global_step,
        'loss': current_loss,
    }, checkpoint_path)
    
    print(f"[CHECKPOINT] Saved to {checkpoint_path}")
finally:
    # CRITICAL: Move model back to GPU for continued training
    model.to(device)
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
```

## Key elements

1. **try/finally wrapper** — guarantees model returns to GPU even if save fails
2. **empty_cache + synchronize** before AND after — ensures clean memory state
3. **Save from CPU** — serialization buffers allocate on CPU, not GPU
4. **No gradient accumulation during save** — wait for optimizer step to complete

## Verified result

- Training step 1000: checkpoint saved successfully at 85.3GB
- No OOM, no crash, training continued
- Directory: `/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_1000/`
- Process: PID 590094, still running after save (8h 35m runtime)

## Pitfall: Empty checkpoint directory

The checkpoint directory may appear empty immediately after creation — the save operation takes time for large models. Do NOT assume failure. Check:
1. Process still alive (`ps -p PID`)
2. No OOM in logs (`grep OOM logfile`)
3. Directory exists (`ls -la checkpoints/`)
4. Wait 30-60s for files to appear

## Integration with watcher

```python
# checkpoint_watcher.py pattern
while True:
    if os.path.exists(checkpoint_dir):
        checkpoints = [d for d in os.listdir(checkpoint_dir) 
                        if d.startswith(f'checkpoint_step_{target_step}')]
        if checkpoints:
            print(f'[WATCHER] SUCCESS: Checkpoint found: {checkpoints[0]}')
            break
    
    # Check for OOM or error in log
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
            if lines:
                latest = lines[-1].strip()
                if 'OOM' in latest or 'out of memory' in latest.lower() or 'CUDA error' in latest:
                    print(f'[WATCHER] FAILURE: OOM detected!')
                    sys.exit(1)
    
    time.sleep(30)
```
