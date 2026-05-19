# MT-GRPO-GTPO-tool-calling-agents

*Researched: 2026-04-10 20:35 CDT*

# Multi-Turn RL for Tool-Calling Agents: MT-GRPO + GTPO + IRC

**Paper:** arXiv 2604.02869v1 (April 2026) — Amity Research and Application Center

## Key Contributions

1. **MT-GRPO + GTPO Hybrid** — First application of Multi-Turn Group Relative Policy Optimization combined with Generalized Token-level Policy Optimization for training tool-calling agents with user simulators on realistic tasks (Tau-Bench airline benchmark).

2. **Iterative Reward Calibration (IRC)** — Systematic methodology for designing per-turn rewards via discriminative analysis of rollout data. Key findings:
   - Dense per-turn rewards can **catastrophically degrade** performance by up to 14pp if reward discriminative power is misaligned with advantage direction
   - Read-only tool calls should receive **zero reward** (not positive)
   - Non-golden state-changing calls should be **penalized**
   - Deep argument comparison eliminates 23.5% false positives in action matching

3. **GTPO Hybrid Advantage** — Eliminates advantage misalignment that arises with standard MT-GRPO under dense rewards. Dead Turn Gradient Focusing further improves signal.

## Results
- **Qwen3.5-4B**: 63.8% → 66.7% (+2.9pp) — exceeds GPT-4.1 (49.4%) and GPT-4o (42.8%) despite being ~50x smaller
- **Qwen3-30B-A3B MoE**: 58.0% → 69.5% (+11.5pp) — approaches Claude Sonnet 4.5 (70.0%)

## Why Sparse Rewards Accidentally Work
- Learning rate accounts for 70% of the gap
- Gradient focusing: 25%
- Advantage misalignment: 5%

## Key Insight for Hermes Agent Training
The finding that naive dense rewards degrade performance is critical. For Hermes RL training environments (hermes-atropos-environments), per-turn reward design must be calibrated empirically — not designed by intuition. IRC methodology should be adopted for reward shaping in tool-use RL environments.


## Sources

- https://arxiv.org/html/2604.02869v1
