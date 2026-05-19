# graph-based-reasoning-agents-2025

*Researched: 2026-04-15 00:04 CDT*

# Graph-Based Reasoning for Autonomous Agents (2025)

## Two key papers on advanced reasoning paradigms beyond ReAct:

### 1. GAP: Graph-Based Agent Planning (arXiv:2510.25320, Oct 2025)
- **Problem:** ReAct is sequential — can't exploit parallelism between independent sub-tasks
- **Solution:** Decompose tasks into dependency-aware sub-task graphs; determine parallel vs serial execution autonomously
- **Training:** SFT on graph-based planning traces + RL with correctness rewards
- **Result:** Significantly outperforms ReAct on multi-step retrieval tasks
- **Repo:** github.com/WJQ7777/Graph-Agent-Planning
- **Relevance to Hermes:** Our `delegate_parallel` already does ad-hoc parallelism. GAP formalizes dependency graph construction, which could improve task decomposition in autonomous mode.

### 2. GLM: Scaling Graph-CoT with Multi-Agent Framework (arXiv:2511.01633, Nov 2025)
- **Problem:** Single-agent Graph-CoT has low accuracy, excessive token usage, high latency
- **Solution:** Decompose into specialized agents (classification, reasoning, action generation, graph retrieval) + graph-aware KV-cache management
- **Result:** +38% accuracy, -95.7% token cost, -90.3% latency, 15.1x throughput
- **Key insight:** Branching + selective context sharing reduces prompt length while preserving reasoning quality
- **Relevance to Hermes:** The multi-agent decomposition pattern (specialized agents per reasoning phase) maps to our subagent delegation model. KV-cache eviction strategies are relevant for long sessions.

## Synthesis for Hermes Agent
Both papers move beyond sequential ReAct toward graph-structured reasoning. GAP focuses on planning (dependency graphs for tool calls), while GLM focuses on execution efficiency (specialized agents + cache management). Together they suggest:
1. **Task decomposition into DAGs** before execution (vs our current ad-hoc approach)
2. **Specialized sub-agents** per reasoning phase (vs general-purpose delegates)
3. **Context sharing optimization** — only pass relevant context to each sub-agent


## Sources

- https://arxiv.org/abs/2510.25320
- https://arxiv.org/abs/2511.01633
