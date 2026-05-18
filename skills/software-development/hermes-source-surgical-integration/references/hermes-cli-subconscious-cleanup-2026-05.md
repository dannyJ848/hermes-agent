# hermes_cli/subconscious/ Cleanup — May 2026

## Context

After bulk-moving 95+ modules from `~/subconscious/` to `~/hermes-agent/agent/` in a previous session, a secondary directory `hermes_cli/subconscious/` was discovered containing 30 additional modules. Many of these were unique and not duplicated in `agent/` or `tools/`.

## Discovery

```python
# Find modules unique to hermes_cli/subconscious/
sub_modules = {f.stem for f in Path("hermes_cli/subconscious").glob("*.py")}
agent_modules = {f.stem for f in Path("agent").glob("*.py")}
tools_modules = {f.stem for f in Path("tools").glob("*.py")}
unique = sub_modules - agent_modules - tools_modules
# Result: 27 unique modules, 3 duplicates
```

## Modules Moved (27)

| Module | Purpose |
|--------|---------|
| `agent_loop_optimizer` | Optimize agent loop performance |
| `auto_compressor` | Automatic context compression |
| `auto_fallback_engine` | Fallback engine for failed tools |
| `auto_launch_monitor` | Monitor auto-launched processes |
| `autobrowse_analyzer` | Autobrowse result analyzer |
| `autobrowse_graduator` | Tip grading from autobrowse |
| `autobrowse_injector` | Inject autobrowse into hooks |
| `autobrowse_synthesizer` | Strategy synthesis |
| `autobrowse_tracer` | Execution tracer |
| `checkpoint_watcher_daemon` | Watch checkpoint files |
| `context_window_guard` | Guard against context overflow |
| `distillation_quality_gate` | Quality gate for distillation |
| `error_pattern_miner` | Mine error patterns from logs |
| `hermes_enhancement_suite` | Enhancement suite |
| `hermes_harness_enhancer` | Harness gap analysis |
| `memory_cortex_bridge` | Bridge memory to CortexDB |
| `memory_daemon` | Background memory daemon |
| `multi_step_validator` | Validate multi-step plans |
| `proactive_memory_guard` | Proactive memory management |
| `self_audit_engine` | Self-audit system |
| `session_continuity_engine` | Session continuity |
| `smart_tool_router` | Intelligent tool routing |
| `subconscious_hook_wiring` | Wire all systems into hooks |
| `subconscious_systems_manifest` | Systems manifest |
| `test_autobrowse_r191` | Autobrowse R191 tests |
| `tiered_memory` | Hot→Warm→Cold memory tiers |
| `tool_intelligence_tracker` | Track tool intelligence |

## Duplicates Removed (3)

- `cortex_access.py` — already in `agent/cortex_access.py`
- `cortex_flywheel.py` — already in `agent/cortex_flywheel.py`
- `llm_judge.py` — already in `agent/llm_judge.py`

## Import Fixes Required

After moving `tiered_memory.py` to `agent/`, these files needed import updates:

```python
# agent/memory_daemon.py
-from tiered_memory import TieredMemory
+from agent.tiered_memory import TieredMemory

# agent/tiered_memory.py (docstring example)
-from tiered_memory import TieredMemory
+from agent.tiered_memory import TieredMemory
```

## Path References Cleaned

Files that had hardcoded paths to `~/subconscious/` or `hermes_cli/subconscious/`:

- `agent/cognitive_infrastructure_hooks.py` — subprocess calls to `hermes_manual_triggers.py`
- `tools/health_daemon.py` — daemon path reference
- `tools/self_manager.py` — self-manager path
- `tools/skill_generator.py` — source file reference
- `hermes_cli/instant_context.py` — quick command references
- `hermes_cli/session_bootstrap.py` — startup references
- `agent/hermes_cli_resume.py` — resume script path
- `agent/testing_gym.py` — benchmark prompt reference
- `agent/agent_scorecard.py` — DB and roadmap paths
- `agent/phantom_extractor.py` — phantom browser script path
- `setup_unified_context.py` — context setup references

## Verification

```python
# Final check: zero remaining references
for py_file in hermes_dir.rglob("*.py"):
    if "~/subconscious/" in py_file.read_text():
        print(f"FOUND: {py_file}")
# Result: 0 files
```

## Key Lesson

Always check for **secondary directories** that may contain additional modules. The `hermes_cli/subconscious/` directory was a copy/backup that became a hidden dependency. After integration, delete the directory to prevent confusion.
