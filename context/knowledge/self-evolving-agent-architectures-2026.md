# self-evolving-agent-architectures-2026

*Researched: 2026-04-07 01:08 CDT*

# Self-Evolving Agent Architectures: 2025-2026 Frontier

## Key Papers

### Group-Evolving Agents (GEA) — arXiv:2602.04837 (Feb 2026)
- Group-level evolution with experience sharing between agents
- 71.0% on SWE-bench (vs 56.7% baselines)
- Fixes framework bugs in 1.4 iterations (vs 5 for tree evolution)
- **For Evey**: Wire mesh task results into shared experience archive

### Hyperagents — arXiv:2603.19461 (Mar 2026)
- Self-referential: meta-agent modifies itself AND task agent
- Meta-procedure is itself editable → self-accelerating improvement
- Meta-level improvements transfer across domains
- **For Evey**: Meta-distillation loop where extraction heuristics are self-modifying

### Darwin Godel Machine — arXiv:2505.22954 (May 2025)
- Archive of diverse agents (tree, not single best)
- Foundation model creates new interesting variants
- SWE-bench 20% → 50% through self-improvement alone
- **For Evey**: Store plugin configs with performance metrics, rollback on degradation

### AgentArk — arXiv:2602.03955 (Feb 2026)
- Distills multi-agent debate into single agent weights
- Three strategies: reasoning-enhanced FT, trajectory augmentation, process-aware distillation
- **For Evey**: Multi-agent task successes → higher confidence tips

### Ares — arXiv:2603.07915 (Mar 2026)
- Per-step dynamic reasoning effort selection
- 52.7% token reduction with minimal accuracy loss
- **For Evey**: Route simple tools to fast models, complex tools to reasoning models

### HippoRAG 2 — arXiv:2502.14802 (ICML 2025)
- KG + Personalized PageRank + online learning
- 7% improvement in associative memory over SOTA
- **For Evey**: KG layer connecting facts via relationships (698 nodes built)


## Sources

- https://arxiv.org/abs/2602.04837
- https://arxiv.org/abs/2603.19461
- https://arxiv.org/abs/2505.22954
- https://arxiv.org/abs/2602.03955
- https://arxiv.org/abs/2603.07915
- https://arxiv.org/abs/2502.14802
