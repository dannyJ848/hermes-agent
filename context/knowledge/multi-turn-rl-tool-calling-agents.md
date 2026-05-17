# multi-turn-rl-tool-calling-agents

*Researched: 2026-04-11 09:31 CDT*

# Multi-Turn RL for Tool-Calling Agents (arXiv 2604.02869, Apr 2026)

## Key Contribution
First application of MT-GRPO (Multi-Turn Group Relative Policy Optimization) combined with GTPO (Generalized Token-level Policy Optimization) for training tool-calling agents on realistic multi-turn tasks (Tau-Bench airline benchmark).

## Critical Findings
1. **Dense rewards can HURT**: Naively designed per-turn dense rewards degrade performance by up to 14pp due to advantage misalignment between reward discriminativeness and advantage direction.
2. **Sparse rewards accidentally work**: 70% of the performance gap comes from learning rate effects, 25% from gradient focusing, 5% from advantage alignment.
3. **Iterative Reward Calibration (IRC)**: Methodology for designing per-turn rewards using empirical discriminative analysis of rollout data.

## Results
- Qwen3.5-4B: 63.8% → 66.7% (+2.9pp) — exceeds GPT-4.1 (49.4%) despite being ~50x smaller
- Qwen3-30B-A3B MoE: 58.0% → 69.5% (+11.5pp) — approaching Claude Sonnet 4.5 (70.0%)

## Techniques for SOMA/Hermes Agent Training
- **Dead Turn Gradient Focusing**: Focuses gradients on turns that actually matter
- **GTPO Hybrid Advantage**: Combines per-turn group-normalized advantages with discounted returns
- **Cross-domain transfer**: Training on airline domain transferred to other domains

## Relevance
Directly applicable to training Hermes Agent's tool-calling capabilities via Atropos RL environments. The finding that dense rewards can be counterproductive is critical — our distillation reward model should use sparse outcome rewards rather than per-step dense signals.

## Sources

- https://arxiv.org/abs/2604.02869
