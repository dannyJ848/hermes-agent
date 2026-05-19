# DGX Hermes Config: Location and Format Pitfalls (May 14, 2026)

## Critical Finding: Config File Location

Hermes reads config from `~/.hermes/config.yaml`, NOT from the repository directory.

**What we tried (WRONG):**
```bash
# Editing repo config - Hermes ignores this
vim /data/SpecForge/hermes-agent/config.yaml
```

**What works (CORRECT):**
```bash
# Edit the actual config Hermes reads
vim /home/djg6228/.hermes/config.yaml
```

## Config Format: Dict vs List

The DGX config had old-format `plugins:` list while MacBook used `enabled:`/`disabled:` dict.

**WRONG format (DGX default, gets ignored):**
```yaml
plugins:
  - learning-brain
  - memory-provider
  - subconscious-loop
```

**CORRECT format (MacBook, works):**
```yaml
plugins:
  enabled:
    - learning-brain
    - memory-provider
    - subconscious-loop
  disabled: []
```

Without the dict format, plugins are silently ignored. Tool count stays at 21 instead of 97.

## Full Working DGX Config

```yaml
model:
  provider: custom
  base_url: http://localhost:8000/v1
  api_key: not-needed
  default: merged-lora
  context_length: 65536  # REQUIRED: Hermes minimum is 64K
  chat_template_kwargs:
    enable_thinking: true

providers:
  custom:
    api: http://localhost:8000/v1
    api_key: not-needed
    models:
      merged-lora:
        context_length: 65536
        supports_tools: true
        supports_reasoning: true

plugins:
  enabled:
    - learning-brain
    - memory-provider
    - subconscious-loop
    - context-engine
    - tool-registry
    - skill-manager
    - knowledge-base
    - session-manager
    - goal-tracker
    - budget-monitor
    - telemetry-collector
    - health-monitor
    - cron-manager
    - notification-router
    - web-search
    - browser-automation
    - file-manager
    - code-executor
    - git-integration
    - docker-manager
    - system-monitor
    - network-tools
    - security-scanner
    - backup-manager
    - log-analyzer
    - performance-profiler
    - error-tracker
    - metrics-exporter
    - alert-manager
    - incident-responder
    - runbook-executor
    - compliance-checker
    - audit-logger
    - secret-manager
    - config-manager
    - deployment-manager
  disabled: []

agent:
  enabled_toolsets: all
  max_iterations: 50
  timeout: 300

memory:
  provider: sqlite
  path: ~/.hermes/cerebrum_memory.db

skills:
  path: ~/.hermes/skills

knowledge:
  path: ~/.hermes/knowledge
```

## Verification Commands

```bash
# Check which config Hermes is actually using
cd /data/SpecForge/hermes-agent
venv/bin/python -c "from hermes_cli.config import get_config_path; print(get_config_path())"

# Check tool count (should be 90+)
venv/bin/python -c "from model_tools import get_tool_definitions; tools = get_tool_definitions(); print(f'Total tools: {len(tools)}')"

# Check loaded plugins
venv/bin/python -c "from hermes_cli.plugins import get_plugin_manager; pm = get_plugin_manager(); print([p.name for p in pm.get_plugins()])"
```

## Environment Variables

```bash
# Add to ~/.bashrc
export PATH=/home/djg6228/node/bin:/data/SpecForge/hermes-agent/venv/bin:$PATH
export HERMES_CONFIG=/home/djg6228/.hermes/config.yaml
```

## Systemd Service PATH

When running Hermes as a systemd service, the PATH must include Node.js for browser tools:

```ini
[Service]
Environment=PATH=/home/djg6228/node/bin:/data/SpecForge/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin
```
