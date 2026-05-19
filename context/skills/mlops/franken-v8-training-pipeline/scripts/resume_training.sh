#!/bin/bash
# Resume Franken V8 training from checkpoint
# Usage: ./resume_training.sh --batch batch_1|batch_2|batch_3 --checkpoint /path/to/checkpoint.pt

BATCH=""
CHECKPOINT=""
HIDDEN_STATES_DIR=""
OUTPUT_DIR=""

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --batch)
            BATCH="$2"
            shift 2
            ;;
        --checkpoint)
            CHECKPOINT="$2"
            shift 2
            ;;
        --hidden-states-dir)
            HIDDEN_STATES_DIR="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate
if [ -z "$BATCH" ] || [ -z "$CHECKPOINT" ]; then
    echo "Usage: $0 --batch batch_1|batch_2|batch_3 --checkpoint /path/to/checkpoint.pt"
    echo "Optional: --hidden-states-dir /path --output-dir /path"
    exit 1
fi

# Set defaults based on batch
if [ -z "$HIDDEN_STATES_DIR" ]; then
    case $BATCH in
        batch_1)
            HIDDEN_STATES_DIR="/data/SpecForge/custom_dflash/batch_1_logits"
            ;;
        batch_2)
            HIDDEN_STATES_DIR="/data/SpecForge/custom_dflash/batch_2_logits"
            ;;
        batch_3)
            HIDDEN_STATES_DIR="/data/SpecForge/custom_dflash/batch_3_logits"
            ;;
    esac
fi

if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR="/data/models/FrankenV8-${BATCH}"
fi

SCRIPT="/data/SpecForge/custom_dflash/train_franken_v8_PROGRESSIVE_FA4.py"

echo "=== RESUMING FRANKEN V8 TRAINING ==="
echo "Batch: $BATCH"
echo "Checkpoint: $CHECKPOINT"
echo "Hidden states: $HIDDEN_STATES_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

# Verify checkpoint exists
if [ ! -f "$CHECKPOINT" ]; then
    echo "ERROR: Checkpoint not found: $CHECKPOINT"
    exit 1
fi

# Verify hidden states exist
if [ ! -d "$HIDDEN_STATES_DIR" ]; then
    echo "ERROR: Hidden states dir not found: $HIDDEN_STATES_DIR"
    exit 1
fi

# Count samples
SAMPLE_COUNT=$(ls "$HIDDEN_STATES_DIR"/*.pt 2>/dev/null | wc -l)
echo "Samples found: $SAMPLE_COUNT"

# Launch training
cd /data/SpecForge/custom_dflash
nohup python3 "$SCRIPT" \
    --hidden-states-dir "$HIDDEN_STATES_DIR" \
    --output-dir "$OUTPUT_DIR" \
    --resume-from "$CHECKPOINT" \
    --batch-size 1 \
    --grad-accum 2 \
    --max-steps 3332 \
    --warmup-steps 200 \
    --lr 0.00005 \
    --save-interval 500 \
    --log-interval 10 \
    --steps-per-wave 100 \
    --bf16 \
    > "${OUTPUT_DIR}/training_${BATCH}.log" 2>&1 &

PID=$!
echo "Training launched with PID: $PID"
echo "Log: ${OUTPUT_DIR}/training_${BATCH}.log"
echo ""
echo "Monitor with: tail -f ${OUTPUT_DIR}/training_${BATCH}.log"
