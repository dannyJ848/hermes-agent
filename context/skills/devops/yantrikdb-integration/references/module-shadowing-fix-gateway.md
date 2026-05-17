# Gateway Module Shadowing Fix

## Problem

`hermes_cli/gateway.py` (a single file module) shadows the `gateway/` package directory. When Python imports `gateway.status`, it resolves `gateway` to `hermes_cli/gateway.py` (a file, not a package), causing:

```
ModuleNotFoundError: No module named 'gateway.status'; 'gateway' is not a package
```

This breaks the gateway service entirely — cron jobs don't fire, messaging platforms don't connect.

## Root Cause

Python's `sys.modules` caches the first successful import of a name. If `hermes_cli.gateway` is imported before `gateway.__init__`, the `gateway` key points to a file module, and all subsequent `import gateway.X` lookups fail because a file module has no submodules.

## Fix: Pre-import the package

Add this block at the top of `hermes_cli/gateway.py`, BEFORE any `from gateway import ...` statements:

```python
import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

_gateway_pkg_dir = PROJECT_ROOT / "gateway"
if _gateway_pkg_dir.is_dir() and "gateway" not in sys.modules:
    _gateway_init = _gateway_pkg_dir / "__init__.py"
    if _gateway_init.exists():
        _gateway_spec = importlib.util.spec_from_file_location(
            "gateway",
            str(_gateway_init),
            submodule_search_locations=[str(_gateway_pkg_dir)]
        )
        _gateway_mod = importlib.util.module_from_spec(_gateway_spec)
        sys.modules["gateway"] = _gateway_mod
        _gateway_spec.loader.exec_module(_gateway_mod)
```

## Same fix for `plugins` package

`hermes_cli/plugins.py` can shadow the `plugins/` directory package. Apply the same pattern in `run_agent.py` or `cli.py` before any `from plugins import ...` or `import plugins`:

```python
_plugins_pkg_dir = PROJECT_ROOT / "plugins"
if _plugins_pkg_dir.is_dir() and "plugins" not in sys.modules:
    _plugins_init = _plugins_pkg_dir / "__init__.py"
    if _plugins_init.exists():
        _plugins_spec = importlib.util.spec_from_file_location(
            "plugins",
            str(_plugins_init),
            submodule_search_locations=[str(_plugins_pkg_dir)]
        )
        _plugins_mod = importlib.util.module_from_spec(_plugins_spec)
        sys.modules["plugins"] = _plugins_mod
        _plugins_spec.loader.exec_module(_plugins_mod)
```

## Verification

```python
import sys
print(sys.modules['gateway'].__file__)   # Should end with gateway/__init__.py
print(sys.modules['plugins'].__file__)   # Should end with plugins/__init__.py

import gateway.status      # Should succeed
import plugins.memory      # Should succeed
```

## Platforms Affected

- DGX Spark (Linux, systemd service)
- MacBook (macOS, launchd service)
- Any Hermes installation where `hermes_cli/` files shadow package directories

## Related

- `hermes-agent` skill: module-shadowing-fix-may15-2026.md reference
- DGX deployment: run_hermes_dgx_fixed.py wrapper script
