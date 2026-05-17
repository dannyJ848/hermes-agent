# qwen27b-training-final-state

*Researched: 2026-05-08 22:10 CDT*

# Qwen 27B Expert Logician — Final Training State

## Configuration
- **Base Model**: Qwen/Qwen3.6-27B-Uncensored (bf16, frozen)
- **LoRA**: r=256, alpha=512, 1.275B params (4.53%)
- **Max Feasible Rank**: 256 (512+ fails on SAE feature extraction OOM)
- **Features**: SAE (layers 16,32,48), teacher distillation (Franken V8), multi-objective loss

## Current Status (May 8, 2026 22:10 UTC)
- **Step**: 2290/10000 (22.9%)
- **Loss**: 1.5435 (CE:1.282, D:1.359, SAE:0.592)
- **Recent trajectory**:
  - Step 2000: 1.8769 | 2010: 1.6443 | 2020: 1.5832 | 2030: 1.1542 | 2040: 1.5870
  - Step 2290: 1.5435 (current)
- **GPU**: 62.6GB active tensors / ~93GB total allocation (nvidia-smi process memory)
- **GPU Util**: 92-93% compute, 63-64°C
- **System RAM**: 116.5GB / 128GB (host memory near saturation)
- **PID**: 443609, running stable
- **ETA**: ~35 hours

## Key Discovery — Memory Reporting Discrepancy
The training log reports `GPU: 62.6GB` but nvidia-smi shows ~93GB process memory. The 62.6GB is only active tensors/optimizer state. Full GPU allocation includes:
- CUDA context overhead
- SAE feature extraction buffers
- Teacher distillation forward passes
- PyTorch caching allocator reserved memory
- Memory oscillates 0-93GB during training (normal behavior)

## Checkpoints
- Step 2200: ✓ (most recent)
- Step 2100: ✓
- Step 2000: 2026-05-08 20:30 ✓
- Step 1900: 2026-05-08 19:56 ✓

## Critical Fixes
1. `weights_only=False` (PyTorch 2.6 checkpoint compatibility)
2. Atomic launch (kill existing before starting new)
3. Loop guard v2 (prevents SSH intent loops)

## Post-Training Pipeline
1. `bash merge_model.sh` → merged BF16 model
2. `python3 evaluate_model.py` → benchmarks
3. `bash deploy_hermes_qwen.sh` → vLLM on port 8000

## File Locations
- Project: `/data/SpecForge/custom_dflash/`
- Training: `train_lora_sae_teacher_v1.py`
- Logs: `/mnt/bigssd/train_r256_final.log`
- Checkpoints: `/data/SpecForge/custom_dflash/checkpoints/`
- Master doc: `/data/SpecForge/custom_dflash/MASTER_DOC.md`
- instant_context.py: `/data/SpecForge/custom_dflash/instant_context.py`

## Deployment
- **Format**: BF16 only (no quantization)
- **Inference**: vLLM on DGX Spark
- **Hermes**: 100% local Qwen, no external fallback
- **Port**: 8000, API key: hermes-local

## DGX Connection
- **IP**: 10.0.0.171
- **Hostname**: spark-85e8.local
- **User**: djg6228
- **SSH Key**: `/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key`
- **GPU**: NVIDIA GB10 (not A100/H100)

## Sources
- https://github.com/dannyJ848/hermes-agent/blob/qwen27b-training-artifacts-may3-2026/instant_context.py
