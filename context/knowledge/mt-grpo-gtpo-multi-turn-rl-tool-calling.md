# MT-GRPO-GTPO-multi-turn-rl-tool-calling

*Researched: 2026-04-10 13:02 CDT*

# Multi-Turn RL for Tool-Calling Agents with Iterative Reward Calibration

**Paper:** arXiv 2604.02869 (April 2026)
**Authors:** Wachiravit Modecrua et al. (Amity Research)

## Key Findings

1. **First MT-GRPO + GTPO applied to realistic tool-calling agents** on Tau-Bench airline benchmark (customer service with DB mutations, policy adherence, multi-step reasoning).

2. **Dense per-turn rewards can catastrophically degrade performance** (-14pp) when reward discriminative power is misaligned with advantage computation. Read-only tool calls should get ZERO reward (not positive).

3. **Iterative Reward Calibration (IRC):** Empirical methodology — measure correlation between reward tiers and task success, then adjust. Deep argument comparison eliminates 23.5% false positives.

4. **GTPO Hybrid Advantage** eliminates advantage misalignment from standard MT-GRPO under dense rewards.

5. **Dead Turn Gradient Focusing:** 25% of improvement comes from suppressing gradients on turns that don't contribute.

## Results
- Qwen3.5-4B: 63.8% → 66.7% (+2.9pp) — exceeds GPT-4.1 (49.4%) and GPT-4o (42.8%) despite being 50x smaller
- Qwen3-30B-A3B MoE: 58.0% → 69.5% (+11.5pp) — approaches Claude Sonnet 4.5 (70.0%)
- Trained model: 50% fewer turns, 65% faster, 3.5x less verbose

## Relevance to Hermes Agent
- Directly applicable to Hermes RL training environments (Atropos)
- IRC methodology can improve reward design for tool-calling training
- Dead Turn Gradient Focusing could reduce wasted computation on no-op turns
- Tau-Bench benchmark is ideal for evaluating Hermes tool-calling capabilities


## Sources

- https://arxiv.org/html/2604.02869v1
