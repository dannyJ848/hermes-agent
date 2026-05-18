#!/bin/bash
# vLLM Health Check Script for DGX Spark
# Usage: bash vllm-health-check.sh

set -e

echo "=== vLLM Health Check ==="
echo ""

# Check container is running
if ! docker ps --format "{{.Names}}" | grep -q "vllm-merged"; then
    echo "FAIL: vllm-merged container not running"
    echo "Fix: docker start vllm-merged  OR  bash /tmp/deploy_vllm_dflash.sh"
    exit 1
fi
echo "PASS: Container running"

# Check API responds
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "FAIL: API not responding on localhost:8000"
    echo "Fix: docker restart vllm-merged"
    exit 1
fi
echo "PASS: API responding"

# Check models are loaded
MODELS=$(curl -s http://localhost:8000/v1/models | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data', [])))" 2>/dev/null || echo "0")
if [ "$MODELS" -lt 1 ]; then
    echo "FAIL: No models loaded"
    exit 1
fi
echo "PASS: $MODELS model(s) loaded"

# Check GPU utilization
GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1)
echo "INFO: GPU utilization: ${GPU_UTIL}%"

# Check memory usage
GPU_MEM=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader | head -1)
echo "INFO: GPU memory: $GPU_MEM"

echo ""
echo "=== All Checks Passed ==="
