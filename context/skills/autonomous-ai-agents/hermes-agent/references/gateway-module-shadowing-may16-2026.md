# Gateway Module Shadowing Investigation (May 16, 2026)

## Problem

When Hermes Agent runs on DGX Spark with full cognitive orchestrator (20 subsystems), the `gateway/` package is shadowed by `hermes_cli/gateway.py`, causing plugin load failures and breaking gateway imports.

## Symptoms

```
ModuleNotFoundError: No module named 'gateway.status'; 'gateway' is not a package
Failed to load plugin 'google_chat-platform': No module named 'gateway.status'; 'gateway' is not a package
Failed to load plugin 'irc-platform': No module named 'gateway.status'; 'gateway' is not a package
Failed to load plugin 'teams-platform': No module named 'gateway.status'; 'gateway' is not a package
```

Error occurs at `agent/prompt_builder.py:745`:
```python
from gateway.session_context import get_session_env
```

This resolves to `hermes_cli/gateway.py` (a file module) instead of `gateway/__init__.py` (a package).

## Root Cause

Python's module resolution order:
1. `sys.modules` cache
2. Built-in modules
3. `sys.path` traversal

When `hermes_cli/` is in `sys.path` before the project root, `hermes_cli/gateway.py` is found before `gateway/__init__.py`. The file module shadows the package.

## Why Plugins Pre-Import Wasn't Enough

The `plugins` pre-import in `run_agent.py` (lines 199-202) works because:
- `hermes_cli/plugins.py` is imported AFTER the pre-import
- The pre-import wins the race

But `gateway` was different:
- `hermes_cli/plugins.py` imports `from gateway.platform_registry import platform_registry` at line 555
- This import happens DURING plugin loading, not during run_agent.py import
- By then, `gateway` may have been overwritten

## Solution: Wrapper Script

The wrapper script (`run_hermes_fixed.py`) pre-imports BOTH packages before ANY hermes_cli imports:

```python
import sys
import os
import importlib.util

project_root = "/data/SpecForge/hermes-agent"
sys.path.insert(0, project_root)

# Step 1: Pre-import plugins package
plugins_init = os.path.join(project_root, "plugins", "__init__.py")
if os.path.exists(plugins_init) and "plugins" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "plugins", plugins_init,
        submodule_search_locations=[os.path.join(project_root, "plugins")]
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["plugins"] = mod
    spec.loader.exec_module(mod)

# Step 2: Pre-import gateway package
gateway_init = os.path.join(project_root, "gateway", "__init__.py")
if os.path.exists(gateway_init) and "gateway" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "gateway", gateway_init,
        submodule_search_locations=[os.path.join(project_root, "gateway")]
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gateway"] = mod
    spec.loader.exec_module(mod)

# Step 3: Now safe to import run_agent
from run_agent import main
import asyncio
asyncio.run(main())
```

## Systemd Service Configuration

```ini
[Unit]
Description=Hermes Agent DGX (Fixed)
After=network.target

[Service]
Type=simple
WorkingDirectory=/data/SpecForge/hermes-agent
Environment=PYTHONPATH=/data/SpecForge/hermes-agent
Environment=HERMES_HOME=/home/djg6228/.hermes
Environment=TERMINAL_ENV=ssh
Environment=TERMINAL_SSH_HOST=macbook
Environment=TERMINAL_SSH_USER=dannygomez
ExecStart=/data/SpecForge/hermes-agent/venv/bin/python3 /data/SpecForge/hermes-agent/run_hermes_fixed.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

## Verification Steps

1. Check running processes:
```bash
ps aux | grep hermes | grep -v grep
```
Should show `run_hermes_fixed.py`, not `venv/bin/hermes --resume`

2. Test gateway imports:
```python
import sys
sys.path.insert(0, "/data/SpecForge/hermes-agent")
from gateway.session_context import get_session_env
print("OK")
```

3. Check for old processes:
```bash
ps aux | grep "venv/bin/hermes" | grep -v "run_hermes_fixed" | grep -v grep
```
If any found, kill them — they cause confusing error logs.

## Key Files

- `/data/SpecForge/hermes-agent/run_hermes_fixed.py` — Wrapper script
- `/data/SpecForge/hermes-agent/run_agent.py` — Has pre-imports at lines 199-210
- `/home/djg6228/.config/systemd/user/hermes-agent.service` — Systemd service
- `/home/djg6228/.hermes/logs/hermes-daemon.log` — Daemon logs

## Related

- `references/module-shadowing-fix-may15-2026.md` — Original plugins shadowing fix
- `references/cognitive-orchestrator-20-subsystems-may15-2026.md` — 20/20 subsystems achievement
