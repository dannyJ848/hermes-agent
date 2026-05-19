# post-training-2026-grpo-dapo-agentic

*Researched: 2026-04-10 13:40 CDT*

# Post-Training in 2026: GRPO, DAPO, RLVR & Agentic Training

## Key Takeaways
- RLHF with human labels is dead. Production models now use GRPO/DAPO/RLVR + synthetic self-play.
- Post-training has 3 stages: SFT → Preference Optimization → RL (reasoning emerges here)
- GRPO eliminates the critic model by computing group-relative advantages (mean/std normalization over 8-64 samples per prompt). Provably optimal within policy gradient class.
- DAPO stabilizes long-horizon reasoning training via: Clip-Higher (anti-entropy-collapse), Dynamic Sampling, Token-level PG Loss (anti-vanishing-gradient on long CoT), Overlong Reward Shaping
- **Agentic Training** is the newest frontier: training models for multi-step tool use and autonomous workflows requires RL environments (not static datasets)

## Relevance to SOMA/Hermes
- Agentic training directly maps to Hermes agent RL environments (Atropos)
- GRPO's group-relative scoring is implementable without a separate critic — critical for resource-constrained training
- DAPO's token-level loss is essential for long tool-call chains where sequence-level loss vanishes

## Sources
- LLM Stats blog (March 2026)
- MERL TR2026-026: Training Task Reasoning LLM Agents for Multi-turn Task Planning


## Sources

- https://llm-stats.com/blog/research/post-training-techniques-2026
- https://www.merl.com/publications/docs/TR2026-026.pdf
