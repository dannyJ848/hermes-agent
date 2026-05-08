#!/bin/bash
# DGX Status Check Script — run this to check teacher cache progress
# Usage: bash /data/SpecForge/custom_dflash/check_teacher_cache.sh

echo "=== Teacher Cache Status ==="
echo "Timestamp: $(date)"
echo ""

# Check if process is running
PID=$(pgrep -f "precompute_teacher_cache.py" || echo "NOT_RUNNING")
echo "Process PID: $PID"

if [ "$PID" != "NOT_RUNNING" ]; then
    echo "Status: RUNNING"
    ps -p "$PID" -o %cpu,%mem,etime 2>/dev/null | tail -1 || echo "Cannot get process stats"
else
    echo "Status: NOT RUNNING"
fi

echo ""
echo "=== Cache Files ==="
CACHE_COUNT=$(ls /mnt/bigssd/teacher_cache/*.pkl 2>/dev/null | wc -l)
echo "Cached samples: $CACHE_COUNT"

if [ -f /mnt/bigssd/teacher_cache/index.json ]; then
    INDEX_COUNT=$(python3 -c "import json; print(len(json.load(open('/mnt/bigssd/teacher_cache/index.json'))))" 2>/dev/null || echo "?")
    echo "Index entries: $INDEX_COUNT"
fi

echo ""
echo "=== Recent Log ==="
if [ -f /mnt/bigssd/precompute_teacher_cache.log ]; then
    tail -10 /mnt/bigssd/precompute_teacher_cache.log
else
    echo "No log file found"
fi

echo ""
echo "=== GPU Status ==="
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader 2>/dev/null || echo "GPU not available"

echo ""
echo "=== Ready for Training? ==="
if [ "$CACHE_COUNT" -gt 1000 ] && [ "$PID" = "NOT_RUNNING" ]; then
    echo "YES - Cache complete. Run: MAX_STEPS=10000 python3 train_lora_sae_teacher_v1.py"
elif [ "$PID" != "NOT_RUNNING" ]; then
    echo "NO - Cache still building. Check again in 1 hour."
else
    echo "MAYBE - Cache has $CACHE_COUNT samples. May be enough for testing."
fi
