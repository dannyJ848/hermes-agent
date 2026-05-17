# MCP Context Crisis - Code Execution Pattern

*Researched: 2026-04-12 21:03 CDT*

# MCP Context Crisis: Why Direct Tool Loading Fails at Scale

**Date**: April 2026
**Source**: Rick Hightower (Towards AI) + Anthropic Engineering Blog

## Key Insight
As MCP adoption scales to thousands of tools across dozens of servers, two critical problems emerge:
1. **Tool definition overload** — Loading all tool definitions upfront floods the context window with hundreds of thousands of tokens
2. **Intermediate result passthrough** — Data must flow through the model between tool calls, doubling token costs for large documents

## Anthropic's Solution: Code Execution with MCP
Instead of direct tool calls, present MCP servers as **code APIs**. The agent writes code to interact with servers:
- Only loads tools it needs (lazy loading)
- Processes data in the execution environment before returning results to the model
- Generates a file tree of available tools: `servers/google-drive/getDocument.ts`, etc.

## Relevance to Hermes Agent
This validates Hermes's skill-based selective loading approach. Skills act as curated tool subsets, preventing context bloat. The "agent skills vs MCP vs CLI" debate is central to Hermes's architecture.

## Tags
MCP, context-management, tool-loading, Anthropic, agent-architecture


## Sources

- https://medium.com/@richardhightower/is-mcp-dead-the-context-crisis-that-broke-naive-tool-loading-agent-skills-vs-mcp-vs-cli-cc7696eba0ba
- https://www.anthropic.com/engineering/code-execution-with-mcp
