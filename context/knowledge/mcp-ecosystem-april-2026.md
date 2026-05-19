# mcp-ecosystem-april-2026

*Researched: 2026-04-01 22:52 CDT*

# MCP Ecosystem Snapshot — April 2026

## Specification State
- MCP ecosystem exploded: 84,977 repos matching "mcp server" on GitHub
- FastMCP (★24K by PrefectHQ) is the standard framework, now part of official MCP Python SDK
- Activepieces (★21K) aggregates ~400 MCP servers
- Protocol supports stdio, SSE, and Streamable HTTP transports

## Top MCP Servers by Stars
| Server | Stars | Purpose |
|--------|-------|---------|
| punkpeye/awesome-mcp-servers | 84K | Directory of all MCP servers |
| microsoft/playwright-mcp | 30K | Browser automation |
| github/github-mcp-server | 28K | GitHub integration |
| PrefectHQ/fastmcp | 24K | Framework for building MCP servers |
| activepieces/activepieces | 21K | ~400 MCP servers platform |
| GLips/Figma-Context-MCP | 14K | Figma layout for AI coders |
| googleapis/genai-toolbox | 13K | Database MCP server |
| BeehiveInnovations/pal-mcp-server | 11K | CLI-to-CLI bridge, multi-model |

## Notable New MCP Servers (March 2026)
| Server | Stars | Innovation |
|--------|-------|------------|
| jxnxts/mcp-brasil | 1K | 41 Brazilian public APIs |
| ghostwright/phantom | 906 | Self-evolving AI co-worker |
| DebugBase/glance | 103 | Browser automation for Claude Code |
| Mibayy/token-savior | 166 | 99% token reduction via codebase indexing |
| ourmem/omem | 96 | Shared persistent memory for agents |
| aak204/MCP-Trust-Kit | 62 | Security scanner for MCP servers |
| cookjohn/teammcp | 28 | Multi-agent collaboration via MCP |
| lispking/ferris-search | 31 | Rust-based multi-engine web search |

## Hermes Agent MCP Integration
- `~/.hermes/config.yaml` → `mcp_servers` key
- `tools/mcp_tool.py` handles server lifecycle
- `tools/mcp_oauth.py` handles OAuth authentication
- Supports stdio, SSE, and streamable_http transports
- Background event loop `_mcp_loop` in daemon thread
- MCP >= 1.24.0 supported with fallback to older API

## Key Patterns for SOMA MCP Development
1. Use FastMCP for rapid server development
2. Follow resource vs tool distinction (resources=data, tools=actions)
3. Implement proper error handling without leaking PHI
4. Add authentication layer for any medical data access
5. Use MCP-Trust-Kit to scan for security vulnerabilities


## Sources

- https://github.com/modelcontextprotocol
- https://gofastmcp.com
- https://github.com/PrefectHQ/fastmcp
