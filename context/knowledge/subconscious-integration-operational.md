# Subconscious Integration — Operational (July 2026)

## Status: ✅ FULLY OPERATIONAL

All 97 cognitive modules from `~/subconscious/` are fully migrated, wired, and running in production.

## Plugin Verification

```bash
$ hermes plugins list | grep cognitive-systems
│ cognitive-systems   │ enabled     │ 2.0.0   │ Integrated cognitive │ user    │
```

**Plugin state:**
- `enabled=True`
- `module loaded=True`
- Source: `~/.hermes/plugins/cognitive-systems/`

## Hook Registration (Verified)

| Hook | Handlers | cognitive-systems | learning-brain | Others |
|------|----------|-------------------|----------------|--------|
| on_session_start | 2 | ✅ _on_session_start_handler | ✅ on_session_start_hook | — |
| pre_tool_call | 4 | ✅ _pre_tool_call_handler | ✅ pre_tool_call_hook | 2 others |
| post_tool_call | 4 | ✅ _post_tool_call_handler | ✅ post_tool_call_hook | 2 others |
| on_session_end | 2 | ✅ _on_session_end_handler | ✅ on_session_end_hook | — |
| pre_llm_call | 3 | ✅ _pre_llm_call_handler | — | 2 others |
| post_llm_call | 1 | ✅ _post_llm_call_handler | — | — |
| post_api_request | 1 | ✅ _on_post_api_request | — | — |

**No conflicts detected.** Both plugins coexist — handlers fire in sequence.

## Tools Registered (Verified)

| Tool | Status | Source |
|------|--------|--------|
| screen_capture | ✅ Ready | cognitive-systems |
| gui_click | ✅ Ready | cognitive-systems |
| gui_type | ✅ Ready | cognitive-systems |

## run_agent.py Wiring (Confirmed)

```
Line 10053: iteration_engine.before_action() — before every tool call
Line 10143: iteration_engine.after_action() — after every tool call
Line 11601: invoke_hook("pre_llm_call") — before every LLM call
Line 14870: invoke_hook("post_llm_call") — after every LLM response
Line 11459: invoke_hook("on_session_start") — session start
Line 14985: invoke_hook("on_session_end") — session end
```

## Self-Evolution Pipeline

```python
from agent.self_evolution import SelfEvolutionPipeline
pipeline = SelfEvolutionPipeline()

# Full cycle
result = pipeline.run_cycle()
# Returns: {distilled: int, tournament_matches: int, evolved: int, top_tip: str}

# Hindsight
pipeline.record_hindsight(task_id, description, approach, result, ...)
pipeline.get_hindsight_for_task("current task description")
```

## Databases (Healthy)

```bash
$ ls -la ~/.hermes/*.db
-rw-r--r-- 1 user staff  81920 Jul 2026 cerebrum_memory.db      # 10 tables
-rw-r--r-- 1 user staff  32768 Jul 2026 distillation_buffer.db  # 4 tables
-rw-r--r-- 1 user staff  24576 Jul 2026 skill_rewards.db        # 3 tables
```

## Cleanup Status

| Item | Status |
|------|--------|
| `~/subconscious/` directory | ✅ Cleared on restart |
| `hermes_cli/plugins.py` dead code | ✅ Removed |
| `run_agent.py` old init call | ✅ Removed |
| Self-imports in agent/ | ✅ Fixed (agent. prefix) |
| Git commit | 0390d936d |

## Python Environment

| Environment | Version | Usage |
|-------------|---------|-------|
| System python3 | 3.8.8 | CLI wrapper |
| venv python3 | 3.11.14 | Hermes runtime, plugin testing |

**Always use venv for plugin testing:**
```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 -c "..."
```

## Known Issues & Resolutions

| Issue | Cause | Resolution |
|-------|-------|------------|
| `_vprint AttributeError` | learning-brain plugin injected code into CLI init | `hermes gateway restart` |
| `TypeError: unsupported operand type` | Used system Python 3.8 instead of venv 3.11 | Use venv python3 |
| `~/subconscious/ recreates` | Running process held old path open | Restart clears it |

## Plugin Coexistence

cognitive-systems and learning-brain plugins both register overlapping hooks. The Hermes plugin system allows multiple handlers per hook — they fire in sequence. No deduplication or conflict resolution is applied; each handler operates independently.

## Quick Verification Commands

```bash
# Verify plugin loaded
hermes plugins list | grep cognitive-systems

# Verify hooks (via venv python)
/Users/dannygomez/hermes-agent/venv/bin/python3 -c "
from hermes_cli.plugins import get_plugin_manager
m = get_plugin_manager()
m.discover_and_load(force=True)
for name, handlers in m._hooks.items():
    if handlers: print(f'{name}: {len(handlers)} handlers')
"

# Verify tools
hermes tools list | grep -E "screen_capture|gui_click|gui_type"

# Test vision
hermes tools screen_capture
```

## Files

| Purpose | Path |
|---------|------|
| Checkpoint | `~/.hermes/workspace/checkpoints/subconscious-integration-operational-july2026.json` |
| Knowledge (this file) | `~/.hermes/knowledge/subconscious-integration-operational.md` |
| Resume context | `~/.hermes/knowledge/subconscious-integration-resume-context.md` |
| Plugin | `~/.hermes/plugins/cognitive-systems/__init__.py` |
| Plugin manifest | `~/.hermes/plugins/cognitive-systems/plugin.yaml` |
| Iteration Engine | `~/hermes-agent/agent/iteration_engine.py` |
| Self-Evolution | `~/hermes-agent/agent/self_evolution.py` |
| Vision System | `~/hermes-agent/agent/vision_loop.py` |
| MASTER_DOC | `~/hermes-agent/MASTER_DOC.md` |

## Date
Verified operational: July 2026
