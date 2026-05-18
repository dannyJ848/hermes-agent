# Training GPU-Bound Diagnosis (May 2026)

## Problem: Training is CPU-bound, not GPU-bound

**Symptoms:**
- Tokenization completes at 100% but no training metrics (loss/epoch/step) appear
- `nvidia-smi` shows 0% GPU utilization
- 24 Python processes active but all CPU-bound (99.8% CPU on main process)
- Training log only shows tokenization progress bars, zero loss lines

**Root cause:** `torch` installed without CUDA support in training venv, or CUDA not visible to axolotl.

## Diagnosis Steps

```bash
# 1. Check if torch sees CUDA
ssh djg6228@10.0.0.171 "source ~/train-venv/bin/activate && python3 -c 'import torch; print(torch.cuda.is_available())'"
# Expected: True
# If False: torch is CPU-only

# 2. Check accelerate config
ssh djg6228@10.0.0.171 "cat ~/.cache/huggingface/accelerate/default_config.yaml"
# Expected: compute_environment: LOCAL_MACHINE, distributed_type: NO, use_cpu: false

# 3. Check torch version
ssh djg6228@10.0.0.171 "source ~/train-venv/bin/activate && python3 -c 'import torch; print(torch.__version__)'"
# Expected: 2.11.0+cu130 (or similar with +cuXXX)
# If no +cu suffix: CPU-only torch
```

## Fix: Reinstall CUDA torch

```bash
# On DGX
source ~/train-venv/bin/activate
pip uninstall -y torch torchvision
cd /data/SpecForge/custom_dflash
pip install -r requirements.txt  # Should pull torch 2.11.0+cu130
# Or explicitly:
pip install torch==2.11.0+cu130 --index-url https://download.pytorch.org/whl/cu130
```

## Prevention

When setting up training venv, ALWAYS verify CUDA torch:
```bash
python3 -c "import torch; assert torch.cuda.is_available(), 'CUDA torch not installed'"
```

## Training Health Monitoring

While training is running, monitor these metrics:

```bash
# GPU utilization (should be >80% during training, not 0%)
nvidia-smi --query-gpu=utilization.gpu,memory.used,temperature.gpu --format=csv,noheader -l 5

# Process state (main training PID should be in R state, not S/D)
cat /proc/<PID>/status | grep State

# Log tail (should show loss values, not just tokenization)
tail -f /data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/logs/training_live.log | grep -E 'loss|epoch|step'
```

## Expected Training Metrics Pattern

Once GPU is active, log should show:
```
{'loss': 2.8473, 'learning_rate': 1.8e-4, 'epoch': 0.01}
{'loss': 2.6234, 'learning_rate': 1.6e-4, 'epoch': 0.02}
{'loss': 2.4512, 'learning_rate': 1.4e-4, 'epoch': 0.03}
```

If you only see tokenization progress bars after 3+ hours, training is stuck.
