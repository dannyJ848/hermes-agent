#!/bin/bash
# Atomic training launcher — prevents ALL duplicates, kills auto-resume scripts
# Created: May 8, 2026 — validated on DGX Spark with Qwen 27B training
set -e

cd /data/SpecForge/custom_dflash

# Kill ALL existing training processes (aggressive)
pkill -9 -f "train_lora_sae_teacher" 2>/dev/null || true
pkill -9 -f "train_bulletproof" 2>/dev/null || true
pkill -9 -f "resume_training" 2>/dev/null || true
pkill -9 -f "training_monitor" 2>/dev/null || true
sleep 3

# Double-check — must be 0 processes
if pgrep -f "train_lora_sae_teacher" > /dev/null || pgrep -f "train_bulletproof" > /dev/null; then
    echo "ERROR: Old processes still running"
    exit 1
fi

# Clear GPU
python3 -c "import torch; torch.cuda.empty_cache(); print('GPU cleared')"

# Remove stale locks and auto-resume scripts
rm -f /tmp/training.lock /tmp/training.pid
rm -f /data/SpecForge/custom_dflash/resume_training.sh \
      /data/SpecForge/custom_dflash/training_monitor.sh \
      /data/SpecForge/custom_dflash/monitor_config.json

# Launch training
# --test_mode for 5-step validation, omit for full training
nohup python3 -u train_bulletproof.py \
    --resume_from_checkpoint /data/SpecForge/custom_dflash/checkpoints/checkpoint_step_700 \
    >> training.log 2>&1 &

PID=$!
echo "Launched PID: $PID"
echo $PID > /tmp/training.pid
sleep 2
ps -p $PID -o pid,stat,%cpu,rss,etime | tail -1
