# CheckpointManager and HermesCLI Startup Fixes

Date: 2026-05-18
Session: CLI startup debugging for DGX Qwen integration

## Issues Fixed

### 1. CheckpointManager.__init__() missing parameters

**Symptom:**
```
Failed to initialize agent: CheckpointManager.__init__() got an unexpected keyword argument 'max_total_size_mb'
Failed to initialize agent: CheckpointManager.__init__() got an unexpected keyword argument 'max_file_size_mb'
```

**Root cause:** `config.yaml` has `checkpoints.max_total_size_mb` and `checkpoints.max_file_size_mb` settings. `cli.py` passes both to `CheckpointManager()`, but the class `__init__` only had `enabled` and `max_snapshots`.

**Fix in `tools/checkpoint_manager.py`:**
```python
def __init__(self, enabled: bool = False, max_snapshots: int = 50, 
             max_total_size_mb: int = 500, max_file_size_mb: int = 10):
    self.enabled = enabled
    self.max_snapshots = max_snapshots
    self.max_total_size_mb = max_total_size_mb
    self.max_file_size_mb = max_file_size_mb
```

**Pattern:** When config adds new checkpoint settings, always check if `CheckpointManager.__init__` needs matching parameters. Config and class must stay in sync.

### 2. HermesCLI.__init__ missing _vprint method

**Symptom:**
```
AttributeError: 'HermesCLI' object has no attribute '_vprint'
```

**Root cause:** Self-manager handoff code at line ~2402 calls `self._vprint()` but the method was never defined in the class.

**Fix in `cli.py`:**
Add right after `__init__` ends (before `_invalidate`):
```python
def _vprint(self, message: str, *, force: bool = False) -> None:
    """Verbose print -- only shows if verbose mode is on or force=True."""
    if force or getattr(self, 'verbose', False):
        print(message)
```

### 3. HermesCLI.__init__ missing log_prefix attribute

**Symptom:**
```
AttributeError: 'HermesCLI' object has no attribute 'log_prefix'
```

**Root cause:** Self-manager handoff code references `self.log_prefix` at line ~2402 but the attribute was never set.

**Fix in `cli.py`:**
Add right after `self.verbose` assignment in `__init__`:
```python
self.verbose = verbose if verbose is not None else (self.tool_progress_mode == "verbose")
self.log_prefix = "[hermes] "
```

## Prevention Pattern

When adding code to `HermesCLI.__init__` that references `self.X`:
1. Check if `self.X` is defined earlier in `__init__`
2. If X is a method, verify it's defined before the call site
3. If X is an attribute, add it right after `self.verbose` or at the top of `__init__`
4. Test with `python3 -c "from cli import HermesCLI; print('OK')"`

## Commits
- `96f8e9fe4` — fix: Add missing _vprint method to HermesCLI
- `151976b63` — fix: Add missing log_prefix attribute to HermesCLI.__init__
- `bf53b5b9b` — fix: Add missing max_file_size_mb parameter to CheckpointManager
