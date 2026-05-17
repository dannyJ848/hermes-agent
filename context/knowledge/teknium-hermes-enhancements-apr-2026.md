# teknium-hermes-enhancements-apr-2026

*Researched: 2026-04-05 14:27 CDT*

# Teknium Hermes Enhancement Analysis (Apr 2026)

## Source
20 Teknium tweets (Mar 24 - Apr 5, 2026) + GitHub release notes v0.4.0 through v0.7.0 + 20 post-v0.7 commits.

## Key Findings

### Already in Upstream (Updated To)
- **v0.7.0**: Pluggable memory providers, credential pool rotation, Camofox, ACP protocol, secret exfiltration blocking, gateway hardening (168 PRs, 46 issues)
- **v0.6.0**: Multi-instance profiles, MCP server mode, Docker container, fallback provider chains, Feishu/WeCom, Telegram webhook mode, Exa search backend
- **v0.5.0**: HuggingFace provider, Telegram Private Chat Topics, Modal SDK, plugin lifecycle hooks, GPT tool-use enforcement
- **v0.4.0**: OpenAI-compatible API server, 6 messaging adapters, @ context references, MCP CLI, prompt caching, streaming by default

### Features to Enable (Already in Codebase)
1. **MCP Server Mode**: `hermes mcp serve` exposes Evey to Claude Desktop, Cursor, VS Code
2. **Exa Search**: Add `EXA_API_KEY` to .env for alternative search backend (fallback when Firecrawl blocks sites)
3. **ACP Protocol**: Already loaded, enables editor integrations to register MCP servers
4. **Credential Pools**: Native rotation for same-provider API keys (we do this manually)
5. **Fallback Provider Chains**: Configure `fallback_providers` in config.yaml

### Our Custom Additions (Beyond Upstream)
- Cerebrum 4-tier biomimetic memory
- Firecrawl Fusion browser provider + web_interact tool
- Evey Tool Intelligence plugin
- Evey Eyes perception plugin
- Brain daemon + distillation bridge
- Self-awareness module
- Context reservoir paging

### X/Twitter Access Status
- Cookie API: AUTH EXPIRED (cookies stale)
- Firecrawl: BLOCKS X/Twitter (policy)
- Browserbase: CDP connection failing
- Local browser: No X cookies (headless Chrome not logged in)
- Need: Fresh cookies from Danny's Chrome session, OR Browserbase working CDP


## Sources

- https://github.com/NousResearch/hermes-agent/releases
- https://github.com/NousResearch/hermes-agent/blob/main/RELEASE_v0.5.0.md
- https://github.com/NousResearch/hermes-agent/blob/main/RELEASE_v0.6.0.md
