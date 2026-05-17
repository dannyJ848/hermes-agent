# Gotchas 79-83: Pre-Launch Research Findings (Apr 19 2026)

## #79: DenseMixer — Plug-and-Play MoE Router Training Improvement (+2-4%)

**WHAT:** DenseMixer (NeurIPS 2025, github.com/yaof20/DenseMixer, MIT license)
provides more precise router gradients during MoE post-training by using a
Straight-Through Estimator (STE) for the non-differentiable Top-K routing.

**WHY IT MATTERS:** MoE training traditionally has zero gradient for the Top-K
routing operation. The router can't learn which experts to pick because the
selection is discrete and non-differentiable. DenseMixer trades one extra
forward pass on ALL experts (not just Top-K) for better gradient estimation.

**RESULTS ON QWEN3 MOE:**
| Model | Conventional | DenseMixer | Gain |
|---|---|---|---|
| Qwen3-30B-A3B (Math, S1 1K) | 62.54 avg | 64.06 avg | +1.52 |
| Qwen3-30B-A3B (Code, Nemotron 35K) | 67.21 avg | 68.80 avg | +1.59 |
| Qwen3-30B-A3B GPQA Diamond | 54.80 | 58.52 | +3.72 |
| Qwen1.5-MoE-A2.7B LoRA | 39.15 avg | 42.01 avg | +2.86 |
| OLMoE-1B-7B | 35.44 avg | 38.35 avg | +2.91 |

**CRITICAL FOR US:** Router quality is our #1 bottleneck. Qwen3.6-35B-A3B
has 256 experts but only activates 8+1 per token. Better routing = better
expert selection = more of the 35B knowledge actually used.

**USAGE (zero code changes):**
```bash
pip install densemixer
densemixer setup
export DENSEMIXER_ENABLED=1
# Then run SFT/GRPO as normal — DenseMixer hooks into the training loop
```

**COST:** One extra forward pass on ALL experts during training only.
For 256 experts at 3B active (each ~137M params), this means computing
all 256 experts' outputs instead of 9. ~28x more compute per forward pass.
On 119GB GH200 this is ~3-5 min extra per epoch. Acceptable for post-training.

**INFERENCE:** ZERO overhead. DenseMixer only affects training backward pass.

**INTEGRATION:**
Add to spark-lora-train.sh and spark-grpo-train.sh:
```bash
# In Docker environment:
pip install densemixer && densemixer setup
export DENSEMIXER_ENABLED=1
```

**CAVEAT:** DenseMixer paper tested on Qwen3-30B (128 experts), not Qwen3.6-35B
(256 experts). Scaling to 256 experts means the dense forward pass computes
~256 x 137M = 35B params — essentially making it a dense forward pass. This
is EXPENSIVE but correct — the whole point is better gradients for the router.
Monitor training time and disable if epoch time becomes unacceptable.

## #80: min_p=0.2 Fixes Infinite Thinking Loops

**BUG:** Qwen3.6-35B-A3B has a known infinite reasoning loop problem where
the model gets stuck repeating the same thinking tokens indefinitely. This
affects both Qwen3.5-35B-A3B and Qwen3.6-35B-A3B, in both FP8 and AWQ formats.

**FIX (community-verified on HuggingFace discussions #39):**
```
--override-generation-config '{"temperature": 1.0, "top_p": 1.0, "top_k": 40, "min_p": 0.2}'
```

**KEY PARAMETER:** min_p=0.2 has the greatest impact. It sets a minimum
probability threshold — any token with probability below 20% of the top
token's probability is excluded. This prevents the model from looping on
low-probability continuation tokens that form repetitive patterns.

**INTEGRATION:**
Add to spark-maxperf.sh vLLM serve commands on both BF16 (port 8000) and
FP8 (port 8001) containers:
```
--override-generation-config '{"min_p": 0.2, "top_k": 40}'
```

**NOTE:** This is a SERVING config, not a training config. The thinking
loop bug is already present in the model weights — training with better
reasoning data (Super pipeline Restore SFT) should reduce it, but min_p=0.2
is the immediate runtime fix.

## #81: vLLM LoRA Module Name Bug (#38520) — Our Merge Strategy Is Correct

**BUG:** vLLM cannot load LoRA adapters for Qwen3/3.5/3.6 MoE models due to
expert module name parsing bug. The parser extracts `experts.0.down_proj`
instead of just `down_proj`, causing all expert LoRA modules to be rejected.

**AFFECTS:** vLLM v0.18.1+ with LoRA enabled for Qwen MoE models.
Fix PRs exist (#38522, #39994) but NOT yet merged.

**WHY WE'RE IMMUNE:** Our Super pipeline does NOT load LoRA into vLLM.
We use save_pretrained_merged(merged_16bit) to merge LoRA into a new
base model, then serve the merged model directly. This completely bypasses
the vLLM LoRA loading path — the buggy code is never reached.

**CONFIRMATION:** NVIDIA forum post (haidij, Apr 10 2026) reports LoRA
trained on attention layers only has "really high loss" — ineffective for
MoE. Attention-only LoRA can't update the MoE experts or router, so the
training barely affects model output. Our approach of merging into base
avoids this entirely.

**ACTION:** No code change needed. Continue using save_pretrained_merged.
If we ever need dynamic LoRA loading in vLLM, wait for #38522/#39994 to merge.

## #82: DFlash Early Results — Accept Length Only 5-7.2 (Lower Than Expected)

**STATUS:** DFlash Qwen3.6-35B-A3B-DFlash model is still under training
(at 2000 steps as of Apr 19 2026). It's a 0.5B BF16 drafter model in a
gated HF repo (z-lab/Qwen3.6-35B-A3B-DFlash).

**EARLY SGLANG RESULTS (with thinking enabled, max_tokens=4096):**

| Dataset | Accept Length |
|---|---|
| GSM8K | 6.5 |
| Math500 | 7.2 |
| HumanEval | 6.2 |
| MBPP | 5.6 |
| MT-Bench | 5.0 |

Avg acceptance length ~6 tokens per speculation attempt (out of 15 drafted).
This is much lower than the 6x speedup claims (those were on other models).

**REALISTIC SPEEDUP ESTIMATE:** With acceptance ~6 and 15 speculative tokens:
- Best case: ~2-3x speedup on simple prompts
- Typical case: ~1.5-2x on reasoning/coding tasks
- Worst case: near-zero if GDN state rollback breaks

**GDN + SPECULATIVE DECODING RISK:**
vLLM #39273 confirms ngram/suffix speculative decoding is BROKEN on GDN
hybrid models because SSM state can't roll back for rejected tokens.
DFlash is model-based (not ngram), but GDN+spec_dec compatibility is UNTESTED.
If it breaks, validation tests (superqwen3-validate.py) catch it, and we
fall back to no speculative decoding (just remove --speculative-config).

**vLLM INSTALL NOTE:** DFlash in vLLM requires nightly build:
```bash
uv pip install vllm
uv pip install -U vllm --torch-backend=auto --extra-index-url https://wheels.vllm.ai/nightly
```
Our v020-tq Docker image may not have DFlash support. Test on launch day.
If DFlash config causes vLLM startup error, it's a Docker version issue —
just remove the --speculative-config flag.

## #83: FP8 Wins Decode on Blackwell — 208 tok/s Benchmark

**BENCHMARK (Allen Kuo, Apr 2026):** vLLM FP8 on RTX PRO 6000 Blackwell:
208 tok/s decode. This is the fastest decode ever measured on vLLM.
Ollama Q4_K_M on same hardware: 144 tok/s (vLLM wins by 45%).

**WHY FP8 WINS ON BLACKWELL (3 factors):**
1. FP8 is native to Blackwell tensor cores — no dequantization overhead.
   vLLM's FP8 weights go straight to FP8 tensor cores.
   Ollama's Q4_K_M requires per-block dequant to FP16 before GEMM.
2. GDN layers eliminate vLLM's PagedAttention overhead. Only 10/40 layers
   use attention (25% vs 100% in pure transformers like Gemma 4).
3. vLLM's FP8 MoE kernels (fused_moe) are heavily optimized for Blackwell.

**IMPLICATIONS FOR SPARK:**
- FP8 port (8001) should be primary for agent inference — fastest tok/s
- BF16 port (8000) for training output validation and quality checks
- Our spark-speed profile (FP8 :8001) is correctly positioned as the
  fast agent inference endpoint
- At 208 tok/s, agent loops (tool call -> response -> tool call) complete
  ~3x faster than BF16 (~58-66 tok/s)

**NOTE:** The 208 tok/s benchmark was on RTX PRO 6000 (96GB VRAM, SM 12.0).
DGX Spark (128GB UMA, SM121) may differ due to UMA memory architecture and
bandwidth differences. Expect 150-200 tok/s on Spark FP8 based on community
reports. Either way, FP8 >> BF16 for decode speed on Blackwell.

**ALSO:** At 60% GPU memory utilization with Qwen3.6 FP8, max_num_seqs
must be <=512 (Mamba cache blocks overflow at default 1024). Already in
our config (gotcha #69).
