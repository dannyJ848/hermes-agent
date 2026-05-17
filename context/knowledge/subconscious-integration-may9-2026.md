# Subconscious Integration Complete — May 9, 2026

## Summary

All cognitive systems, training infrastructure, and support modules from `~/subconscious/` have been surgically integrated into the Hermes Agent source tree (`~/hermes-agent/`). This eliminates the external dependency and makes all systems first-class citizens of the agent.

## What Was Done

### Phase 1 — Module Migration
- **97 Python modules** from `~/subconscious/` copied to `~/hermes-agent/agent/` (177 total files) and `tools/` (106 total files)
- **128 data/config files** moved to `~/.hermes/` directory structure
- Import paths updated across all modules:
  - `from subconscious.X import ...` → `from agent.X import ...`
  - `from hermes_hands import ...` → `from tools.hands import ...`
- `sys.path.insert("~/subconscious")` calls removed from all files

### Phase 2 — Configuration Updates
- **Cron job prompts** updated to reference `~/hermes-agent/agent/` paths
- **MEMORY.md** corrected (LLM Judge provider: DeepSeek v4-pro)
- **SKILL.md** corrected (training gym paths)
- **5 cron jobs** updated with new paths

### Phase 3 — Agent Loop Integration
- **Iteration engine** (`agent/iteration_engine.py`) wired into `run_agent.py`:
  - Import added at line ~159
  - Initialization after subconscious plugin loader
  - Pre-action hooks in `_invoke_tool` and `_execute_tool_calls_sequential`
  - Post-action hooks with timing capture in both paths
- **Blackboard** (`agent/multi_agent_blackboard.py`) integrated:
  - `get_blackboard()` and `get_tool_cache()` imported
  - Initialized in `AIAgent.__init__`
  - Tool cache populated after successful tool calls
- **Multi-agent coordinator** created but not yet wired into runtime

### Phase 4 — Path Reference Cleanup
- Fixed `agent/hermes_harness_v2.py` line 61: changed `~/subconscious` → `~/hermes-agent/agent`
- Fixed `agent/pruner_integration.py` line 35: removed sys.path.insert, uses `from agent.memory_auto_pruner import prune`
- Verified zero `~/subconscious/` path references remain in active source code

## Verification Results

- ✅ Full agent initialization succeeds
- ✅ `iteration_engine`, `blackboard`, `tool_cache`, `subconscious_plugins` all operational
- ✅ Blackboard test: message posting and tool cache retrieval work
- ✅ Module counts: 177 agent/, 106 tools/
- ✅ All 17 key modules import successfully
- ✅ Zero source code references to `~/subconscious/`

## Known Issue — Pending

⚠️ **~/subconscious/ directory keeps being recreated**

- File created: `tool_capability.db` (40960 bytes)
- Recreated within 1-2 seconds after deletion
- Main hermes process (PID 98882) has file open (confirmed via lsof)
- Source code contains NO references to `~/subconscious/` path
- Likely cause: Cached bytecode or module-level path constants in loaded modules

**Resolution needed:**
1. Clear all `__pycache__` directories: `find ~/hermes-agent -type d -name __pycache__ -exec rm -rf {} +`
2. Restart hermes agent to clear module state
3. Verify directory is no longer recreated

## Files Modified

- `run_agent.py` — iteration engine imports, initialization, hooks
- `agent/hermes_harness_v2.py` — path fix
- `agent/pruner_integration.py` — import fix
- `MASTER_DOC.md` — updated integration status
- `agent/multi_agent_blackboard.py` — new file
- `agent/multi_agent_coordinator.py` — new file

## Next Steps

1. Clear `__pycache__` and restart hermes
2. Verify `~/subconscious/` eradication
3. Wire multi-agent coordinator into runtime
4. Update daemon launch paths to use `~/hermes-agent/agent/`
5. Test full cognitive system stack end-to-end
