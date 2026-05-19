# PyTorch 2.6+ `weights_only` Default Breaks Checkpoint Resume

**Date:** May 8, 2026
**Session:** DGX Spark training crash debug
**Severity:** HIGH — training dies immediately on resume, no stack trace

## What Happened

PyTorch 2.6 changed `torch.load()` default from `weights_only=False` to `weights_only=True`. Optimizer state files contain custom `TrainConfig` classes that aren't in the safe globals list. Training dies immediately on resume with `_pickle.UnpicklingError`.

## Symptoms

- Process starts, loads model, preloads cache, then dies at "Resuming from checkpoint_step_N"
- Log shows: `WeightsUnpickler error: Unsupported global: GLOBAL __main__.TrainConfig was not an allowed global`
- No stack trace beyond `torch.load()` call
- Process exits cleanly (not OOM), leaving GPU memory cleared

## Fix

Add `weights_only=False` to ALL `torch.load()` calls in training script:

```python
# WRONG — PyTorch 2.6 default breaks on custom classes
state = torch.load(opt_path, map_location="cpu")

# CORRECT — explicit weights_only=False for trusted checkpoints
state = torch.load(opt_path, map_location="cpu", weights_only=False)
```

## Where to Apply

Search all `torch.load()` calls in training script:
```bash
grep -n "torch.load" train_script.py
# Apply weights_only=False to every call that loads optimizer state or custom objects
```

## Security Note

`weights_only=False` allows arbitrary code execution from pickle files. Only use this for checkpoints you created yourself (trusted source). Never use on downloaded checkpoints from untrusted sources.

## One-Liner Fix (sed)

```bash
sed -i 's/torch.load(\([^,]*\), map_location=\([^)]*\))/torch.load(\1, map_location=\2, weights_only=False)/g' train_script.py
# Then manually verify each call — some may already have weights_only
```
