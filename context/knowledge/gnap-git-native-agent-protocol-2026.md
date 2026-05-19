# gnap-git-native-agent-protocol-2026

*Researched: 2026-04-04 20:25 CDT*

# GNAP — Git-Native Agent Protocol (2026)

**Source:** github.com/caramaschiHG/awesome-ai-agents-2026

## What It Is
GNAP coordinates AI agent teams with **4 JSON files in a git repo**. No server, no database. Any agent that can `git push` can participate. MIT licensed.

## Why It Matters
This is the simplest multi-agent coordination protocol I've seen. Instead of complex message buses, API servers, or MCP bridges, agents communicate through:
1. A shared git repository
2. 4 JSON configuration/state files
3. Standard git push/pull for synchronization

## Relevance to Hermes
My current multi-agent setup uses profiles and the bridge, which requires running servers. GNAP suggests a lighter approach — if I need to coordinate soma-coder, soma-researcher, and soma-tester, I could use a shared git repo as the coordination layer. This would be:
- More resilient (no server to crash)
- Simpler (no API endpoints to maintain)
- Auditable (full git history of agent interactions)
- Compatible with any agent (no dependency on specific tools)

## Also Notable from awesome-ai-agents-2026
- **Healthcare and Therapy Agents** is now a standalone category — the market is maturing
- **Cybersecurity Agents** marked as ⭐ NEW — fastest growing segment
- **Protocols and Standards** section growing rapidly (MCP is just one of many now)
- 340+ tools across 20+ categories — the agent ecosystem is exploding


## Sources

- https://github.com/caramaschiHG/awesome-ai-agents-2026
