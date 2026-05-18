# DGX Hermes Module Shadowing Fix (May 16, 2026)

## Problem

When `hermes_cli/gateway.py` exists in the Hermes source tree, it shadows the `gateway/` package directory. Python's module resolution finds `hermes_cli.gateway` (the file) before `gateway` (the package), causing:

```
ModuleNotFoundError: No module named 'gateway.plugins'
```

This prevents the Hermes gateway and plugins from loading correctly.

## Root Cause

Python's import system resolves modules in this order:
1. `sys.path` entries (including current directory)
2. `PYTHONPATH` entries
3. Installed packages

When `hermes_cli/gateway.py` exists and `hermes_cli/` is on `sys.path`, any `import gateway.plugins` resolves to `hermes_cli/gateway.py` (a module, not a package) which has no `plugins` submodule.

## Solution

Use a wrapper script that pre-imports both packages via `importlib.util` before importing `run_agent`:

```python
#!/usr/bin/env python3
"""Hermes Agent launcher with module shadowing fix."""

import importlib.util
import sys

# Pre-import gateway package BEFORE hermes_cli can shadow it
gateway_spec = importlib.util.find_spec("gateway")
if gateway_spec is None:
    # Add gateway directory to path
    sys.path.insert(0, "/data/SpecForge/hermes-agent")
    gateway_spec = importlib.util.find_spec("gateway")

gateway_module = importlib.util.module_from_spec(gateway_spec)
sys.modules["gateway"] = gateway_module
gateway_spec.loader.exec_module(gateway_module)

# Now import hermes_cli (safe — gateway is already in sys.modules)
from hermes_cli import run_agent

# Run the agent
run_agent.main()
```

## Deployment Steps

1. **Create wrapper script** on DGX:
```bash
ssh djg6228@spark-85e8.local "cat > /data/SpecForge/hermes-agent/run_hermes_fixed.py << 'EOF'
#!/usr/bin/env python3
import importlib.util
import sys

# Pre-import gateway package
sys.path.insert(0, "/data/SpecForge/hermes-agent")
gateway_spec = importlib.util.find_spec("gateway")
gateway_module = importlib.util.module_from_spec(gateway_spec)
sys.modules["gateway"] = gateway_module
gateway_spec.loader.exec_module(gateway_module)

# Import and run
from hermes_cli import run_agent
run_agent.main()
EOF"
```

2. **Kill old Hermes processes** (they hold stale module references):
```bash
ssh djg6228@spark-85e8.local "ps aux | grep -E 'hermes|run_agent' | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null; echo 'Old processes killed'"
```

3. **Run with wrapper**:
```bash
ssh djg6228@spark-85e8.local "cd /data/SpecForge/hermes-agent && source venv/bin/activate && python3 run_hermes_fixed.py"
```

## Verification

```bash
# Check no old processes
ssh djg6228@spark-85e8.local "ps aux | grep -E 'hermes|run_agent' | grep -v grep || echo 'Clean'"

# Check module resolution
ssh djg6228@spark-85e8.local "cd /data/SpecForge/hermes-agent && source venv/bin/activate && python3 -c 'import gateway; print(gateway.__file__)'"
# Should show: /data/SpecForge/hermes-agent/gateway/__init__.py
# NOT: /data/SpecForge/hermes-agent/hermes_cli/gateway.py
```

## Alternative: Rename Shadowing File

If wrapper is too complex, rename the shadowing file:
```bash
cd /data/SpecForge/hermes-agent
mv hermes_cli/gateway.py hermes_cli/gateway_cmd.py
# Update all imports: from .gateway import → from .gateway_cmd import
```

## Related

- `dgx-hermes-cognitive-orchestrator-init-may16-2026.md` — Initializing cognitive orchestrator after fix
- `dgx-hermes-full-system-verification.md` — Full system verification post-deployment
