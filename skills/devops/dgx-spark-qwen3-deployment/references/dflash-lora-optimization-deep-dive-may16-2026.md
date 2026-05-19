# DFlash + Dynamic LoRA Optimization Deep Dive - May 16 2026

## Optimal num_speculative_tokens Finding

After systematic testing, the optimal configuration for DFlash speculative decoding with dynamic LoRA on Qwen3.6-27B-Uncensored:

| num_speculative_tokens | Acceptance Rate | Mean Acceptance | Speed | Notes |
|------------------------|-----------------|-----------------|-------|-------|
| 4 | 47-54% | 2.9-3.2 | ~5 tok/s | Good balance |
| **5** | **54-60%** | **3.7-4.0** | **~6 tok/s** | **🏆 OPTIMAL** |
| 6 | 34% | 3.1 | ~1 tok/s | Pos 6 = 0% acceptance |
| 8 | 22-44% | 2.8-3.1 | ~0.6 tok/s | Too many positions |

## Key Insight: Position 6+ Always 0%

The draft model (Qwen3.5-27B-DFlash) cannot predict beyond position 5. This is a fundamental limitation, not a configuration issue. Setting num_speculative_tokens > 5 wastes compute.

## Why num_speculative_tokens=5 is Optimal

1. **Acceptance rate**: 54-60% of tokens accepted
2. **Mean acceptance**: 3.7-4.0 tokens per speculation
3. **Speed**: ~6 tok/s (vs ~4 tok/s without speculative decoding)
4. **No wasted positions**: Positions 1-5 all have >0% acceptance

## Deployment Command

```bash
docker run -d \
  --name vllm-base-lora \
  --runtime nvidia \
  --gpus all \
  -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/SpecForge/custom_dflash/checkpoints \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --max-model-len 131072 \
  --enable-lora \
  --max-lora-rank 256 \
  --lora-modules custom-model=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --speculative-config '{"method": "dflash", "model": "/data/models/Qwen3.5-27B-DFlash", "num_speculative_tokens": 5}' \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 256 \
  --gpu-memory-utilization 0.95 \
  --dtype bfloat16 \
  --trust-remote-code \
  --enable-prefix-caching \
  --no-enable-prefix-caching \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

## Critical Flags for Hermes

- `--enable-auto-tool-choice` — Required for tool calling
- `--tool-call-parser hermes` — Required for Hermes tool format
- `--max-lora-rank 256` — Must match LoRA adapter rank (default 16 is too low)

## Verification

```bash
# Check vLLM is serving with speculative decoding
curl http://localhost:8000/v1/models

# Check model names
# Should show: /data/models/Qwen3.6-27B-Uncensored and custom-model

# Test inference
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/data/models/Qwen3.6-27B-Uncensored", "messages": [{"role": "user", "content": "Hello"}]}'
```
