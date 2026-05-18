# Monolithic Cognitive Integration — Session Reference

**Date**: 2026-05-18
**Commit**: c2cccabf1 (origin/main)
**Score**: 100/100

## What This Is

This reference documents the monolithic cognitive integration that replaced plugin hook indirection with direct function calls. The 7 cognitive systems were previously loaded through a plugin mechanism (`cognitive_systems_plugin.py` using `_load_system()`) that broke when class names drifted between the plugin loader and actual module exports.

## The 7 Cognitive Systems

| System | Module | Type | Hook API Added |
|--------|--------|------|----------------|
| iteration_engine | `agent/iteration_engine.py` | Class `IterationEngine` | `on_task_end()` |
| cortex_flywheel | `agent/cortex_access.py` | Class `CortexDB` | `record_turn()` |
| agent_scorecard | `agent/agent_scorecard.py` | Module (functions) | `record_tool_call()`, `get_recent_tool_stats()` |
| red_team_hippocampus | `agent/red_team_hippocampus.py` | Module (functions) | `mine_error()` |
| tool_misuse_prevention | `agent/tool_misuse_prevention.py` | Module (functions) | `check_misuse()` |
| memory_cortex_bridge | `agent/memory_cortex_bridge.py` | Class `MemoryCortexBridge` | `consolidate_turn()` |
| hermes_enhancement_suite | `agent/hermes_enhancement_suite.py` | Class `HermesEnhancementSuite` | `track_turn()` |

## Class Name Mismatches Discovered

The old `cognitive_systems_plugin.py` imported these non-existent names:
- `AgentScorecard` → actual module exports functions only
- `ToolHealthMonitor` → actual module exports functions only
- `ErrorMiner` → actual module exports functions only
- `MemoryBridge` → actual class is `MemoryCortexBridge`
- `EnhancementTracker` → actual class is `HermesEnhancementSuite`

**Lesson**: Always verify with `dir(mod)` before assuming class names. The modules `agent_scorecard`, `tool_misuse_prevention`, and `red_team_hippocampus` are function-only — they have no classes.

## Integration Points

### `run_agent.py` — 5 hooks inlined

```python
# Before (broken plugin indirection):
csp = load_cognitive_systems_plugin()
csp.invoke_hook("on_session_start", ...)

# After (direct calls):
import agent.cognitive_systems_plugin as csp
# on_session_start
csp.iteration_engine.get_learning_stats()
# pre_llm_call
csp.iteration_engine.get_learning_stats()
# pre_tool_call
csp.tool_misuse_prevention.check_misuse(tool_name, tool_args)
# post_tool_call
csp.agent_scorecard.record_tool_call(tool_name, success, latency_ms)
csp.red_team_hippocampus.mine_error(error_msg, tool_name, phase)
# post_llm_call
csp.cortex_flywheel.record_turn(role, content)
csp.memory_cortex_bridge.consolidate_turn(user_msg, assistant_msg, tool_calls)
csp.hermes_enhancement_suite.track_turn(role, content)
# on_session_end
csp.iteration_engine.on_task_end(session_summary)
```

### `model_tools.py` — 2 hooks inlined

Same pattern: replace `csp.invoke_hook("pre_tool_call", ...)` with direct `csp.tool_misuse_prevention.check_misuse(...)`.

## Critical Recovery Notes

1. **memory_cortex_bridge.py corruption**: Early edit attempts using `with open()/lines/split/concat` on a malformed file produced a 69-line truncation that destroyed the `MemoryCortexBridge` class. **Fix**: Restore from git (`git show e2fe308b1:agent/memory_cortex_bridge.py`) then re-apply patches.

2. **iteration_engine.py indent error**: First attempt to add `on_task_end()` was at module level (line 582, indent 4) instead of inside `IterationEngine` class. Python saw "unexpected indent". **Fix**: Remove wrongly-placed method, re-insert inside class before `def get_engine`.

3. **cortex_flywheel vs cortex_access**: The plugin loader's `_load_system("cortex_flywheel")` returned `CortexDB` from `agent.cortex_access`, NOT `CortexFlywheel` from `agent.cortex_flywheel`. The `record_turn()` method must be on `CortexDB`.

## Verification Command

```python
import agent.cognitive_systems_plugin as csp

systems = {
    "iteration_engine": (csp.iteration_engine, ["get_learning_stats", "on_task_end"]),
    "cortex_flywheel": (csp.cortex_flywheel, ["record_turn"]),
    "agent_scorecard": (csp.agent_scorecard, ["record_tool_call", "get_recent_tool_stats"]),
    "red_team_hippocampus": (csp.red_team_hippocampus, ["mine_error"]),
    "tool_misuse_prevention": (csp.tool_misuse_prevention, ["check_misuse"]),
    "memory_cortex_bridge": (csp.memory_cortex_bridge, ["consolidate_turn"]),
    "hermes_enhancement_suite": (csp.hermes_enhancement_suite, ["track_turn"]),
}

for name, (obj, methods) in systems.items():
    assert obj is not None, f"{name} failed to load"
    for m in methods:
        assert hasattr(obj, m), f"{name}.{m} missing"
    print(f"✓ {name}")
```

## Git History Cleanup

Large files (>100MB cache/dataset, checkpoints) and secrets (`.env`, `auth.json`, `bin/tirith` containing GitHub PAT) were removed from history using `git filter-branch`. Force-push was acceptable because this was a personal repo. Always verify no secrets remain before pushing.

## Files Modified

- `agent/cognitive_systems_plugin.py` — rewritten with module-level attribute exports
- `agent/iteration_engine.py` — added `on_task_end()`
- `agent/cortex_access.py` — added `record_turn()` to `CortexDB`
- `agent/agent_scorecard.py` — added `record_tool_call()`, `get_recent_tool_stats()`
- `agent/red_team_hippocampus.py` — added `mine_error()`
- `agent/tool_misuse_prevention.py` — added `check_misuse()`
- `agent/memory_cortex_bridge.py` — restored from git, added `consolidate_turn()`
- `agent/hermes_enhancement_suite.py` — added `track_turn()`
- `run_agent.py` — inline hook calls
- `.gitignore` — added `*.db`, `checkpoints/`, `backups/`, `state-snapshots/`
