# SAGE-RL-Self-Improving-Agent-Skill-Library

*Researched: 2026-04-12 19:02 CDT*

# SAGE: Reinforcement Learning for Self-Improving Agent with Skill Library

**Paper:** arXiv:2512.17102 (Dec 2025, revised Mar 2026)
**Authors:** Jiongxiao Wang et al.

## Key Contribution
SAGE (Skill Augmented GRPO for self-Evolution) — a novel RL framework that systematically incorporates skills into agent learning using GRPO.

## Architecture
- **Sequential Rollout**: Iteratively deploys agents across chains of similar tasks. Skills from previous tasks accumulate in a library and become available for subsequent tasks.
- **Skill-integrated Reward**: Complements outcome-based rewards with skill generation/utilization metrics.

## Results (AppWorld benchmark)
- 8.9% higher Scenario Goal Completion vs baselines
- 26% fewer interaction steps
- 59% fewer tokens generated
- Applied to supervised-finetuned model with expert experience

## Relevance to Hermes
- Directly applicable to Hermes's skill_manage system — skills could be trained via GRPO rather than manual curation
- Sequential Rollout pattern mirrors how Hermes already chains tasks in autonomous mode
- Skill-integrated reward could improve delegation scoring
- The "skill library" concept is essentially what Hermes skills already are, but RL-optimized instead of hand-written

## Key Insight
Skills generated during training accumulate and transfer across similar tasks — this is the same principle as Hermes's skill_manage but automated via RL instead of requiring human/agent authoring.


## Sources

- https://arxiv.org/abs/2512.17102
