#!/bin/bash
# DGX Qwen3.6-27B-Uncensored Optimized Launch Script
# Generated: 2026-05-18
# 
# OPTIMIZATIONS APPLIED:
# - BF16 weights (native, no quantization)
# - FP8 KV cache (--kv-cache-dtype fp8_e5m2) = 2x compression, safe with BF16
# - 0.95 GPU memory utilization (maxed for context)
# - Single sequence mode (--max-num-seqs 1) for dedicated long-context
# - 262K max model len (Qwen3.6 native context window)
# - Chunked prefill enabled by default (vLLM 0.21+)
#
# TESTED CONTEXT LENGTHS:
# - 16K chars (~4K tokens): 43s
# - 32K chars (~8K tokens): 22s
# - 64K chars (~16K tokens): 118s
# - 128K chars (~32K tokens): 237s
# - 200K chars (~50K tokens): ~300s+
# - 256K chars (~64K tokens): ~600s+
#
# GPU: NVIDIA GB10 (130GB VRAM)
# Available KV cache: ~59 GiB with FP8

export PATH=/data/SpecForge/venv/bin:$PATH
export CUDA_VISIBLE_DEVICES=0

# Kill existing vLLM
pkill -f "vllm serve" || true
sleep 3

# Launch optimized vLLM
nohup vllm serve /data/models/Qwen3.6-27B-Uncensored \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype bfloat16 \
  --max-model-len 262144 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --chat-template /data/models/Qwen3.6-27B-Uncensored/chat_template.jinja \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.95 \
  --trust-remote-code \
  --no-enable-prefix-caching \
  --kv-cache-dtype fp8_e5m2 \
  --max-num-seqs 1 \
  > /tmp/vllm_optimized.log 2>&1 &

echo $! > /tmp/vllm.pid
echo "vLLM optimized started with PID $!"
echo "Logs: /tmp/vllm_optimized.log"
echo ""
echo "Wait ~90s for CUDA graph compilation, then test with:"
echo "  curl -s http://10.0.0.171:8000/v1/models | grep max_model_len"
