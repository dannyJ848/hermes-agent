#!/bin/bash
# Kill old CPU precompute and restart with GPU version
# Run this on DGX when ready

echo "=== Killing old CPU precompute ==="
pkill -9 -f "precompute_teacher_cache.py"
sleep 3

# Verify killed
if pgrep -f "precompute_teacher_cache.py" > /dev/null; then
    echo "ERROR: Old process still running"
    exit 1
fi

echo "=== Old process killed ==="

# Backup existing cache
echo "=== Backing up existing cache ==="
mkdir -p /mnt/bigssd/teacher_cache_backup
cp /mnt/bigssd/teacher_cache/index.json /mnt/bigssd/teacher_cache_backup/ 2>/dev/null
echo "Backup done"

# Fix index — add missing PKL files
echo "=== Fixing index ==="
python3 << 'EOF'
import json, glob, os
from pathlib import Path

cache_dir = "/mnt/bigssd/teacher_cache"
index_path = Path(cache_dir) / "index.json"

if index_path.exists():
    with open(index_path) as f:
        index = json.load(f)
else:
    index = {}

pkl_files = glob.glob(f"{cache_dir}/*.pkl")
added = 0
for pkl in pkl_files:
    base = os.path.basename(pkl).replace(".pkl", "")
    if base not in index:
        index[base] = pkl
        added += 1

with open(index_path, 'w') as f:
    json.dump(index, f)

print(f"Index fixed: {len(index)} entries, {added} added")
EOF

# Launch GPU version
echo "=== Launching GPU-accelerated precompute ==="
cd /data/SpecForge/custom_dflash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
nohup python3 training/qwen27b-lora-sae-teacher/precompute_teacher_cache_gpu.py > /mnt/bigssd/precompute_teacher_cache_gpu.log 2>&1 &
NEW_PID=$!
echo "New process PID: $NEW_PID"
echo $NEW_PID > /mnt/bigssd/precompute_gpu.pid

echo "=== Launched ==="
echo "Monitor with: tail -f /mnt/bigssd/precompute_teacher_cache_gpu.log"
