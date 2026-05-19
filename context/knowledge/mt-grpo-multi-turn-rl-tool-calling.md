# mt-grpo-multi-turn-rl-tool-calling

*Researched: 2026-04-20 06:27 CDT*

# Multi-Turn RL for Tool-Calling Agents with Iterative Reward Calibration

**Paper:** arxiv 2604.02869 (April 2026)

## Key Innovation
MT-GRPO (Multi-Turn Group Relative Policy Optimization) + GTPO (Generalized Token-level Policy Optimization) with Iterative Reward Calibration (IRC) for training tool-calling agents.

## Critical Findings

### Advantage Misalignment Problem
Dense per-turn rewards can catastrophically degrade performance because their discriminative power is misaligned with advantage computation. A small positive reward for a correct "read-only" tool call (+0.3) gets overwhelmed by a large negative outcome advantage (-0.87), creating a net suppressing signal for correct actions.

### Hybrid Advantage Formula
`A_hybrid = GN(sum of discounted per-turn rewards + discounted outcome) + lambda * A_outcome`
- gamma=0.9 discount factor attenuates outcome influence on early turns
- lambda=0.3 dampens outcome advantage to prevent overwhelming per-turn signals

### Iterative Reward Calibration (IRC)
1. Collect rollout trajectories
2. Classify turns into tiers (Gold, Soft Match, Read-only, State-change, Error)
3. Measure Point-Biserial Correlation between each tier and task success
4. Adjust rewards proportional to discriminative power, not intuition
5. Verify advantage alignment

Key calibration: Read-only actions had near-zero discriminative power → reward set to 0.0. State-change actions correlated with failure → flipped to -0.1.

### Sparse > Dense Rewards
Sparse rewards (outcome only) often outperform naive dense rewards due to "Dead Turn Gradient Focusing" — 86.4% of gradient focuses on positions where agent choice actually matters.

## Performance
- Qwen3.5-4B + IRC: 66.7% on Tau-Bench (beats GPT-4.1 at 49.4%)
- Qwen3-30B MoE + IRC: 69.5% (near Claude Sonnet 4.5 at 70.0%)
- Efficiency: 50% fewer turns, 65% faster completion, 100% action accuracy

## Relevance to Hermes Agent
- Directly applicable to improving Hermes tool-calling via RL fine-tuning
- IRC methodology can calibrate reward signals for Hermes-specific tool chains
- Sparse reward finding suggests Hermes's current approach of outcome-only evaluation may be optimal
- Deep argument comparison technique (normalizing JSON tool args) applicable to tool_intelligence scoring

## Sources

- https://arxiv.org/html/2604.02869v1
