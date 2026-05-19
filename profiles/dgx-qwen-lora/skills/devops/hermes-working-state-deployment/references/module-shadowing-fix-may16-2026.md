# Module Shadowing Fix for DGX Hermes Deployment
## Session: May 16, 2026

## Problem

When Hermes source is synced to DGX, Python module shadowing breaks imports:

1. `hermes_cli/gateway.py` shadows the `gateway/` package directory
2. `hermes_cli/cron.py` shadows the `cron` package

**Error**:
```
ModuleNotFoundError: No module named 'gateway.tools'
```

**Root cause**: Python's import system resolves `hermes_cli/gateway.py` before `gateway/__init__.py` when `hermes_cli` is in PYTHONPATH.

## Solution A: Pre-import via importlib.util (Preferred)

Create a wrapper script that pre-imports both packages before importing hermes_cli:

```python
#!/usr/bin/env python3
# run_hermes_fixed.py — Wrapper to prevent module shadowing

import importlib.util
import sys
import os

# Add hermes source to path
sys.path.insert(0, '/data/SpecForge/hermes-agent')

# Pre-import gateway package before hermes_cli shadows it
gateway_spec = importlib.util.spec_from_file_location(
    "gateway", 
    "/data/SpecForge/hermes-agent/gateway/__init__.py"
)
gateway_mod = importlib.util.module_from_spec(gateway_spec)
sys.modules["gateway"] = gateway_mod
gateway_spec.loader.exec_module(gateway_mod)

# Pre-import plugins package
plugins_spec = importlib.util.spec_from_file_location(
    "plugins",
    "/data/SpecForge/hermes-agent/plugins/__init__.py"
)
plugins_mod = importlib.util.module_from_spec(plugins_spec)
sys.modules["plugins"] = plugins_mod
plugins_spec.loader.exec_module(plugins_mod)

# Now safe to import hermes_cli modules
from hermes_cli import run_agent

if __name__ == "__main__":
    run_agent.main()
```

## Solution B: Rename Shadowing Files

```bash
cd /data/SpecForge/hermes-agent

# Rename files
mv hermes_cli/gateway.py hermes_cli/gateway_cmd.py
mv hermes_cli/cron.py hermes_cli/cron_cmd.py

# Update imports in main.py
sed -i 's/from .gateway import/from .gateway_cmd import/g' hermes_cli/main.py
sed -i 's/from .cron import/from .cron_cmd import/g' hermes_cli/main.py

# Update tests
sed -i 's/from hermes_cli.cron import/from hermes_cli.cron_cmd import/g' tests/hermes_cli/test_cron.py
```

## Solution C: Fix PYTHONPATH Order

Ensure `gateway/` and `plugins/` directories are in PYTHONPATH before `hermes_cli/`:

```bash
export PYTHONPATH="/data/SpecForge/hermes-agent/gateway:/data/SpecForge/hermes-agent/plugins:/data/SpecForge/hermes-agent:$PYTHONPATH"
```

**Note**: This is fragile — any script that modifies PYTHONPATH may break the ordering.

## Verification

```bash
cd /data/SpecForge/hermes-agent
venv/bin/python -c "
import gateway.tools
import plugins.manager
print('Module shadowing fixed: gateway and plugins import correctly')
"
```

## Impact on Subsystems

Without this fix, the cognitive orchestrator cannot initialize because:
- `gateway.tools` is needed for tool registration
- `plugins.manager` is needed for plugin loading
- 20 subsystems depend on these modules

**Symptom**: Orchestrator reports 0/20 subsystems active instead of 20/20.

## Deployment Checklist

- [ ] Check if `gateway.py` or `cron.py` exist in `hermes_cli/`
- [ ] If yes, apply Solution A (wrapper script) or Solution B (rename)
- [ ] Verify with import test
- [ ] Restart Hermes and check subsystem count
- [ ] Update systemd service to use wrapper script if using Solution A
