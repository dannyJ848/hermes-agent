# dgx-spark-qwen3.6-maximum-bf16-optimization

*Researched: 2026-04-17 12:48 CDT*

# DGX Spark + Qwen3.6-35B-A3B: Maximum BF16 Optimization Guide

**Updated:** April 17, 2026 | **Status:** Pre-deployment preparation

## REVISED Performance Table (Community-Verified)

| Config | Decode (tok/s) | 262K Context? | Quality | Source |
|---|---|---|---|---|
| BF16, stock vLLM (NO SM121 kernels) | 13 | Yes | 100% | troy.e.davis NVIDIA forum |
| BF16, SM121 native kernels | 31-35 | Yes | 100% | adadrag, hellohal2064 |
| BF16 + SM121 + MTP-3 | 40-49 | Yes | 100% | hellohal2064, albond |
| FP8 (official) + SM121 + MTP-3 | 52-54 | Yes | ~99% | cosinus NVIDIA forum (single Spark, Apr 16) |
| FP8 + MTP-3, dual Spark (TP2) | 64-78 | Yes | ~99% | serapis NVIDIA forum (77.7 t/s, Apr 16) |
| AWQ-4bit + Marlin + DFlash (Atlas) | 102-115 | Yes | ~96% | Reddit verified |
| Hybrid INT4+FP8 + MTP | 100+ | Yes | ~96% | phuongncn speed hack |

## OPTIMIZATION LAYERS (Ordered by Impact)

### Layer 0: SM121 Native Kernels — 3.65x WIN (13 → 49 tok/s) **NON-NEGOTIABLE**

Stock `vllm/vllm-openai:cu130-nightly` does NOT include SM121 cubins. CMake bug.

**Fix:** Change `12.0f` to `12.0a` in CMakeLists.txt line ~651:
```cmake
# BEFORE (BROKEN):
cuda_archs_loose_intersection(FP4_ARCHS "12.0f" "${CUDA_ARCHS}")
# AFTER (FIXED):
cuda_archs_loose_intersection(FP4_ARCHS "12.0a" "${CUDA_ARCHS}")
```
Apply to BOTH `VERSION_GREATER_EQUAL 13.0` and `else()` branches.

**Why it works:** SM121 lacks NVFP4 microscaling instructions (`cvt with .e2m1x2`).
The CMake guard incorrectly includes SM121 in NVFP4 compilation, causing ptxas errors.
Excluding SM121 from NVFP4 while keeping all other Blackwell kernels = 3.65x speedup.

**Multi-stage build:** Compile SM121 kernels in builder stage, inject only `_C.abi3.so`
and `_moe_C.abi3.so` into pristine stock image. Build takes ~90 min on ARM64.

**Verification:** `cuobjdump -lelf _C.abi3.so | grep -c sm_120` should show 50+.

**OR use pre-built community image** (saves 90 min):
- `hellohal2064/vllm-qwen3.5-gb10:latest` (50 tok/s sustained, 1M context)
- `scitrera/dgx-spark-sglang:0.5.9-t5` (60 tok/s with EAGLE-3)

Source: https://forums.developer.nvidia.com/t/dgx-spark-13-49-tok-s-with-qwen3-5-35b-native-sm121-kernel-build-guide/365083

### Layer 1: MTP Speculative Decoding — +25-40%

Always use MTP-3 (`num_speculative_tokens=2`).

| Num Spec Tokens | Avg tok/s | Verdict |
|---|---|---|
| 0 (no MTP) | 31-35 | Baseline |
| 1 (MTP-2) | ~44 | Good |
| 2 (MTP-3) | ~49-54 | **BEST — always use this** |
| 3 (MTP-4) | ~39 | DON'T USE — acceptance collapses |

Source: albond NVIDIA forum benchmarks + community consensus.

**Long context gotcha:** MTP acceptance degrades at 150K+ context. Add DFlash.

### Layer 2: FP8 KV Cache + Prefix Caching (+5-10% each)

```bash
--kv-cache-dtype fp8           # 2x KV compression, no quality loss
--enable-prefix-caching         # Hermes ~2K injection computed ONCE
--enable-chunked-prefill         # Overlap prefill with decode
```

**Why prefix caching matters for Hermes:** Distillation plugin injects ~2K tokens
every turn. Without prefix caching, reprocessed every request.

### Layer 3: DFlash / LSTM Speculative (Context-Agnostic)

MTP degrades at long context. DFlash/LSTM drafters don't.

```bash
huggingface-cli download z-lab/Qwen3.5-35B-A3B-DFlash --local-dir ./dflash-drafter
# Add to launch:
--speculative-model ./dflash-drafter --speculative-draft-device cpu --speculative-algo HOWL
```

**CPU offloading key:** DGX Spark has unified memory. 20 ARM cores draft while GPU verifies.

**Alternative: OWL/LongSpec** custom drafter for 150K+ sustained performance.

Source: https://forums.developer.nvidia.com/t/dflash-llm-for-dgx-spark-too-good-to-be-true/366445

### Layer 4: FlashInfer Attention Backend (+5-10% MoE)

```bash
--attention-backend flashinfer
```

FlashInfer 0.6.7 + CUTLASS 4.4.2 includes SM121-optimized MoE kernels.
MoE kernel configs for Qwen3.x: E=256, N=512, block 128x128.

### Layer 5: HF Kernels Hub (1.7-2.5x MoE Ops)

Launched April 14, 2026. Pre-compiled for exact GPU/PyTorch/OS combo.
Check https://huggingface.co/kernels-community for GB10 availability.

### Layer 6: GPU Clock Boost (+15% possible)

hellohal2064 achieved 50 tok/s at 2400 MHz GPU clock.
```bash
sudo nvidia-smi -pm 1    # Persist performance mode
sudo nvidia-smi -ac 2400,5005   # Check safe values for GB10
```
CAUTION: 240W power budget. Monitor for thermal throttle.

### Layer 7: TurboQuant KV Cache (2.6x Capacity — NOT speed)

**On DGX Spark (bjk110, Apr 4, 2026):**
- KV cache capacity: 155K → 405K tokens (2.6x increase)
- Decode throughput: initially -18% slower, WPH v2 recovers to -26%
- Quality: 12/12 Korean QA pass (no loss)
- **Use case:** When you need MORE CONTEXT CAPACITY, not speed

Source: https://forums.developer.nvidia.com/t/dgx-spark-gb10-vllm-0-19-1-turboquant-kv-cache-integration-results-on-qwen3-5-and-nemotron-including-gather-free-triton-decode-and-cuda-wph-decode/365627

## COMPLETE BF16 LAUNCH COMMAND (Optimized)

```bash
docker run -d --name qwen36-bf16 --gpus all --ipc host --shm-size 64gb \
  -p 8000:8000 \
  -e VLLM_MARLIN_USE_ATOMIC_ADD=1 \
  -e VLLM_FLASHINFER_MOE_BACKEND=latency \
  -e VLLM_TEST_FORCE_FP8_MARLIN=1 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm-custom:sm121-inject \
  vllm serve Qwen/Qwen3.6-35B-A3B \
    --served-model-name qwen3.6-bf16 \
    --port 8000 --host 0.0.0.0 \
    --max-model-len 262144 \
    --max-num-batched-tokens 16384 \
    --gpu-memory-utilization 0.80 \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder \
    --reasoning-parser qwen3 \
    --kv-cache-dtype fp8 \
    --load-format fastsafetensors \
    --attention-backend flashinfer \
    --enable-prefix-caching \
    --enable-chunked-prefill \
    --speculative-config '{"method":"qwen3_next_mtp","num_speculative_tokens":2}'
```

**Expected:** ~40-50 tok/s short context, ~25-35 at 100K+. Full 262K. 100% quality.

## FP8 LAUNCH COMMAND (Coding Speed Mode)

Same but use `Qwen/Qwen3.6-35B-A3B-FP8`, port 8001, `--gpu-memory-utilization 0.70`.
Expected: ~52-54 tok/s. ~1% quality loss.

## DUAL SPARK Qwen3.6 FP8 BENCHMARKS (serapis, Apr 16 2026)

| Context | Prefill (tok/s) | Decode (tok/s) | TTFT (ms) |
|---|---|---|---|
| 2K | 7,824 | 77.7 | 264 |
| 4K | 8,496 | 76.4 | 725 |
| 8K | 8,403 | 75.8 | 1,220 |
| 16K | 8,217 | 74.8 | 2,245 |
| 32K | 7,434 | 73.4 | 4,685 |
| 65K | 6,310 | 69.9 | 10,712 |
| 131K | 4,673 | 64.3 | 28,491 |

100/100 ToolCall-15 at all context lengths.

## SINGLE SPARK Qwen3.6 FP8 BENCHMARKS (cosinus, Apr 16 2026)

| Context | Decode (tok/s) |
|---|---|
| Short (2K) | 52.7 |
| 4K+2K | 52.3 |
| 8K+2K | 52.3 |
| 16K+2K | 52.2 |

vLLM version: 0.19.1rc1.dev337+g17d87168d.d20260416

## CRITICAL GOTCHAS

1. **SM121 native kernels = non-negotiable.** 13 tok/s without, 49 tok/s with.
2. **SM121 is Ampere ISA for tensor cores** (uses mma.sync like SM80).
3. **NVFP4 is BROKEN on SM121.** ptxas errors. Use FP8 or BF16 ONLY.
4. **MTP-3 is sweet spot** (num_speculative_tokens=2). MTP-4 collapses.
5. **Long context cliff at 100K+.** Add DFlash for 150K+ work.
6. **TurboQuant expands capacity, not speed.** Good for long context.
7. **First request warmup ~57s** (torch.compile caching). Subsequent fast.
8. **OOM after extended use:** Reduce gpu-memory-utilization to 0.80.
9. **Dual Spark RDMA:** NCCL silently falls back to TCP if /dev/infiniband/*
   not accessible. Verify NCCL_DEBUG=INFO shows "IB" not "Socket".
10. **DFlash is Qwen3.5-specific.** Same architecture, "should work" with 3.6.
    Verify before relying on it. Check z-lab HuggingFace for updates.
11. **Qwen3.6 = same architecture as Qwen3.5.** All playbooks are drop-in.

## BEST QUALITY UPGRADE (Single Spark, No 2nd Spark)

**Qwen3.5-122B-A10B INT4** — fits in ~65GB, 10B active (3.3x smarter than 35B-A3B).
Up to 51 tok/s with hybrid INT4+FP8+MTP-1.
Repo: https://github.com/albond/DGX_Spark_Qwen3.5-122B-A10B-AR-INT4

## KEY REFERENCES

- SM121 Build Guide: https://forums.developer.nvidia.com/t/dgx-spark-13-49-tok-s-with-qwen3-5-35b-native-sm121-kernel-build-guide/365083
- Qwen3.6 Benchmarks: https://forums.developer.nvidia.com/t/qwen-qwen3-6-35b-a3b-and-fp8-has-landed/366822
- 122B Hybrid MTP: https://forums.developer.nvidia.com/t/qwen3-5-122b-a10b-on-single-spark-up-to-51-tok-s-v2-1-patches-quick-start-benchmark/365639
- TurboQuant on GB10: https://forums.developer.nvidia.com/t/dgx-spark-gb10-vllm-0-19-1-turboquant-kv-cache-integration-results-on-qwen3-5-and-nemotron-including-gather-free-triton-decode-and-cuda-wph-decode/365627
- DFlash for Spark: https://forums.developer.nvidia.com/t/dflash-llm-for-dgx-spark-too-good-to-be-true/366445
- Long Context Solutions: https://forums.developer.nvidia.com/t/does-qwen3-5-35b-a3b-on-gb10-leave-a-lot-of-performance-on-the-table/362200
- NVIDIA Blog (35% llama.cpp uplift): https://developer.nvidia.com/blog/new-software-and-model-optimizations-supercharge-nvidia-dgx-spark/
- adadrag Guide: https://github.com/adadrag/qwen3.5-dgx-spark
- hellohal2064 Docker: https://github.com/seli-equinix/vllm
- albond 122B: https://github.com/albond/DGX_Spark_Qwen3.5-122B-A10B-AR-INT4


## Sources

- https://forums.developer.nvidia.com/t/dgx-spark-13-49-tok-s-with-qwen3-5-35b-native-sm121-kernel-build-guide/365083
- https://forums.developer.nvidia.com/t/qwen-qwen3-6-35b-a3b-and-fp8-has-landed/366822
- https://forums.developer.nvidia.com/t/qwen3-5-122b-a10b-on-single-spark-up-to-51-tok-s-v2-1-patches-quick-start-benchmark/365639
- https://forums.developer.nvidia.com/t/dgx-spark-gb10-vllm-0-19-1-turboquant-kv-cache-integration-results-on-qwen3-5-and-nemotron-including-gather-free-triton-decode-and-cuda-wph-decode/365627
- https://forums.developer.nvidia.com/t/dflash-llm-for-dgx-spark-too-good-to-be-true/366445
- https://forums.developer.nvidia.com/t/does-qwen3-5-35b-a3b-on-gb10-leave-a-lot-of-performance-on-the-table/362200
- https://forums.developer.nvidia.com/t/custom-built-vllm-qwen3-5-35b-on-nvidia-dgx-spark-gb10-sustained-50-tok-s-1m-context/362590
- https://developer.nvidia.com/blog/new-software-and-model-optimizations-supercharge-nvidia-dgx-spark/
- https://github.com/adadrag/qwen3.5-dgx-spark
- https://github.com/vllm-project/vllm/issues/35519
