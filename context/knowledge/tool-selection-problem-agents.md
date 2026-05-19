# tool-selection-problem-agents

*Researched: 2026-04-12 08:03 CDT*

# The Tool Selection Problem: Agent Tool Routing at Scale

**Source:** Tian Pan (April 9, 2026) — tianpan.co

## Key Findings

### Accuracy Collapse at Scale
- Berkeley Function Calling Leaderboard: accuracy drops from **43% to 2%** on calendar tasks when tools expand from 4→51 across domains
- This is not graceful degradation — it's catastrophic

### Why Naive Tool Dumping Fails
1. **Token explosion**: 58 tool definitions ≈ 55,000 tokens (Anthropic internal testing). Every agent turn carries baseline overhead of "summarizing a short novel" before user query.
2. **Selection accuracy degradation**: Model doesn't say "I don't know" — picks wrong tool with valid-format but semantically incorrect calls
3. **Documentation quality variance**: Tools like `send_notification` vs `push_alert` with similar descriptions confuse models

### RAG-Based Tool Selection (First Fix)
- Embed tool descriptions + user query, pass top-k to model
- Cuts token usage and narrows selection space
- But pure embedding retrieval misses behavioral differences not captured in description text

### Layered Approaches
- Static retrieval → semantic routing → hierarchical tool organization
- Key insight: tool routing is a **retrieval + reasoning** hybrid problem, not pure similarity

## Relevance to Hermes Agent
- Hermes has 50+ tools with overlapping descriptions (browser_navigate vs web_extract vs web_research)
- The `tool_planner.py` subsystem already implements hierarchical planning
- Optimization tips domain has low coverage (0.060) despite being highest explore priority
- Consider: semantic tool clustering to reduce selection space at inference time

## Related Papers
- **ToolTree** (arXiv 2603.12740): Dual-granularity tool planning improving efficiency
- **AutoTool** (arXiv 2511.14650): Structured representation traversal for minimal LLM inference
- **Ant Colony Optimization for LLM MAS routing** (OpenReview): Bio-inspired traffic allocation


## Sources

- https://tianpan.co/blog/2026-04-09-tool-selection-problem-agent-tool-routing-at-scale
- https://arxiv.org/abs/2603.12740
- https://arxiv.org/abs/2511.14650
