# tool-selection-optimization-2026

*Researched: 2026-04-11 23:22 CDT*

# Tool Selection Optimization for LLM Agents (2026)

## The Tool Selection Problem at Scale

**Key finding:** Berkeley Function Calling Leaderboard shows accuracy drops from 43% to 2% on calendar scheduling tasks when tools expand from 4 to 51 across domains. This is not graceful degradation.

### Why Naive Tool Dumping Fails (10-15 tool limit)

1. **Token explosion**: Anthropic testing found 58 tool definitions = ~55,000 tokens. Every agent turn carries baseline overhead of a "short novel" before the user query.
2. **Selection accuracy degradation**: Model rarely says "I don't know which tool." Instead picks plausible-but-wrong tool, combines tools incorrectly, or calls with parameters from a different tool's schema.
3. **Documentation quality variance**: 50 tools inevitably have overlapping, vague descriptions. `send_notification` vs `push_alert` confuses models.

### RAG-Based Tool Selection (Better but Not Enough)

- **Vocabulary mismatch**: User says "reschedule meeting" but tool is `calendar_event_update` — embedding similarity may miss.
- **Static retrieval in dynamic workflows**: Right tool for step 2 depends on step 1's output. Query-only retrieval misses mid-execution tools.
- **Top-k truncation**: Correct tool at position k+1 — model never sees it.
- **Semantic covering attack**: Overlapping generic descriptions consume all top-k slots.

### What Works: Layered Routing (Production Pattern)

1. **Tier 1 — Intent Classification**: Lightweight classifier maps request to domain/tool category. Structured dispatch.
2. **Tier 2 — Conditioned Retrieval**: RAG on the filtered subset, incorporating both original intent AND evolving execution context.
3. **Tier 3 — Dynamic Context**: Only pass relevant tool schemas per step, not all tools.

### Radical Simplification (Vercel d0 Case Study)

Vercel's text-to-SQL agent had 16 specialized tools. They deleted 80%, replaced with single capability: run arbitrary bash commands against file system.

**Results:**
- Success rate: 80% → 100%
- Response time: 274s → 77s (3.5x faster)
- Token usage: -37%
- Steps to complete: -42%

**Key insight**: "Addition by subtraction is real." More tools ≠ better agents.

### Implications for Hermes Agent

1. **Toolset gating already helps** — Hermes groups tools into toolsets. Only enable what's needed per platform.
2. **Dynamic tool pruning** — Consider pruning tools based on task type before each call (our tool_intelligence data supports this).
3. **WEAK TOOLS data confirms** — Our 0% success tools (knowledge_search, browser_navigate, cached_delegate) should be pruned from default sets.
4. **Layered routing opportunity** — Intent classification → toolset selection → schema injection matches Hermes's toolset architecture.

### AutoTool Reference

Li (2026) "AutoTool: efficient tool selection for large language model agents" — cited in arxiv 2603.22862 as relevant work on automated tool selection optimization.


## Sources

- https://tianpan.co/blog/2026-04-09-tool-selection-problem-agent-tool-routing-at-scale
- https://medium.com/@stawils/more-agents-more-tools-worse-results-the-2026-evidence-for-radical-simplification-7bad6c1858a5
- https://arxiv.org/html/2603.22862v2
