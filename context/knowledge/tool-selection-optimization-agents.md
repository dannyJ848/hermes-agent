# tool-selection-optimization-agents

*Researched: 2026-04-11 23:31 CDT*

# Tool Selection Optimization for AI Agents (2026)

## The Core Problem
When LLM agents scale past ~15 tools, accuracy collapses. Berkeley Function Calling Leaderboard found accuracy dropping from 43% to 2% on calendar scheduling tasks when tools expanded from 4 to 51 across multiple domains.

## Failure Modes at Scale
1. **Token explosion**: 58 tool definitions ≈ 55,000 tokens. Every agent turn carries baseline overhead equivalent to summarizing a short novel.
2. **Selection accuracy degradation**: Model picks plausible-sounding wrong tool, combines multiple tools incorrectly, or calls tools with parameters from different schemas. Response format is often still valid — just semantically incorrect.
3. **Documentation quality variance**: Tools with overlapping, vague descriptions (e.g., `send_notification` vs `push_alert`) confuse models.

## RAG-Based Tool Selection (First Fix)
Embed tool descriptions + user query → top-k similar tools → pass only those. Better than static inclusion but has failure modes:
- **Vocabulary mismatch**: "reschedule the meeting" ≠ `calendar_event_update` in embedding space
- **Static retrieval in dynamic workflows**: Right tool for step 2 depends on step 1 output
- **Top-k truncation**: Correct tool at position k+1, model never sees it
- **Semantic covering attack**: Overlapping generic descriptions consume all top-k slots

## What Actually Works: Layered Routing
1. **Tier 1: Intent classification** — lightweight classifier maps request to domain/tool category (structured dispatch)
2. **Tier 2: Conditioned retrieval** — RAG within the selected category, incorporating both original intent and evolving execution context
3. **Tier 3: Model selection** — LLM picks from narrowed candidate set

## Key Insight for Hermes
Hermes has 50+ tools across multiple toolsets. The toolset grouping already acts as Tier 1 routing. The gap is Tier 2 — conditioned retrieval that incorporates execution context (not just user query) into tool relevance scoring. This could significantly improve tool dispatch accuracy.

## Source
- Tian Pan, "The Tool Selection Problem" (April 2026) — tianpan.co
- Berkeley Function Calling Leaderboard benchmarks
- Anthropic internal testing on tool definition token costs


## Sources

- https://tianpan.co/blog/2026-04-09-tool-selection-problem-agent-tool-routing-at-scale
