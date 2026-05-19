#!/bin/bash
# Launch training cleanly — single instance only
# Usage: bash launch_training.sh <checkpoint_dir>
# Example: bash launch_training.sh /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_700

set -e

CHECKPOINT="${1:-/data/SpecForge/custom_dflash/checkpoints/checkpoint_step_700}"
TRAIN_DIR="/data/SpecForge/custom_dflash"
LOG_FILE="${TRAIN_DIR}/training.log"

cd "$TRAIN_DIR"

# Kill any existing training processes
pkill -9 -f "train_lora_sae_teacher" 2>/dev/null || true
sleep 2

# Clear GPU cache
python3 -c "import torch; torch.cuda.empty_cache()"

# Launch single instance with low priority to preserve SSH responsiveness
nice -n 10 nohup python3 -u train_lora_sae_teacher_v1.py \
    --resume_from_checkpoint "$CHECKPOINT" \
    >> "$LOG_FILE" 2>&1 &

PID=$!
echo "Launched PID: $PID"
echo "$PID" > /tmp/training.pid

# Quick health check
sleep 2
if ps -p "$PID" > /dev/null 2>&1; then
    ps -p "$PID" -o pid,stat,%cpu,rss,etime | tail -1
else
    echo "ERROR: Process died immediately"
    exit 1
fi
