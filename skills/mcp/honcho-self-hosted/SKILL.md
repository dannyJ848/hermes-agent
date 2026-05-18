---
name: honcho-self-hosted
description: Deploy Honcho (plastic-labs/honcho) self-hosted with custom LLM providers (Z.AI GLM-5.1) and local Ollama embeddings. Full Docker stack with monitoring.
version: 1.0
last_used: 2026-04-03
---

# Honcho Self-Hosted Deployment

Deploy Honcho locally with GLM-5.1 (Z.AI) for dialectic reasoning and Ollama (nomic-embed-text) for embeddings. Zero data leaves the machine.

## Prerequisites
- Docker Desktop running
- Ollama installed with `nomic-embed-text` pulled (768 dims)
- Z.AI API key (GLM-5.1 coding plan)

## Critical Traps (learned the hard way)

### 1. Dimension Mismatch (1536 vs 768)
Honcho hardcodes 1536 dimensions everywhere (OpenAI's text-embedding-3-small). Ollama's nomic-embed-text outputs 768. Must patch ALL of:
- `src/models.py` — Vector(1536) → Vector(768) (2 locations)
- `src/embedding_client.py` — output_dimensionality: 1536 → 768 (3 locations)
- `src/config.py` — default=1536 → 768 (2 locations)
- `migrations/versions/*.py` — ALL migration files with Vector(1536) → Vector(768)
- `src/vector_store/lancedb.py` and `src/dreamer/surprisal.py` — comments only

### 2. Provider Type: Use "custom", NOT "openai_compatible"
SupportedProviders Literal only accepts: anthropic, openai, google, groq, custom, vllm. The Z.AI OpenAI-compatible endpoint uses `custom` which maps to `LLM_OPENAI_COMPATIBLE_*` settings.

### 3. ALL LLM Subsystems Need Provider Override
Defaults are google/anthropic. Must set ALL of:
- DERIVER_PROVIDER=custom, DERIVER_MODEL=glm-5.1
- SUMMARY_PROVIDER=custom, SUMMARY_MODEL=glm-5.1
- DREAM_PROVIDER=custom, DREAM_MODEL=glm-5.1
- DIALECTIC_LEVELS__*__PROVIDER=custom, DIALECTIC_LEVELS__*__MODEL=glm-5.1

### 4. All 5 Dialectic Levels Are Required
Keys must be: minimal, low, medium, high, max. Each needs thinking_budget_tokens and max_tool_iterations. MAX_OUTPUT_TOKENS must be > highest thinking_budget_tokens.

### 5. Embedding Client Needs Patching for Ollama
The `openrouter` provider in embedding_client.py uses `LLM_OPENAI_COMPATIBLE_BASE_URL` which conflicts with dialectic's base URL. Patch to use separate env vars:
- EMBEDDING_BASE_URL=http://host.docker.internal:11434/v1
- EMBEDDING_API_KEY=ollama
- EMBEDDING_MODEL=nomic-embed-text

Add `import os` to embedding_client.py. In the `openrouter` branch, read from `os.environ.get("EMBEDDING_BASE_URL")` / `os.environ.get("EMBEDDING_API_KEY")` / `os.environ.get("EMBEDDING_MODEL")`.

### 6. Dev Volume Mounts Override Image Code
The example docker-compose.yml mounts `.:/app` and `venv:/app/.venv` — this overrides the built image's code. Remove these volume mounts for production-style deployment. Without them, the entrypoint `docker/entrypoint.sh` won't exist in the container either — remove the entrypoint override from compose.

### 7. Provision DB Before Starting API
Run `docker compose run --rm api python scripts/provision_db.py` AFTER database is healthy but BEFORE api/deriver start. Must be done after every `down -v`.

## Startup
```bash
/tmp/honcho/start.sh
```

## Verification
```bash
# Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# Test API
curl -s http://localhost:8000/openapi.json | python3 -c "import sys,json; print(len(json.load(sys.stdin)['paths']), 'routes')"

# Test embedding pipeline
curl -s -X POST http://localhost:8000/v3/workspaces/hermes/peers/danny/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

## Ports
- 8000: Honcho API
- 5432: Postgres+pgvector
- 6379: Redis
- 3000: Grafana
- 9090: Prometheus
