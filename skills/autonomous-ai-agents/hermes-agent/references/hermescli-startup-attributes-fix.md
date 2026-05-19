# HermesCLI Startup Attribute Fixes

Date: 2026-05-18
File: `cli.py` (HermesCLI class)
Commits: `96f8e9fe4` (_vprint), `151976b63` (log_prefix)

## Problem

After inserting self-manager handoff code into `HermesCLI.__init__`, CLI startup failed with:

```
AttributeError: 'HermesCLI' object has no attribute '_vprint'
```

Then after fixing that:

```
AttributeError: 'HermesCLI' object has no attribute 'log_prefix'
```

## Root Cause

The self-manager auto-resume code at line ~2402 in `__init__` calls:
```python
self._vprint(f"{self.log_prefix}🔄 Auto-resuming from handoff: {resume}", force=True)
```

But both `_vprint` (method) and `log_prefix` (attribute) were not yet defined when this line executed.

## Fix 1: Add _vprint method

Insert right after `__init__` ends (before `_invalidate`):

```python
    def _vprint(self, message: str, *, force: bool = False) -> None:
        """Verbose print -- only shows if verbose mode is on or force=True."""
        if force or getattr(self, 'verbose', False):
            print(message)

    def _invalidate(self, min_interval: float = 0.25) -> None:
```

## Fix 2: Add log_prefix attribute

Insert right after `self.verbose` assignment in `__init__`:

```python
        self.verbose = verbose if verbose is not None else (self.tool_progress_mode == "verbose")
        self.log_prefix = "[hermes] "
```

## Verification

```python
from cli import HermesCLI
import inspect

# Check _vprint exists
assert hasattr(HermesCLI, '_vprint')
sig = inspect.signature(HermesCLI._vprint)
assert 'message' in sig.parameters
assert 'force' in sig.parameters

# Check log_prefix is set during __init__
# (requires instantiation, verify no AttributeError)
```

## Pattern: __init__ Dependency Ordering

When adding code to `__init__` that references `self.X`:
1. Verify `self.X` is defined earlier in `__init__` (for attributes)
2. Or verify `X` is a method defined before the call site (for methods)
3. If `X` doesn't exist yet, add it before the code that uses it
4. For methods called from `__init__`, define them right after `__init__` ends

This applies to any class, not just HermesCLI. Common missing attributes during refactoring:
- `_vprint`, `_emit_status`, `_show_status` — print helpers
- `log_prefix`, `session_prefix` — string prefixes
- `_background_tasks`, `_task_counter` — background job tracking
