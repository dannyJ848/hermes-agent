# Module Shadowing: `hermes_cli.plugins` vs `plugins/` Package

## Problem

When `run_agent.py` imports `hermes_cli.plugins` (a single-file module), Python registers `plugins` in `sys.modules` pointing to `hermes_cli/plugins.py`. This shadows the `plugins/` directory package, breaking ALL `plugins.X` imports.

## Error Signatures

```
Memory provider plugin init failed: No module named 'plugins.memory'; 'plugins' is not a package
Failed to load plugin 'spotify': No module named 'plugins.spotify'; 'plugins' is not a package
Failed to load plugin 'google_chat-platform': No module named 'gateway.status'; 'gateway' is not a package
```

## Root Cause

```python
import sys

# Before importing run_agent.py:
'plugins' not in sys.modules  # True

# After importing run_agent.py:
import run_agent
sys.modules['plugins']  # <module 'plugins' from 'hermes_cli/plugins.py'>
hasattr(sys.modules['plugins'], '__path__')  # False — NOT a package
```

## Fix

Add at the VERY TOP of `run_agent.py`, before any other imports:

```python
import sys
import importlib.util

# Force plugins package to load BEFORE hermes_cli.plugins can shadow it
_plugins_spec = importlib.util.spec_from_file_location(
    "plugins",
    "/data/SpecForge/hermes-agent/plugins/__init__.py",
    submodule_search_locations=["/data/SpecForge/hermes-agent/plugins"]
)
_plugins_mod = importlib.util.module_from_spec(_plugins_spec)
sys.modules["plugins"] = _plugins_mod
_plugins_spec.loader.exec_module(_plugins_mod)
```

## Verification

```python
import sys
print(sys.modules['plugins'].__file__)  # Should end in plugins/__init__.py
print(hasattr(sys.modules['plugins'], '__path__'))  # Should be True
```

## Related Shadowing Issues

Same pattern affects `gateway` package if `hermes_cli/gateway.py` exists:
```
Failed to load plugin 'google_chat-platform': No module named 'gateway.status'; 'gateway' is not a package
```

Fix: Same pre-import pattern for `gateway` package.

## Session Context

- **Date:** May 15, 2026
- **System:** DGX Spark, Hermes Agent with 20 cognitive subsystems
- **Trigger:** Memory provider 'holographic' failed to initialize
- **Impact:** 19/20 subsystems active (cortex_flywheel blocked)
- **Resolution:** Pre-import fix restored all 20 subsystems
