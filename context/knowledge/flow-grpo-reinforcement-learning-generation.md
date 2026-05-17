# flow-grpo-reinforcement-learning-generation

*Researched: 2026-04-10 17:26 CDT*

# Flow-GRPO: Training Flow Matching Models via Online RL

**Source:** arXiv 2505.05470 (NeurIPS 2025 poster)
**Authors:** Jie Liu et al. (CUHK, Tsinghua, Kuaishou/Kling)

## Key Innovation
First method to integrate online policy gradient RL into flow matching models. Two strategies:

1. **ODE-to-SDE Conversion**: Transforms deterministic ODE into equivalent SDE matching marginal distribution at all timesteps, enabling statistical sampling for RL exploration.
2. **Denoising Reduction**: Reduces training denoising steps while retaining original inference steps — improves sampling efficiency without sacrificing performance.

## Results
- Compositional generation: SD3.5-M GenEval accuracy 63% → 95%
- Visual text rendering: accuracy 59% → 92%
- Human preference alignment: substantial gains
- Minimal reward hacking — rewards increase without quality/diversity degradation

## Relevance to Agent RL Training
- Shows GRPO (Group Relative Policy Optimization) generalizes beyond LLMs to generation models
- Denoising reduction is analogous to "trajectory reduction" in agent RL — fewer training steps but full inference quality
- ODE→SDE conversion pattern could inspire deterministic→stochastic conversions in other domains

## GitHub
https://github.com/yifan123/flow_grpo


## Sources

- https://arxiv.org/html/2505.05470v5
- https://github.com/yifan123/flow_grpo
