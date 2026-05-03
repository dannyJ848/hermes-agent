#!/bin/bash
# Custom DFlash Training Pipeline for Qwen3.6-27B on DGX Spark GB10
set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
ROOT_DIR=/data/SpecForge
CUSTOM_DIR=$ROOT_DIR/custom_dflash

TARGET_MODEL="/data/models/Qwen3.6-27B-Uncensored"
DATA_PATH="$ROOT_DIR/cache/dataset/ultrachat_train.jsonl/ultrachat_train.jsonl"
HIDDEN_DIR="$CUSTOM_DIR/hidden_states"
OUTPUT_DIR="/data/models/Qwen3.6-27B-DFlash-Custom"
LOG_FILE="/tmp/dflash_custom.log"

export HF_DATASETS_CACHE=$ROOT_DIR/cache/hf_datasets
export TORCHINDUCTOR_CACHE_DIR=$ROOT_DIR/cache/compiled_kernels
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_VISIBLE_DEVICES=0

echo "========================================" | tee -a $LOG_FILE
echo "Custom DFlash Training Pipeline" | tee -a $LOG_FILE
echo "Target: $TARGET_MODEL" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE

mkdir -p "$HIDDEN_DIR"
mkdir -p "$OUTPUT_DIR"

# Phase 1: Generate hidden states
echo "PHASE 1: Generating hidden states..." | tee -a $LOG_FILE
python3 "$CUSTOM_DIR/phase1_generate_hidden_states.py"     --model-path "$TARGET_MODEL"     --data-path "$DATA_PATH"     --output-dir "$HIDDEN_DIR"     --max-length 1024     --num-samples 5000     --trust-remote-code     2>&1 | tee -a $LOG_FILE

echo "Phase 1 complete! Hidden states saved to $HIDDEN_DIR" | tee -a $LOG_FILE

# Phase 2: Train draft model
echo "PHASE 2: Training draft model..." | tee -a $LOG_FILE
python3 "$CUSTOM_DIR/phase2_train_draft.py"     --hidden-states-dir "$HIDDEN_DIR"     --target-model-path "$TARGET_MODEL"     --output-dir "$OUTPUT_DIR"     --num-epochs 3     --batch-size 1     --learning-rate 6e-4     --max-length 1024     --block-size 16     --save-interval 500     --trust-remote-code     2>&1 | tee -a $LOG_FILE

echo "Phase 2 complete! Draft model saved to $OUTPUT_DIR" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE
echo "PIPELINE COMPLETE" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE
