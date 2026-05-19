# rl-training-agents-2026

*Researched: 2026-04-10 09:39 CDT*

# RL Training for LLM Agents (2026 State of Art)

## Key Paper: Multi-Turn RL for Tool-Calling Agents (arXiv 2604.02869)

**Core insight:** Dense per-turn rewards DEGRADE performance by up to 14pp when naively designed. The solution is Iterative Reward Calibration (IRC) using empirical rollout analysis.

**MT-GRPO + GTPO hybrid advantage:**
- Qwen3.5-4B trained to 66.7% on Tau-Bench (exceeds GPT-4.1 at 49.4%)
- Qwen3-30B-A3B MoE reached 69.5% (approaching Claude Sonnet 4.5 at 70.0%)
- First published RL results on Tau-Bench

**Why sparse rewards accidentally work:**
- Learning rate: 70% of performance gap
- Gradient focusing: 25%
- Advantage misalignment: only 5%

**Tree-GRPO (ICLR 2026):** Tree-structured rollouts for better credit assignment in multi-step agent trajectories.

**Implications for Hermes/Atropos:**
1. IRC methodology applicable to Atropos environment reward design
2. GTPO hybrid advantage could improve training stability
3. Dead Turn Gradient Focusing prevents zero-gradient dilution
4. Dense reward design requires careful calibration — not more = better

## Sources

- https://arxiv.org/html/2604.02869v1
- https://github.com/AMAP-ML/Tree-GRPO
