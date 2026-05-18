# vLLM 0.20.2 + N-gram Speculative Decoding + FP8 Weights — Verified Deployment

**Date:** May 14, 2026
**Model:** Qwen3.6-27B-Uncensored + LoRA (r=256, alpha=512)
**vLLM Version:** 0.20.2
**Hardware:** NVIDIA DGX Spark (GB10, 128GB unified memory)

## Deployment Script

```bash
#!/bin/bash
set -e

# Stop existing container
docker stop vllm-merged 2>/dev/null || true
docker rm vllm-merged 2>/dev/null || true

# Start optimized vLLM container
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
  --enable-prefix-caching \
  --enable-chunked-prefill \
  --speculative-config '{"method":"ngram","num_speculative_tokens":5}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 8192 \
  --max-num-seqs 256

echo 'vLLM container started with optimizations'
sleep 15
curl -s http://localhost:8000/v1/models | python3 -m json.tool
```

## Key Findings

### N-gram Speculative Decoding

- **Works correctly in vLLM 0.20.2** (earlier corruption reports were from 0.19.x)
- Acceptance rate: 60-85% (varies by prompt diversity)
- Mean acceptance length: 2-5 tokens
- Zero quality degradation (lossless)
- No authentication required (unlike DFlash/EAGLE-3)
- Less effective on creative/diverse text (20-40% acceptance)

### FP8 Weight Quantization

- **Works correctly in vLLM 0.20.2** (earlier pickling errors were from 0.19.x)
- Uses CutlassFP8ScaledMMLinearKernel (confirmed in logs)
- Tool calling works correctly (tested with forced and auto tool_choice)
- No quality degradation observed
- ~1.5x speedup over BF16 weights from reduced memory bandwidth

### Performance Benchmarks

| Concurrent | Throughput | Latency |
|-----------:|-----------:|--------:|
| 1 | 6.6 tok/s | 7.5s |
| 4 | 26.6 tok/s | 4.5s |
| 8 | 49.0 tok/s | 4.9s |
| 16 | 80.9 tok/s | 5.9s |
| 32 | 143.2 tok/s | 6.7s |
| 64 | 200.1 tok/s | 9.6s |
| 128 | 203.6 tok/s | 18.9s |
| 200 | 198.9 tok/s | 30.2s |

Sweet spot: 64-128 concurrent requests for maximum throughput.

### Tool Calling Verification

Forced tool call (with `tool_choice: {"type": "function", "function": {"name": "web_search"}}`):
- Response time: 2-5s
- Returns proper `tool_calls` array
- Function name and arguments correct

Auto tool call (with `tool_choice: "auto"`):
- Response time: 25-30s
- Model reasons before calling tool
- Returns proper `tool_calls` array after reasoning

### Startup Timeline

1. Container start: instant
2. Model shard loading: ~3 min (15 shards)
3. torch.compile: ~66s (cached on subsequent boots)
4. CUDA graph capture: ~74s
5. Total to ready: ~5-6 minutes

## vLLM 0.20.2 Format Changes

### Speculative Config (Dict Format)

```bash
# CORRECT (vLLM 0.20.2+):
--speculative-config '{"method":"ngram","num_speculative_tokens":5}'

# INCORRECT (old format, removed):
--speculative-model [ngram] --num-speculative-tokens 5
```

### EngineArgs Signature

`speculative_model` parameter removed from `EngineArgs.__init__()`. Use `speculative_config` dict instead.

## Prefix Caching Note

Enabled but showing 0% hit rate in benchmarks. Likely because:
- Test prompts were too short to benefit
- Mamba cache mode experimental warning in logs
- May improve with longer shared prefixes in production workloads

## Shell Escaping Pitfall

When creating deployment scripts via SSH, NEVER use heredocs with triple-quoted strings containing newlines. The shell interprets `\n` and quote characters. Use base64 encoding instead:

```bash
# WRONG — causes unterminated string literal errors
ssh host "cat > script.py << 'EOF'
...python code with quotes...
EOF"

# CORRECT — base64 encode locally, decode on remote
base64 -w 0 script.py | ssh host "base64 -d > script.py"
```
