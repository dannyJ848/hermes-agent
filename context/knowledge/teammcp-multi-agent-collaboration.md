# teammcp-multi-agent-collaboration

*Researched: 2026-04-01 22:51 CDT*

# TeamMCP — MCP-Native Multi-Agent Collaboration

**Source:** [cookjohn/teammcp](https://github.com/cookjohn/teammcp) (★28, MIT License)

## Overview
A lightweight collaboration server that gives AI agent teams real-time communication via MCP. Replaces orchestration (centralized control) with **collaboration** (autonomous agents communicating naturally).

## Architecture
```
AI Agent (Claude Code) ──MCP stdio──> TeamMCP Server ──HTTP──> Web Dashboard
                                           │
                                     SQLite (WAL mode)
                                     agents | channels | messages
                                     tasks | read_status | FTS5
```

## Key Design Decisions

### Orchestration vs Collaboration
| Approach | CrewAI/AutoGen/LangGraph | TeamMCP |
|----------|--------------------------|---------|
| Model | Temporary functions | Persistent processes |
| Human | Special flag/proxy | Equal participant |
| Dependencies | Heavy ecosystem | 1 npm package |
| Protocol | Proprietary | MCP open standard |
| Control | Central controller | Self-organized |

### Channel Types
- **group**: Open channels (#general, #dev)
- **dm**: Direct messages between two agents
- **topic**: Subscription-based channels (#design, #deploy, #bugs)

### API Design
- `POST /api/register` — Register agent with name + role
- `POST /api/send` — Send message to channel or DM
- `GET /api/events` — SSE real-time push
- `GET /api/history` — Message history with FTS5 full-text search
- Task management: assign, update status, claim

## Metrics
| Metric | Value |
|--------|-------|
| npm dependencies | 1 (better-sqlite3) |
| MCP tools | 20 |
| HTTP endpoints | 27 |
| Concurrent agents tested | 14 |
| Uptime | 20+ hours |
| Messages | 1,000+ |
| Search latency | 90-99ms |

## Integration for SOMA Squad

### Current SOMA Setup
- 3 Hermes agents in tmux (coder, researcher, tester)
- Coordination via `/tmp/squad-board.json` file polling
- No real-time communication between agents

### Proposed TeamMCP Integration
```yaml
# In each agent's config.yaml
mcp_servers:
  teammcp:
    command: node
    args: ["/path/to/teammcp/server/index.js"]
    env:
      TEAMMCP_API_KEY: <per-agent-key>
```

### Channel Structure
- `#soma-dev` — General development coordination
- `#medical-research` — Research findings shared from soma-researcher
- `#build-status` — Build/test results from soma-tester
- `#code-review` — Code review requests from soma-coder
- DM: researcher → coder for specific implementation requests

### Benefits over squad-board.json
1. **Real-time**: SSE push instead of file polling
2. **Searchable**: FTS5 full-text search across all messages
3. **Structured**: Proper channel/DM/message model
4. **Web dashboard**: Visual monitoring of agent coordination
5. **Task management**: Built-in task assignment and tracking


## Sources

- https://github.com/cookjohn/teammcp
