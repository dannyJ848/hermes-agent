# reasoning-advances-tstar-externalized-reflection

*Researched: 2026-04-09 19:38 CDT*

# Reasoning Advances: T-STAR and Externalized Agent Reflection (Apr 2026)

## Key Papers
1. **T-STAR** (arXiv:2604.07165) — Tree-structured Self-Taught Agent Rectification. Consolidates trajectories into Cognitive Trees, back-propagates rewards via Introspective Valuation, performs In-Context Thought Grafting at critical divergence points. Achieves consistent improvements on embodied, interactive, reasoning, and planning benchmarks.

2. **Self-Revising Agent Decomposition** (arXiv:2604.07236) — Externalizes agent reasoning into inspectable runtime structure (belief tracking, world-model planning, symbolic reflection, LLM revision). Shows explicit world-model planning (+24.1pp win rate) far outweighs sparse LLM revision (+0.005 F1). Methodology for studying marginal LLM contribution.

## Application to Hermes Agent
- **Distillation improvement:** Adopt tree-structured trajectory analysis. Merge similar failure sessions into cognitive trees, identify the critical step where outcomes diverge. Currently recovery tips have 0% survival — this could fix extraction quality.
- **Runtime structure:** Our subconscious modules (domain_certainty, meta_loop, tool_planner) already externalize reasoning. The "declared reflective runtime" concept validates this architecture.
- **Sparse LLM principle:** Structured planning > more LLM calls. Our cron rescue + aggressive_continue layers benefit from this insight.

## Sources

- https://arxiv.org/abs/2604.07165
- https://arxiv.org/abs/2604.07236
