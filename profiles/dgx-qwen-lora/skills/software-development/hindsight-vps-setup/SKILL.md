---
name: hindsight-vps-setup
description: Deploy Hindsight knowledge graph API to a VPS with PostgreSQL + pgvector. Covers the 6 gotchas that block deployment (root user, env var names, pgvector, API auth, migrations, systemd). Includes bulk migration script for importing tips from SQLite.
version: 1.0
tags: [hindsight, knowledge-graph, vps, deployment, postgresql, pgvector]
---

# Hindsight Knowledge Graph — VPS Deployment

Deploy the Hindsight API to a Linux VPS with external PostgreSQL and cloud LLM for fast extraction.

## Prerequisites

- VPS with root access (tested: Ubuntu 24.04, 2vCPU/8GB)
- PostgreSQL installed
- OpenRouter API key (or other OpenAI-compatible LLM API)
- Hermes venv already installed at `/root/hermes-agent/venv/`

## Step-by-Step

### 1. Install PostgreSQL + pgvector

```bash
apt-get install -y postgresql postgresql-contrib postgresql-16-pgvector
systemctl enable postgresql
systemctl start postgresql

# Create DB user + database
su - postgres -c "psql -c \"CREATE USER hindsight WITH PASSWORD 'hindsight123';\""
su - postgres -c "psql -c \"CREATE DATABASE hindsight OWNER hindsight;\""
su - postgres -c "psql -d hindsight -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
```

**GOTCHA #1: pgvector must be installed BEFORE running migrations.** Without it, `hindsight-admin run-db-migration` fails with `extension "vector" is not available`.

### 2. Install Hindsight

```bash
source /root/hermes-agent/venv/bin/activate
pip install hindsight-api
```

**GOTCHA #2: Don't use `pip3 install --break-system-packages`.** Use the Hermes venv instead — it has the right Python version and avoids PEP 668 issues.

### 3. Run Database Migrations

```bash
export HINDSIGHT_API_DATABASE_URL="postgresql://hindsight:hindsight123@localhost:5432/hindsight"
export HINDSIGHT_API_LLM_API_KEY="your-openrouter-key"
export HINDSIGHT_API_LLM_BASE_URL="https://openrouter.ai/api/v1"
export HINDSIGHT_API_LLM_MODEL="google/gemini-2.0-flash-001"

hindsight-admin run-db-migration
```

**GOTCHA #3: Run migrations BEFORE starting the API.** The API will crash on startup if migrations haven't been run.

**GOTCHA #4: The env var is `HINDSIGHT_API_DATABASE_URL`, NOT `DATABASE_URL`.** Using `DATABASE_URL` causes Hindsight to try embedded PostgreSQL, which fails because it can't run as root (`initdb: error: cannot be run as root`).

### 4. Create systemd Service

```ini
[Unit]
Description=Hindsight Knowledge Graph API
After=network.target postgresql.service

[Service]
Type=simple
User=root
Environment=HINDSIGHT_API_LLM_API_KEY=YOUR_OPENROUTER_KEY
Environment=HINDSIGHT_API_LLM_BASE_URL=https://openrouter.ai/api/v1
Environment=HINDSIGHT_API_LLM_MODEL=google/gemini-2.0-flash-001
Environment=HINDSIGHT_API_DATABASE_URL=postgresql://hindsight:hindsight123@localhost:5432/hindsight
Environment=HINDSIGHT_API_LLM_TIMEOUT=600
ExecStart=/root/hermes-agent/venv/bin/hindsight-api --host 127.0.0.1 --port 8890
Restart=always
RestartSec=10
StandardOutput=append:/var/log/hindsight.log
StandardError=append:/var/log/hindsight.log

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable hindsight
systemctl start hindsight
```

Wait ~20s for model loading, then verify:
```bash
curl http://127.0.0.1:8890/health
# {"status":"healthy","database":"connected"}
```

### 5. LLM Provider Selection

**GOTCHA #5: Z.AI API keys (`3239ea...` format) are NOT OpenAI-compatible.** They fail with 401 Authentication Failed when used with `base_url=https://api.z.ai/api/coding/paas/v4`. Use OpenRouter instead.

| Provider | Base URL | Works | Speed |
|---|---|---|---|
| OpenRouter | `https://openrouter.ai/api/v1` | YES | ~2.3s/tip |
| Z.AI Coding API | `https://api.z.ai/api/coding/paas/v4` | NO (401) | N/A |
| Local Llama (Mac) | `http://127.0.0.1:8082/v1` | YES | ~60-180s/tip |

**Recommended:** OpenRouter with `google/gemini-2.0-flash-001` — fast, cheap, reliable.

**GOTCHA #6: Free model names change.** `meta-llama/llama-3.1-8b-instruct:free` returned 404. Use a paid model or verify the model name first.

### 6. Create Bank + Bulk Migrate

```bash
# Create bank
curl -s -X PUT "http://127.0.0.1:8890/v1/default/banks/hermes-cerebrum" \
  -H "Content-Type: application/json" \
  -d '{"name": "hermes-cerebrum", "mission": "Hermes behavioral knowledge"}'
```

For bulk migration from SQLite cerebrum DB, use the batch migration script:
- SCP `cerebrum_memory.db` to VPS `/tmp/`
- Batch size 5 tips per POST request
- ~65 tips/min with cloud LLM (vs 1-3 min/tip with local Llama)
- 2400 tips takes ~36 minutes
- Progress saved to `/tmp/hindsight_migration_progress.json` for resume

### Performance Profile

| Component | RAM | Notes |
|---|---|---|
| Hindsight API | ~685MB | Includes local embedding + reranker models |
| PostgreSQL | ~100MB | With pgvector indexes |
| Total | ~800MB | Fits in 8GB VPS with room to spare |

### 7. API Integration — Wiring Hindsight into Plugins

Use `curl http://HOST:8890/openapi.json` to discover all endpoints and their schemas. Key endpoints:

#### Recall (query the knowledge graph)
```
POST /v1/default/banks/{bank_id}/memories/recall
Body: {"query": "search terms here"}
Response: {"results": [{"text": "...", "score": N}, ...]}
```

**GOTCHA #7: No `limit` parameter in recall body.** Hindsight ignores it with a warning: "Unknown parameters ignored: [limit]". Apply limit client-side by slicing `results[:N]`.

**GOTCHA #8: Recall is LLM-powered and SLOW (7-60s per query).** You MUST cache aggressively. Recommended: 300s TTL cache with query-keyed dict. First call blocks; cache hits return in 0ms.

**GOTCHA #9: Consolidation batches compete with recall for LLM resources.** During active consolidation, recalls may time out. Design code to gracefully degrade (return empty list on timeout).

#### Retain (push new memories to the graph)
```
POST /v1/default/banks/{bank_id}/memories
Body: {"items": [{"content": "fact text here"}], "async": true}
Response: 200 or 202 (async accepted)
```

**GOTCHA #10: NOT `POST /memories/retain`.** That endpoint returns 405 Method Not Allowed. The correct endpoint is `POST /memories` with the `RetainRequest` schema (`{"items": [{"content": "..."}]}`). Use `"async": true` for fire-and-forget pushes.

**GOTCHA #11: GLM-5.1 via Z.AI WORKS as Hindsight LLM.** Despite GOTCHA #5 saying Z.AI keys fail, the issue was the model name, not the provider. With correct config (`HINDSIGHT_API_LLM_BASE_URL=https://api.z.ai/api/coding/paas/v4`, `HINDSIGHT_API_LLM_MODEL=glm-5.1`), GLM-5.1 works perfectly for Hindsight extraction (~10s/call).

**GOTCHA #12: ALL metadata values MUST be strings.** The retain endpoint returns 422 Unprocessable Entity if any metadata value is a float or int. You MUST convert: `str(confidence)` not `confidence`, `str(count)` not `count`. This silently breaks bulk syncs — a single float value kills the entire batch.

**GOTCHA #13: Bulk sync batch size sweet spot is 5-10 items.** Larger batches (50+) are more likely to hit timeouts or 422 errors from a single bad item. Use small batches with progress tracking (save last synced ID to a JSON file) so you can resume after failures.

#### Plugin Integration Pattern

```python
# Module-level cache (recall is expensive!)
_hindsight_cache = {"data": None, "time": 0, "query": ""}
_HINDSIGHT_CACHE_TTL = 300  # 5 minutes

def _query_hindsight(query, limit=3, timeout=12):
    """Returns list of {"text": str, "score": float}."""
    now = time.time()
    if cache hit (same query, within TTL): return cached data
    try:
        POST to /memories/recall with {"query": query}
        parse results, dedupe by first 80 chars, cache, return
    except: return []  # graceful degradation

def _retain_hindsight(text, metadata=None):
    """Push fact to graph. Fire-and-forget."""
    try:
        # CRITICAL: all metadata values MUST be strings (GOTCHA #12)
        safe_meta = None
        if metadata:
            safe_meta = {k: str(v) for k, v in metadata.items()}
        item = {"content": text}
        if safe_meta:
            item["metadata"] = safe_meta
        POST to /memories with {"items": [item], "async": true}
        return response.status in (200, 202)
    except: return False
```

Wire into:
- **pre_llm_call**: recall facts matching task keywords → inject as `[KNOWLEDGE GRAPH]` context
- **post_tool_call tip creation**: auto-retain new tips via `_retain_hindsight()`
- **Error enrichment**: recall similar past failures before generating hardcoded patches

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `cannot be run as root` | Embedded PG tried instead of external | Use `HINDSIGHT_API_DATABASE_URL` env var |
| `extension "vector" not available` | pgvector not installed | `apt install postgresql-16-pgvector` |
| `Authentication Failed (401)` | Z.AI key format incompatible | Use OpenRouter API key OR correct Z.AI model name |
| `No endpoints found (404)` | Model name wrong/changed | Verify model on openrouter.ai/models |
| Connection refused after start | Still loading models | Wait 15-25s, retry |
| Memory OOM | 8GB VPS with Hermes + Hindsight | ~800MB each, 6.8GB available — fine |
| Recall returns empty | Timeout too short OR consolidation running | Increase timeout to 12-20s, cache aggressively |
| Retain returns 405 | Wrong endpoint `/memories/retain` | Use `POST /memories` with `{"items": [...]}` |
| "Unknown parameters ignored: [limit]" | Recall doesn't accept limit param | Apply limit client-side on results array |
