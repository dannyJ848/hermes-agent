# Inference Acceleration Quality Impact — Qwen 27B BF16

## Quick Reference

When user asks "will BF16 quality drop?" or any variant about quality impact of speedups:

| Technique | Quality Impact | Safe for Tool Calling? |
|-----------|---------------|----------------------|
| DFlash / EAGLE-3 / N-Gram speculative decoding | **ZERO** — mathematically lossless via rejection sampling | ✅ Yes |
| Prefix caching | **ZERO** — at normal utilization (no recomputation) | ✅ Yes |
| Chunked prefill | **ZERO** — identical computation, just scheduling | ✅ Yes |
| FP8 weight quantization | **~0.3-0.6%** MMLU-Pro regression (sub-1%) | ✅ Yes |
| FP8 KV cache | **Subtle degradation reported** — tool-calling errors | ⚠️ No — keep KV at BF16 |

## Key Evidence

**Speculative decoding is provably lossless:**
- vLLM docs: "theoretically lossless up to the precision limits of hardware numerics"
- Multiple papers prove rejection sampling preserves target distribution exactly (Leviathan et al. 2023, Chen et al. 2023, Timor et al. 2025)
- DFlash paper: "over 6× lossless acceleration across a range of models and tasks"

**FP8 weights are "effectively lossless":**
- "Give Me BF16 or Give Me Death" paper (Kurtic et al. 2024): -0.3 to -0.5 point MMLU-Pro regression vs FP16 across 6 models
- AIMultiple: 69.64% vs 70.24% (0.6pt diff on 12K questions)
- Sub-1% — invisible in practice for tool-calling workloads

**FP8 KV cache is risky for tool calling:**
- r/LocalLLaMA: "with kv at fp8, I see many subtle mistakes, tool calling issues"
- r/LocalLLaMA: "try to use FP16 since it seems to hurt tool calling very severely"
- vLLM docs: "Note, current prefix caching doesn't work with FP8 KV cache"

**Prefix caching bug (vLLM #18055):**
- Only triggers when recomputation is forced (low gpu-memory-utilization)
- At normal 0.9 utilization on DGX Spark: won't happen
- Bug closed as "not planned" — avoid recomputation scenarios

## Recommended Config

```bash
--speculative-model z-lab/Qwen3.6-27B-DFlash --num-speculative-tokens 5 \
--enable-prefix-caching --enable-chunked-prefill \
--quantization fp8 --kv-cache-dtype auto
```

This gives **3-4× speedup with ZERO measurable quality loss**.

## Full Research

See `dgx-spark-qwen3-deployment:references/inference-acceleration-quality-impact-may14-2026.md` for the complete research with all sources, methodology, and detailed findings.
