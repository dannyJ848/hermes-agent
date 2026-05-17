# Subconscious Integration Pattern — May 9, 2026

## Overview

This documents the complete pattern for integrating external cognitive systems from `~/subconscious/` into the Hermes Agent source tree.

## Phase 1: Module Migration

### File Counts
- **97 Python modules** from `~/subconscious/` → `~/hermes-agent/agent/` (177 total files) and `tools/` (106 total files)
- **128 data/config files** → `~/.hermes/` directory structure

### Destination Rules

| Source Type | Hermes Destination | Import Pattern |
|-------------|-------------------|----------------|
| Core cognitive (brain, memory, learning) | `agent/` | `from agent.X import ...` |
| Tools (hands, autobrowse, diagnostics) | `tools/` | `from tools.X import ...` |
| Tip system modules | `agent/tip_system/` | `from agent.tip_system.X import ...` |
| Autobrowse modules | `tools/autobrowse/` | `from tools.autobrowse.X import ...` |

### Import Rewriting

Replace across all files:
- `from subconscious.X import` → `from agent.X import`
- `from hermes_X import` → `from tools.X import`
- `from tip_X import` → `from agent.tip_system.X import`
- `from autobrowse_X import` → `from tools.autobrowse.X import`
- `sys.path.insert(0, "~/subconscious")` → REMOVE

## Phase 2: Agent Loop Integration

### Iteration Engine Wiring

Add to `run_agent.py`:
1. Import: `from agent.iteration_engine import IterationEngine, get_engine as _get_iteration_engine`
2. Init: `self.iteration_engine = _get_iteration_engine()`
3. Pre-action hooks in `_invoke_tool` and `_execute_tool_calls_sequential`
4. Post-action hooks with timing capture

### Blackboard Integration

Add to `run_agent.py`:
1. Import: `from agent.multi_agent_blackboard import get_blackboard, get_tool_cache`
2. Init: `self.blackboard = get_blackboard(); self.tool_cache = get_tool_cache()`
3. Populate tool cache after successful tool calls

## Phase 3: Configuration Cleanup

Files to update:
- `~/.hermes/cron/jobs.json` — cron job prompts
- `~/.hermes/memories/MEMORY.md` — memory entries
- `~/.hermes/skills/*/*/SKILL.md` — skill files
- `~/.hermes/config.yaml` — provider configs
- `agent/cognitive_infrastructure_hooks.py` — subprocess paths

## Phase 4: Post-Integration Eradication

**Critical: The old `~/subconscious/` directory may keep being recreated.**

### Detection
```bash
lsof -p $(pgrep -f "hermes") | grep subconscious
```

### Resolution
1. Kill old daemon processes: `ps aux | grep subconscious | grep -v grep`
2. Clear cached bytecode: `find ~/hermes-agent -type d -name __pycache__ -exec rm -rf {} +`
3. Restart hermes
4. Verify: `cd ~ && rm -rf subconscious/ && sleep 5 && ls subconscious/`

## Verification Checklist

- [ ] All modules copied to correct destinations
- [ ] Import paths rewritten
- [ ] sys.path.insert calls removed
- [ ] run_agent.py has iteration engine hooks
- [ ] run_agent.py has blackboard init
- [ ] Tool modules have registry.register()
- [ ] Configuration files updated
- [ ] __pycache__ cleared
- [ ] Hermes restarted
- [ ] ~/subconscious/ NOT recreated
- [ ] Agent initialization succeeds
- [ ] All cognitive systems operational
