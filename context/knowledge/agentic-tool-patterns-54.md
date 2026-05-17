# agentic-tool-patterns-54

*Researched: 2026-04-09 21:12 CDT*

# 54 Patterns for Building Better MCP/Agent Tools

**Source:** Arcade.dev blog (Guru Sattanathan, Renato Byrro, Evan Tahler, 2026-02-09)

## Key Insight
A tool can return the right data and STILL FAIL because the agent couldn't figure out when to call it. "Working" ≠ "agent-usable." Arcade built 8000+ tools across 100+ integrations and distilled patterns.

## The Paradigm Shift
Traditional integration (ESB, workflow engines) had predetermined orchestration. Agent tooling collapses that layer — the agent decides which tool to call, interprets parameters, handles responses, and figures out next steps. Orchestration is now emergent, reconstructed on every invocation.

## Key Patterns (from 8000+ tools of production experience)
1. **Agent-optimized documentation** — Tool descriptions must be written for LLM consumers, not humans. Unclear descriptions = wrong tool selection.
2. **Recovery guidance over error messages** — Instead of dead letter queues, return structured error context that helps the agent retry differently.
3. **Stateful sessions vs stateless messages** — Agent tool calls happen within sessions, not as isolated messages. Design for session continuity.
4. **Non-deterministic routing** — The agent selects tools, not a predetermined flow. Tools must be independently discoverable and composable.

## Relevance to Hermes
Directly applicable to how we write tool schemas. The `description` field in tool schemas is THE most important field for agent performance. Every Hermes tool should be audited against these patterns.

## Sources

- https://blog.arcade.dev/mcp-tool-patterns
