# tool-optimization-autotool-tooltree-2026

*Researched: 2026-04-11 23:25 CDT*

# Tool Optimization for LLM Agents (2025-2026)

## AutoTool (AAAI 2026) — arXiv:2511.14650
**Graph-based tool selection bypassing repeated LLM inference.**
- Key insight: **Tool Usage Inertia** — tool invocations follow predictable sequential patterns
- Constructs a directed graph from historical trajectories: nodes=tools, edges=transition probabilities
- Integrates parameter-level info to refine tool input generation
- **30% inference cost reduction** while maintaining competitive task completion
- Practical for inference-heavy frameworks like ReAct

**Application to Hermes:** Could build a transition graph from `tool_usage` tips (267 entries) and `tool_history` data. If tool A is called, predict tool B with high probability and pre-populate schema.

## ToolTree (ICLR 2026) — arXiv:2603.12740
**Monte Carlo Tree Search for multi-step tool planning.**
- Replaces greedy reactive tool selection with lookahead planning
- Dual-stage LLM evaluation + bidirectional pruning
- Explores tool-use trajectories before and after execution
- **~10% improvement** over SOTA on 4 benchmarks
- Handles inter-tool dependencies that greedy methods miss

**Application to Hermes:** For complex multi-tool tasks (research → distillation → save_finding chain), MCTS-style planning could reduce wasted tool calls. The `tool_planner.py` already does basic planning — could integrate MCTS concepts.

## Cross-Domain Insight
Both papers confirm: statistical structure in tool usage (inertia + dependencies) is exploitable. This validates the `tool_planner.py` and `tool_intelligence.py` approaches already in Hermes. The next step is building transition graphs from tool history data.


## Sources

- https://arxiv.org/abs/2511.14650
- https://arxiv.org/abs/2603.12740
