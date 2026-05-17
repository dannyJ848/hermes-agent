# rl-training-multi-turn-best-practices

*Researched: 2026-04-09 23:28 CDT*

# Best Practices for Multi-Turn RL (Fireworks AI, Dec 2025)

## Key Insight
SFT on golden traces is insufficient for multi-turn agents. RL is needed because:
- **Credit assignment is hard:** Final failure may come from any earlier decision
- **Combinatorial explosion:** Tool sequences create massive interaction spaces
- **Decomposition breaks down:** What matters is final outcome, not local step quality

## Multi-Turn RL Architecture
1. **Reward Design:** Partial vs trajectory-level rewards
2. **Reward Function:** Must survive contact with reality (handle tool failures, timeouts, edge cases)
3. **Training Recipes:** Pin tool versions, cache responses, handle environment non-determinism

## Practical Tips
- Pin versions of all tools, models, and dependencies during training
- Cache tool responses whenever possible to reduce variance
- Design rewards that are robust to environment noise
- Full trajectory rewards > per-step rewards for complex tasks

## Relevance to Hermes
- Directly applicable to Hermes Atropos environments
- Multi-turn tool sequences are exactly what Hermes does
- Trajectory-level reward design maps to Hermes session evaluation
- Tool version pinning critical for reproducible training


## Sources

- https://fireworks.ai/blog/best-practices-for-multi-turn-RL
