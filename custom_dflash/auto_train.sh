#!/bin/bash
# Auto-run DFlash training after hidden state generation completes
set -e

LOG="/tmp/dflash_auto_train.log"
echo "$(date): Starting auto-training pipeline" > $LOG

# Wait for Phase 1 to complete (check every 5 minutes)
TARGET=10000
OUTPUT_DIR="/data/SpecForge/custom_dflash/hidden_states_full"

while true; do
    COUNT=$(ls $OUTPUT_DIR/*.pt 2>/dev/null | wc -l)
    echo "$(date): $COUNT/$TARGET samples generated" >> $LOG
    if [ "$COUNT" -ge "$TARGET" ]; then
        echo "$(date): Phase 1 complete! Starting training..." >> $LOG
        break
    fi
    sleep 300
done

# Phase 2: Train DFlash draft model
cd /data/SpecForge/custom_dflash
source /data/sglang-venv/bin/activate

python3 phase2_train_draft.py     --hidden-states-dir $OUTPUT_DIR     --output-dir /data/models/Qwen3.6-27B-DFlash-Custom     --num-epochs 10     --batch-size 4     --learning-rate 5e-4     --save-every 100     >> $LOG 2>&1

echo "$(date): Training complete!" >> $LOG

# Phase 3: Convert to vLLM format
python3 convert_dflash_v2.py     --checkpoint /data/models/Qwen3.6-27B-DFlash-Custom/checkpoint_final.pt     --output-dir /data/models/Qwen3.6-27B-DFlash-vLLM-v2     >> $LOG 2>&1

echo "$(date): Conversion complete! Ready for vLLM integration." >> $LOG
