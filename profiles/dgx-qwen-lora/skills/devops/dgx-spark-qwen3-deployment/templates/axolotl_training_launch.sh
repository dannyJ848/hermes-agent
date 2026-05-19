#!/bin/bash
# Axolotl LoRA Training Launch Script for DGX Spark GB10
# Usage: bash axolotl_training_launch.sh [config_path]

set -e

CONFIG_PATH="${1:-/data/SpecForge/custom_dflash/axolotl_config.yaml}"
TRAIN_VENV="${HOME}/train-venv"

echo "=== Qwen 27B LoRA Training Launch ==="
echo "Config: $CONFIG_PATH"
echo "Timestamp: $(date)"

# Activate training venv
source "$TRAIN_VENV/bin/activate"

# Verify CUDA is available
python3 -c "import torch; assert torch.cuda.is_available(), 'CUDA not available'; print(f'PyTorch: {torch.__version__}, CUDA: {torch.version.cuda}')"

# Set memory optimization env vars
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_VISIBLE_DEVICES=0

# Create log directory
LOG_DIR="/data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/training_$(date +%Y%m%d_%H%M%S).log"

# Preprocess if needed (check for cached dataset)
echo "Preprocessing datasets..."
axolotl preprocess "$CONFIG_PATH" 2>&1 | tee "$LOG_DIR/preprocess_$(date +%Y%m%d_%H%M%S).log"

# Launch training
echo "Starting training..."
echo "Logs: $LOG_FILE"
axolotl train "$CONFIG_PATH" 2>&1 | tee "$LOG_FILE"

echo "Training complete at $(date)"
echo "Adapter saved to: /data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/"
