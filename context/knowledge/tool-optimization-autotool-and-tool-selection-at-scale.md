# tool-optimization-autotool-and-tool-selection-at-scale

*Researched: 2026-04-12 10:20 CDT*

# Tool Optimization: AutoTool and Tool Selection at Scale

## AutoTool (AAAI 2026, Jia & Li, arXiv:2511.14650)

**Key insight:** "Tool usage inertia" — tool invocations follow predictable sequential patterns. By constructing a directed graph from historical trajectories (nodes=tools, edges=transition probabilities), AutoTool bypasses repeated LLM inference for tool selection.

**Results:** Up to 30% inference cost reduction while maintaining competitive task completion rates. Integrates parameter-level information for refined tool input generation.

**Relevance to Hermes:** We track tool_usage patterns (267 observations at 0.837 confidence). Could build a similar transition graph from our own tool_usage observations to predict next-tool and skip LLM deliberation for common patterns (e.g., read_file → patch → terminal for code fixes).

## The Tool Selection Problem (Tian Pan, Apr 2026)

**Critical stat:** Berkeley Function Calling Leaderboard shows accuracy drops from 43% to 2% when expanding from 4 to 51 tools across domains. Not graceful degradation — catastrophic.

**Three failure modes at scale:**
1. **Token explosion:** 58 tool definitions = ~55,000 tokens baseline per turn (Anthropic data)
2. **Selection accuracy collapse:** Model picks plausible-but-wrong tool, or combines tools incorrectly
3. **Documentation quality variance:** Vague/overlapping descriptions across tools written by different teams

**Layered routing solution:**
1. Static retrieval (RAG-based tool selection): embed tools + query, top-k similarity
2. Semantic routing: classify intent first, then narrow tool space
3. Dynamic tool loading: load tool schemas on-demand based on conversation context

**Relevance:** Hermes has 80+ tools. The tool_intelligence data shows weak tools (knowledge_search 0%, browser_navigate 0%, cached_delegate 0%) alongside proven ones (delegate_parallel 87%, web_extract 90%). A transition-graph approach could pre-route to proven tools and avoid weak ones automatically.


## Sources

- https://arxiv.org/abs/2511.14650
- https://tianpan.co/blog/2026-04-09-tool-selection-problem-agent-tool-routing-at-scale
