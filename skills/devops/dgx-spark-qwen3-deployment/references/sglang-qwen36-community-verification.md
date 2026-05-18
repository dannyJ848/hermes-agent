# SGLang + Qwen3.6-27B Dense: Community Verification (May 15, 2026)

**Date:** May 15, 2026
**SGLang version tested:** v0.5.11 (Docker image `lmsysorg/sglang:latest`, 30.4GB)
**Model:** Qwen3.6-27B-Uncensored (dense variant, NOT hybrid Mamba/SSD)
**Status:** BLOCKED — weight loading hangs indefinitely, community confirms non-functional

## Our Server's Symptoms

- SGLang container launches, model directory found
- Hangs at "Load weight begin" with memory frozen at ~52GB
- No error messages, no crash, no progress after 5+ minutes
- `sglang::scheduler` process holds ~100GB GPU memory
- `docker rm -f` does NOT release GPU memory — requires `kill -9`
- vLLM then fails to start with "Free memory on device cuda:0 (12.37/121.69 GiB) is less than desired GPU memory utilization"

## Community Evidence

### GitHub Issue #23687 — "Qwen3.6-27B-FP8 (dense): FP8 weight_scale_inv silently dropped → garbage output"

- **Opened:** April 25, 2026 by gucasbrg
- **Status:** Still OPEN (no fix merged as of May 15, 2026)
- **Symptom 1:** 256 loader warnings during weight load: `Parameter model.layers.14.mlp.gate_gate_up_proj.weight_scale_inv not found in params_dict`
- **Symptom 2:** "gate_gate_up_proj (double gate_) — strong hint at a string-mutation bug in the loader"
- **Symptom 3:** Server starts and says "ready" but produces **pure garbage output** — reasoning tokens without content, Chinese text mixed with non-characters
- **Root cause:** SGLang's `qwen3_5.py` has a `gate_gate_up_proj` loop bug that drops FP8 weight scales for the dense variant
- **Same SGLang version + hardware loads Qwen3.5-27B-FP8 cleanly** — proving the issue is specific to Qwen3.6's checkpoint format

### GitHub Issue #24589 — "Crash during weight loading for Qwen3.6-27B-AWQ-INT4"

- **Opened:** ~1 week ago
- **Status:** Still open
- **Details:** Even with a partial fix (SGLang 0.5.10.post2), the server loads weights but remains **unresponsive** (doesn't serve requests)
- **Environment:** RTX 3090s, Docker, SGLang latest

### GitHub Issue #24364 — "Qwen3.6 hybrid Mamba: OOM on Blackwell"

- **Opened:** ~10 days ago
- **Status:** Still open
- **Details:** Memory pool allocation failure (18 GiB for Mamba pool) on RTX PRO 6000 Blackwell
- **Disabling overlap schedule** since mamba no detected

### HuggingFace Discussion #5 — "Deploying with sglang, weight name not matching"

- **Opened:** 2 days ago by Kyoma001
- **Details:** SGLang 0.5.10, weight loading hangs at 3/66 shards
- **Error:** `weight_scale_inv not found in params_dict`
- **No resolution** yet

### SGLang Tracking Issue #20069 — "Qwen3.5 bugs"

- Updated regularly with Qwen3.5/3.6 compatibility issues
- Mentions: `Qwen3.5-397B-A17B-NVFP4 illegal memory access`, `Qwen3.5-27B AWQ/INT8: Marlin repack alignment error`, `Qwen3.5 NVFP4 produces gibberish output`
- **No mention of dense Qwen3.6-27B being fixed or supported**

### Reddit Findings

- **r/LocalLLaMA:** Users report Qwen3.6-27B working **only with vLLM**, not SGLang. One user mentioned DFlash draft model works with Qwen3.5 but not 3.6. Multiple threads discussing vLLM vs SGLang — no one has reported SGLang with Qwen3.6-27B dense.
- **r/LocalLLM:** One user reported that Qwen3.6-27B "holds up against Claude Code" — running on vLLM.
- **NVIDIA Developer Forums:** Users reporting Qwen3.6 on DGX Spark with vLLM, Atlas, and Sparkrun — no mention of SGLang success for Qwen3.6-27B.

### What's Available That Works (from forums)

- **vLLM** — confirmed working with Qwen3.6-27B-FP8 and BF16
- **Atlas** — open-source Rust/CUDA engine, claims 100+ tok/s on Qwen3.6-35B-FP8
- **Hugging Face Transformers** — slow but functional
- **llama.cpp** — GGUF quantized versions available

## Root Cause Alignment with Our Server

The weight-loading hang we observed (`params_dict` warnings, stuck at shard 3/66) matches the **exact** symptoms in Issues #23687, #24589, and HF Discussion #5. The SGLang `qwen3_5.py` has a string-mutation bug in the weight-loader loop that drops parameters for the dense variant and incorrectly constructs the `gate_gate_up_proj` name.

## Weight Format Mismatch Details

| Component | Checkpoint Format (Qwen3.6-27B) | SGLang Expects (qwen3_5.py) |
|-----------|--------------------------------|----------------------------|
| Linear attention QKV | `in_proj_qkv` + `in_proj_z` (separate) | `in_proj_qkvz` (merged) |
| Linear attention BA | `in_proj_b` + `in_proj_a` (separate) | `in_proj_ba` (merged) |
| Attention QKV | `q_proj`, `k_proj`, `v_proj` (separate) | `qkv_proj` (merged) |
| MLP gate+up | `gate_proj`, `up_proj` (separate) | `gate_up_proj` (merged) |

**Checkpoint:** 1199 weight tensors
**SGLang model:** 754 parameters
**Difference:** 445 tensors = exactly the split-vs-merged weight formats

The `gate_gate_up_proj` bug is a **string-mutation error** in SGLang's weight loader loop that doubles the "gate_" prefix when processing the dense variant's MLP weights.

## Verdict

**No evidence anywhere that anyone has successfully served Qwen3.6-27B (dense) with SGLang.** The issues are:

1. **Weight format mismatch** — Qwen3.6-27B checkpoint uses different weight naming than SGLang expects
2. **Dense variant bugs** — SGLang's `qwen3_5.py` was written for the MoE variant; dense path has string-mutation bugs causing weight scale drops → garbage output
3. **Memory management** — Mamba pool allocation failures on some GPUs
4. **Core hangs** — Even when weights load, the server remains unresponsive

## Recommendation

**Stay on vLLM.** Attempting a weight-conversion bridge would be futile because the core SGLang code for Qwen3.6 dense is broken at the `qwen3_5.py` level, not just a weight-format incompatibility. The only viable path is to wait for an upstream SGLang fix or explore other engines (Atlas, llama.cpp GGUF, HF Transformers).

## References

- GitHub Issue #23687: https://github.com/sgl-project/sglang/issues/23687
- GitHub Issue #24589: https://github.com/sgl-project/sglang/issues/24589
- GitHub Issue #24364: https://github.com/sgl-project/sglang/issues/24364
- HuggingFace Discussion #5: https://huggingface.co/Qwen/Qwen3.6-27B/discussions/5
- SGLang Tracking Issue #20069: https://github.com/sgl-project/sglang/issues/20069
- Reddit r/LocalLLaMA: Multiple threads on vLLM vs SGLang for Qwen3.6
- NVIDIA Developer Forums: Qwen3.6 on DGX Spark with vLLM/Atlas/Sparkrun
