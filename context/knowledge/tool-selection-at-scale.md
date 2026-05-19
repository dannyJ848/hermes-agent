# tool-selection-at-scale

*Researched: 2026-04-12 06:41 CDT*

# Tool Selection Problem at Scale in LLM Agents

**Source:** Tian Pan (April 2026), Berkeley Function Calling Leaderboard, Anthropic internal testing

## Core Finding
Agent tool selection accuracy collapses catastrophically as tool count grows:
- 4 tools → 43% accuracy on calendar scheduling
- 51 tools → 2% accuracy (same task)
- This is NOT gradual — it's a phase transition

## Why It Breaks
1. **Token overhead:** 58 tool definitions = ~55K tokens baseline per turn
2. **Hallucinated tool calls:** Model picks wrong tool with valid-format parameters
3. **Description collision:** Tools with overlapping descriptions (send_notification vs push_alert) cause systematic confusion

## Mitigation Strategies
- RAG-based tool retrieval (embed descriptions → top-k selection)
- Layered routing: toolset filter → semantic retrieval → behavioral matching
- Precise, non-overlapping tool descriptions
- Two-stage selection for 50+ tool systems

## Relevance to Hermes
Hermes has 60+ tools. The toolset system provides first-level filtering. Schema descriptions are already requirement-gated. Opportunity: add semantic similarity layer for ambiguous tool selection scenarios.


## Sources

- https://tianpan.co/blog/2026-04-09-tool-selection-problem-agent-tool-routing-at-scale
- https://www.statsig.com/perspectives/tool-calling-optimization
