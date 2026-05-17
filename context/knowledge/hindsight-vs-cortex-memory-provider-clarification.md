# hindsight-vs-cortex-memory-provider-clarification

*Researched: 2026-05-16 12:19 CDT*

# Hindsight vs Cortex Memory Provider — Clarification

## The Confusion

Multiple audit sessions attempted to "fix" Hindsight because port 8890 was not listening and the Hindsight API appeared down. However, this was a misunderstanding of the architecture.

## Actual Architecture

| Component | Role | Status |
|-----------|------|--------|
| **Cortex** (cerebrum SQLite) | **Active memory provider** | Configured in `~/.hermes/config.yaml` as `memory.provider: cortex` |
| **Hindsight plugin** | Available but NOT active | Exists in `~/hermes-agent/plugins/memory/hindsight/` but not selected |
| **Hindsight embedded daemon** | On-demand only | Starts automatically when Hermes boots IF Hindsight is the active provider |
| **evey-rag plugin** | Knowledge retrieval | Falls back to cerebrum SQLite when Hindsight is unavailable |

## Key Insight

The `memory.provider` field in `~/.hermes/config.yaml` determines which memory provider is active. It was set to `cortex`, meaning:

1. Hindsight daemon does NOT start at boot (correct behavior)
2. Port 8890 is NOT expected to be listening (correct behavior)
3. Cerebrum SQLite handles all memory operations
4. evey-rag uses cerebrum fallback for knowledge retrieval

## Hindsight When Needed

If Hindsight IS desired as the active provider:

```bash
# 1. Set as active provider
hermes config set memory.provider hindsight

# 2. Configure Hindsight for local embedded mode
cat > ~/.hermes/hindsight/config.json << 'EOF'
{
  "mode": "local_embedded",
  "bank_id": "hermes-training",
  "llm_provider": "openai",
  "llm_model": "qwen3:14b",
  "llm_base_url": "http://127.0.0.1:11434/v1",
  "llm_api_key": "ollama"
}
EOF

# 3. Restart Hermes — daemon will start automatically
```

## The External API Red Herring

The standalone `hindsight-api` CLI (`~/hermes-agent/venv/bin/hindsight-api`) is a separate server binary, NOT how the plugin works. Attempting to run it manually:
- Requires `HINDSIGHT_API_LLM_API_KEY` env var
- Uses its own embedded PostgreSQL (not the system one)
- Conflicts with the plugin's own daemon management

**This approach was wrong.** The plugin manages its own daemon lifecycle.

## Current Correct State

- Memory provider: **cortex** (cerebrum SQLite)
- Cerebrum DB: **1,282 tips**, canonical schema
- Knowledge retrieval: **FUNCTIONAL** via evey-rag fallback
- Hindsight: **Available on-demand** if ever switched to active provider

## Lesson

Always check `memory.provider` in config.yaml before diagnosing memory provider issues. The provider that is CONFIGURED is the one that matters, not the one that has files on disk.


## Sources

- Hermes Agent source code
- plugins/memory/hindsight/__init__.py
- ~/.hermes/config.yaml
