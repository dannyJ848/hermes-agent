# rl-training-gigpo-multi-turn-agents

*Researched: 2026-04-10 21:35 CDT*

# Group-in-Group Policy Optimization (GiGPO) for Multi-Turn LLM Agent Training

**Paper:** arXiv 2505.10978v3 (NeurIPS 2025 poster)
**Authors:** Lang Feng, Zhenghai Xue, Tingcong Liu, Bo An (NTU Singapore / Skywork AI)

## Key Innovation
GiGPO extends GRPO from single-turn to multi-turn agent training with a **two-level credit assignment** structure:
1. **Episode-level**: Macro relative advantages from groups of complete trajectories (same as GRPO)
2. **Step-level**: Anchor state grouping — retroactively groups actions from the same environment state across trajectories for micro relative advantage estimation

## Why It Matters
- Standard GRPO collapses step-level distinctions in multi-turn settings (sparse/delayed rewards)
- GiGPO achieves >12% improvement on ALFWorld and >9% on WebShop over GRPO
- Same GPU memory, same rollouts, near-zero additional time cost
- Critic-free, low memory, stable convergence (preserves GRPO benefits)

## Architecture Relevance to Hermes/Atropos
- Uses verl-agent codebase (open source)
- Hierarchical advantage estimation could improve Hermes RL environments
- The anchor state grouping mechanism is key: identifies repeated env states across trajectories to form step-level groups
- Tested on Qwen2.5-1.5B/3B/7B-Instruct — same model family as potential training targets

## Credit Assignment Formula
- Episode relative advantage: standard group-based (trajectory outcomes vs group mean)
- Step relative advantage: for each step, find all trajectories that visited the same state, group their actions, compute relative advantage within that group
- Combined with weighting parameter ω (ablation shows ω=0.5 works well)


## Sources

- https://arxiv.org/html/2505.10978v3
- https://github.com/langfengQ/verl-agent
