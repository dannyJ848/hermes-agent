# vLLM Context Window Upgrade Pattern

## Problem

When upgrading vLLM's context window (e.g., 64K → 128K), simply changing `--max-model-len` is NOT sufficient if the container was launched with a different value. The vLLM server caches the model's config at startup time.

## Solution: Full Container Restart

```bash
# 1. Stop and remove old container
docker stop vllm-merged 2>/dev/null
docker rm vllm-merged 2>/dev/null

# 2. Launch with new --max-model-len
docker run -d \
  --name vllm-merged \
  --runtime nvidia \
  --gpus all \
  -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints/final_model:/data/checkpoints/final_model \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.95
```

## Verification

```bash
# Wait for startup (~2-3 minutes for compilation)
curl -s http://localhost:8000/v1/models | python3 -m json.tool | grep max_model_len
# Expected: "max_model_len": 131072
```

## KV Cache Impact

| Context | KV Cache | Concurrency (131K req) |
|---------|----------|------------------------|
| 64K | 885,310 tokens | ~13.5x |
| 128K | 828,589 tokens | ~6.32x |

Note: Higher context = less concurrency. For agent workloads, 64K is usually sufficient.

## Common Failure: LoRA Path Mismatch

If vLLM fails with `LoRAAdapterNotFoundError`, the `--lora-modules` path is wrong:

```
vllm.exceptions.LoRAAdapterNotFoundError: Loading lora merged-lora failed:
No adapter found for /data/checkpoints/final_model_merged_vllm
```

**Fix:** Point to the actual adapter directory (with `adapter_config.json` and `adapter_model.safetensors`), NOT the merged model directory:

```bash
# WRONG: Merged model dir (no adapter files)
--lora-modules merged-lora=/data/checkpoints/final_model_merged_vllm

# CORRECT: Adapter dir (has adapter_config.json + adapter_model.safetensors)
--lora-modules merged-lora=/data/checkpoints/final_model
```

## Startup Timeline

1. **Model loading:** ~80 seconds (55 GiB)
2. **LoRA adapter loading:** ~20 seconds
3. **CUDA graph compilation:** ~45 seconds (102 piecewise + 70 decode graphs)
4. **FlashInfer autotuning:** ~2 seconds
5. **Total:** ~2.5-3 minutes

## Connection Reset During Startup

If `curl` returns `Recv failure: Connection reset by peer`, the server is still initializing. Wait for CUDA graph compilation to complete (watch logs for "Application startup complete").
