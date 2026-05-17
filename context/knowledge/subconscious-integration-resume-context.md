# Subconscious Integration — Resume Context (July 2026)

## For New CLI Session

### Quick Resume
```bash
hermes --resume subconscious-integration-operational-july2026
```

### Current State: ✅ FULLY OPERATIONAL
- **Integration**: 97 cognitive modules in `agent/` (177 files) + `tools/` (106 files)
- **Plugin**: `~/.hermes/plugins/cognitive-systems/` v2.0.0 **ENABLED** and **LOADED**
- **Coexists with**: `learning-brain` plugin (bundled) — no conflicts
- **Databases**: `cerebrum_memory.db`, `skill_rewards.db`, `distillation_buffer.db` — all healthy
- **Wiring**: Iteration engine at run_agent.py lines 10053-10154
- **Hooks**: 7 hooks registered, 14 total handlers across both plugins
- **Tools**: `screen_capture`, `gui_click`, `gui_type` — all ready
- **`~/subconscious/`**: ✅ Cleared on restart

### Verified Working
1. Every tool call → iteration engine logs before/after
2. Every LLM call → plugin injects context via pre_llm_call hook
3. Session start/end → both plugins' lifecycle hooks fire
4. Self-evolution pipeline → Elo tournaments, tip evolution, hindsight
5. Vision tools → registered and available for use
6. Plugin coexistence → cognitive-systems + learning-brain work together

### Key Commands for Verification
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

### Troubleshooting
| Issue | Fix |
|-------|-----|
| `_vprint AttributeError` | `hermes gateway restart` |
| Plugin test fails with `TypeError` | Use venv python3 (3.11.14), not system (3.8.8) |
| cognitive-systems not showing | `hermes plugins enable cognitive-systems` then restart |

### Files
| Purpose | Path |
|---------|------|
| Checkpoint | `~/.hermes/workspace/checkpoints/subconscious-integration-operational-july2026.json` |
| Full docs | `~/.hermes/knowledge/subconscious-integration-operational.md` |
| Plugin | `~/.hermes/plugins/cognitive-systems/__init__.py` |
| MASTER_DOC | `~/hermes-agent/MASTER_DOC.md` |

### Checkpoint
Label: `subconscious-integration-operational-july2026`
Path: `~/.hermes/workspace/checkpoints/subconscious-integration-operational-july2026.json`
