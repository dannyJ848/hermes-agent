#!/bin/bash
# DFlash Training for Qwen3.6-27B on DGX Spark

set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
ROOT_DIR=/data/SpecForge

TARGET_MODEL="/data/models/Qwen3.6-27B-Uncensored"
DRAFT_CONFIG="$SCRIPT_DIR/qwen3.6-27b-dflash.json"
OUTPUT_DIR="/data/models/Qwen3.6-27B-DFlash"
TRAIN_DATA="$ROOT_DIR/cache/dataset/ultrachat_train.jsonl/ultrachat_train.jsonl"

export HF_DATASETS_CACHE=$ROOT_DIR/cache/hf_datasets
export TORCHINDUCTOR_CACHE_DIR=$ROOT_DIR/cache/compiled_kernels
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_VISIBLE_DEVICES=0

# Use EAGER attention backend (flex_attention fails on SM121a)
ATTENTION_BACKEND=eager
NUM_GPUS=1

BATCH_SIZE=1
LEARNING_RATE=6e-4
NUM_EPOCHS=3
MAX_LENGTH=2048
BLOCK_SIZE=16
NUM_ANCHORS=512
LOSS_DECAY_GAMMA=7.0

echo "=== DFlash Training for Qwen3.6-27B ==="
echo "Target: $TARGET_MODEL"
echo "Output: $OUTPUT_DIR"
echo "Attention: $ATTENTION_BACKEND (SM121a compatible)"

if [ ! -f "$TRAIN_DATA" ]; then
    echo "ERROR: Training data not found at $TRAIN_DATA"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

cd "$ROOT_DIR"

torchrun     --standalone     --nproc_per_node $NUM_GPUS     $ROOT_DIR/scripts/train_dflash.py     --target-model-path "$TARGET_MODEL"     --target-model-backend hf     --draft-config-path "$DRAFT_CONFIG"     --train-data-path "$TRAIN_DATA"     --output-dir "$OUTPUT_DIR"     --num-epochs $NUM_EPOCHS     --batch-size $BATCH_SIZE     --learning-rate $LEARNING_RATE     --warmup-ratio 0.04     --max-grad-norm 1.0     --max-length $MAX_LENGTH     --chat-template qwen3.5     --attention-backend $ATTENTION_BACKEND     --num-anchors $NUM_ANCHORS     --loss-decay-gamma $LOSS_DECAY_GAMMA     --log-interval 10     --save-interval 1000     --block-size $BLOCK_SIZE     --trust-remote-code     --build-dataset-num-proc 4     --embedding-key "model.language_model.embed_tokens.weight"     --lm-head-key "lm_head.weight"

echo "Training complete! Output: $OUTPUT_DIR"
