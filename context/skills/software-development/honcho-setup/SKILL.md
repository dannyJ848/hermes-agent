---
name: honcho-setup
version: 1.0.0
description: Complete guide for deploying and configuring self-hosted Honcho (plastic-labs/honcho) with GLM-5.1 dialectic and Ollama embeddings on macOS.
triggers:
  - deploy honcho
  - setup honcho
  - restart honcho
---

# Honcho Self-Hosted Setup

## Prerequisites
- Docker Desktop (running)
- Ollama with nomic-embed-text pulled
- Z.AI API key (GLM-5.1 coding plan)

## Quick Start
```bash
/tmp/honcho/start.sh
```

## Full Deployment (if starting fresh)

### 1. Clone & Configure
```bash
git clone --depth 1 https://github.com/plastic-labs/honcho.git /tmp/honcho
```

### 2. Critical Patches (1536→768 for nomic-embed-text)
All files referencing `Vector(1536)` must be changed to `Vector(768)`:
- `src/models.py` (2 locations)
- `src/embedding_client.py` (3 locations: output_dimensionality)
- `src/config.py` (2 locations: default value)
- `src/dreamer/surprisal.py` (1 comment)
- `src/vector_store/lancedb.py` (1 comment)
- `migrations/versions/a1b2c3d4e5f6_initial_schema.py`
- `migrations/versions/917195d9p5e9_add_messageembedding_table.py`
- `migrations/versions/119a52b73c60_support_external_embeddings.py` (2 locations)

```bash
cd /tmp/honcho
find src/ migrations/ -name "*.py" -exec sed -i '' 's/Vector(1536)/Vector(768)/g' {} +
find src/ -name "*.py" -exec sed -i '' 's/"output_dimensionality": 1536/"output_dimensionality": 768/g' {} +
sed -i '' 's/default=1536/default=768/g' src/config.py
sed -i '' 's/] = 1536/] = 768/g' src/config.py
```

### 3. Add `openai_compatible` to SupportedProviders
`src/utils/types.py` has the provider Literal. Add `openai_compatible` so it's valid:
```python
# In src/utils/types.py:
SupportedProviders = Literal["anthropic", "openai", "google", "groq", "custom", "vllm", "openai_compatible"]
```
NOTE: For LLM providers (deriver, dialectic, summary, dream), use `custom` — which maps to the `AsyncOpenAI` client using `OPENAI_COMPATIBLE_API_KEY` + `OPENAI_COMPATIBLE_BASE_URL`. The `openai_compatible` string is only needed for the **embedding** provider which has its own Literal type in config.py.

### 4. Patch embedding_client.py for Ollama
The `openai_compatible` provider block in embedding_client.py needs custom env vars:
```python
# In the "openai_compatible" elif block:
api_key = os.environ.get("EMBEDDING_API_KEY") or "ollama"
base_url = os.environ.get("EMBEDDING_BASE_URL") or "http://localhost:11434/v1"
self.model = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
```
Also add `import os` at top if not present.

### 5. docker-compose.yml (minimal 4-container setup)
```yaml
services:
  database:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: honcho
      POSTGRES_PASSWORD: honcho_secret
      POSTGRES_DB: honcho
    ports: ["5433:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U honcho"]
      interval: 5s

  redis:
    image: redis:7-alpine
    ports: ["6380:6379"]
    volumes: [redisdata:/data]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  api:
    build: { context: ., dockerfile: Dockerfile }
    entrypoint: ["sh", "docker/entrypoint.sh"]
    ports: ["8000:8000"]
    volumes:
      - ./.env:/app/.env:ro    # CRITICAL: must mount .env for pydantic-settings
    depends_on:
      database: { condition: service_healthy }
      redis: { condition: service_healthy }
    extra_hosts: ["host.docker.internal:host-gateway"]
    environment:
      - DB_CONNECTION_URI=postgresql+psycopg://honcho:honcho_secret@database:5432/honcho
      - CACHE_URL=redis://redis:6379/0

  deriver:
    build: { context: ., dockerfile: Dockerfile }
    entrypoint: ["sh", "-c", "python -m src.deriver"]  # NOT "honcho.deriver"!
    volumes:
      - ./.env:/app/.env:ro
    depends_on:
      database: { condition: service_healthy }
      redis: { condition: service_healthy }
    extra_hosts: ["host.docker.internal:host-gateway"]
    environment:
      - DB_CONNECTION_URI=postgresql+psycopg://honcho:honcho_secret@database:5432/honcho
      - CACHE_URL=redis://redis:6379/0
```

### 6. .env Configuration
CRITICAL PITFALLS:
- **Embedding provider** = `openai_compatible` (has its own Literal in config.py L215)
- **LLM providers** = `custom` (deriver, dialectic, summary, dream — maps to OPENAI_COMPATIBLE_* keys)
- **Vector store type** = `pgvector` (NOT `postgres` — will get Literal validation error)
- **Dialectic env vars** use LOWERCASE `validation_alias` names, not uppercase Python field names:
  - `DIALECTIC_LEVELS__minimal__provider=custom` (not `PROVIDER=custom`)
  - `DIALECTIC_LEVELS__minimal__thinking_budget_tokens=0` (not `THINKING_BUDGET_TOKENS=0`)
  - `DIALECTIC_LEVELS__minimal__model=glm-5.1` (not `MODEL=glm-5.1`)
  - `DIALECTIC_LEVELS__minimal__max_tool_iterations=1` (not `MAX_TOOL_ITERATIONS=1`)
- **ALL 5 dialectic levels** required: minimal, low, medium, high, max. Each needs provider, model, thinking_budget_tokens, max_tool_iterations
- **thinking_budget_tokens is REQUIRED** (no default). Must be 0 for non-Anthropic providers. For Anthropic, must be >= 1024.
- **.env must be mounted** into container as volume (`./.env:/app/.env:ro`) — pydantic-settings DotEnvSettingsSource reads from /app/.env inside container
- **EMBEDDING_BASE_URL** must use `host.docker.internal` not `localhost` (container can't reach host localhost)

Key .env settings:
```
LLM_OPENAI_COMPATIBLE_API_KEY=<Z.AI key>
LLM_OPENAI_COMPATIBLE_BASE_URL=https://openrouter.ai/v1
LLM_EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_BASE_URL=http://host.docker.internal:11434/v1
EMBEDDING_MODEL=nomic-embed-text
DERIVER_PROVIDER=custom
DERIVER_MODEL=glm-5.1
SUMMARY_PROVIDER=custom
DREAM_PROVIDER=custom
VECTOR_STORE_TYPE=pgvector
VECTOR_STORE_DIMENSIONS=768
DIALECTIC_LEVELS__minimal__provider=custom
DIALECTIC_LEVELS__minimal__thinking_budget_tokens=0
DIALECTIC_LEVELS__minimal__model=glm-5.1
DIALECTIC_LEVELS__minimal__max_tool_iterations=1
# ... same pattern for low, medium, high, max
```

### 7. Build & Run
```bash
cd /tmp/honcho
docker compose down -v  # Clean slate
docker compose build api deriver
docker compose up -d
sleep 15
# Verify API started
docker logs honcho-api-1 2>&1 | tail -5
# Should see: "Uvicorn running on http://0.0.0.0:8000"
```

### 8. Create Workspace & Peers
```bash
curl -s -X POST http://localhost:8000/v3/workspaces -H "Content-Type: application/json" -d '{"name": "hermes"}'
curl -s -X POST http://localhost:8000/v3/workspaces/hermes/peers -H "Content-Type: application/json" -d '{"name": "evey", "metadata": {"type": "agent"}}'
curl -s -X POST http://localhost:8000/v3/workspaces/hermes/peers -H "Content-Type: application/json" -d '{"name": "danny", "metadata": {"type": "user"}}'
```

### 9. Verify
```bash
curl -sf http://localhost:8000/openapi.json | python3 -c "import sys,json; print(f'{len(json.load(sys.stdin)[\"paths\"])} routes')"
# Should show: 36 routes
```

## Ports
- 8000: Honcho API
- 5433: Postgres+pgvector (mapped from 5432)
- 6380: Redis (mapped from 6379)

## Hermes Restart Procedure
The `hermes` CLI requires a TTY (prompt_toolkit crashes without it). Use gateway mode instead:
```bash
# Kill existing
pkill -f "hermes_cli.main"
sleep 2
# Start gateway (non-interactive, survives terminal close)
cd ~/hermes-agent && source venv/bin/activate
nohup python -m hermes_cli.main gateway run --replace > /tmp/hermes-gateway.log 2>&1 &
```
Plugins are loaded **per-agent-spawn** (each conversation turn), NOT at gateway startup. So new plugins in `~/.hermes/plugins/` are picked up automatically on the next message — no restart needed for plugin discovery. Gateway restart only needed for config.yaml changes.

## Troubleshooting
- **PendingRollbackError / vector dimension mismatch**: Source code patches are NOT enough. Alembic migration files in `migrations/versions/` also hardcode dimensions. Must patch BOTH `src/` AND `migrations/`, then `docker compose down -v` (remove volumes!) and rebuild: `docker compose build --no-cache api deriver`. Just restarting keeps the old DB schema.
- **PendingRollbackError**: DB column dimension mismatch (rebuild with correct 768 patches)
- **Missing client for Summary: google**: Set SUMMARY_PROVIDER=custom
- **Missing configuration for reasoning levels**: Must define ALL 5 levels (minimal, low, medium, high, max)
- **MAX_OUTPUT_TOKENS > THINKING_BUDGET_TOKENS**: Set DIALECTIC_MAX_OUTPUT_TOKENS=32768 (higher than max thinking budget)
- **Honcho unreachable**: Run /tmp/honcho/start.sh (starts Docker + Ollama)
- **ValidationError: "thinking_budget_tokens Field required"**: Dialectic level env vars use LOWERCASE validation_alias names. Must be `DIALECTIC_LEVELS__minimal__thinking_budget_tokens=0`, NOT `THINKING_BUDGET_TOKENS=0`. Same for provider→provider, model→model, max_tool_iterations→max_tool_iterations.
- **ValidationError: "VECTOR_STORE_TYPE Input should be 'pgvector'"**: Use `VECTOR_STORE_TYPE=pgvector`, NOT `postgres`.
- **ModuleNotFoundError: No module named 'honcho'**: Deriver entrypoint must be `python -m src.deriver`, NOT `python -m honcho.deriver`.
- **Container crashes on startup (no env vars loaded)**: The .env file must be mounted as a volume into the container: `volumes: - ./.env:/app/.env:ro`. Pydantic-settings DotEnvSettingsSource reads from the working directory's .env file INSIDE the container.
- **"Literal error" for provider=openai_compatible**: The `SupportedProviders` type in `src/utils/types.py` must include `"openai_compatible"`. For LLM providers, use `custom` instead (maps to OPENAI_COMPATIBLE_API_KEY/BASE_URL).

## Hermes Plugin
Plugin at ~/.hermes/plugins/evey-honcho/ provides 5 tools:
- honcho_store, honcho_recall, honcho_search, honcho_offload, honcho_status

## API Routes (v3, NOT v1)
Honcho uses `/v3/` prefixed routes, NOT `/api/v1/`. There is NO `/health` endpoint.
Key routes:
- `GET /v3/workspaces` — list workspaces (use as health check)
- `GET /v3/workspaces/{id}` — get workspace
- `GET /v3/workspaces/{id}/peers` — list peers
- `GET /v3/workspaces/{id}/peers/{peer_id}/sessions` — list sessions
- `POST /v3/workspaces/{id}/peers/{peer_id}/sessions` — create session with messages
- `POST /v3/workspaces/{id}/peers/{peer_id}/search` — semantic search memories
- `GET /v3/workspaces/{id}/peers/{peer_id}/card` — peer card (dialectic user model)
- Workspace name: "hermes", Peers: "evey" (agent), "danny" (user)

Common mistake: code written against `/api/v1/` or `/sessions/{id}/messages` will 404.
Always use `/v3/workspaces/{workspace}/peers/{peer}/...` paths.

## Cerebrum Integration
Cerebrum (plugins/memory/cerebrum/) uses Honcho as its dialectic layer (Layer 4).
Health check: `GET /v3/workspaces` (in `provider.py:_check_honcho()`)
Sync turns: `POST /v3/workspaces/hermes/peers/evey/sessions` (in `provider.py:_honcho_sync_turn()`)
Config: `memory.provider: cerebrum` in config.yaml enables cerebrum which auto-connects to Honcho.
If Honcho is down, cerebrum degrades gracefully (4 layers still work, just no dialectic).

## Memory Compression Cron
Runs daily at 4am (after dojo at 3am).
Job ID: ece3733a111c
Script: /tmp/honcho/memory_compression.py

## Cerebrum Bulk Migration
Migration script at `/tmp/migrate_to_cerebrum.py` — imports MEMORY.md, USER.md, knowledge findings, and Honcho memories into cerebrum's semantic_facts table.
DB: `~/.hermes/cerebrum_memory.db` (SQLite).
Categories: research, project, medical, tool, user_pref, general, honcho_dialectic.
Re-run safe: INSERT OR IGNORE deduplicates on content.
