# Module Shadowing Fix: hermes_cli Files vs Package Directories

## Problem

When `hermes_cli/<name>.py` exists (e.g., `hermes_cli/gateway.py`, `hermes_cli/plugins.py`), it shadows the `<name>/` package directory. Python's `sys.modules` caches the first import, so `import gateway.status` resolves to the file module (no submodules) instead of the package.

## Root Cause

Python's import system: if `hermes_cli.gateway` is imported before `gateway.__init__`, the `gateway` key in `sys.modules` points to a file module. All subsequent `import gateway.X` lookups fail because a file module has no submodules.

## Symptoms

- `hermes gateway status` → `ModuleNotFoundError: No module named 'gateway.status'`
- `hermes gateway restart` → same error, gateway service down
- `hermes cron status` → "Gateway is NOT running"
- Plugin loading fails: `No module named 'plugins.memory'; 'plugins' is not a package`

## Fix: Pre-import the package

Add this block at the top of `hermes_cli/<name>.py`, BEFORE any `from <name> import ...`:

```python
import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

_pkg_dir = PROJECT_ROOT / "<name>"
if _pkg_dir.is_dir() and "<name>" not in sys.modules:
    _init = _pkg_dir / "__init__.py"
    if _init.exists():
        _spec = importlib.util.spec_from_file_location(
            "<name>",
            str(_init),
            submodule_search_locations=[str(_pkg_dir)]
        )
        _mod = importlib.util.module_from_spec(_spec)
        sys.modules["<name>"] = _mod
        _spec.loader.exec_module(_mod)
```

## Affected Names

- `gateway` → `hermes_cli/gateway.py` shadows `gateway/` package
- `plugins` → `hermes_cli/plugins.py` shadows `plugins/` package
- Any other `<name>` where both `hermes_cli/<name>.py` and `<name>/__init__.py` exist

## Verification

```python
import sys
print(sys.modules['gateway'].__file__)   # Should end with gateway/__init__.py
print(hasattr(sys.modules['gateway'], '__path__'))  # Should be True

import gateway.status      # Should succeed
import plugins.memory       # Should succeed
```

## Platforms Affected

- DGX Spark (Linux)
- MacBook (macOS)
- Any Hermes installation with `hermes_cli/` files shadowing package directories

## Related

- `hermes-cron-infrastructure` skill: `references/gateway-module-shadowing-fix-2026-05-17.md`
- `yantrikdb-integration` skill: `references/module-shadowing-fix-gateway.md`
