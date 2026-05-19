# MT-GRPO-GTPO-multi-turn-tool-calling-RL

*Researched: 2026-04-10 05:53 CDT*

# Multi-Turn RL for Tool-Calling Agents (MT-GRPO + GTPO)

**Paper:** arXiv:2604.02869v1 (Apr 2026) — Wachiravit Modecrua et al., Amity Research

## Key Findings

1. **MT-GRPO + GTPO Hybrid** — First application of Multi-Turn GRPO combined with Generalized Token-level Policy Optimization for tool-calling agents. Evaluated on Tau-Bench airline benchmark.

2. **Dense rewards HURT** — Naïvely designed per-turn dense rewards degrade performance by up to 14pp due to advantage misalignment. Sparse rewards accidentally work better because:
   - Learning rate accounts for 70% of the performance gap
   - Gradient focusing accounts for 25%
   - Advantage misalignment only 5%

3. **Iterative Reward Calibration (IRC)** — Methodology for designing per-turn rewards using empirical discriminative analysis of rollout data. Iteratively calibrates reward tiers.

4. **Dead Turn Gradient Focusing** — Technique to focus gradients on meaningful turns, ignoring empty/no-op turns.

5. **Results on Tau-Bench:**
   - Qwen3.5-4B: 63.8% → 66.7% (+2.9pp)
   - Qwen3-30B-A3B MoE: 58.0% → 69.5% (+11.5pp)
   - Trained 4B model exceeds GPT-4.1 (49.4%) and GPT-4o (42.8%) — ~50x smaller
   - 30.5B MoE approaches Claude Sonnet 4.5 (70.0%)

## Relevance to Hermes/SOMA

- **Directly applicable** to training Hermes for better tool-calling via RL
- IRC methodology could improve our distillation tip reward signals
- Dead Turn Gradient Focusing addresses our exact problem: agent no-op loops during autonomous execution
- GTPO hybrid advantage formulation eliminates advantage misalignment in multi-turn tool use

## Resources
- **Code:** github.com/hyc2026/M3-Agent-Training (verl-based, supports PPO, GRPO, ReMax, REINFORCE++, RLOO, PRIME, DAPO)
- **NVIDIA NeMo Gym** — Interactive RL environments for multi-turn tool-calling verification


## Sources

- https://arxiv.org/html/2604.02869v1
- https://github.com/hyc2026/M3-Agent-Training
