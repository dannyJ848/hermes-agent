# tool-optimization-agent-2026

*Researched: 2026-04-12 07:23 CDT*

# Tool Optimization for LLM Agents (2026 Research)

## The Tool Selection Problem at Scale
- Berkeley Function Calling Leaderboard: accuracy drops from **43% to 2%** on calendar scheduling when tools expand from 4→51 across domains
- 58 tool definitions = ~55,000 tokens baseline per turn (Anthropic internal testing)
- Failure mode: model picks plausible-but-wrong tool, combines tools incorrectly, or uses wrong parameter schemas
- Tool description quality variance is an underappreciated failure mode (overlapping descriptions confuse models)

## AutoTool (AAAI 2026) — Graph-Based Tool Selection
- **Key insight: "Tool usage inertia"** — tool invocations follow predictable sequential patterns
- Constructs directed graph from historical trajectories: nodes=tools, edges=transition probabilities
- Traverses graph to select tools + parameters with minimal LLM inference
- Reduces inference costs by **up to 30%** while maintaining competitive task completion
- Practical for inference-heavy frameworks like ReAct

## ToolTree — Dual-Phase Tool Planning
- Addresses greedy/reactive tool selection that lacks foresight
- Uses dual-phase approach for more strategic tool planning

## EvoTool — Self-Evolving Tool-Use Policies
- Optimizes tool-use policies through self-evolution
- Addresses challenge of policy optimization in complex tool landscapes

## RAG-Based Tool Selection (Baseline Improvement)
- Embed tool descriptions + user query, retrieve top-k similar tools
- Cuts token usage and narrows selection space
- But pure embedding retrieval misses behavioral dependencies between tools

## Application to Hermes Agent
- Hermes has 50+ tools across multiple toolsets — squarely in the "collapse zone"
- Tool usage inertia applies: agent often calls terminal→read_file→patch in sequence
- Could build transition graph from cerebrum tool history to pre-filter tools per task type
- Toolset grouping already partially addresses this (tools only loaded if toolset enabled)


## Sources

- https://tianpan.co/blog/2026-04-09-tool-selection-problem-agent-tool-routing-at-scale
- https://arxiv.org/abs/2511.14650
- https://openreview.net/forum?id=cd68eYVKuH
- https://arxiv.org/abs/2603.12740
