#!/bin/bash
# Train EAGLE-3 draft model for Qwen3.6-35B-A3B on DGX Spark
# Run this AFTER hidden state generation completes

set -e

cd /data/SpecForge

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Target model path (abliterated)
TARGET_MODEL="/data/models/Qwen3.6-35B-A3B-Uncensored"

# Draft model config (Qwen3.5-35B-A3B is same architecture as Qwen3.6-35B-A3B)
DRAFT_CONFIG="configs/qwen3.5-35b-a3b-eagle3.json"

# Paths
DATA_PATH="cache/dataset/ultrachat_train.jsonl/ultrachat_train.jsonl"
HIDDEN_STATES_PATH="cache/hidden_states/qwen3.6-35b-a3b-ultrachat"
OUTPUT_DIR="cache/outputs/qwen3.6-35b-a3b-eagle3"
CACHE_DIR="cache"

# Training hyperparameters
NUM_EPOCHS=10
BATCH_SIZE=1
TP_SIZE=1
LEARNING_RATE=5e-5
MAX_LENGTH=4096

# Run training with HF backend (avoids SGLang SM121a issues)
/data/sglang-venv/bin/torchrun \
    --standalone \
    --nproc_per_node 1 \
    scripts/train_eagle3.py \
    --target-model-path "$TARGET_MODEL" \
    --target-model-backend hf \
    --trust-remote-code \
    --draft-model-config "$DRAFT_CONFIG" \
    --train-data-path "$DATA_PATH" \
    --train-hidden-states-path "$HIDDEN_STATES_PATH" \
    --output-dir "$OUTPUT_DIR" \
    --num-epochs "$NUM_EPOCHS" \
    --batch-size "$BATCH_SIZE" \
    --tp-size "$TP_SIZE" \
    --learning-rate "$LEARNING_RATE" \
    --max-length "$MAX_LENGTH" \
    --chat-template qwen \
    --cache-dir "$CACHE_DIR" \
    --embedding-key "model.language_model.embed_tokens.weight" \
    --lm-head-key "lm_head.weight" \
    --build-dataset-num-proc 4

echo "Training complete. Draft model saved to $OUTPUT_DIR"
