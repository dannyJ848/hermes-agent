# DGX Native Hermes Gateway — May 15 2026

Session: Discovered DGX Spark already had a full Hermes Agent installation and activated it as an independent cognitive instance.

## Key Discovery

**DGX Spark already had a complete Hermes Agent at `/data/SpecForge/hermes-agent/`** — not just vLLM inference. The installation included:
- Full source code (v0.13.0)
- 89 skills in `~/.hermes/skills/`
- 73 meta/cognitive skills
- Cerebrum memory DB (`~/.hermes/cerebrum_memory.db`)
- Configured plugins (cognitive-systems, distillation, 35+ evey plugins)
- Distillation daemon already running (`scripts/dgx_distillation_daemon.py`)
- Qdrant knowledge base configured (but not running)

**Lesson: ALWAYS check for existing installations before assuming you need to install from scratch.**

## What Was Missing / Broken

| Component | Status | Fix |
|-----------|--------|-----|
| vLLM container | Running | Already deployed with DFlash speculative decoding |
| Qdrant vector DB | Not running | `docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest` |
| Hermes gateway | Not running | Started via systemd service |
| Cron ticker | Crashing | Fixed import conflict (see below) |
| Config context | 262k | Reduced to 131k for better throughput |

## The Cron Import Conflict

**Symptom:** Gateway started but cron ticker thread crashed immediately:
```
ModuleNotFoundError: No module named 'cron.scheduler'; 'cron' is not a package
```

**Root cause:** `hermes_cli/cron.py` (a CLI command module) shadowed the `cron/` package (the scheduler package). When `gateway/run.py` tried `from cron.scheduler import tick`, Python imported `hermes_cli/cron.py` instead of `cron/scheduler.py`.

**Fix:** Rename the CLI module to avoid shadowing:
```bash
mv /data/SpecForge/hermes-agent/hermes_cli/cron.py \
   /data/SpecForge/hermes-agent/hermes_cli/cron_cmd.py

# Update imports in files that reference it:
sed -i 's/from hermes_cli.cron import/from hermes_cli.cron_cmd import/g' \
    /data/SpecForge/hermes-agent/hermes_cli/main.py
sed -i 's/import hermes_cli.cron/import hermes_cli.cron_cmd/g' \
    /data/SpecForge/hermes-agent/hermes_cli/main.py
# (Also update tests/hermes_cli/test_cron.py)
```

**Pitfall:** This is a structural issue in the Hermes codebase. The `cron` package name conflicts with `hermes_cli/cron.py`. Any DGX deployment with the full source will hit this.

## Systemd Service for DGX Gateway

```ini
[Unit]
Description=Hermes Agent Gateway (DGX Native)
After=network.target qdrant.service vllm-dflash.service
Wants=qdrant.service vllm-dflash.service

[Service]
Type=simple
User=djg6228
Group=djg6228
WorkingDirectory=/data/SpecForge/hermes-agent
Environment=HERMES_CONFIG=/data/SpecForge/hermes-agent/config.yaml
Environment=PYTHONPATH=/data/SpecForge/hermes-agent
Environment=PATH=/data/SpecForge/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/data/SpecForge/hermes-agent/venv/bin/python -m gateway.run
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Key points:**
- `PYTHONPATH=/data/SpecForge/hermes-agent` — required for module resolution
- `WorkingDirectory=/data/SpecForge/hermes-agent` — required for relative imports
- Uses `python -m gateway.run` instead of `hermes gateway run` (avoids CLI import issues)

## Config Structure

DGX Hermes uses `/data/SpecForge/hermes-agent/config.yaml` (repo config), NOT `~/.hermes/config.yaml`:

```yaml
model:
  default: merged-lora
  provider: local-dgx
  api_mode: chat_completions
  api_key: not-needed
providers:
  local-dgx:
    api: http://localhost:8000/v1
    api_key: not-needed
    models:
      merged-lora:
        context_length: 131072
        supports_tools: true
        supports_reasoning: true
plugins:
  enabled:
    - cognitive-systems
    - distillation
    - evey-autonomy
    - evey-bridge
    # ... 35+ plugins
memory:
  provider: sqlite
  sqlite:
    path: ~/.hermes/cerebrum_memory.db
knowledge:
  provider: qdrant
  qdrant:
    url: http://localhost:6333
    collection: hermes_knowledge
```

## Verification Commands

```bash
# Check all services
sudo systemctl status vllm-dflash.service --no-pager | head -3
sudo systemctl status hermes-dgx-gateway.service --no-pager | head -3
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'vllm|qdrant'

# Check cognitive plugins
export HERMES_CONFIG=/data/SpecForge/hermes-agent/config.yaml
/data/SpecForge/hermes-agent/venv/bin/hermes plugins list | grep 'enabled' | wc -l
# → 40 plugins enabled

# Check Hermes status
/data/SpecForge/hermes-agent/venv/bin/hermes status 2>&1 | head -20
```

## DGX vs MacBook Hermes — Separation of Concerns

| Aspect | MacBook Hermes | DGX Hermes |
|--------|---------------|------------|
| **Purpose** | Self-improvement, tip distillation, Elo scoring | Model training, inference serving, training-data generation |
| **Default model** | DeepSeek V4 Pro (via API) | Qwen3.6-27B-Uncensored + merged-lora (local) |
| **Cognitive systems** | Full autobrowse pipeline | Learning-brain, distillation, goal management |
| **Gateway** | Telegram, Discord | None (internal use only) |
| **Knowledge base** | Qdrant (local) | Qdrant (Docker) |
| **Skills** | 89 skills | 89 skills (synced) |
| **Memory** | `~/.hermes/cerebrum_memory.db` | `~/.hermes/cerebrum_memory.db` (independent) |

**Critical rule:** The two instances are INDEPENDENT. They do NOT share memory, sessions, or state. Each learns and improves on its own.

## Auto-Start Services

All DGX services configured for boot:
```bash
sudo systemctl enable vllm-dflash.service
sudo systemctl enable hermes-dgx-gateway.service
# Qdrant starts via docker restart policy (--restart unless-stopped)
```

## Result

- **Before:** DGX = dumb vLLM inference endpoint only
- **After:** DGX = fully autonomous Hermes Agent with 40 cognitive plugins, independent learning loop, and local Qwen3.6-27B inference
