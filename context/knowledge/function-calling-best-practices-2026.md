# function-calling-best-practices-2026

*Researched: 2026-04-07 10:29 CDT*

# Function Calling LLM Best Practices 2026 (Mar 2026)

**Source:** AI Agents Plus, "Function Calling LLM Best Practices: Complete 2026 Guide"

## Key Practices
1. **Clear tool descriptions** — Write descriptions as if teaching a junior dev; include examples, edge cases, and when NOT to use
2. **Structured parameter schemas** — Use JSON Schema with enums, defaults, and constraints to reduce hallucinated parameters
3. **Error handling in tool results** — Return structured errors, not unstructured text; let the model retry with context
4. **Parallel tool calling** — Design tools to be stateless and independent so the model can call multiple in one turn
5. **Tool selection monitoring** — Track which tools are called, success rates, and latency per tool
6. **Token budgeting** — Each tool schema costs tokens in the prompt; keep schemas minimal but complete
7. **Fallback strategies** — When a tool call fails, provide enough context in the error for graceful degradation

## Hermes Agent Relevance
- Hermes already uses registry-based tool schemas — validates this pattern
- Token budgeting is critical for Hermes' large toolset (150+ tools)
- Error handling pattern matches Hermes' JSON error return convention
- Parallel tool calling aligns with delegate_parallel architecture

## Sources

- https://www.ai-agentsplus.com/blog/function-calling-llm-best-practices-2026-march
