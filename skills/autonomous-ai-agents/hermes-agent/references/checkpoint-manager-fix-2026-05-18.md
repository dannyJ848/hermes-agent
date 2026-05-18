# CheckpointManager Startup Parameter Fixes

**Date:** 2026-05-18
**File:** `tools/checkpoint_manager.py`
**Commits:** `be3aa6d30` (max_total_size_mb), `bf53b5b9b` (max_file_size_mb)

## Problem 1: max_total_size_mb

CLI startup failed with:
```
Failed to initialize agent: CheckpointManager.__init__() got an unexpected keyword argument 'max_total_size_mb'
```

## Problem 2: max_file_size_mb

Later, after fixing the first error:
```
Failed to initialize agent: CheckpointManager.__init__() got an unexpected keyword argument 'max_file_size_mb'
```

## Root Cause

`CheckpointManager.__init__` only had 2 parameters (`enabled`, `max_snapshots`) but callers in multiple locations passed additional parameters:
- `max_total_size_mb`: passed by `hermes_cli/config.py`, `hermes_cli/checkpoints.py`, `run_agent.py`, `cli.py`
- `max_file_size_mb`: passed by `cli.py` line ~3926

Both parameters were omitted during earlier refactoring when checkpoint config was extended but the consuming class wasn't updated.

## Fix

Patch `tools/checkpoint_manager.py` line ~291:

```python
# BEFORE (original):
def __init__(self, enabled: bool = True, max_snapshots: int = 50):
    self.enabled = enabled
    self.max_snapshots = max_snapshots

# AFTER (final):
def __init__(self, enabled: bool = False, max_snapshots: int = 50, max_total_size_mb: int = 500, max_file_size_mb: int = 10):
    self.enabled = enabled
    self.max_snapshots = max_snapshots
    self.max_total_size_mb = max_total_size_mb
    self.max_file_size_mb = max_file_size_mb
```

## Verification

```bash
grep -n "def __init__" tools/checkpoint_manager.py
# Expected: def __init__(self, enabled: bool = False, max_snapshots: int = 50, max_total_size_mb: int = 500, max_file_size_mb: int = 10):
```

## Related Config

```yaml
checkpoints:
  enabled: true
  max_snapshots: 50
  max_total_size_mb: 500
  max_file_size_mb: 10
```

## Pattern: Config-Class Sync

When config adds new settings, always check if the consuming class `__init__` needs matching parameters. When adding code to `__init__` that references `self.X`, verify `X` is defined earlier. This applies to CheckpointManager, HermesCLI, and any class that receives config values.
