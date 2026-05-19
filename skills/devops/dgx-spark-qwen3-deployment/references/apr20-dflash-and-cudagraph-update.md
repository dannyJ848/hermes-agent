# Apr 20 2026 Update: DFlash Docker Image + max-cudagraph-capture-size + Pre-Launch Research Sweep

## What Changed (Apr 20 Research Sweep)

A systematic pre-launch research sweep across NVIDIA forums, Reddit r/LocalLLaMA,
vLLM GitHub issues, and HuggingFace revealed several critical updates for
Qwen3.6-35B-A3B on DGX Spark. All findings were applied to the 6 launch scripts.

---

## 1. Docker Image: AEON-7/vllm-dflash (NEW PRIMARY)

**PREVIOUS PRIMARY:** `ghcr.io/bjk110/vllm-spark:v020-tq`
**NEW PRIMARY:** `ghcr.io/aeon-7/vllm-dflash:latest`

The AEON-7 image is a community pre-build specifically for DGX Spark (GB10 Blackwell,
SM121) with DFlash block-diffusion speculative decoding compiled in. It also includes:
- FlashInfer compiled for SM121
- CUTLASS FP4 GEMM with autotuning
- GDN Triton allocator fixes for hybrid attention (Linear + Full attention layers)
- NVFP4 NaN guard for hardware-native execution

**Migration:** All scripts now pull and tag the AEON-7 image:
```bash
docker pull ghcr.io/aeon-7/vllm-dflash:latest
docker tag ghcr.io/aeon-7/vllm-dflash:latest vllm-spark:tq
docker tag ghcr.io/aeon-7/vllm-dflash:latest vllm-spark:base
```

The old bjk110 image is fully replaced. The embedded Dockerfile in spark-day1.sh
also now builds FROM the AEON-7 image instead of `vllm/vllm-openai:cu130-nightly`.

**Note:** GB10 MoE kernel configs (E=256, E=512) were baked into the old bjk110
Dockerfile. The AEON-7 image may or may not have these tuned configs pre-installed.
Monitor startup logs for: "Using default MoE config. Performance might be sub-optimal!"
If seen, copy the moe_config JSONs from `spark_vllm_docker/patches/` into the
container at `/usr/local/lib/python3.12/dist-packages/vllm/model_executor/layers/fused_moe/configs/`.

---

## 2. --max-cudagraph-capture-size 256 (NEW REQUIRED FLAG)

**Why:** Qwen3.6 is a GDN hybrid model (30 GDN/linear attention layers + 10 dense
attention layers). On vLLM, the CUDA graph capture size can exceed the Mamba cache
size, causing a fatal assertion failure:
```
assert num_cache_lines >= batch
```

**Fix:** Add `--max-cudagraph-capture-size 256` to EVERY vLLM serve command.
The default is 512, which is too large for GDN hybrid models on Blackwell.

**Applied to:** spark-day1.sh, spark-maxperf.sh, superqwen3-super.sh,
deploy-spark-day1.sh, spark-grpo-train.sh, dual-training-orchestrator.sh.

---

## 3. DFlash Speculative Decoding (CONFIRMED WORKING, NOW DEFAULT)

**Previous status:** DFlash was "integrated but untested on GDN hybrid" (gotcha #72).
**Current status:** Confirmed working. The z-lab draft model exists specifically
for Qwen3.6: `z-lab/Qwen3.6-35B-A3B-DFlash` (0.5B params, ~1GB download).

**vLLM command:**
```bash
--speculative-config '{"method":"dflash","model":"/data/models/Qwen3.6-35B-A3B-DFlash","num_speculative_tokens":15}'
```

**Performance:** On B200, DFlash achieves 2.9x speedup (682 tok/s on Math500).
On DGX Spark, expect significant boost over the ~50 tok/s baseline. Mean acceptance
length: 5.5-7.4 tokens per draft. The AEON-7 image has DFlash compiled in — using
a stock vLLM image may error with "method dflash not supported."

**Safe speculative decoding chain for Qwen3.6:**
1. DFlash (primary, model-based) — SAFE
2. No speculative decoding (baseline) — SAFE
3. ngram/suffix — BROKEN on GDN hybrid (vLLM #39273, PR #39463 NOT merged)
4. MTP — DEGRADES prefix cache by 62% (vLLM #38182, still open)

**Note:** The AEON-7 repo mentions `KV_CACHE_DTYPE=auto` for DFlash due to non-causal
attention in the draft model. Our scripts currently use `--kv-cache-dtype fp8_e5m2`.
If DFlash crashes with KV cache errors, try switching to `auto` or omitting the flag.

---

## 4. MTP Speculative Decoding (STILL BROKEN — DO NOT USE)

**Status:** vLLM issues #38182/#39680 remain OPEN as of Apr 20, 2026.
MTP causes the KV cache manager to force-drop the last matched block, collapsing
prefix cache hit rate from 92% to 71% on Qwen3.5/3.6. This results in a net
62.5% throughput degradation despite high token acceptance rates.

**All MTP references in scripts remain commented out.** Do not re-enable until
vLLM merges the fix.

---

## 5. Ngram Speculative Decoding (STILL BROKEN — NEVER USE)

**Status:** vLLM issue #39273, PR #39463 NOT merged.
Ngram speculative decoding on GDN hybrid models produces silently corrupted output
(repeated fragments, degenerate text, unicode gibberish after ~2k tokens).
There is no crash or error — the model just outputs garbage.

**All ngram references were REMOVED from scripts in the Apr 19 audit.**
Do NOT add ngram as a fallback. The safe fallback is "no speculative decoding."

---

## 6. Performance Baselines (Community-Verified, Apr 20 2026)

| Config | DGX Spark tok/s | Source |
|---|---|---|
| BF16 baseline (no spec decode) | ~50 tok/s | ZengboJamesWang GitHub + NVIDIA forum |
| FP8 baseline (no spec decode) | ~50-55 tok/s | NVIDIA forum (cosinus) |
| DFlash + BF16/FP8 | TBD (2-3x theoretical) | z-lab benchmarks on B200 |
| vLLM FP8 vs Ollama Q4_K_M | +45% decode (208 vs 144) | Allen Kuo, RTX PRO 6000 Blackwell |

**Memory:** ~43 GiB GPU memory at 38% utilization with FP8. 262K context window
fully supported. GPU utilization can be pushed to 0.95 for more KV cache headroom.

---

## 7. MoE Kernel Tuning Verification

vLLM emits "Using default MoE config. Performance might be sub-optimal!" when
hardware-specific tuned configs are missing. On Blackwell/GB10, this can cost
~50% performance.

**Check:** After starting vLLM, grep logs for the warning.
**Fix:** If missing, run vLLM's `benchmarks/kernels/benchmark_moe.py` on the Spark
to generate tuned configs, then set `VLLM_TUNED_CONFIG_FOLDER=/path/to/configs`.

The old bjk110 Dockerfile baked in GB10 configs. The AEON-7 image may already
have them — verify at launch.

---

## 8. Mamba Cache Error Prevention

**Error:** `assert num_cache_lines >= batch` (Mamba cache overflow)
**Trigger:** CUDA graph capture size > Mamba cache size on GDN hybrid models
**Prevention:** `--max-cudagraph-capture-size 256` (already patched into all scripts)
**Fallback:** If error still occurs, reduce further to 128.

---

## 9. Pre-Launch Research Sweep Methodology

This update was produced by a systematic multi-source sweep:

1. **NVIDIA Developer Forums** — DGX Spark / GB10 section. Real user benchmarks,
   bug reports, image recommendations.
2. **Reddit r/LocalLLaMA** — Community benchmarks, hardware-specific configs,
   performance comparisons (vLLM vs Ollama).
3. **vLLM GitHub** — Issues #39273, #38182, #40124, PR #39463 status. Release notes.
4. **HuggingFace** — z-lab DFlash model cards, Qwen3.6 model page, gated repo status.
5. **Medium / Blogs** — Allen Kuo's Blackwell benchmarks, technical deep-dives.

**Rule:** Always check live sources within 48h of launch. Training cutoff knowledge
is stale for fast-moving model + inference stack combinations.
