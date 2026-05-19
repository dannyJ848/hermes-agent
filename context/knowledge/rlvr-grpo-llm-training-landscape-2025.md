# rlvr-grpo-llm-training-landscape-2025

*Researched: 2026-04-10 17:26 CDT*

# RLVR + GRPO: The Dominant LLM Training Paradigm of 2025

**Source:** Sebastian Raschka, "The State of LLMs 2025"

## Key Insight
2025 was dominated by reasoning models using RLVR (Reinforcement Learning with Verifiable Rewards) and GRPO.

## Year-by-year LLM focus:
- 2022: RLHF + PPO
- 2023: LoRA SFT
- 2024: Mid-Training (synthetic data, data mix optimization)
- 2025: RLVR + GRPO

## DeepSeek R1 Impact
- Open-weight model comparable to proprietary models
- Training cost: ~$294K on top of DeepSeek V3 (much cheaper than assumed)
- RLVR allows post-training on large amounts of data using deterministic correctness labels
- Verifiable rewards (math, code) sufficient for complex problem-solving

## Why RLVR + GRPO Matters
- Removes bottleneck of expensive human-written responses/preference labels
- Enables scaling compute during post-training
- Every major LLM developer released reasoning/thinking variants following DeepSeek R1

## Relevance to Agent Training
- GRPO is the algorithm of choice for RL-based LLM improvement
- Verifiable rewards extend beyond math/code — tool-call success is also verifiable
- Post-training compute scaling is the new frontier


## Sources

- https://magazine.sebastianraschka.com/p/state-of-llms-2025
