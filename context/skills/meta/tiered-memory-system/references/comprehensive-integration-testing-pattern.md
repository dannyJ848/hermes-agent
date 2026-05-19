# Comprehensive Integration Testing Pattern

**Session:** May 6, 2026 — Testing 6 new cognitive systems built after another CLI failed to implement them.

## The Problem

When building multiple interconnected modules (error miner, validator, guard, gate, monitor, watcher), you need to verify:
1. Each module loads independently
2. Each module's core functions work
3. Modules work together in realistic workflows
4. Hook integration points execute without errors
5. Edge cases (dict vs string, missing files, dead PIDs) are handled

## The Pattern

### Phase 1: Individual Module Tests

Test each module in isolation before any integration:

```python
modules = [
    'error_pattern_miner',
    'multi_step_validator', 
    'context_window_guard',
    'distillation_quality_gate',
    'auto_launch_monitor',
    'checkpoint_watcher_daemon'
]

for mod in modules:
    try:
        __import__(mod)
        print(f'✓ {mod}')
    except Exception as e:
        print(f'✗ {mod}: {e}')
```

**Why this matters:** Catches import errors, missing dependencies, syntax errors immediately.

### Phase 2: Functional Tests Per Module

For each module, test its primary functions:

```python
# Error Pattern Miner
miner = ErrorPatternMiner()
result = miner.record_error("patch", "Could not find match")
assert result['category'] == 'patch_match_failure'
patterns = miner.mine_recent(hours=1)
assert len(patterns) >= 1

# Multi-Step Validator
validator = MultiStepValidator()
result = validator.validate_chain(plan_steps)
assert 'valid' in result
assert 'gaps' in result

# Context Window Guard
guard = ContextWindowGuard()
pressure = guard.check_pressure(messages)
assert pressure['status'] in ['ok', 'compress', 'emergency']

# Distillation Quality Gate
gate = DistillationQualityGate()
result = gate.validate_tip("WHEN X, DO Y", evidence_sources=["s1", "s2", "s3"])
assert 'passed' in result
assert 'overall_score' in result

# Auto-Launch Monitor
monitor = AutoLaunchMonitor()
monitor.watch_process("test", pid=99999, restart_cmd="echo 'ok'")
result = monitor.check_process("test")
assert result['status'] in ['alive', 'restarted', 'dead']

# Checkpoint Watcher
watcher = CheckpointWatcherDaemon()
parsed = watcher.parse_log_line("Step 60/4000 | Loss: 3.999")
assert parsed['step'] == 60
```

### Phase 3: Full Workflow Integration

Test modules interacting in a realistic sequence:

```python
# Scenario: Tool fails → error recorded → plan validated → memory checked → tip validated → process monitored

# 1. Record error
miner.record_error("patch", "Could not find match")

# 2. Validate plan that avoids the error
validator.validate_chain([
    {"id": 1, "tool": "read_file", ...},
    {"id": 2, "tool": "patch", ...}
])

# 3. Check memory pressure
bridge.get_stats()

# 4. Validate tip about the fix
gate.validate_tip("WHEN patch fails, use read_file first", evidence_sources=[...])

# 5. Monitor process
monitor.check_process("training")

# 6. Check training log
watcher.check_log("/path/to/train.log", target_step=1000)
```

### Phase 4: Hook Integration Tests

Test that hook functions execute without errors:

```python
# Test all hooks
pre_tool_call_hook({})           # Should return dict
memory_add_hook("k", "v")        # Should return bool
post_tool_call_hook("tool", "error", args={}, session_id="test")  # Should not crash
validate_plan_hook([...])        # Should return validation dict
pre_llm_call_hook([...])         # Should return messages list
```

**Critical:** Use `session_id="test"` (NOT "default") to catch the `_INSTANCES[session_id]` KeyError bug.

## Bug Found: Context Type Mismatch

**Issue:** `post_tool_call_hook` received `context={}` (dict from **kwargs) but tried to slice it as string:
```python
context[:500]  # TypeError: unhashable type: 'slice'
```

**Fix:** Type-check before slicing:
```python
context[:500] if isinstance(context, str) else str(context)[:500]
```

**Lesson:** Hook interfaces that accept **kwargs must handle unexpected types. Always type-check before string operations.

## Key Files

- `hermes_cli/subconscious/error_pattern_miner.py` — 437 lines
- `hermes_cli/subconscious/multi_step_validator.py` — 374 lines
- `hermes_cli/subconscious/context_window_guard.py` — 313 lines
- `hermes_cli/subconscious/distillation_quality_gate.py` — 448 lines
- `hermes_cli/subconscious/auto_launch_monitor.py` — 362 lines
- `hermes_cli/subconscious/checkpoint_watcher_daemon.py` — 413 lines

## Results

| Test | Status | Notes |
|------|--------|-------|
| Module loading | ✅ | 6/6 modules load |
| Functional tests | ✅ | All core functions work |
| Workflow integration | ✅ | Full chain executes |
| Hook integration | ✅ | After bugfix |
| Edge cases | ✅ | Dict context, missing logs, dead PIDs |

**Total test suites:** 9
**Bugs found:** 1 (context type mismatch)
**Fixes applied:** 1
