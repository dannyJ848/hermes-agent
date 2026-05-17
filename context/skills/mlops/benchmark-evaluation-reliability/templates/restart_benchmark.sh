#!/bin/bash
# restart_benchmark.sh — Recovery script after silent death
# Usage: Edit TASKS and MODEL_PATH, then run via terminal(background=true)

MODEL_PATH="/path/to/merged/model"
OUTPUT_DIR="/path/to/evaluation_results"
STATE_FILE="$OUTPUT_DIR/benchmark_state.txt"
VENV_PATH="/path/to/venv"

TASKS="mmlu gsm8k humaneval bbh arc_challenge winogrande"

# 1. Kill any lingering processes
echo "Killing old processes..."
pkill -9 -f lm_eval
pkill -9 -f python3.*benchmark
sleep 5

# 2. Verify clean state
if pgrep -f lm_eval > /dev/null; then
    echo "ERROR: Could not kill old lm_eval processes"
    exit 1
fi

# 3. Check GPU is free
nvidia-smi | grep -q "No running processes" || echo "WARNING: GPU may have stale context"

# 4. Load completed tasks
COMPLETED=""
if [ -f "$STATE_FILE" ]; then
    COMPLETED=$(cat "$STATE_FILE")
fi

# 5. Activate environment
source "$VENV_PATH/bin/activate"
mkdir -p "$OUTPUT_DIR"

# 6. Run remaining benchmarks
for task in $TASKS; do
    if echo "$COMPLETED" | grep -q "$task"; then
        echo "Skipping $task (already done)"
        continue
    fi
    
    echo "========================================"
    echo "Running $task..."
    echo "========================================"
    
    lm_eval --model hf \
        --model_args pretrained=$MODEL_PATH,dtype=bfloat16 \
        --tasks $task \
        --batch_size 1 \
        --output_path "$OUTPUT_DIR/$task" \
        --device cuda \
        2>&1 | tee -a "$OUTPUT_DIR/benchmark_suite.log"
    
    if [ $? -eq 0 ]; then
        echo "$task" >> "$STATE_FILE"
        echo "$task DONE" | tee -a "$OUTPUT_DIR/benchmark_suite.log"
    else
        echo "$task FAILED — stopping for manual inspection" | tee -a "$OUTPUT_DIR/benchmark_suite.log"
        exit 1
    fi
done

echo "========================================"
echo "ALL BENCHMARKS COMPLETE"
echo "========================================"
date | tee -a "$OUTPUT_DIR/benchmark_suite.log"
