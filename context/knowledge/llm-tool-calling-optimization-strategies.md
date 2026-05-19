# llm-tool-calling-optimization-strategies

*Researched: 2026-04-11 21:05 CDT*

# LLM Tool Calling Optimization Strategies (2025)

## Core Problem
Performance degrades when agents have too many tools. Anthropic research: >10-15 tools = significant performance drop.

## Key Optimization Strategies (from practitioner reports)
1. **Break big tools into smaller ones**: Instead of one "database" tool, have "query", "insert", "update" as separate tools. Improves model accuracy in picking the right one.
2. **Add simple routing rules**: Pre-filter which tools are available per task context. Don't expose all tools to every call.
3. **Use strict schemas**: JSON Schema with required fields, enums, and descriptions. Reduces hallucinated parameters.
4. **Log every tool call**: Build a dataset of successful/failed calls to identify patterns and fine-tune routing.

## Relevance to Hermes Agent
- Hermes's toolset system already implements routing rules (disabled_toolsets filters)
- The tool registry pattern (tools/registry.py) with explicit schemas matches best practices
- The delegation pattern (delegate_task) effectively reduces per-agent tool count to a manageable set
- **Optimization opportunity**: Dynamic tool filtering based on task type could further improve accuracy

## Sources

- https://www.reddit.com/r/LLMDevs/comments/1j4xhjj/strategies_for_optimizing_llm_tool_calling/
