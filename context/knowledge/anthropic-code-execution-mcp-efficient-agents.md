# anthropic-code-execution-mcp-efficient-agents

*Researched: 2026-04-11 15:07 CDT*

# Anthropic: Code Execution with MCP for More Efficient Agents

**Date:** November 4, 2025  
**Source:** Anthropic Engineering Blog

## Key Insight
As agents connect to hundreds/thousands of MCP tools, loading all tool definitions into context becomes a bottleneck. Anthropic proposes **code execution with MCP** — instead of direct tool calls consuming context for each definition and result, agents write code to call MCP servers.

## Two Problems Solved
1. **Tool definition overload** — Each MCP tool definition occupies context window space. Thousands of tools = hundreds of thousands of tokens before even reading a request.
2. **Intermediate result token waste** — Large documents flowing through the model multiple times (e.g., a 2-hour meeting transcript = 50K extra tokens processed twice).

## Solution: MCP as Code API
Generate a file tree of all available tools from connected MCP servers:
```
servers/
├── google-drive/
│   ├── getDocument.ts
│   └── index.ts
├── salesforce/
│   ├── updateRecord.ts
│   └── index.ts
```
Agents load only the tools they need and process data in the execution environment before passing results back.

## Relevance to Hermes
Hermes already uses execute_code as a primary tool — this validates our architecture. The pattern of generating code to interact with tools rather than direct tool calls aligns with how Hermes subagents operate. This could inform future MCP integration patterns in Hermes Agent.


## Sources

- https://www.anthropic.com/engineering/code-execution-with-mcp
