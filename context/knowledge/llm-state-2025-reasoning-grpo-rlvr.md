# llm-state-2025-reasoning-grpo-rlvr

*Researched: 2026-04-12 21:06 CDT*

# State of LLMs 2025 — Sebastian Raschka Year in Review

## Key Finding: GRPO/RLVR Revolutionized Post-Training
DeepSeek R1 (Jan 2025) showed reasoning behavior can be developed with RL, not just scale. Cost estimates: ~$5M to train frontier-class model (vs assumed $50-500M).

## Major Themes of 2025

### 1. Reasoning Models (The DeepSeek Moment)
- DeepSeek R1: open-weight model comparable to ChatGPT/Gemini
- Introduced RLVR (Reinforcement Learning with Verifiable Rewards) with GRPO algorithm
- Training R1 on top of V3 cost only $294K in compute
- Caveats: compute credits only, excludes researcher salaries and hyperparameter experiments

### 2. Tool Use Becoming Standard
- "In the coming years, enabling and allowing tool use will become increasingly common when using LLMs locally"
- Tool use is moving from API-only to local inference
- Key for agent architectures

### 3. Post-Training > Pre-Training
- GRPO and RLVR are more cost-effective than scaling pre-training
- Reasoning traces improve answer accuracy
- Open-weight models closing gap with proprietary ones

## Implications for Agent Development
- Smaller models with GRPO-style training can achieve reasoning comparable to large models
- Tool use optimization should focus on post-training rather than just prompt engineering
- Cost of frontier capability is dropping rapidly — good for autonomous agents

## Sources

- https://magazine.sebastianraschka.com/p/state-of-llms-2025
