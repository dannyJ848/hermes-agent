# CheckpointManager `max_total_size_mb` Fix

**Date:** 2026-05-18
**File:** `tools/checkpoint_manager.py`
**Commit:** `be3aa6d30`

## Problem

CLI startup failed with:
```
Failed to initialize agent: CheckpointManager.__init__() got an unexpected keyword argument 'max_total_size_mb'
```

## Root Cause

`CheckpointManager.__init__` only had 2 parameters (`enabled`, `max_snapshots`) but callers in 4 locations passed `max_total_size_mb`:
- `hermes_cli/config.py`
- `hermes_cli/checkpoints.py`
- `run_agent.py`
- `cli.py`

The parameter was omitted during earlier refactoring.

## Fix

Patch `tools/checkpoint_manager.py` line ~291:

```python
# BEFORE:
def __init__(self, enabled: bool = True, max_snapshots: int = 50):
    self.enabled = enabled
    self.max_snapshots = max_snapshots

# AFTER:
def __init__(self, enabled: bool = True, max_snapshots: int = 50, max_total_size_mb: int = 500):
    self.enabled = enabled
    self.max_snapshots = max_snapshots
    self.max_total_size_mb = max_total_size_mb
```

## Verification

```bash
grep -n "def __init__" tools/checkpoint_manager.py
# Expected: def __init__(self, enabled: bool = True, max_snapshots: int = 50, max_total_size_mb: int = 500):
```

## Related Config

```yaml
checkpoints:
  enabled: true
  max_snapshots: 50
  max_total_size_mb: 500
```
