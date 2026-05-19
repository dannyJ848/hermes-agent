# sorl-stabilizing-off-policy-rl-llm-agents

*Researched: 2026-04-10 04:08 CDT*

# SORL: Stabilizing Off-Policy RL for Long-Horizon LLM Agent Training

**Paper:** "Stabilizing Off-Policy Training for Long-Horizon LLM Agent via Turn-Level Importance Sampling and Clipping-Triggered Normalization" (arXiv 2511.20718v2)

**Authors:** Chenliang Li et al. (Texas A&M, GE HealthCare, U Minnesota)

## Key Problem
Standard PPO/GRPO become unstable in off-policy multi-turn LLM agent training due to:
1. **Granularity mismatch** — token-level policy optimization vs turn-structured interactions
2. **High-variance gradients** — off-policy importance sampling + inaccurate advantage estimation

## Solution: SORL Framework
Two principled mechanisms:
- **Turn-Level Importance Sampling** — aligns policy optimization with multi-turn interaction structure
- **Clipping-Triggered Normalization** — adaptively suppresses unreliable off-policy updates

Instantiates two algorithms: **SO-PPO** and **SO-GRPO**.

## Results
- Prevents training instabilities and performance collapses seen in standard PPO/GRPO
- Maintains lower clipping ratios and stable optimization trajectories
- Superior or comparable task performance on multi-turn search benchmarks
- Evaluated on general QA, multi-hop QA, and **medical multiple-choice QA**

## Relevance to Hermes
- Directly applicable to Hermes agent RL training environments (Atropos)
- The turn-level IS approach could improve GRPO training for tool-calling tasks
- Medical QA evaluation is directly relevant to SOMA's domain
- The clipping-triggered normalization prevents the exact failure mode we've seen in training runs (gradient collapse)


## Sources

- https://arxiv.org/html/2511.20718v2
