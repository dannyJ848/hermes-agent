#!/bin/bash
# Deploy vLLM with optimized configuration for Qwen3.6-27B on DGX Spark
# Created: May 15, 2026
# See references/vllm-systematic-optimization-may15-2026.md for methodology

set -e

docker stop vllm-merged 2>/dev/null || true
docker rm vllm-merged 2>/dev/null || true

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

echo "vLLM optimized deployment started"
sleep 15
curl -s http://localhost:8000/v1/models | python3 -m json.tool 2>/dev/null || echo "Model not ready yet"
