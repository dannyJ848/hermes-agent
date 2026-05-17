# imagine-intrinsic-motivation-llm-2026

*Researched: 2026-04-05 03:02 CDT*

# IMAGINE: Intrinsic Motivation for LLM Reasoning (Jan 2026)

## Paper: arXiv 2505.17621

## Core Problem
RL approaches (PPO, GRPO) suffer from:
1. Sparse, outcome-based rewards
2. Weak exploration incentives
3. Bias toward familiar trajectories over novel reasoning paths

## Solution: IMAGINE
Three innovations:
1. **Trajectory-aware exploration reward**: Dense rewards based on reasoning path novelty
2. **Novelty detection**: Identifies when the agent is exploring truly new territory
3. **Dense reward shaping**: Replaces sparse outcome rewards with step-by-step feedback

## Key Insight for Evey
We already implement a form of this via:
- Active inference / EFE scores (curiosity-driven task selection)
- Distillation bridge (step-by-step feedback from tool outcomes)
- Perspective diversity (encouraging novel reasoning paths)

What we're MISSING:
- **Novelty detection**: We should measure how "novel" each reasoning path is
- **Dense reward shaping**: Our rewards are still sparse (tool success/failure)
- **Trajectory awareness**: We should reward novel SUCCESSFUL paths, not just any novel path

## Action Items
1. Add novelty scoring to distillation tips (how different is this from previous approaches?)
2. Track reasoning path diversity over time
3. Reward exploration of new domains, not just exploitation of known ones


## Sources

- https://arxiv.org/abs/2505.17621
