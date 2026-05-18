# Apr 22 2026: NVFP4 + OPSD Research Findings

Deep research sweep across Reddit r/LocalLLaMA, NVIDIA Developer Forums, vLLM GitHub, and arXiv for remaining optimizations before Qwen3.6-27B training pipeline.

---

## 1. NVFP4 Weight Quantization on DGX Spark

### 1.1 Community Breakthroughs

Multiple groups have unlocked NVFP4 on SM121 (DGX Spark):

| Source | Achievement | Relevance |
|---|---|---|
| **Avarok** (`avarok/vllm-nvfp4-gb10-sm120`) | Qwen3-Next-A3B-80B at **60-110 tok/s** with speculative decoding | Proves NVFP4 works at scale on Spark |
| **RedHatAI** (`Qwen3.5-122B-A10B-NVFP4`) | 115 tok/s on single Spark | Community-validated model |
| **VincentKaufmann** (custom FP4 kernel) | **129 TFLOPS** on Spark via CUTLASS 3.8 | Standalone library, not vLLM-integrated |
| **NVIDIA Forum** (natfiii) | **+12% decode** via Stream-K FP4 GEMM | Custom kernel patch |

### 1.2 What NVFP4 Would Mean for Qwen3.6-27B

- **Weight compression:** 54GB (BF16) → ~13.5GB (NVFP4) = 4x
- **Speed potential:** 15-25 tok/s sustained (vs current 4.5 tok/s eager)
- **Memory headroom:** Massive — 262K context becomes comfortable
- **Tensor core utilization:** FP4 uses Blackwell's native FP4 tensor cores

### 1.3 The REASONING QUALITY PROBLEM

**Danny's #1 priority is reasoning quality. Quantization is suspect.**

NVFP4 is 4-bit weight quantization. While Avarok claims ~99% quality retention, this has NOT been verified on:
- Clinical reasoning tasks
- Multi-step mathematical proofs
- Chain-of-thought generation
- Tool-use accuracy

**Benchmark plan (post-EAGLE-3):**
```bash
# 1. Quantize 27B to NVFP4 using Avarok's method or modelopt
# 2. Serve with vLLM NVFP4 backend
# 3. Run identical reasoning benchmarks on BF16 vs NVFP4:
#    - MATH-500 (multi-step math)
#    - HumanEval (code generation)
#    - MedQA-USMLE (clinical reasoning)
#    - GSM8K (grade school math)
#    - ToolCall-15 (function calling)
# 4. Acceptance threshold: <1% degradation on ANY benchmark
# 5. If threshold exceeded: DISCARD NVFP4, keep BF16
```

**Decision rule:** Reasoning quality > speed. Always. If NVFP4 fails the benchmark, it is permanently rejected regardless of speed gains.

### 1.4 Implementation Path (If Benchmark Passes)

**Option A: Use Avarok's image**
```bash
docker pull avarok/vllm-nvfp4-gb10-sm120
# May lack EAGLE-3/TurboQuant patches
```

**Option B: Backport NVFP4 patches to AEON-7**
- Extract NVFP4 kernels from Avarok's build
- Apply to our AEON-7 + TurboQuant + EAGLE-3 image
- Higher integration effort, maintains our stack

**Option C: PrismQuant (already documented)**
- `rdtand/Qwen3.6-35B-A3B-PrismQuant-4.75bit-vllm`
- 4.75-bit mixed precision, -0.56pp quality loss
- Works TODAY with standard vLLM

### 1.5 Verdict

**HIGH REWARD, HIGH RISK.** NVFP4 is the biggest untapped speedup but threatens the sacred reasoning quality threshold. Do NOT implement before EAGLE-3 training completes. Benchmark first, adopt only if reasoning is preserved.

---

## 2. OPSD: On-Policy Self-Distillation

### 2.1 Why OPSD Over GRPO

| Property | GRPO | OPSD |
|---|---|---|
| Teacher model | Separate (usually larger) | Same model (self-distillation) |
| Generation budget | 16k tokens | 2k tokens (8x more efficient) |
| Feedback density | Sparse (per-response reward) | Dense (per-token divergence) |
| Qwen3 tested | Yes | Yes (paper specifically tests Qwen3) |
| Sample efficiency | Moderate | High |

**Core mechanism:** Single model acts as both teacher and student. Teacher conditions on privileged information (verified reasoning traces). Student sees only the question. Training minimizes KL divergence between teacher and student distributions over the student's own rollouts.

### 2.2 Implementation on DGX Spark

```bash
# Clone and install
git clone https://github.com/siyan-zhao/OPSD.git /data/repos/OPSD
cd /data/repos/OPSD
pip install -e .

# Training (runs after EAGLE-3 completes)
python opsd_train.py \
  --model_name_or_path /data/models/Qwen3.6-27B-Uncensored \
  --dataset_path /data/datasets/reasoning/ \
  --output_dir /data/models/Qwen3.6-27B-OPSD \
  --num_train_epochs 2 \
  --per_device_train_batch_size 1 \
  --learning_rate 5e-5 \
  --max_length 2048 \
  --bf16
```

**Datasets:**
- OpenThoughts-114k (math/code/science)
- Bespoke-Stratos-17k (DeepSeek-R1 distilled)
- medical-o1-reasoning-SFT (clinical reasoning)
- PRM800K (step-level human labels)

**Expected:** +15-25% on MATH-500, GSM8K, HumanEval

### 2.3 When to Run

- AFTER EAGLE-3 draft training completes
- AFTER base SFT on general datasets completes
- GPU sequential: cannot run concurrently with vLLM serving

---

## 3. Zero-Bubble Async Scheduling (vLLM 0.19.0+)

Already present in our vLLM 0.19.1rc1 image. No action needed.

Feature: Overlaps orchestration with execution during speculative decoding. Improves throughput for concurrent requests.

---

## 4. Research Sweep Methodology

**Pattern proven on Apr 22:**

1. **Breadth:** Parallel web_search across:
   - `site:reddit.com/r/LocalLLaMA <model> <optimization>`
   - `site:forums.developer.nvidia.com <hardware> <topic>`
   - `site:github.com/vllm-project/vllm <feature>`
   - `"<method>" <model family> arxiv 2026`

2. **Deep dive:** web_extract on 3-5 most promising results

3. **Cross-reference:** Check GitHub issues/PRs for known bugs

4. **Risk assessment:** For each finding, evaluate:
   - Speed impact
   - Quality risk
   - Implementation effort
   - Compatibility with existing stack

5. **Decision:** Only adopt if quality risk is acceptable AND implementation is feasible

**Key sources for GPU/ML optimizations:**
- Reddit r/LocalLLaMA (community benchmarks, real-world configs)
- NVIDIA Developer Forums (official + community kernel work)
- vLLM GitHub issues/PRs (known bugs, upcoming features)
- HuggingFace discussions (model-specific issues)
- arXiv (latest training methods)

---

## 5. Updated Optimization Saturation Assessment

**DONE (pre-training):**
- EAGLE-3 draft training pipeline
- TurboQuant KV compression image
- fp8_e5m2 fallback
- 0.95 GPU util
- Auto-monitor with vLLM auto-restart
- 6 training datasets
- Abliteration

**QUEUED (post-EAGLE-3):**
| Opportunity | Impact | Risk | Trigger |
|---|---|---|---|
| OPSD reasoning training | +15-25% reasoning | Low | After EAGLE-3 + base SFT |
| NVFP4 benchmark | 3-5x speed potential | **HIGH** (quality) | After EAGLE-3, benchmark first |

**REJECTED:**
- SGLang (dependency hell, slower than vLLM+DFlash)
- FlashKDA (fundamental GDN incompatibility)
- MTP speculative decoding (vLLM bug #38182)
- ngram speculative decoding (silently corrupts output)
