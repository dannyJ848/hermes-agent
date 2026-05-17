---
name: reasoning-distillation-lora
version: 1.0.0
description: Improve LLM reasoning via LoRA fine-tuning on distilled chain-of-thought traces. Structure > content, datasets ranked, config differs from behavioral LoRA.
trigger: When fine-tuning a model to improve reasoning ability, building reasoning training data, or planning a reasoning distillation pipeline.
tags: [reasoning, distillation, lora, fine-tuning, chain-of-thought, deepseek-r1, qwen]
---

# Reasoning Distillation via LoRA

Complete guide for improving LLM reasoning through fine-tuning on distilled CoT traces.

## THE KEY INSIGHT

**Structure of long CoT matters MORE than content correctness** (Li et al 2025, arxiv:2502.07374).

| Corruption Type | Accuracy Impact |
|---|---|
| 100% wrong answers in traces | -3.2% |
| 67% of digits randomized | -4.3% |
| 67% of steps DELETED | -12.8% |
| 67% of steps SHUFFLED | -14.3% |

You don't need perfect teacher traces. What transfers is the STRUCTURAL pattern of reflection, backtracking, self-verification.

## Datasets Ranked by Impact

| Dataset | Size | Source | Best For |
|---|---|---|---|
| **OpenThoughts3-1.2M** | 1.2M (28GB) | QwQ-32B annotated, 850K math+250K code+100K science | **BEST overall — supersedes OT2, beats all open-data models** |
| OpenR1-Math-220k | 220K | DeepSeek-R1 math, majority-vote filtered | Math reasoning |
| Bespoke-Stratos-17k | 17K (126MB) | DeepSeek-R1, rejection-sampled | Proven LoRA baseline (+15.2%) |
| NuminaMath-CoT | 73K | AMC/AIME/Olympiad step-by-step | Competition math |
| CodeContests | 13K | DeepMind, Codeforces/CodeChef explanations | Code reasoning |
| **MedReason** | 31K (115MB) | UCSC-VLAA, structured medical reasoning traces | **Medical reasoning (MedReason-8B beat Huatuo-o1-8B by 4.2%)** |
| **MedReason-Stenographic** | 31K (87MB) | Compressed stenographic medical traces | Compact format variant of MedReason |
| medical-o1-reasoning-SFT | 25K (236MB) | FreedomIntelligence, GPT-4o generated | Medical CoT reasoning |
| OpenThoughts2-1M | 1M (8.3GB) | DeepSeek-R1, math+code+science+puzzles | Superseded by OT3 but still effective |

**Tool-Calling / Agent Datasets (for LoRA Phase 2+):**

| Dataset | Size | Best For |
|---|---|---|
| **XLAM FC 60k** (GATED — see huggingface-gated-repos skill) | 60K (93MB) | Multi-turn function calling |
| **Agent-FLAN** | ~219MB | Disentangles format-following from agent reasoning — fixes "knows format but can't use tools" |
| ToolBench G123 DFS | 188K (1.9GB) | Real API tool-use conversations (at Yhyu13/ToolBench_toolllama_G123_dfs — NOT xlang-ai) |
| Glaive FC v2 | 100K (259MB) | Function-calling examples |
| ToolACE-Qwen-cleaned | Qwen-formatted | Specifically formatted for Qwen tool-calling |

All free on HuggingFace. OpenR1-Math performed best in OpenThoughts2 curation tests.

## LoRA Config: Reasoning vs Behavioral

| Parameter | Behavioral LoRA | Reasoning LoRA |
|---|---|---|
| Rank | 16 | 64-128 |
| Alpha | 32 | 128-256 (alpha = 2*rank) |
| LR | 5e-5 | 1e-4 to 3e-4 |
| Target modules | q/k/v/o/gate_proj | Same + up_proj/down_proj |
| Sequence length | 4096 | 8192 (reasoning traces are LONG) |
| Epochs | 3 | 2-3 (fewer with more data) |
| Data size needed | ~300K tokens | 10M+ tokens |

Reasoning needs HIGHER rank because you're teaching fundamentally new patterns.

## Critical Prompt for Generating Reasoning Traces

```
Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of analysis, summarizing, exploration, reassessment, reflection, backtracking, and iteration to develop a well-considered thinking process.

Please structure your response into two main sections: Thought and Solution.

In the Thought section, detail your reasoning process using the specified format: <|begin of thought|> thought with steps separated with \n\n <|end of thought|> Each step should include detailed considerations such as analyzing questions, summarizing relevant findings, brainstorming new ideas, verifying the accuracy of the current steps, refining any errors, and revisiting previous steps.

In the Solution section, based on various attempts, explorations, and reflections from the Thought section, systematically present the final solution that you deem correct. <|begin of solution|> final formatted, precise, and clear solution <|end of solution|>
```

## Data Mix Recommendation

| Domain | % | Why |
|---|---|---|
| Math | 30-35% | Core reasoning foundation |
| Code | 15-20% | Structured problem-solving |
| STEM/Science | 15-20% | General analytical reasoning |
| Domain-specific | 10-15% | Generate from strongest available model |
| Base-model-native | 10-15% | Distribution match (same tokenizer) |
| Self-generated | 5-10% | Model's own correct traces (self-play) |

## Phased Approach

### Phase 0: OPSD On-Policy Self-Distillation (RECOMMENDED for Qwen3)

**OPSD outperforms GRPO for Qwen3 reasoning** (Zhao et al. 2026, arXiv 2604.13016). A single model acts as both teacher and student — teacher sees correct reasoning traces, student sees only the question. Training minimizes per-token divergence on the student's own rollouts.

**Why OPSD > GRPO for Qwen3:**
- **8x token efficiency:** 2k generation budget vs GRPO's 16k
- **Dense token-level feedback** vs GRPO's sparse reward signal
- **No separate teacher needed** — uses its own base model as teacher
- Tested specifically on Qwen3 family in paper

**Implementation:**
```bash
git clone https://github.com/siyan-zhao/OPSD.git /data/repos/OPSD
cd /data/repos/OPSD
# Requires transformers, torch, accelerate
pip install -e .
```

**Training command:**
```bash
python opsd_train.py \
  --model_name_or_path /data/models/Qwen3.6-27B-Uncensored \
  --dataset_path /data/datasets/reasoning/ \
  --output_dir /data/models/Qwen3.6-27B-OPSD \
  --num_train_epochs 2 \
  --per_device_train_batch_size 1 \
  --learning_rate 5e-5 \
  --max_length 2048 \
  --fp16
```

**Datasets for OPSD:**
- OpenThoughts-114k (math/code/science reasoning)
- Bespoke-Stratos-17k (DeepSeek-R1 distilled)
- medical-o1-reasoning-SFT (clinical reasoning traces)
- PRM800K (step-level human labels for sound reasoning)

**Expected gain:** +15-25% on MATH-500, GSM8K, HumanEval vs base model

### Phase 1: Proven Baseline (1 week)
- Data: Bespoke-Stratos-17k (126MB)
- Config: rank=64, alpha=128, LR 2e-4, 3 epochs
- Expected: +10-15% accuracy

### Phase 2: Extended Reasoning (2-3 weeks)
- Data: OpenR1-Math-220k + NuminaMath + domain traces
- Config: rank=64, alpha=128, LR 1e-4, 3 epochs
- Generate domain traces from strongest model, rejection sample

### Phase 3: Maximum Scale (Month 2+)
- Data: OpenThoughts2-1M (subset if needed)
- Config: rank=128, alpha=256, LR 5e-5, 2 epochs

### Phase 4: Self-Play Loop (Ongoing)
1. Run fine-tuned model on hard problems
2. Verify answers (math: exact match, code: test execution)
3. Keep only correct traces
4. Add to training set, fine-tune again
5. Compounds indefinitely at zero cost

## Anti-Patterns

1. Don't just train on correct answers — the PROCESS transfers
2. Don't filter too aggressively — content-corrupted traces still work within 3-4%
3. Don't mix behavioral and reasoning data at same rank — different LoRA configs
4. Don't use rank 16 for reasoning — needs 64+
5. Don't skip <|begin of thought|> markers — they anchor structure
6. Don't train on too-short traces — need 2K-8K tokens
7. Don't skip rejection sampling — keep only verifiably correct traces

## SFT Dataset Format (ShareGPT/ChatML for Qwen)

```json
{"conversations": [
  {"from": "system", "value": "<long-thinking prompt>"},
  {"from": "human", "value": "<problem>"},
  {"from": "gpt", "value": "<|begin of thought|>...<|end of thought|><|begin of solution|>...<|end of solution|>"}
], "category": "math_reasoning"}
```

## Key References

- Li et al 2025: arxiv:2502.07374
- OpenThoughts2: arxiv:2506.04178
- Bespoke-Stratos: bespokelabs.ai/blog/bespoke-stratos
- OpenR1: huggingface.co/open-r1
