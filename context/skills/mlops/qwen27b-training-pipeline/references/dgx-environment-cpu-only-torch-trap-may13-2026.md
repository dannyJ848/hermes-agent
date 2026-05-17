# DGX Environment Trap: CPU-Only PyTorch Masquerading as Training Deadlock

**Date:** May 13, 2026
**System:** DGX Spark (NVIDIA GB10)
**Impact:** Hours of wasted debugging on a non-existent "gradient checkpointing deadlock"

## The Trap

The DGX has TWO Python environments:
1. **System Python** (`/usr/bin/python3`): `torch 2.11.0+cu130` — CUDA works
2. **train-venv** (`/home/djg6228/train-venv`): `torch 2.10.0+cpu` — NO CUDA

When training scripts are run from `train-venv`, PyTorch cannot access CUDA. This manifests as:
- Model loads to CPU (0GB GPU shown in logs)
- Process hangs when trying to move tensors to CUDA device
- `ps` shows PID in D state (uninterruptible sleep)
- `nvidia-smi` shows 0% GPU utilization
- Looks EXACTLY like a deadlock

## Symptoms vs Reality

| Symptom | Assumed Cause | Actual Cause |
|---------|--------------|--------------|
| Process in D state | Gradient checkpointing deadlock with linear attention | CPU-only torch failing on `.to('cuda')` |
| GPU memory shows 0GB | Model not loading to GPU | Model loading to CPU because torch has no CUDA |
| Hangs at first forward pass | Model architecture bug | `AssertionError: Torch not compiled with CUDA enabled` |
| 100% CPU, 0% GPU | Dataloader bottleneck | PyTorch retrying failed CUDA init |

## Detection

```bash
# Check which Python has CUDA
/usr/bin/python3 -c "import torch; print(f'System: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
/home/djg6228/train-venv/bin/python -c "import torch; print(f'Venv: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```

Expected output:
```
System: 2.11.0+cu130, CUDA: True
Venv: 2.10.0+cpu, CUDA: False
```

## The Fix

**Always use system Python for training:**
```bash
# In systemd service
ExecStart=/usr/bin/python3 /data/SpecForge/custom_dflash/train_script.py

# In SSH commands
ssh djg6228@10.0.0.171 "/usr/bin/python3 train_script.py"

# NOT:
# source /home/djg6228/train-venv/bin/activate && python train_script.py
```

**If you need packages only in train-venv:**
Install them in system Python instead:
```bash
sudo /usr/bin/python3 -m pip install transformers peft bitsandbytes
```

Or fix the venv by reinstalling CUDA torch:
```bash
/home/djg6228/train-venv/bin/pip uninstall torch torchvision torchaudio
/home/djg6228/train-venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cu130
```

## Prevention Checklist

Before debugging ANY training issue on DGX:
- [ ] Verify `torch.cuda.is_available()` returns True
- [ ] Verify `torch.version.cuda` is not None
- [ ] Check which Python binary is being used (`which python`)
- [ ] Check PyTorch version includes `+cu` suffix

## Lesson

The environment is the most likely culprit for "mysterious" training failures. Always verify the basics (CUDA availability, correct Python environment) before investigating model architecture bugs, deadlock hypotheses, or complex workarounds.

**Related:** See also `references/gb10-training-intractability-qlora-vs-gradient-checkpointing-may13-2026.md` for the earlier (incorrect) analysis that blamed GPU throughput.
