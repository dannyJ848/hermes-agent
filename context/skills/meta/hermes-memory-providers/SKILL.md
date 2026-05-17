---
name: hermes-memory-providers
description: "Configure and manage Hermes Agent's 7 memory provider plugins. Covers setup, comparison, and migration between Honcho, OpenViking, Mem0, Hindsight, Holographic, RetainDB, and ByteRover."
version: 1.0
tags: [memory, providers, honcho, holographic, openviking, mem0, hindsight, retaindb, byterover]
---

# Hermes Memory Providers

Hermes Agent ships with 7 pluggable memory providers. Only **ONE** external provider can be active at a time. Built-in memory (MEMORY.md / USER.md) is always active alongside whichever external provider you choose.

## Commands

```bash
hermes memory setup      # interactive picker + configuration
hermes memory status     # check what's active
hermes memory off        # disable external provider (built-in only)
```

## Config

In `~/.hermes/config.yaml`:
```yaml
memory:
  provider: holographic   # or honcho, mem0, openviking, hindsight, retaindb, byterover
```

## Provider Comparison (April 2026)

| Provider | Storage | Cost | Tools | Unique Feature |
|----------|---------|------|-------|---------------|
| **Honcho** | Cloud/Self-hosted | Free (self-hosted) | 4 | Dialectic user modeling, peer cards |
| **OpenViking** | Self-hosted | Free (AGPL-3.0) | 5 | Filesystem hierarchy, tiered loading (L0/L1/L2), auto 6-category extraction |
| **Mem0** | Cloud | Paid | 3 | Server-side LLM extraction, dedup, reranking |
| **Hindsight** | Cloud/Local | Free (local) | 3 | Knowledge graph, entity resolution, cross-memory synthesis via `hindsight_reflect` |
| **Holographic** | Local SQLite | Free | 2 | FTS5 + HRR algebra + trust scoring + contradiction detection, ZERO deps |
| **RetainDB** | Cloud | $20/mo | 5 | Hybrid search (Vector+BM25+Reranking), delta compression |
| **ByteRover** | Local/Cloud | Free (local) | 3 | Pre-compression extraction, knowledge tree, `brv` CLI |

## Hindsight Embedded Daemon Configuration (May 2026)

**Critical distinction:** Hindsight can run in THREE modes, but only ONE is relevant for most Hermes setups:

| Mode | How it starts | Use case |
|------|--------------|----------|
| `cloud` | Connects to vectorize.io API | Paid hosted service |
| `local_external` | Connects to standalone `hindsight-api` process | Manual daemon management |
| `local_embedded` | Hermes plugin manages daemon lifecycle automatically | **Recommended** |

**The common mistake:** Trying to start `hindsight-api` manually when the plugin is configured for `local_embedded`. The embedded daemon is managed by the HindsightMemoryProvider plugin — it's NOT meant to be started manually.

**Config resolution order:**
1. `$HERMES_HOME/hindsight/config.json` (profile-scoped, preferred)
2. `~/.hindsight/config.json` (legacy shared)
3. Environment variables (`HINDSIGHT_MODE`, `HINDSIGHT_API_LLM_*`)

**Working config for Ollama backend:**
```json
{
  "mode": "local_embedded",
  "bank_id": "hermes-training",
  "llm_provider": "openai",
  "llm_model": "qwen3:14b",
  "llm_base_url": "http://127.0.0.1:11434/v1",
  "llm_api_key": "ollama",
  "recall_budget": "high"
}
```

**Important:** The active memory provider is set in `~/.hermes/config.yaml` under `memory.provider`. If this is `cortex` (not `hindsight`), then Hindsight is NOT the active provider — the evey-rag plugin will use cerebrum SQLite fallback instead. This is a valid configuration; the fallback works fine.

**To check active provider:**
```bash
grep "provider:" ~/.hermes/config.yaml
```

**Hindsight profile env file:**
```bash
# Create profile-specific env for the embedded daemon
mkdir -p ~/.hindsight/profiles/hermes
cat > ~/.hindsight/profiles/hermes/.env << 'EOF'
HINDSIGHT_API_LLM_PROVIDER=openai
HINDSIGHT_API_LLM_API_KEY=ollama
HINDSIGHT_API_LLM_MODEL=qwen3:14b
HINDSIGHT_API_LLM_BASE_URL=http://127.0.0.1:11434/v1
HINDSIGHT_MODE=local_embedded
EOF
```

**Verification:**
```python
from hindsight_embed.profile_manager import ProfileManager
pm = ProfileManager()
profiles = pm.list_profiles()
# → [ProfileInfo(name='hermes', port=8890, ...)]
```

**Hindsight status check (May 2026):**
```bash
# Check if Hindsight is the active provider
grep "provider:" ~/.hermes/config.yaml

# Check Hindsight config
cat ~/.hermes/hindsight/config.json 2>/dev/null || cat ~/.hindsight/config.json 2>/dev/null

# Check if Ollama is running (for local_embedded mode)
curl -s http://127.0.0.1:11434/api/tags | head -5
```

**If Hindsight is NOT the active provider:** The `memory.provider` field in `~/.hermes/config.yaml` may be set to `cortex` (which uses Cerebrum SQLite fallback) or another provider. This is valid — Hindsight does not need to be active for the system to work. The evey-rag plugin will use whichever provider is configured.

**Hindsight knowledge graph recovery (May 2026):**
If Hindsight was previously active but is now showing as unavailable:
1. Check config: `cat ~/.hermes/hindsight/config.json`
2. Verify Ollama model exists: `curl -s http://127.0.0.1:11434/api/tags | grep qwen3`
3. If model missing: `ollama pull qwen3:14b`
4. Check if the unified Cortex DB (PostgreSQL) was previously deployed — it may have merged Hindsight + Cerebrum
5. To reactivate Hindsight: set `memory.provider: hindsight` in `~/.hermes/config.yaml` and restart CLI session

**Note:** There was a "Cortex Unified DB" experiment that merged Hindsight (PostgreSQL) + Cerebrum into a single database. If this was deployed and then stopped, Hindsight may appear "down" because the unified DB is not running. Check `~/.hermes/goals.md` for any pending "Restore Hindsight" tasks.

## Best Picks for Self-Hosted / Free

1. **Holographic** -- Zero deps, local SQLite. Trust scoring perfect for reliability-sensitive domains (medical, legal). Contradiction detection. Compositional HRR queries. `fact_store` has 9 actions (add/search/probe/related/reason/contradict/update/remove/list) + `fact_feedback` for training trust.

2. **OpenViking** -- Best for structured knowledge. Tiered context loading saves tokens: L0 (~100 tok) → L1 (~2k) → L2 (full). Auto-extracts into 6 categories. Self-hosted via `openviking-server` on port 1933. Requires embedding/VLM model config in `~/.openviking/ov.conf`.

3. **Hindsight (local mode)** -- Best for relationship-heavy knowledge. Knowledge graph with entity resolution. `hindsight_reflect` synthesizes across all memories. Local mode uses embedded PostgreSQL.

4. **Honcho (self-hosted)** -- Already running in Docker at localhost:8000. Dialectic user modeling builds psychological profiles over time. Best for understanding user preferences and communication patterns.

## How the Plugin System Works

When a memory provider is active, Hermes automatically:
1. Injects provider context into the system prompt
2. Prefetches relevant memories before each turn (background, non-blocking)
3. Syncs conversation turns to the provider after each response
4. Extracts memories on session end (for providers that support it)
5. Mirrors built-in memory writes to the external provider
6. Adds provider-specific tools

## Profile Isolation

Each provider's data is isolated per profile:
- **Local storage** (Holographic, ByteRover): `$HERMES_HOME/` paths differ per profile
- **Config file** (Honcho, Mem0, Hindsight): config in `$HERMES_HOME/` per profile
- **Cloud** (RetainDB): auto-derives profile-scoped project names
- **Env var** (OpenViking): configured via each profile's `.env` file

## Source Code Location

All providers live in `~/hermes-agent/plugins/memory/<provider>/` with:
- `__init__.py` (main implementation)
- `plugin.yaml` (metadata)
- `README.md` (setup docs)

Docs: `~/hermes-agent/website/docs/user-guide/features/memory-providers.md`

## Pitfalls

- Only ONE external provider active at a time -- cannot combine natively
- To use multiple providers, must build custom meta-provider or pipe data manually between backends
- `hermes update` may pull new provider plugins -- run `hermes memory setup` to configure
- Some providers (Mem0, RetainDB) require paid cloud accounts
- OpenViking requires running a separate server process
- Holographic is the only zero-dependency option
- **Hindsight local_embedded mode:** The plugin manages the daemon lifecycle automatically. Do NOT try to start `hindsight-api` manually. If the active provider in config.yaml is `cortex` (not `hindsight`), the evey-rag plugin uses cerebrum SQLite fallback — this is expected behavior, not an error

## Troubleshooting: "Unknown tool" After Config Change

**Symptom:** Memory provider tool (e.g., `cerebrum`) shows in system prompt tool schema but returns "Unknown tool" when called.

**Root cause:** Memory providers load per **CLI agent session**, not per gateway restart. The gateway handles Telegram/cron/API — it does NOT load memory providers. The tool schema injection and `_memory_manager` initialization both happen in `run_agent.py` during `__init__` of the AIAgent class.

**Fix:** You must start a **fresh CLI session** (quit `hermes` and relaunch). A gateway restart (`Ctrl+C` in gateway tmux pane) is NOT sufficient.

**Debugging checklist:**
1. Verify config: `grep provider ~/.hermes/config.yaml` → should show `provider: <name>`
2. Test load with venv Python: `~/hermes-agent/venv/bin/python3 -c "from plugins.memory import load_memory_provider; p = load_memory_provider('cerebrum'); print(p.is_available())"`
3. **IMPORTANT:** Always use the venv Python (`~/hermes-agent/venv/bin/python3`), NOT system `python3`. System python may be 3.8 which fails on `Path | None` union type syntax in `hermes_constants.py`.
4. Check dispatch path: tools go through `_invoke_tool()` in `run_agent.py` (~line 5574). Memory provider tools hit `elif self._memory_manager and self._memory_manager.has_tool(function_name):` (~line 5620). If `_memory_manager` is None, it falls through to `handle_function_call()` which returns "Unknown tool".
5. Init errors are silently caught at ~line 1088: `except Exception as _mpe: self._memory_manager = None`

**Custom providers (like Cerebrum):** Must have `__init__.py` with either:
- A `register(ctx)` function that calls `ctx.register_memory_provider(provider)`, OR
- A top-level class extending `MemoryProvider` ABC

The discovery system (`plugins/memory/__init__.py`) scans all subdirectories, reads `plugin.yaml` for metadata, and calls `is_available()` for the health check.

**Variable scoping trap (run_agent.py ~line 1031):** The memory provider init block uses `mem_config` from a PREVIOUS try/except block (lines 1009-1024). If that first block's exception is silently caught (`pass`), `mem_config` may be undefined or empty, causing the provider name to resolve to `""`. The outer exception handler at ~line 1099 also silently swallows NameError. **Fix:** Always add file-based diagnostics (`open("/tmp/diag.log","a")`) when debugging this path, because logger output may not reach any log file depending on how the session was created (gateway vs CLI).

**File-based diagnostic technique:** When logger.info/error output doesn't appear in gateway.log or errors.log (common for lazy-initialized per-message agents), use raw file writes:
```python
_diag_f = open("/tmp/cerebrum_diag.log", "a")
_diag_f.write(f"[{datetime.now()}] mem_config={mem_config}\n")
_diag_f.flush()
```
This works because file I/O has no logger configuration dependency. Place at the exact code path entry point (before any try/except) to confirm whether the code is even reached.

## Pitfall: __init__ vs initialize() — db_path Scoping

**Symptom:** Provider crashes with `NameError: name 'db_path' is not defined` at startup, but only in gateway mode (works in standalone test scripts that pass the path directly).

**Root cause:** Hermes memory providers have a two-phase init:
- `__init__(self, config: dict | None = None)` — receives config dict only, NO db_path
- `initialize(self, session_id: str, **kwargs)` — receives `hermes_home` via kwargs, computes `db_path` at line ~190

Any resource that needs the database path (SQLite connections, table creation) MUST go in `initialize()`, not `__init__`.

**Pattern for deferred init:**
```python
def __init__(self, config=None):
    # Set to None — created in initialize()
    self._db_resource = None

def initialize(self, session_id, **kwargs):
    db_path = str(Path(kwargs.get("hermes_home", "")) / "cerebrum_memory.db")
    self._db_resource = SomeDbClass(db_path)  # Now db_path is in scope
```

**Guard pattern must match:** When attributes are set to `None` in `__init__` (instead of not set at all), `hasattr(self, '_resource')` ALWAYS returns True. Change guards from:
```python
if not hasattr(self, '_predictive_self'):  # WRONG — always True if set to None
```
to:
```python
if not self._predictive_self:  # CORRECT — catches None
```

**Post-fix verification:**
```bash
# Clear all Python caches before restart
find ~/hermes-agent -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find ~/hermes-agent -name "*.pyc" -delete 2>/dev/null
# Verify tables created
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT name FROM sqlite_master WHERE type='table'"
```

## Related: Session Reset Policy

Config in `config.yaml` under `session_reset`:
```yaml
session_reset:
  mode: both           # "daily", "idle", "both", or "none"
  idle_minutes: 1440   # 24h idle timeout
  at_hour: 4           # daily reset hour (0-23)
```

Source: `~/hermes-agent/gateway/config.py` class `SessionResetPolicy`
