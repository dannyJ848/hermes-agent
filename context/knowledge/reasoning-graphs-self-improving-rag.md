# reasoning-graphs-self-improving-rag

*Researched: 2026-04-19 15:00 CDT*

# Reasoning Graphs: Self-Improving RAG (arXiv:2604.07595, Apr 2026)

**Key insight:** Persist per-evidence chain-of-thought as graph edges rather than discarding after each query. This enables evidence-centric feedback — traversing all prior evaluations for an evidence item when it appears in a new query.

**Architecture:** Reasoning Graphs (evidence evaluation edges) + Retrieval Graphs (candidate funnel tightening) = self-improving loop with no retraining.

**Results:** 47% error reduction, +11pp on 4-hop questions, Pareto-dominant in cost/latency/accuracy.

**Application to Hermes:** Our distilled_tips is analogous but flat. Migrating reasoning_traces to graph structure (using existing kg_nodes/kg_edges) could reduce variance and improve consistency in repeated tasks.

Also found: SGA-MCTS (decoupled planning/execution), entropy-guided branching for large tool spaces, and plan-following accuracy studies — all relevant to Hermes tool selection and autonomous execution.

## Sources

- https://arxiv.org/abs/2604.07595
- https://arxiv.org/search/?searchtype=all&query=LLM+reasoning+agent+planning+2026
