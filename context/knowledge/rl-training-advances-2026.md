# rl-training-advances-2026

*Researched: 2026-04-10 13:49 CDT*

# RL Training Advances for LLM Agents (April 2026)

## Paper 1: Multi-Turn RL for Tool-Calling Agents (arXiv:2604.02869, Apr 3 2026)

**Key Innovation:** MT-GRPO (Multi-Turn Group Relative Policy Optimization) + GTPO (Generalized Token-level Policy Optimization) for training tool-calling agents.

**Critical Finding:** Naively designed dense per-turn rewards DEGRADE performance by up to 14pp due to misalignment between reward discriminativeness and advantage direction. They introduce **Iterative Reward Calibration** — designing per-turn rewards through empirical discriminative analysis of rollout data.

**Results on Tau-Bench Airline:**
- Qwen3.5-4B: 63.8% → 66.7% (+2.9pp)
- Qwen3-30B-A3B: 58.0% → 69.5% (+11.5pp)
- 4B model EXCEEDS GPT-4.1 (49.4%) and GPT-4o (42.8%) — 50x smaller!
- 30.5B MoE model approaches Claude Sonnet 4.5 (70.0%)

**Relevance to Hermes:** Directly applicable to RL training environments for tool-calling. The reward calibration insight is critical — naive reward design actively hurts performance.

## Paper 2: Evolution Strategies at Scale (arXiv:2509.24372, Feb 2026)

**Key Innovation:** First successful ES application to full-parameter fine-tuning of billion-parameter LLMs WITHOUT dimensionality reduction.

**Advantages over RL:**
- Better tolerance to long-horizon and delayed rewards
- Robustness across diverse base LLMs
- Reduced susceptibility to reward hacking
- Improved training stability
- Backpropagation-free post-training paradigm

**Relevance to Hermes:** ES could be an alternative to PPO/GRPO for Atropos environments, especially where reward signals are sparse or delayed (like multi-turn tool-use).

## Key Takeaway for Agent Development

The reward calibration problem from Paper 1 is the most actionable insight. When designing RL environments for tool-calling agents, per-turn rewards must be empirically validated through rollout analysis — not just assumed to be helpful. Dense rewards that aren't properly calibrated can be WORSE than sparse outcome rewards.


## Sources

- https://arxiv.org/abs/2604.02869
- https://arxiv.org/abs/2509.24372
