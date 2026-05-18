#!/bin/bash
# Restart vLLM with merged LoRA adapter on DGX Spark
# Usage: bash restart_vllm_merged.sh
#
# UPDATED May 15, 2026: Removed --enable-prefix-caching (broken on hybrid models),
# increased --max-num-batched-tokens 8192 -> 32768, reduced --max-num-seqs 256 -> 128
# See references/vllm-systematic-optimization-may15-2026.md for methodology.

set -e

# Stop and remove existing container
docker stop vllm-merged 2>/dev/null || true
docker rm vllm-merged 2>/dev/null || true

# Kill any stuck SGLang processes that hold GPU memory
for pid in $(nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader | grep sglang | cut -d',' -f1); do
    echo "Killing stuck SGLang process $pid"
    sudo kill -9 "$pid" 2>/dev/null || true
done

# Wait for GPU memory release
sleep 3

# Verify GPU is clear
echo "GPU processes after cleanup:"
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader || echo "No GPU processes"

# Start vLLM with optimized config (May 15, 2026)
# Key changes from previous config:
# - REMOVED --enable-prefix-caching: Qwen3.6 hybrid reports is_prefix_caching_supported=False
# - INCREASED --max-num-batched-tokens 8192 -> 32768: better concurrent batching
# - REDUCED --max-num-seqs 256 -> 128: more efficient memory allocation
# - KEPT n-gram speculative decoding: 20% acceptance, ~5-10% speedup, lossless
# - KEPT FP8 weights + BF16 KV: working in vLLM 0.20.2, ~1.5x speedup
# - KEPT chunked prefill: better batching for concurrent requests
# - KEPT CUDA graphs + torch.compile: stable, marginal gains

docker run -d \
  --name vllm-merged \
  --runtime nvidia \
  --gpus all \
  -p 8000:8000 \
  -v /data:/data \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e VLLM_LOGGING_LEVEL=INFO \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --enable-chunked-prefill \
  --speculative-config '{"method":"ngram","num_speculative_tokens":5}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 128

echo 'vLLM container started. Waiting for readiness...'
sleep 60

# Health check
for i in {1..10}; do
    if curl -s http://localhost:8000/v1/models >/dev/null 2>&1; then
        echo 'vLLM is READY'
        curl -s http://localhost:8000/v1/models | python3 -c 'import json,sys; d=json.load(sys.stdin); print("Models:", [m["id"] for m in d.get("data",[])])'
        exit 0
    fi
    echo "Attempt $i/10: not ready yet, waiting 30s..."
    sleep 30
done

echo 'vLLM failed to start. Check logs:'
docker logs --tail 50 vllm-merged
exit 1
