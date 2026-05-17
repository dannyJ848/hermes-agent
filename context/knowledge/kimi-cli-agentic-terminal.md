# kimi-cli-agentic-terminal

*Researched: 2026-03-31 22:38 CDT*

# Kimi CLI: Open-Source Agentic Coding Terminal

## Key Insight
kimi-cli is Moonshot AI's answer to Claude Code -- an open-source terminal-based coding agent. It's a direct competitor/peer to Claude Code, Codex CLI, and Hermes-style agents.

## Architecture & Features
- **Language**: Python (uv-based)
- **Shell Integration**: Ctrl-X switches between agent mode and raw shell
- **VS Code Extension**: Built-in IDE integration
- **ACP Support**: Agent Client Protocol for Zed/JetBrains integration
- **Zsh Plugin**: oh-my-zsh compatible, Ctrl-X to toggle agent mode
- **MCP Support**: Full Model Context Protocol tool integration
  - `kimi mcp add --transport http <server>` (streamable HTTP)
  - `kimi mcp add --transport stdio <server>` (stdio)
  - OAuth authorization support
  - Ad-hoc config files in standard MCP format
- **Kosong**: LLM abstraction layer for agent applications (separate package)
- **Skills System**: `.agents/skills` directory (similar to Hermes)
- **Web UI**: Built-in web interface

## Agentic Design Patterns
1. **Shell-Agent Hybrid**: Seamless toggle between shell and agent modes
2. **Multi-IDE Support**: ACP protocol for any compatible editor
3. **MCP-First**: External tools via MCP, not hard-coded integrations
4. **Skill-Based**: Skills in `.agents/skills` directory
5. **SDK**: Separate kimi-agent-sdk for programmatic access

## Relevance to Hermes
- MCP support pattern matches our approach
- Shell-agent hybrid is the dominant paradigm (Hermes does this too)
- Skills directory structure is very similar to ours
- Open-source means we can study their agent loop implementation
- Kosong abstraction layer could inspire our delegation plugin

## Source
- https://github.com/MoonshotAI/kimi-cli (7.5k stars, Apache-2.0)


## Sources

- https://github.com/MoonshotAI/kimi-cli
