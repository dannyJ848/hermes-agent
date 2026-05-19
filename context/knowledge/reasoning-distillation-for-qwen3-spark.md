# reasoning-distillation-for-qwen3-spark

*Researched: 2026-04-17 13:40 CDT*

# Reasoning Distillation for Qwen3.6-35B-A3B on DGX Spark

## THE KEY INSIGHT (Li et al 2025, Snorkel AI review)

**Structure of long CoT matters MORE than content correctness.**

| Corruption Type | Accuracy Impact |
|---|---|
| 100% wrong answers in traces | -3.2% |
| 67% of digits randomized | -4.3% |
| 67% of reasoning keywords removed | -3.3% |
| 67% of steps DELETED | -12.8% |
| 67% of steps RANDOMLY ADDED | -14.3% |
| 67% of steps SHUFFLED | Massive drop |

**Implication:** You don't need perfect teacher traces. What transfers is the STRUCTURAL pattern of reflection/backtracking/self-verification — words like "Wait", "Let me verify", "Alternatively", "Hmm", "Just to be thorough".

## Proven Results

**Bespoke-Stratos-17k → Qwen-2.5-32B-Instruct via LoRA:**
- 17,000 examples, $800 to generate (DeepSeek-R1 traces)
- 15.2% average accuracy improvement
- LoRA = on par with full SFT for reasoning
- Matched o1-preview on MATH500, exceeded on some coding benchmarks
- AIME2024: 63.3 (vs o1-preview 40.0)
- MATH500: 93.0 (vs o1-preview 81.4)

**OpenThoughts2-1M → OpenThinker2-32B:**
- 1M examples, 8.3GB
- AIME24: 76.7, MATH500: 90.8, GPQA-D: 64.1
- Best open reasoning model at 32B class

## Datasets Ranked by Impact

| Dataset | Size | Source | Best For | Stars |
|---|---|---|---|---|
| **OpenThoughts2-1M** | 1M examples (8.3GB) | DeepSeek-R1 traces, math+code+science+puzzles | General reasoning, max coverage | Highest |
| **OpenR1-Math-220k** | 220K examples | DeepSeek-R1 math traces, majority-vote filtered | Math reasoning specifically | Very High |
| **Bespoke-Stratos-17k** | 17K examples (126MB) | DeepSeek-R1 traces, rejection-sampled | Proven LoRA-effective baseline | High |
| **NuminaMath-CoT** | 73K examples | AMC/AIME/Olympiad with step-by-step solutions | Competition math | High |
| **CodeContests** | 13K problems | DeepMind, Codeforces/CodeChef with explanations | Code reasoning | High |
| **MedQA-CoT** | ~12.8K + expansions | USMLE with chain-of-thought explanations | Medical reasoning | Medium |
| **MetaMathQA** | 395K examples | Augmented math problems with CoT | Broad math coverage | Medium |

## The Recipe for Qwen3.6-35B on Spark

### Phase 1: Basic Reasoning Foundation (Week 1)
**Data:** Bespoke-Stratos-17k (126MB) — proven at exactly this scale for LoRA
**Config:** rank=64, alpha=128, targets q/k/v/o/gate_proj, LR 2e-4, 3 epochs
**Expected:** +10-15% on math/reasoning benchmarks (mirroring Stratos results)

### Phase 2: Extended Reasoning (Week 2-3)
**Data:** OpenR1-Math-220k + NuminaMath-CoT (293K combined)
+ Generate medical reasoning traces from GLM-5.1 via FriendliAI (use the Snorkel prompt format)
**Config:** rank=64, alpha=128, LR 1e-4, 3 epochs
**Expected:** +15-25% cumulative, especially on math and medical domains

### Phase 3: Maximum Scale (Month 2+)
**Data:** OpenThoughts2-1M (8.3GB, may need to subset for Spark memory)
**Config:** rank=128, alpha=256, LR 5e-5, 2 epochs (more data = fewer epochs needed)
**Expected:** Approaching DeepSeek-R1-Distill-32B level performance

### Phase 4: Domain Specialization (Ongoing)
**Data:** Medical reasoning traces from GLM-5.1/Claude + Cortex experiences
- Use GLM-5.1 via FriendliAI to generate long CoT on USMLE/clinical problems
- Rejection sample: keep only traces that produce correct answers
- Add to dataset and fine-tune another LoRA epoch
- This is where the compounding loop kicks in

## The Critical Prompt for Generating Reasoning Traces

Use THIS prompt when generating traces from GLM-5.1 (or any stronger model):

```
Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of analysis, summarizing, exploration, reassessment, reflection, backtracking, and iteration to develop a well-considered thinking process.

Please structure your response into two main sections: Thought and Solution.

In the Thought section, detail your reasoning process using the specified format: <|begin of thought|> thought with steps separated with \n\n <|end of thought|> Each step should include detailed considerations such as analyzing questions, summarizing relevant findings, brainstorming new ideas, verifying the accuracy of the current steps, refining any errors, and revisiting previous steps.

In the Solution section, based on various attempts, explorations, and reflections from the Thought section, systematically present the final solution that you deem correct. <|begin of solution|> final formatted, precise, and clear solution <|end of solution|>
```

This prompt produces the KEY structural patterns: reflection, backtracking, self-verification.

## LoRA Config Differences: Reasoning vs Behavioral

| Parameter | Behavioral LoRA (our Claude Code dataset) | Reasoning LoRA |
|---|---|---|
| Rank | 16 | 64-128 |
| Alpha | 32 | 128-256 |
| LR | 5e-5 | 1e-4 to 3e-4 |
| Target modules | q/k/v/o/gate_proj | Same + up_proj/down_proj |
| Sequence length | 4096 | 8192 (reasoning traces are LONG) |
| Epochs | 3 | 2-3 (fewer with more data) |
| Data size | 283K tokens | 10M+ tokens |

**Reasoning needs higher rank** because you're teaching fundamentally new reasoning patterns (backtracking, verification), not just adapting existing behavior. The rank 16 that works for behavioral LoRA is too low for reasoning.

## The Self-Play Loop (Long Term)

1. Fine-tune Qwen3.6 on reasoning traces (Phase 1-3)
2. Run the fine-tuned model on hard problems
3. Grade with verification (math: exact match, code: test execution, medical: gold answer)
4. Keep only correct traces — these are GOLD (model's OWN reasoning that works)
5. Add to training set and fine-tune again
6. Each iteration, the model generates slightly better traces
7. Compounds indefinitely at zero cost on the Spark

This is the SAME loop DeepSeek-R1 uses for RL training, but with SFT instead of RL — simpler, cheaper, still effective.

## Data Mix Recommendation for Danny's Use Case

| Domain | % of Dataset | Source | Why |
|---|---|---|---|
| Math | 30-35% | OpenR1-Math-220k + NuminaMath | Core reasoning foundation |
| Code | 15-20% | CodeContests + SWE-bench trajectories | Structured problem-solving transfer |
| STEM/Science | 15-20% | OpenThoughts2 subset | General analytical reasoning |
| Medical | 10-15% | MedQA-CoT (generated from GLM-5.1) | Danny's primary domain |
| Qwen-native | 10-15% | Any Qwen reasoning releases | Distribution match (same tokenizer) |
| Self-generated | 5-10% | Qwen's own correct traces (self-play) | Compounding loop |

## Anti-Patterns to Avoid

1. **Don't just train on correct answers** — the reasoning PROCESS is what matters
2. **Don't filter too aggressively** — even content-corrupted traces still transfer (within 3-4%)
3. **Don't mix behavioral and reasoning data at the same rank** — they need different LoRA configs
4. **Don't use rank 16 for reasoning** — too low, needs 64+
5. **Don't skip the <|begin of thought|> markers** — they anchor the structure the model learns
6. **Don't train on too-short traces** — reasoning traces should be 2K-8K tokens
7. **Don't forget rejection sampling** — keep only traces where the final answer is correct


## Sources

- https://snorkel.ai/blog/research-spotlight-is-long-chain-of-thought-structure-all-that-matters-when-it-comes-to-llm-reasoning-distillation/
- https://huggingface.co/datasets/bespokelabs/Bespoke-Stratos-17k
- https://huggingface.co/datasets/open-thoughts/OpenThoughts2-1M
- https://arxiv.org/abs/2502.07374
- https://arxiv.org/abs/2506.04178
