# autotool-graph-based-tool-selection

*Researched: 2026-04-11 23:16 CDT*

# AutoTool: Graph-Based Tool Selection for LLM Agents

**Paper:** arXiv:2511.14650 (AAAI 2026)
**Authors:** Jingyi Jia, Qinbin Li

## Key Innovation
AutoTool exploits **tool usage inertia** — the empirical observation that tool invocations follow predictable sequential patterns in agent trajectories.

## Architecture
- Constructs a **directed graph** from historical agent trajectories
- Nodes = tools, edges = transition probabilities
- Models inertia in tool selection statistically
- Integrates **parameter-level information** to refine tool input generation
- Traverses the graph to select tools/params with **minimal LLM inference**

## Results
- **30% inference cost reduction** while maintaining competitive task completion rates
- Practical and scalable enhancement for inference-heavy frameworks (ReAct, etc.)

## Relevance to Hermes Agent
Hermes already collects tool usage trajectories. Could build a similar transition graph:
- `tool_usage` domain has 267 tips — rich data source
- `tool-selection` and `tool-reasoning` domains exist but under-explored
- A transition probability model could pre-rank tools before LLM dispatch
- Complements the existing `tool_planner.py` capability planner

## Actionable Insight
Build a lightweight transition graph from `cerebrum_memory.db` tool usage logs. Use it to reorder tool schemas presented to the LLM — most-likely-next-tool first. This is a zero-cost optimization that could reduce token usage in tool selection by ~30%.


## Sources

- https://arxiv.org/abs/2511.14650
