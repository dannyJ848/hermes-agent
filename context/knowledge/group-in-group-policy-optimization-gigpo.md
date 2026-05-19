# group-in-group-policy-optimization-gigpo

*Researched: 2026-04-10 01:20 CDT*

# Group-in-Group Policy Optimization (GiGPO) for LLM Agent Training

**Source:** NeurIPS 2025 Poster (Feng, Xue, Liu, An)

## Key Innovation
GiGPO extends GRPO from single-turn to multi-turn LLM agent training with a two-level relative advantage estimation:
1. **Episode-level (macro):** Groups complete trajectories, computes macro relative advantages (like standard GRPO)
2. **Step-level (micro):** Anchor state grouping — retroactively groups actions from the same environment state across trajectories, enabling fine-grained per-step credit assignment

## Why It Matters
- Standard GRPO struggles with sparse/delayed rewards in multi-turn agent tasks
- GiGPO achieves fine-grained credit assignment WITHOUT auxiliary critic models or extra rollouts
- Same GPU memory overhead as GRPO, near-zero additional time cost

## Results
- **ALFWorld:** >12% improvement over GRPO
- **WebShop:** >9% improvement over GRPO  
- **QA tasks (tool-integrated):** 42.1% on 3B, 47.2% on 7B models
- Tested on Qwen2.5-1.5B/3B/7B-Instruct

## Properties
- Critic-free (no value function needed)
- Low memory
- Stable convergence
- Scales from 1.5B to 7B parameters

## Relevance to Hermes Agent
- Directly applicable to RL training environments in `hermes-agent/environments/`
- Could improve tool-calling precision via per-step credit assignment
- Anchor state grouping mechanism could identify similar tool-call contexts across episodes
- Compatible with Atropos-based training infrastructure

## Sources

- https://neurips.cc/virtual/2025/poster/118123
