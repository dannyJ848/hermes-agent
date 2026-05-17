# LLM tool-use optimization patterns 2025

*Researched: 2026-04-17 21:06 CDT*

# LLM Tool-Use & Structured Generation Patterns (2025)

**Source:** Zylos Research synthesis, Jan 2025

## Key Insights

### 1. Programmatic Tool Calling (Anthropic Pattern)
Instead of the LLM calling tools one-by-one through inference, Claude writes a **Python script** that orchestrates the workflow programmatically. Results from prior tool calls are processed by the script, not appended to context.
- **37% token reduction**
- **19+ fewer inference passes**
- Tool results don't bloat context window

### 2. Constrained Decoding is Production-Ready
Three libraries now compete for grammar-guaranteed LLM output:
- **Outlines**: FSM-based, 97% success rate, 0.4% hallucination
- **XGrammar**: Pushdown automata for complex grammars
- **llguidance**: 50μs CPU/token — fastest option

For self-hosted models, constrained decoding eliminates structured output failures entirely.

### 3. Hybrid Orchestration Pattern
Production agents should combine **ReAct + Planning + Reflection** — not pick one:
- ReAct: fast, flexible for simple queries
- Planning: structured multi-step for complex tasks
- Reflection: self-critique for quality assurance

### 4. Output Token Optimization is King
- Output tokens cost ~4x input tokens
- 50% output token reduction → 50% latency reduction
- "Not every problem needs an LLM call"

### 5. Key 2025 Trends
- Programmatic tool orchestration (not just sequential function calls)
- Multi-agent over single general agents
- Tool use is now commodity across all providers
- Coding agents breakout year (Claude Code, GPT Codex)

## Actionable Takeaways for Hermes
1. Consider programmatic tool calling: batch related tool calls into a Python script rather than sequential inference passes
2. Use constrained decoding for self-hosted models (Outlines) to guarantee tool call format
3. Combine ReAct+Planning+Reflection rather than choosing one pattern
4. Audit output token usage — this is where cost and latency hide

## Sources

- https://zylos.ai/research/llm-tool-use-patterns-2025
