#!/bin/bash
# Check disk space and predict if training will fit
# Usage: ./check_disk.sh

echo "=== DISK SPACE ANALYSIS ==="
echo ""

# Current usage
echo "--- Current Disk Usage ---"
df -h /data | grep -v tmpfs
echo ""

# Key directories
echo "--- Key Directories ---"
for dir in \
    "/data/SpecForge/custom_dflash/hidden_states_full" \
    "/data/SpecForge/custom_dflash/batch_2_logits" \
    "/data/models/FrankenV8-Batch1-Final" \
    "/data/models/FrankenV8-Batch2" \
    "/data/models/FrankenV8-Modular" \
    "/data/models/Qwen3.6-27B-Uncensored"; do
    if [ -d "$dir" ]; then
        SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1)
        echo "  $SIZE  $dir"
    fi
done
echo ""

# Projections
echo "--- Projections ---"
FREE_GB=$(df /data | tail -1 | awk '{print int($4/1024/1024)}')
echo "Free space: ~${FREE_GB}G"

echo ""
echo "Per-batch checkpoint growth: ~15G per 500 steps"
echo "Full batch training: ~180G total (checkpoints + final model)"
echo ""
echo "If training current batch: need ~200G free"
echo "If extracting new logits: need ~1.5T free"
echo ""

# Recommendations
if [ "$FREE_GB" -lt 200 ]; then
    echo "⚠️  WARNING: Less than 200G free. Recommend:"
    echo "   1. Delete completed batch logits"
    echo "   2. Delete old checkpoints (keep last 2 + final)"
    echo "   3. Wait for external SSD (8TB arriving Friday)"
elif [ "$FREE_GB" -lt 500 ]; then
    echo "⚠️  TIGHT: 200-500G free. Can finish current batch but:"
    echo "   - Delete logits immediately after training"
    echo "   - Keep only essential checkpoints"
else
    echo "✅ OK: >500G free. Space for current batch + buffer"
fi

echo ""
echo "=== END ==="
