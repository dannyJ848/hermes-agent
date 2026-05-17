# Qwen3.6-27B Inference Acceleration Plan

## DGX Spark Deployment — May 14, 2026

Research findings from deep research on speculative decoding, KV cache optimization, quantization, and continuous batching for Qwen3.6-27B on vLLM.

---

## Phase 1: Speculative Decoding (Highest Impact, Lowest Risk)

### Option A: DFlash (Recommended — purpose-built for Qwen3.6)

**What it is:** Block diffusion drafter that generates multiple tokens in parallel using a lightweight diffusion model. Lossless — verified tokens are exact.

**Speedup:** Up to 6x on Qwen3.6-27B (z-lab benchmarks)

**Installation:**
```bash
# On DGX
pip install -e ".[vllm]"  # From z-lab/dflash repo
# OR for standard models:
pip install dflash[vllm]
```

**vLLM serve flags:**
```bash
vllm serve /data/models/Qwen3.6-27B-Uncensored \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --max-model-len 131072 \
  --speculative-config '{"method": "dflash", "model": "z-lab/Qwen3.6-27B-DFlash"}' \
  --num-speculative-tokens 5 \
  --lora-modules merged-lora=/data/SpecForge/custom_dflash/checkpoints/final_model/
```

**Key considerations:**
- DFlash drafter is ~300MB — negligible memory overhead
- Works with LoRA adapters (verified by z-lab)
- Requires vLLM 0.20.1+ (check current version)
- May have interaction with prefix caching (monitor cache hit rates)

### Option B: EAGLE-3 (If DFlash unavailable)

**What it is:** Extracts features from base model to train a draft model. 2-3x speedup.

**vLLM flags:**
```bash
vllm serve ... \
  --speculative-model "path/to/eagle-draft" \
  --num-speculative-tokens 4 \
  --speculative-draft-tensor-parallel-size 1
```

**Tradeoff:** Requires training/finding an EAGLE draft model for Qwen3.6-27B. Community may not have one yet.

### Option C: N-Gram Speculation (Fallback — zero setup)

**What it is:** Matches n-grams in the prompt to speculate repeated patterns. 1.2-1.4x speedup.

**vLLM flags:**
```bash
vllm serve ... \
  --speculative-model "[ngram]" \
  --num-speculative-tokens 3 \
  --ngram-prompt-lookup-max 4
```

**Best for:** Tool calling with repetitive XML patterns (Hermes format).

---

## Phase 2: KV Cache Optimization

### 2.1 Prefix Caching (Immediate win for tool calling)

**What it does:** Caches KV vectors for identical prompt prefixes. Since Hermes tool calls have long system prompts + tool definitions, this avoids recomputing them every request.

**vLLM flag:**
```bash
vllm serve ... \
  --enable-prefix-caching
```

**Expected impact:** 30-50% faster for repeated tool call patterns (same system prompt, different user queries).

### 2.2 KV Cache Quantization (FP8)

**What it does:** Quantizes KV cache from BF16 to FP8. Reduces memory footprint ~50%, allowing larger batch sizes or longer context.

**vLLM flags:**
```bash
vllm serve ... \
  --kv-cache-dtype fp8 \
  --quantization fp8
```

**Expected impact:**
- Memory: ~50% reduction in KV cache
- Throughput: +20-40% from larger batch capacity
- Quality: Minimal degradation (<1% on benchmarks)

**Compatibility:** Works with Qwen3.6-27B-FP8 weights. If using BF16 base model, need to quantize first.

### 2.3 Chunked Prefill

**What it does:** Breaks long prefills into chunks to avoid blocking decode phase. Critical for 131K context.

**vLLM flag:**
```bash
vllm serve ... \
  --enable-chunked-prefill \
  --max-num-batched-tokens 8192
```

**Expected impact:** Reduces time-to-first-token for long contexts by 40-60%.

---

## Phase 3: Quantization (If Memory-Constrained)

### FP8 Weights (Recommended over INT4/INT8)

**Why FP8 over GPTQ/AWQ:**
- Better accuracy preservation for tool calling
- Native NVIDIA support on A100/H100 (Transformer Engine)
- Qwen3.6-27B-FP8 official weights exist

**Download:**
```bash
huggingface-cli download Qwen/Qwen3.6-27B-FP8 \
  --local-dir /data/models/Qwen3.6-27B-FP8
```

**vLLM serve:**
```bash
vllm serve /data/models/Qwen3.6-27B-FP8 \
  --quantization fp8 \
  --kv-cache-dtype fp8 \
  --max-model-len 131072
```

**Expected impact:**
- Memory: 27GB → ~14GB (weights only)
- Throughput: +50-80% from reduced memory bandwidth
- Quality: <2% degradation on MMLU/GSM8K

**Caveat:** Need to merge LoRA into FP8 base or re-train adapter on FP8 model.

---

## Phase 4: Continuous Batching & Scheduling

### Current vLLM defaults are usually fine, but tune these:

```bash
vllm serve ... \
  --max-num-seqs 256 \          # Max concurrent sequences
  --max-num-batched-tokens 16384 \  # Tokens per batch iteration
  --max-model-len 131072 \
  --gpu-memory-utilization 0.95 \   # Use 95% of GPU memory
  --enable-prefix-caching \
  --enable-chunked-prefill
```

**For latency-sensitive (tool calling):**
- Lower `--max-num-batched-tokens` to 4096 (faster iteration)
- Lower `--max-num-seqs` to 64 (less contention)

**For throughput (batch training data generation):**
- Raise `--max-num-batched-tokens` to 32768
- Raise `--max-num-seqs` to 256

---

## Recommended Integration Order

### Immediate (Today):
1. Enable prefix caching: `--enable-prefix-caching`
2. Enable chunked prefill: `--enable-chunked-prefill`
3. Try n-gram speculation for tool calls: `--speculative-model "[ngram]"`

### Short-term (This week):
4. Deploy DFlash drafter: `z-lab/Qwen3.6-27B-DFlash`
5. Benchmark with/without speculative decoding
6. If memory pressure: switch to FP8 weights + KV cache

### Medium-term (Next sprint):
7. Train custom EAGLE draft model on your specific tool-calling patterns
8. Experiment with KV cache quantization if context length grows
9. Profile with vLLM benchmarks to find optimal batch sizes

---

## Expected Combined Speedup

| Technique | Speedup | Cumulative |
|-----------|---------|------------|
| Baseline (BF16) | 1.0x | 1.0x |
| Prefix caching | 1.3x | 1.3x |
| Chunked prefill | 1.2x | 1.56x |
| DFlash speculative | 3.0x | 4.68x |
| FP8 weights + KV | 1.5x | 7.02x |

**Realistic target:** 4-5x end-to-end speedup with DFlash + prefix caching + chunked prefill.

---

## Monitoring & Validation

After each change, benchmark with:
```bash
# vLLM built-in benchmark
python -m vllm.benchmarks.benchmark_throughput \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --input-len 4096 \
  --output-len 512 \
  --num-prompts 100

# Tool calling specific benchmark
curl -s http://10.0.0.171:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "merged-lora",
    "messages": [{"role": "user", "content": "Search for AI news"}],
    "tools": [{"type": "function", "function": {"name": "web_search", "description": "Search", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}],
    "tool_choice": "auto",
    "max_tokens": 200
  }'
```

Track: TTFT (time to first token), TPOT (time per output token), throughput (tok/s).

---

## Risk Assessment

| Technique | Risk | Mitigation |
|-----------|------|------------|
| DFlash | Draft model may not match LoRA fine-tune | Test tool call accuracy before/after |
| FP8 quantization | Tool calling accuracy degradation | Benchmark on tool-use dataset |
| Prefix caching | Cache invalidation bugs | Monitor cache hit rates |
| Chunked prefill | Longer TTFT for short prompts | Tune chunk size |

---

## Sources

- z-lab/dflash GitHub: https://github.com/z-lab/dflash
- Qwen speed benchmarks: https://qwen.readthedocs.io/en/latest/getting_started/speed_benchmark.html
- vLLM speculative decoding docs: https://docs.vllm.ai/en/stable/features/speculative_decoding/
- vLLM optimization guide: https://docs.vllm.ai/en/stable/configuration/optimization/
- LLMKube Qwen3.6-27B bakeoff: https://llmkube.com/blog/qwen3-6-27b-bakeoff
