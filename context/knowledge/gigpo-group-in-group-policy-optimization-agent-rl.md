# GiGPO-Group-in-Group-Policy-Optimization-Agent-RL

*Researched: 2026-04-10 20:31 CDT*

# GiGPO: Group-in-Group Policy Optimization for LLM Agent Training

**Paper:** arxiv 2505.10978 (NeurIPS 2025 poster)
**Authors:** Lang Feng, Zhenghai Xue, Tingcong Liu, Bo An (Nanyang Technological University / Skywork AI)
**Code:** https://github.com/langfengQ/verl-agent

## Key Innovation
Two-level hierarchical credit assignment for multi-turn LLM agent RL:
1. **Episode-level**: Macro relative advantages from groups of complete trajectories
2. **Step-level**: Anchor state grouping — identifies repeated environment states across trajectories, groups actions from same state for micro relative advantage estimation

## Why It Matters
Standard GRPO works well for single-turn (math reasoning) but struggles with multi-turn agents due to sparse/delayed rewards. GiGPO solves credit assignment across steps without auxiliary models or extra rollouts.

## Results
- **ALFWorld**: >12% improvement over GRPO
- **WebShop**: >9% improvement over GRPO
- **QA tasks**: 42.1% (3B model), 47.2% (7B model)
- **Cost**: Same GPU memory, identical LLM rollout, minimal extra time
- Models tested: Qwen2.5-1.5B/3B/7B-Instruct

## Properties
- Critic-free (no value function needed)
- Low memory overhead
- Stable convergence
- Orthogonal to single-turn group-based RL improvements

## Relevance to Hermes Agent
GiGPO's step-level credit assignment via anchor states is directly applicable to Atropos environments for Hermes agent training. The verl-agent codebase provides a ready framework for multi-turn RL with tool-calling agents.


## Sources

- https://arxiv.org/html/2505.10978v3
- https://neurips.cc/virtual/2025/poster/118123
