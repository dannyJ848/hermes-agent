# GiGPO-Group-in-Group-Policy-Optimization-Agent-Training

*Researched: 2026-04-10 01:10 CDT*

# GiGPO: Group-in-Group Policy Optimization for LLM Agent Training

**Source:** NeurIPS 2025 Poster (Lang Feng, Zhenghai Xue, Tingcong Liu, Bo An)

## Key Innovation
GiGPO extends group-based RL (like GRPO) from single-turn tasks to **multi-turn LLM agent training**. It solves the credit assignment problem across many agent-environment interaction steps.

## Two-Level Advantage Estimation
1. **Episode-level (macro):** Computes relative advantages based on groups of complete trajectories (like standard GRPO)
2. **Step-level (micro):** Uses an "anchor state grouping" mechanism — retroactively constructs step-level groups by identifying repeated environment states across trajectories. Actions from the same state are grouped together for micro relative advantage estimation.

## Properties
- **Critic-free** — no value function needed
- **Low memory** — same GPU overhead as GRPO
- **Stable convergence** — preserves GRPO's stability
- **No auxiliary models or additional rollouts** needed

## Results (Qwen2.5-1.5B/3B/7B-Instruct)
- ALFWorld: **>12% improvement** over GRPO
- WebShop: **>9% improvement** over GRPO
- QA tasks: 42.1% (3B), 47.2% (7B)
- Same GPU memory, identical LLM rollout, minimal additional time cost

## Relevance to Hermes Agent RL Training
- Directly applicable to Atropos environments for Hermes agent fine-tuning
- The anchor state grouping mechanism could improve credit assignment in tool-use trajectories
- Multi-turn agent training is exactly the Hermes use case (tool calls over many steps)
- Compatible with Qwen models already in our training pipeline

## Related Survey
"Advances in GRPO for Generation Models: A Survey" (arXiv 2603.06623) covers 50+ GRPO variants including Flow-GRPO, DenseGRPO, TreeGRPO, Chunk-GRPO, and extensions to video, 3D, and embodied AI.


## Sources

- https://neurips.cc/virtual/2025/poster/118123
- https://arxiv.org/html/2603.06623v1
