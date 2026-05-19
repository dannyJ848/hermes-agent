# CheckpointManager Startup Fixes Reference

Date: 2026-05-18
Related: hermes-agent skill `references/checkpoint-manager-fix-2026-05-18.md`

## Summary

When wiring local inference servers (vLLM, etc.), Hermes CLI startup may fail with CheckpointManager parameter errors. This is a config-class synchronization issue, not an inference server issue.

## Errors and Fixes

### Error 1: max_total_size_mb
```
Failed to initialize agent: CheckpointManager.__init__() got an unexpected keyword argument 'max_total_size_mb'
```

### Error 2: max_file_size_mb
```
Failed to initialize agent: CheckpointManager.__init__() got an unexpected keyword argument 'max_file_size_mb'
```

## Root Cause

Config.yaml has checkpoint settings that get passed to CheckpointManager, but the class __init__ doesn't accept them.

## Quick Fix

See hermes-agent skill `references/checkpoint-manager-fix-2026-05-18.md` for the full fix pattern.

## Prevention

When adding local inference providers to config, always verify:
1. `CheckpointManager.__init__` accepts all parameters that config passes
2. `HermesCLI.__init__` defines all attributes before they are used
3. Clear Python cache after code changes: `find ~/.hermes -name "__pycache__" -type d -exec rm -rf {} +`
