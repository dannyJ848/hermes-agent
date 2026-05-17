# cosmo-agent-tool-augmented-rl-apr2026

*Researched: 2026-04-08 11:54 CDT*

# COSMO-Agent: Tool-Augmented RL for CAD-CAE Closed-Loop
**Paper**: arXiv:2604.05547 (April 2026)
**Authors**: Liyuan Deng et al.

## Key Innovation
RL framework teaching LLMs to orchestrate tools for closed-loop design-simulation optimization. Small open-source LLMs with RL beat large closed-source models.

## Multi-Constraint Reward Design
3-axis reward: (1) feasibility, (2) toolchain robustness, (3) structured output validity. Jointly optimized. Better than binary success/failure.

## Results
- Small RL-tuned LLMs exceed GPT-4 at tool orchestration
- 25 component categories for training
- Closed-loop: generate → simulate → parse → revise until constraints satisfied

## Applications to Evey
- Multi-constraint reward → track feasibility, robustness, validity separately for tip confidence
- Small models with targeted RL can beat large models at specific tasks → our distillation tips are domain-specific RL
- Tool orchestration as RL environment → frame multi-tool workflows as sequential decisions


## Sources

- https://arxiv.org/abs/2604.05547
