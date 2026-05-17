# rl-training-gigpo-agent-credit-assignment

*Researched: 2026-04-10 16:38 CDT*

# GiGPO: Group-in-Group Policy Optimization for Multi-Turn Agent RL

## Key Finding
GiGPO (NeurIPS 2025) solves the per-step credit assignment problem in multi-turn LLM agent RL training using a two-level advantage estimation:
- Episode-level: macro relative advantages from trajectory groups (standard GRPO)
- Step-level: anchor state grouping — actions from the same env state across trajectories get grouped for micro advantages

## Results
- ALFWorld: >12% over GRPO, WebShop: >9% over GRPO
- Same GPU memory, no auxiliary models, near-zero extra time cost

## Application to Hermes
Hermes's Atropos environments face identical credit assignment challenges. GiGPO's anchor state grouping maps directly to tool-call sequences (episode=task, step=tool call). Could replace current reward signal design in RL training environments.

## Sources
- arXiv:2505.10978 (GiGPO)
- arXiv:2603.06623 (Flow-GRPO Survey)
- OpenReview: Training-Free GRPO (tyUnYbE7Gi)


## Sources

- https://arxiv.org/abs/2505.10978
- https://arxiv.org/abs/2603.06623
- https://openreview.net/forum?id=tyUnYbE7Gi
