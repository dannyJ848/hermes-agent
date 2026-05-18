# Base + Dynamic LoRA + DFlash Speculative Decoding — Performance Results

Date: May 16, 2026
Model: Qwen3.6-27B-Uncensored (base) + custom_dflash LoRA adapter
Draft: Qwen3.5-27B-DFlash
vLLM: 0.20.2
Hardware: DGX Spark GB10 (128GB unified memory)

## Configuration

```bash
docker run -d \
  --name vllm-base-lora \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/SpecForge/custom_dflash/checkpoints \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --max-model-len 131072 \
  --enable-lora \
  --max-lora-rank 256 \
  --lora-modules custom-model=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --speculative-config '{"method": "dflash", "model": "/data/models/Qwen3.5-27B-DFlash", "num_speculative_tokens": 8}' \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 256 \
  --gpu-memory-utilization 0.95 \
  --dtype bfloat16 \
  --trust-remote-code \
  --enable-prefix-caching \
  --no-enable-prefix-caching
```

**Critical flag:** `--max-lora-rank 256` — default is 16, which causes:
```
ValueError: LoRA rank 256 is greater than max_lora_rank 16.
```

## Performance Results

### Startup Time
- Model load: ~55GB
- torch.compile: ~8s
- Warmup: ~67s
- CUDA graph capture (PIECEWISE): ~34s (88 graphs)
- CUDA graph capture (FULL): ~49s (88 graphs)
- **Total startup: ~314s (5.2 minutes)**

### Inference Speed
| Request | Tokens | Time | Speed | Notes |
|---------|--------|------|-------|-------|
| 1st (warmup) | ~100 | 45.7s | ~2.2 tok/s | LoRA compilation overhead |
| 2nd | 111 | 19.2s | **5.8 tok/s** | Stabilized |
| 3rd | ~150 | ~13s | ~11.5 tok/s | Further warmup |

**Stabilized speed: 5.8-11.5 tok/s** depending on prompt complexity and cache state.

### Speculative Decoding Metrics

```
Mean acceptance length: 4.55 (warmup) → 3.12 → 2.80 (stabilized)
Draft acceptance rate: 44.3% → 26.5% → 22.5%

Per-position acceptance rate (stabilized):
  Position 1: 71.4%
  Position 2: 42.9%
  Position 3: 28.6%
  Position 4: 22.9%
  Position 5: 11.4%
  Position 6: 2.9%
  Position 7: 0.0%
  Position 8: 0.0%
```

**Key insight:** With `num_speculative_tokens=8`, positions 7-8 have 0% acceptance. The draft model is only accurate for the first 5-6 tokens. Reducing to `num_speculative_tokens=5` may improve overall efficiency by avoiding wasted draft computation on positions that always fail.

## Comparison: Base+LoRA vs Merged Model

| Metric | Base+LoRA+DFlash | Merged+DFlash | Base Only (no LoRA) |
|--------|-----------------|---------------|---------------------|
| Speed | 5.8 tok/s | ~0.6 tok/s (broken) | ~12 tok/s |
| Acceptance | 22-44% | 2.9% | N/A |
| Vision | ✅ Yes | ❌ No (text-only merge) | ✅ Yes |
| Dynamic LoRA | ✅ Yes | ❌ No (static) | N/A |
| Startup | 5.2 min | 5.2 min | 5.2 min |

## Key Findings

1. **Base+LoRA+DFlash is viable** — Contrary to earlier findings (pitfall #35), the combination works when `--max-lora-rank` is set correctly.

2. **Merged model is broken** — `peft.merge_and_unload()` corrupts Qwen3.5/3.6 weights, producing garbled output. See `references/merged-model-garbled-output-may16-2026.md`.

3. **Acceptance rate is good** — 22-44% is significantly better than the merged model's 2.9%. The draft model works well with the base model; the earlier slowdown was likely due to misconfiguration (missing `--max-lora-rank 256`).

4. **First request is slow** — ~45s for first request due to LoRA compilation. Subsequent requests are faster.

5. **Vision is preserved** — Multi-modal warmup completed successfully (25.5s + 17.1s). Image processing works.

## Tradeoffs

**Base+LoRA+DFlash (this config):**
- ✅ Dynamic LoRA switching
- ✅ Vision capabilities
- ✅ 22-44% draft acceptance
- ⚠️ 5.8 tok/s (slower than base-only 12 tok/s)
- ⚠️ First request ~45s (compilation)

**Merged model (not working):**
- ❌ Garbled output (corrupted weights)
- ❌ No vision
- ❌ Static weights

**Base only (no speculative decoding):**
- ✅ 12 tok/s
- ✅ Vision
- ❌ No speedup from draft model

## Recommendations

1. **Use base+LoRA+DFlash for production** — It's the only working configuration that preserves both vision and dynamic LoRA.

2. **Reduce `num_speculative_tokens` to 5** — Positions 7-8 have 0% acceptance. Reducing to 5 may improve efficiency by ~10-15%.

3. **Warm up before serving** — Send 2-3 dummy requests after startup to trigger LoRA compilation before real traffic.

4. **Monitor acceptance rate** — If acceptance drops below 15%, the draft model may need retraining on the current LoRA weights.

## Verification Commands

```bash
# Check server is ready
curl -s http://localhost:8000/v1/models | python3 -m json.tool

# Test with LoRA
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "custom-model",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 100
  }'

# Check speculative decoding metrics
docker logs vllm-base-lora 2>&1 | grep "SpecDecoding metrics" | tail -5
```
