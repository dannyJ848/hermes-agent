#!/bin/bash
# Check Franken V8 training status on Spark
# Usage: ./check_status.sh

echo "=== FRANKEN V8 TRAINING STATUS ==="
echo "Timestamp: $(date)"
echo ""

# Check if training process is running
echo "--- Training Process ---"
ps aux | grep -E 'python.*train_franken' | grep -v grep || echo "No training process found"
echo ""

# Check GPU
echo "--- GPU Status ---"
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader
echo ""

# Check latest log
echo "--- Latest Log Entries ---"
LOG_FILE="/data/models/FrankenV8-Batch2/training_dual_mode.log"
if [ -f "$LOG_FILE" ]; then
    tail -20 "$LOG_FILE"
else
    echo "Log file not found: $LOG_FILE"
fi
echo ""

# Check checkpoints
echo "--- Checkpoints ---"
ls -lt /data/models/FrankenV8-Batch2/*.pt 2>/dev/null | head -5 || echo "No checkpoints found"
echo ""

# Check disk
echo "--- Disk Usage ---"
df -h /data | grep -v tmpfs
echo ""

# Check memory
echo "--- Memory ---"
free -h 2>/dev/null | head -3 || cat /proc/meminfo | head -5
echo ""

echo "=== END STATUS ==="
