# agent-tool-optimization-autotool-tooltree-2026

*Researched: 2026-04-12 09:22 CDT*

# Agent Tool Optimization: AutoTool & ToolTree (2026)

## AutoTool (AAAI 2026) — arXiv:2511.14650
- **Key concept:** Tool usage inertia — tool invocations follow predictable sequential patterns in agent trajectories
- **Approach:** Constructs a directed graph from historical trajectories where nodes = tools, edges = transition probabilities. Traverses this graph to select tools with minimal LLM inference
- **Results:** Reduces inference costs by up to 30% while maintaining competitive task completion rates
- **Relevance to Hermes:** Hermes agent's tool_planner.py already uses a simplified MCTS approach. AutoTool's graph-based transition model could be layered on top to predict next-tool from historical patterns (e.g., `web_research → web_extract → save_finding` is a common chain)

## ToolTree (ICLR 2026) — arXiv:2603.12740
- **Key concept:** Greedy reactive tool selection lacks foresight and misses inter-tool dependencies
- **Approach:** MCTS-inspired planning with dual-stage LLM evaluation and bidirectional pruning (prune before AND after tool execution)
- **Results:** ~10% average improvement over state-of-the-art on 4 benchmarks
- **Relevance to Hermes:** The tool_planner.py currently scores single plans. ToolTree's dual-feedback mechanism (evaluate before execution, re-evaluate after result) could improve plan quality significantly

## Actionable Insight for Hermes
Both papers validate the approach of statistical/historical tool chain modeling. The current tool_planner uses basic plan scoring. Upgrading to:
1. Transition graph from historical trajectories (AutoTool pattern)
2. Dual-feedback evaluation (ToolTree pattern)
Would improve tool selection accuracy and reduce wasted tool calls (currently knowledge_search: 0%, browser_navigate: 0%).


## Sources

- https://arxiv.org/abs/2511.14650
- https://arxiv.org/abs/2603.12740
