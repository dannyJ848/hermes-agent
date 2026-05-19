# mt-grpo-tool-calling-agents

*Researched: 2026-04-10 04:23 CDT*

# Multi-Turn RL for Tool-Calling Agents (MT-GRPO + GTPO)

**Paper:** arXiv:2604.02869v1 (Apr 2026) — Amity Research and Application Center

## Key Contributions
1. **First application of MT-GRPO + GTPO** for training tool-calling agents on realistic multi-turn tasks
2. **Iterative Reward Calibration (IRC)** — methodology for designing per-turn rewards using empirical discriminative analysis
3. **GTPO Hybrid Advantage** eliminates advantage misalignment between reward discriminativeness and advantage direction

## Critical Findings
- **Naïve dense per-turn rewards DEGRADE performance by up to 14pp** due to misalignment
- **Sparse rewards accidentally work**: Learning rate accounts for 70% of the gap, gradient focusing 25%, advantage misalignment 5%
- **Dead Turn Gradient Focusing** — technique to handle turns where the agent does nothing meaningful

## Results (Tau-Bench airline benchmark)
| Model | Base → Trained | Comparison |
|-------|---------------|------------|
| Qwen3.5-4B | 63.8% → 66.7% (+2.9pp) | Exceeds GPT-4.1 (49.4%), GPT-4o (42.8%) |
| Qwen3-30B-A3B MoE | 58.0% → 69.5% (+11.5pp) | Approaches Claude Sonnet 4.5 (70.0%) |

## Relevance to Hermes Agent
- Directly applicable to Hermes Atropos RL environments for tool-calling optimization
- IRC methodology could improve reward design in agent training environments
- GTPO hybrid advantage formulation could be integrated into training recipes
- Cross-domain transfer results suggest training on customer service tasks generalizes to other tool-use domains


## Sources

- https://arxiv.org/html/2604.02869v1
- https://github.com/FareedKhan-dev/multi-agent-training-grpo
