# Hybrid Attention Model Prefix Caching Limitations

**Date:** May 15, 2026
**Model:** Qwen3.6-27B-Uncensored (Qwen3_5ForConditionalGeneration)
**vLLM:** 0.20.2+
**Hardware:** DGX Spark (GB10, Blackwell SM121)

## The Problem

When vLLM serves Qwen3.6-27B with `--enable-prefix-caching`, logs show:

```
Prefix cache hit rate: 0.0%
```

Despite the flag being passed and the Mamba cache "align" mode activating with warnings:

```
WARNING: Mamba cache mode is set to 'align' for Qwen3_5ForConditionalGeneration by default when prefix caching is enabled
WARNING: Prefix caching in Mamba cache 'align' mode is currently enabled. Its support for Mamba layers is experimental.
```

## Root Cause: Hybrid Architecture Disables Prefix Caching Internally

Qwen3.6-27B uses a **hybrid attention architecture**:
- 48 layers: `linear_attention` (Mamba/GDN)
- 16 layers: `full_attention` (standard transformer)
- Full attention interval: every 4th layer (indices 3, 7, 11, 15, 19, 23, 27, 31, 35, 39, 43, 47, 51, 55, 59, 63)

vLLM's model config reports:

```python
is_hybrid: True
supports_mamba_prefix_caching: False
is_prefix_caching_supported: False
```

These flags are **read-only** — they are computed from the model architecture, not user-configurable. When `is_prefix_caching_supported` is `False`, vLLM silently disables prefix caching regardless of the CLI flag.

## Why Hybrid Models Can't Use Prefix Caching

1. **Two different KV cache managers** run simultaneously:
   - `FullAttentionManager` — scans block hashes left-to-right
   - `MambaManager` — scans block hashes right-to-left, returns only the last matching block

2. **Block size alignment problem:**
   - Attention block size: 16 tokens
   - Mamba page size: architecture-dependent
   - Cache hits require alignment to **both** block sizes (LCM)

3. **Mamba "align" mode is explicitly experimental:**
   - vLLM warns: "Its support for Mamba layers is experimental. Please report any issues you may observe."
   - The align mode was added as a compatibility shim, not a working feature

4. **N-gram speculative decoding may interfere:**
   - The `skip_reading_prefix_cache` flag can be set by the n-gram drafter
   - Even if prefix caching were enabled, speculative decoding might bypass it

## Verification Commands

Check if YOUR model supports prefix caching:

```bash
# Inside vLLM container
docker exec vllm-merged python3 -c '
from vllm.engine.arg_utils import EngineArgs
args = EngineArgs(
    model="/data/models/Qwen3.6-27B-Uncensored",
    max_model_len=131072,
    enable_prefix_caching=True,
    gpu_memory_utilization=0.9
)
ec = args.create_engine_config()
print("is_hybrid:", ec.model_config.is_hybrid)
print("supports_mamba_prefix_caching:", ec.model_config.supports_mamba_prefix_caching)
print("is_prefix_caching_supported:", ec.model_config.is_prefix_caching_supported)
'
```

If `is_prefix_caching_supported` is `False`, prefix caching will NOT work regardless of the `--enable-prefix-caching` flag.

## What Actually Works (Speedups That Are Active)

| Speedup | Status | Evidence |
|---------|--------|----------|
| **FP8 weight quantization** | Active | `quantization=fp8`, CutlassFP8ScaledMM selected |
| **N-gram speculative decoding** | Active | 0-85% draft acceptance, mean ~5 tokens |
| **Chunked prefill** | Active | `enable_chunked_prefill=True`, max 8192 tokens |
| **CUDA graphs** | Active | 96 capture sizes, 2.14 GiB pool |
| **FlashAttention v2** | Active | Backend FLASH_ATTN confirmed |
| **Prefix caching** | **DISABLED** | `is_prefix_caching_supported: False` |

## Performance Reality

With the working speedups (FP8 + n-gram + chunked prefill + CUDA graphs):

| Concurrent | Throughput | Latency |
|-----------:|-----------:|--------:|
| 1 | 6.6 tok/s | 7.5s |
| 4 | 26.6 tok/s | 4.5s |
| 8 | 49.0 tok/s | 4.9s |
| 16 | 80.9 tok/s | 5.9s |
| 32 | 143.2 tok/s | 6.7s |
| 64 | 200.1 tok/s | 9.6s |
| 128 | 203.6 tok/s | 18.9s |

Sweet spot: 64-128 concurrent requests for max throughput (~200 tok/s).

## Path Forward

**Option A — Accept 0% prefix caching:** The other speedups (FP8, n-gram, chunked prefill, CUDA graphs) still provide significant gains. For agent workloads with short context turns, prefix caching would have minimal impact anyway.

**Option B — Disable speculative decoding for cleaner execution:** Remove `--speculative-config '{"method":"ngram","num_speculative_tokens":5}'`. This removes a potential interference source and simplifies the execution path. Trade-off: lose 0-20% speedup from draft acceptance.

**Option C — Wait for vLLM upstream:** Hybrid model prefix caching is a known limitation. The vLLM team is actively working on it. Check vLLM GitHub issues #38182, #39680 for progress.

**Option D — Use DFlash speculative decoding instead of n-gram:** DFlash uses a LoRA-based draft head compatible with the target model architecture. Requires HF access to `z-lab/Qwen3.6-27B-DFlash` (gated repo). See `dgx-spark-qwen3-deployment` skill Section 3.2 for DFlash setup.

**Option E — Switch to dense attention model:** If prefix caching is critical for your use case, consider a model without hybrid attention (e.g., Llama 3.1, Mistral). These models report `is_prefix_caching_supported: True`.

## Key Takeaway

**Don't chase prefix caching on Qwen3.6 hybrid models.** The architecture fundamentally disables it. Focus optimization effort on:
1. FP8 weight quantization (working, ~1.5x speedup)
2. N-gram speculative decoding (working, variable 0-20% speedup)
3. Chunked prefill + CUDA graphs (working, better batching)
4. Concurrent request tuning (sweet spot 64-128)

The time spent debugging "why prefix caching shows 0%" is better spent tuning batch size and concurrency.
