# GiGPO Group-in-Group Policy Optimization for Multi-Turn LLM Agents

*Researched: 2026-04-10 21:32 CDT*

# GiGPO: Group-in-Group Policy Optimization (NeurIPS 2025)

**Authors:** Lang Feng, Zhenghai Xue, Tingcong Liu, Bo An

## Summary
GiGPO extends GRPO to multi-turn LLM agent training with hierarchical two-level credit assignment:
- **Episode-level:** Macro relative advantages across trajectory groups
- **Step-level:** Anchor state grouping — identifies repeated environment states across trajectories and groups actions from the same state

## Key Results
- >12% improvement on ALFWorld over GRPO
- >9% improvement on WebShop over GRPO  
- 42.1% (3B) and 47.2% (7B) on QA tasks
- Same GPU memory, same rollout, minimal extra time

## Why It Matters for Hermes
- Multi-turn tool-calling agents need per-step credit, not just per-trajectory
- Critic-free approach fits resource-constrained training
- Anchor state grouping is elegant — no extra rollouts needed
- Directly applicable to Atropos/Hermes RL environments

## Action Items
- [ ] Implement anchor state grouping in Hermes RL envs
- [ ] Compare GiGPO vs GRPO on tool-calling benchmarks
- [ ] Test on Qwen2.5-7B-Instruct with Hermes tool schemas

## Sources

- https://neurips.cc/virtual/2025/poster/118123
