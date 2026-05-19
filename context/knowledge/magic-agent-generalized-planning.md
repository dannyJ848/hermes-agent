# magic-agent-generalized-planning

*Researched: 2026-04-12 22:49 CDT*

# MagicAgent: Generalized Agent Planning via RL + MoE

## Summary
MagicAgent (Honor Device / Fudan Univ, 2026) trains foundation models specifically for **generalized agent planning** across 5 heterogeneous task types:
1. Hierarchical Task Decomposition
2. Tool-Augmented Planning
3. Multi-Constraint Scheduling
4. Procedural Logic Orchestration
5. Long-Horizon Tool Execution

## Key Techniques
- **Synthetic data framework**: lightweight, scalable trajectory generation across diverse planning tasks
- **Two-stage training**: SFT → multi-objective RL (offline + online)
- **χPO (ChiPO)**: Token-level entropy regularization for exploration, think-level and action-level entropy smoothing, information bottleneck for exploitation
- **Load-balanced MoE strategy**: Balanced expert loading + specialization to prevent gradient interference across heterogeneous tasks

## Results
- MagicAgent-32B: 75.1% Worfbench, 55.9% NaturalPlan, 57.5% τ²-Bench, 86.9% BFCL-v3, 81.2% ACEBench
- Substantially outperforms existing SOTA on generalized planning

## Relevance to Hermes/SOMA
- The **hierarchical task decomposition** and **tool-augmented planning** paradigms directly mirror what Hermes does (autonomous_decide → plan → execute)
- The **multi-objective RL** approach could inform Hermes's distillation pipeline — using reward signals across heterogeneous agent tasks
- **Gradient interference mitigation** is relevant to multi-skill agent training
- χPO's entropy regularization for exploration mirrors the domain_certainty exploration strategy already deployed


## Sources

- https://arxiv.org/html/2602.19000v1
