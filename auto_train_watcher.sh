#!/bin/bash
# Auto-launch EAGLE-3 training when hidden states generation completes

TARGET_PID=177337
LOG_FILE="/tmp/auto_train_watcher.log"
TRAIN_SCRIPT="/data/SpecForge/train_eagle3_qwen36.sh"
HIDDEN_DIR="/data/SpecForge/cache/hidden_states/qwen3.6-35b-a3b-ultrachat/rows_0-5000"
TRAIN_LOG="/tmp/eagle3_training.log"

echo "[$(date)] Watcher started. Monitoring PID $TARGET_PID" >> "$LOG_FILE"

# Wait for the hidden states process to finish
while kill -0 "$TARGET_PID" 2>/dev/null; do
    sleep 30
done

echo "[$(date)] PID $TARGET_PID exited. Checking completion..." >> "$LOG_FILE"

# Give filesystem a moment to flush
sleep 5

# Check if hidden states were actually generated
CKPT_COUNT=$(ls "$HIDDEN_DIR"/*.ckpt 2>/dev/null | wc -l)
if [ "$CKPT_COUNT" -lt 10 ]; then
    echo "[$(date)] ERROR: Only $CKPT_COUNT ckpt files found. Aborting auto-launch." >> "$LOG_FILE"
    exit 1
fi

echo "[$(date)] Found $CKPT_COUNT ckpt files. Proceeding to training." >> "$LOG_FILE"

# Disable sleep again just in case
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Run training
bash "$TRAIN_SCRIPT" >> "$TRAIN_LOG" 2>&1
TRAIN_EXIT=$?

if [ "$TRAIN_EXIT" -eq 0 ]; then
    echo "[$(date)] Training completed successfully." >> "$LOG_FILE"
    echo "[$(date)] Draft model ready. Restarting vLLM..." >> "$LOG_FILE"
    bash /data/switch-model.sh >> /tmp/vllm_restart.log 2>&1
else
    echo "[$(date)] Training FAILED with exit code $TRAIN_EXIT. Check $TRAIN_LOG" >> "$LOG_FILE"
fi
