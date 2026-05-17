# GiGPO-Group-in-Group-Policy-Optimization

*Researched: 2026-04-10 07:22 CDT*

# GiGPO: Group-in-Group Policy Optimization for LLM Agent Training

**Source:** arXiv 2505.10978v3 (NeurIPS 2025 poster)
**Authors:** Lang Feng, Zhenghai Xue, Tingcong Liu, Bo An (Nanyang Technological University / Skywork AI)
**Code:** https://github.com/langfengQ/verl-agent

## Key Innovation
GiGPO extends GRPO to multi-turn LLM agent training with a **two-level relative advantage** structure:
1. **Episode-level**: Macro relative advantages from groups of complete trajectories (like standard GRPO)
2. **Step-level**: Anchor state grouping mechanism that retroactively groups actions from repeated environment states across trajectories — enabling micro relative advantage estimation per step

## Why It Matters
- GRPO works well for single-turn tasks (math reasoning) but struggles with multi-turn agent tasks due to sparse/delayed rewards
- GiGPO solves the credit assignment problem across many agent-environment interaction steps
- **Critic-free, low memory, stable convergence** — same appealing properties as GRPO
- No auxiliary models or additional rollouts needed

## Results
- **ALFWorld**: >12% improvement over GRPO
- **WebShop**: >9% improvement over GRPO
- **QA tasks**: 42.1% (3B model), 47.2% (7B model)
- **Same GPU memory overhead, identical LLM rollout, minimal additional time cost**
- Tested on Qwen2.5-1.5B/3B/7B-Instruct

## Relevance to Hermes/SOMA
- Directly applicable to training tool-calling agents with multi-turn interactions
- The anchor state grouping mechanism could improve Hermes's RL environments
- verl-agent codebase provides implementation reference for Atropos environments
- Step-level credit assignment is exactly what's needed for complex tool-use chains


## Sources

- https://arxiv.org/html/2505.10978v3
- https://github.com/langfengQ/verl-agent
