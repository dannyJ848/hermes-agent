# mcp-agent-workflow-patterns

*Researched: 2026-04-03 21:03 CDT*

# MCP-Agent: Workflow Patterns for MCP-Based Agents

**Source:** lastmile-ai
**Repo:** github.com/lastmile-ai/mcp-agent (8,196 stars, 816 forks)
**Language:** Python

## What It Does
- Build effective agents using Model Context Protocol with composable workflow patterns
- Patterns: map-reduce, orchestrator, evaluator-optimizer, router
- Connects LLMs to MCP servers in simple, composable ways

## Key Features
- Workflow patterns inspired by Google's agent design paper
- MCP server integration (connects to any MCP-compatible tool)
- Composable agent architectures
- Python-based, pip installable

## Relevance to SOMA / Hermes
- Hermes already uses MCP extensively — these patterns could improve agent orchestration
- Map-reduce pattern useful for parallel medical data processing
- Evaluator-optimizer pattern useful for medical content quality assurance
- Router pattern useful for bilingual query routing (EN/ES)

## Integration Notes
- `pip install mcp-agent`
- Works with existing MCP servers (BioMCP, FHIR, etc.)
- Could enhance Hermes's delegation architecture


## Sources

- https://github.com/lastmile-ai/mcp-agent
- https://www.analyticsvidhya.com/blog/2026/02/top-mcp-servers/
