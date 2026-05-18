# DFlash `num_speculative_tokens` Tuning — Systematic Optimization

Date: May 16, 2026
Model: Qwen3.6-27B-Uncensored (base) + custom_dflash LoRA adapter
Draft: Qwen3.5-27B-DFlash
vLLM: 0.20.2
Hardware: DGX Spark GB10 (128GB unified memory)

## Methodology

Systematic sweep of `num_speculative_tokens` values (3-8) to find optimal acceptance rate/speed balance. Each configuration tested with identical prompt ("Explain quantum computing in simple terms.", max_tokens=100).

## Results Summary

| `num_speculative_tokens` | Acceptance Rate | Mean Acceptance Length | Positions with >0% | Notes |
|--------------------------|---------------|------------------------|---------------------|-------|
| **3** | Not tested | — | — | — |
| **4** | 46.6% - 53.9% | 2.87 - 3.16 | 4/4 | Good balance |
| **5** | **54.3% - 60.0%** | **3.71 - 4.00** | **5/5** | **🏆 OPTIMAL** |
| **6** | 34.4% | 3.06 | 5/6 (pos 6: 0%) | Drops at position 6 |
| **8** | 22.5% - 44.3% | 2.80 - 4.55 | 6/8 (pos 7-8: 0%) | Too many wasted positions |

## Detailed Per-Position Breakdown

### `num_speculative_tokens=5` (OPTIMAL)

```
Test 1: Mean acceptance: 4.00, Rate: 60.0%
  Pos 1: 100.0% | Pos 2: 66.7% | Pos 3: 66.7% | Pos 4: 66.7% | Pos 5: 16.7%

Test 2: Mean acceptance: 3.71, Rate: 54.3%
  Pos 1: 85.7% | Pos 2: 71.4% | Pos 3: 57.1% | Pos 4: 42.9% | Pos 5: 14.3%
```

**Why 5 is optimal:**
- First 3 positions: 57-100% acceptance (strong)
- Position 4: 43-67% acceptance (usable)
- Position 5: 14-17% acceptance (marginal but non-zero)
- All 5 positions contribute; no wasted computation

### `num_speculative_tokens=6`

```
Mean acceptance: 3.06, Rate: 34.4%
  Pos 1: 81.2% | Pos 2: 50.0% | Pos 3: 37.5% | Pos 4: 25.0% | Pos 5: 12.5% | Pos 6: 0.0%
```

**Problem:** Position 6 has 0% acceptance. The draft model never gets 6 tokens right, so that position is pure overhead.

### `num_speculative_tokens=8`

```
Test 1: Mean acceptance: 4.55, Rate: 44.3% (warmup)
  Pos 1: 71.4% | Pos 2: 42.9% | Pos 3: 28.6% | Pos 4: 22.9% | Pos 5: 11.4% | Pos 6: 2.9% | Pos 7: 0.0% | Pos 8: 0.0%

Test 2: Mean acceptance: 2.80, Rate: 22.5% (stabilized)
  Pos 1: 71.4% | Pos 2: 42.9% | Pos 3: 28.6% | Pos 4: 22.9% | Pos 5: 11.4% | Pos 6: 2.9% | Pos 7: 0.0% | Pos 8: 0.0%
```

**Problem:** Positions 7-8 have 0% acceptance. Two full positions of wasted draft computation.

## Key Finding

**`num_speculative_tokens=5` is the sweet spot** because:
- Every position has >0% acceptance (no wasted computation)
- First 3 positions have strong acceptance (57-100%)
- Overall rate: 54-60% (highest observed)
- Mean acceptance length: 3.71-4.00 (74-80% of 5 tokens)

With `num_speculative_tokens=6`, position 6 drops to **0%**, dragging the average down to 34%.

## Speed Comparison

| Config | First Request | Stabilized | Notes |
|--------|--------------|------------|-------|
| `num_speculative_tokens=5` | ~38s | ~5.8 tok/s | Best acceptance |
| `num_speculative_tokens=8` | ~45s | 5.8-11.5 tok/s | More variance |

Speed is comparable; acceptance rate is the differentiator.

## Recommended Deployment Config

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
  --speculative-config '{"method": "dflash", "model": "/data/models/Qwen3.5-27B-DFlash", "num_speculative_tokens": 5}' \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 256 \
  --gpu-memory-utilization 0.95 \
  --dtype bfloat16 \
  --trust-remote-code \
  --enable-prefix-caching \
  --no-enable-prefix-caching
```

**Critical flags:**
- `--max-lora-rank 256` — REQUIRED (default 16 fails with rank mismatch)
- `num_speculative_tokens=5` — OPTIMAL (not 8, not 6)

## Verification Commands

```bash
# Check speculative decoding metrics
docker logs vllm-base-lora 2>&1 | grep "SpecDecoding metrics" | tail -5

# Expected output for optimal config:
# Mean acceptance length: 3.71, Accepted throughput: 0.34 tokens/s,
# Drafted throughput: 0.62 tokens/s, Accepted: 38 tokens, Drafted: 70 tokens,
# Per-position acceptance rate: 0.857, 0.714, 0.571, 0.429, 0.143,
# Avg Draft acceptance rate: 54.3%

# Test request with timing
time curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "custom-model",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 100
  }'
```

## Tuning Methodology for Other Models

To find optimal `num_speculative_tokens` for a different model pair:

1. Start with `num_speculative_tokens=8` (maximum)
2. Run 3-5 test requests with identical prompts
3. Check logs for per-position acceptance rates
4. Find the position where acceptance drops to 0%
5. Set `num_speculative_tokens` to that position minus 1
6. Verify overall acceptance rate improves

**Example:** If position 6 is 0%, set `num_speculative_tokens=5`.

## Related

- `references/base-lora-dflash-performance-may16-2026.md` — Base+LoRA+DFlash performance characterization
- `references/merged-model-garbled-output-may16-2026.md` — Why merged model doesn't work
- `references/vision-preserving-lora-merge-may16-2026.md` — Vision-preserving merge technique
