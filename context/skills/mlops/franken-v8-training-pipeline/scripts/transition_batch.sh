#!/bin/bash
# Transition between batches in the Franken V8 pipeline
# Usage: ./transition_batch.sh --from batch_2 --to batch_1

FROM_BATCH=""
TO_BATCH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --from)
            FROM_BATCH="$2"
            shift 2
            ;;
        --to)
            TO_BATCH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -z "$FROM_BATCH" ] || [ -z "$TO_BATCH" ]; then
    echo "Usage: $0 --from batch_1|batch_2|batch_3 --to batch_1|batch_2|batch_3"
    exit 1
fi

echo "=== BATCH TRANSITION: $FROM_BATCH → $TO_BATCH ==="
echo ""

# Step 1: Verify FROM batch training completed
echo "Step 1: Verify $FROM_BATCH training completed..."
CHECKPOINT_DIR="/data/models/FrankenV8-${FROM_BATCH}"
LATEST_CHECKPOINT=$(ls -t ${CHECKPOINT_DIR}/checkpoint-*.pt 2>/dev/null | head -1)

if [ -z "$LATEST_CHECKPOINT" ]; then
    echo "ERROR: No checkpoint found in $CHECKPOINT_DIR"
    exit 1
fi

echo "  Latest checkpoint: $LATEST_CHECKPOINT"
echo ""

# Step 2: Delete FROM batch logits
echo "Step 2: Delete $FROM_BATCH logits to free space..."
LOGITS_DIR="/data/SpecForge/custom_dflash/${FROM_BATCH}_logits"
if [ -d "$LOGITS_DIR" ]; then
    SIZE=$(du -sh "$LOGITS_DIR" | cut -f1)
    rm -rf "$LOGITS_DIR"
    echo "  Deleted $LOGITS_DIR (~$SIZE freed)"
else
    echo "  Logits dir already deleted or not found"
fi
echo ""

# Step 3: Extract TO batch logits (if not already extracted)
echo "Step 3: Prepare $TO_BATCH logits..."
TO_LOGITS_DIR="/data/SpecForge/custom_dflash/${TO_BATCH}_logits"

if [ -d "$TO_LOGITS_DIR" ] && [ "$(ls -A $TO_LOGITS_DIR)" ]; then
    echo "  Logits already extracted: $TO_LOGITS_DIR"
else
    echo "  Need to extract logits from hidden states..."
    case $TO_BATCH in
        batch_1)
            HS_DIR="/data/SpecForge/custom_dflash/hidden_states_full"
            ;;
        batch_2)
            HS_DIR="/data/SpecForge/custom_dflash/hidden_states_batch2"
            ;;
        batch_3)
            HS_DIR="/data/SpecForge/custom_dflash/hidden_states_batch3"
            ;;
    esac
    
    echo "  Hidden states: $HS_DIR"
    echo "  Run extract script:"
    echo "    python3 /data/SpecForge/custom_dflash/extract_logits.py \\"
    echo "      --hidden-states-dir $HS_DIR \\"
    echo "      --output-dir $TO_LOGITS_DIR \\"
    echo "      --model-path /data/models/Qwen3.6-27B-Uncensored"
    echo ""
    echo "  OR use the skill script:"
    echo "    ./extract_logits.py --hidden-states-dir $HS_DIR --output-dir $TO_LOGITS_DIR"
    exit 0
fi

echo ""

# Step 4: Resume training on TO batch
echo "Step 4: Resume training on $TO_BATCH..."
echo "  Checkpoint: $LATEST_CHECKPOINT"
echo "  Logits: $TO_LOGITS_DIR"
echo ""
echo "  Run:"
echo "    ./resume_training.sh --batch $TO_BATCH --checkpoint $LATEST_CHECKPOINT"
echo ""

echo "=== TRANSITION READY ==="
