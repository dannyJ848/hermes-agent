---
name: teammcp-setup
description: Deploy TeamMCP (cookjohn/teammcp) for MCP-native multi-agent squad coordination. SQLite+SSE, replaces file-based coordination boards.
version: 1.0
category: autonomous-ai-agents
---

# TeamMCP Multi-Agent Setup

Deploy cookjohn/teammcp for real-time squad coordination between Hermes agent profiles.

## Prerequisites

- Node.js >= 18
- `AGENTS_BASE_DIR` path (any dir, used for process management)
- Hermes agent profiles already created (`hermes profile list`)

## Step 1: Install

```bash
cd /tmp
git clone --depth 1 https://github.com/cookjohn/teammcp.git
cd teammcp/server && npm install
cd ../mcp-client && npm install
```

## Step 2: Start Server

```bash
export AGENTS_BASE_DIR=/tmp/soma-agents
mkdir -p $AGENTS_BASE_DIR
node /tmp/teammcp/server/index.mjs
# Server runs on http://localhost:3100
```

Verify: `curl http://localhost:3100/api/health` should return `{"status":"ok",...}`

## Step 3: Register Agents

```bash
# Register each agent (one-time, persists in SQLite)
curl -s -X POST http://localhost:3100/api/register \
  -H "Content-Type: application/json" \
  -d '{"name": "soma-coder", "role": "Developer"}'

curl -s -X POST http://localhost:3100/api/register \
  -H "Content-Type: application/json" \
  -d '{"name": "soma-researcher", "role": "Researcher"}'

curl -s -X POST http://localhost:3100/api/register \
  -H "Content-Type: application/json" \
  -d '{"name": "soma-tester", "role": "QA"}'
```

**CRITICAL**: The response truncates API keys! To get full keys, query SQLite directly:

```bash
node -e "
const Database = require('/tmp/teammcp/server/node_modules/better-sqlite3');
const db = new Database('/tmp/teammcp/data/teammcp.db', {readonly: true});
const agents = db.prepare('SELECT name, api_key FROM agents').all();
agents.forEach(a => console.log(a.name + ' -> ' + a.api_key));
db.close();
"
```

Save keys to `/tmp/squad-team-keys.env`.

## Step 4: Create Channel

```bash
# NOTE: Requires BOTH "id" and "type" fields (not just "name")
curl -s -X POST http://localhost:3100/api/channels \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <FULL_API_KEY>" \
  -d '{"id":"squad-general","type":"group","name":"Squad General"}'
```

## Step 5: Send Messages

```bash
# Endpoint is /api/send (NOT /api/messages)
curl -s -X POST http://localhost:3100/api/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <FULL_API_KEY>" \
  -d '{"channel":"squad-general","content":"Agent online."}'
```

## Step 6: Make Persistent

Create launch script:
```bash
cat > /tmp/teammcp/start-teammcp.sh << 'EOF'
#!/bin/bash
export AGENTS_BASE_DIR=/tmp/soma-agents
export TEAMMCP_PORT=3100
cd /tmp/teammcp
exec node server/index.mjs
EOF
chmod +x /tmp/teammcp/start-teammcp.sh
```

Add to tmux or launchd for persistence across reboots.

## Pitfalls

| Issue | Fix |
|-------|-----|
| API keys truncated in response | Query SQLite DB directly (`/tmp/teammcp/data/teammcp.db`) |
| `{"error":"id and type are required"}` | POST /api/channels needs both `id` and `type` fields |
| `{"error":"Not found"}` on `/api/messages` | Use `/api/send` instead (not `/api/messages`) |
| `{"error":"Unauthorized"}` | Use `Authorization: Bearer <FULL_KEY>` header (not `X-API-Key`) |
| `setup.sh` hangs | Install server + mcp-client manually with separate `npm install` commands |
| Channel members "Not found" | Skip membership API — just send messages to the channel, agents auto-join |
| Re-registration returns same key | Safe to re-register — returns existing agent + same key |

## Key URLs

- Server: `http://localhost:3100`
- Health: `GET /api/health`
- Dashboard: `http://localhost:3100` (web UI)
- Messages: `POST /api/send`
- Channels: `POST /api/channels`
- Register: `POST /api/register`
- SSE stream: `GET /sse?key=<API_KEY>`

## Architecture

```
soma-coder ──MCP stdio──> TeamMCP Server ──HTTP──> Web Dashboard
                                │
                          SQLite (WAL mode)
                          agents | channels | messages
                          tasks | read_status | FTS5

soma-researcher ──MCP stdio──> ┘
soma-tester ──MCP stdio──> ┘
```
