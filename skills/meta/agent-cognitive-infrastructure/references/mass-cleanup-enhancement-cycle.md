# Mass Cleanup + Enhancement Cycle Pattern

## Session: May 9, 2026 — Hermes Apparatus v2.1 Enhancement

## Context
After months of training gym rounds (R100-R264+), the cognitive apparatus had accumulated massive bloat:
- 530 subconscious modules (91% orphaned, never imported)
- 46 custom tools (only 1 registered with Hermes)
- 42 databases (32 empty ghosts)
- 6 high-value plugins disabled
- No tip survival tracking
- No project-based memory
- No predictive tool routing

## The Pattern: 5-Phase Enhancement Cycle

### Phase 1: AUDIT & CLEANUP
1. **Identify orphans**: Build import map — which modules are actually imported by plugins?
2. **Archive dead code**: Move orphaned modules to `~/subconscious/archive/` (don't delete, preserve history)
3. **Delete empty databases**: Drop 0.0MB schema ghosts after backing up schemas
4. **Register stranded tools**: Add `@register_tool` decorators to high-value custom tools

**Key technique**: Use `execute_code` to build the import map programmatically:
```python
modules = [f for f in os.listdir(sub_dir) if f.endswith('.py')]
imported_by = {m: [] for m in modules}
for m in modules:
    with open(os.path.join(sub_dir, m)) as f:
        content = f.read()
    for other in modules:
        if other != m and f"import {other.replace('.py', '')}" in content:
            imported_by[other].append(m)
orphans = [m for m, importers in imported_by.items() if len(importers) == 0]
```

### Phase 2: ACTIVATE DORMANT SYSTEMS
1. **Enable high-value plugins**: `hermes plugins enable <name>`
   - evey-honcho (unlimited semantic memory)
   - evey-mesh (multi-agent coordination)
   - evey-sandbox (Docker security)
2. **Create missing tables**: Use `execute_code` + sqlite3 to add tables the code expects
3. **Wire tracking hooks**: Patch the distillation plugin's post_tool_call to call new functions

### Phase 3: BUILD QUALITY SYSTEMS
1. **Tip survival tracking**: 
   - Table: `tip_survival(tip_id, opportunities, applications, survival_rate)`
   - Hook: `_update_tip_opportunities()` in post_tool_call
   - Detection: `_detect_tip_application()` via keyword matching
   - Pruning: `_auto_prune_weak_tips()` at <30% after 100 ops
2. **Adversarial validation**:
   - Function: `_adversarial_validate_tip()` using DeepSeek V4 Pro
   - Table: `tip_adversarial(tip_id, robustness, verdict, failure_modes)`
   - Batch runner: `_run_adversarial_batch(limit=50)`
3. **Predictive tool router**:
   - DB: `tool_performance_summary` in `tool_intelligence.db`
   - Tool: `predictive_router(tool_name, task_keywords)`
   - Rankings: Proven (>95%), Reliable (80-95%), Weak (50-80%), Broken (<50%)

### Phase 4: ADVANCED COGNITION
1. **Project-based memory clustering**:
   - Tables: `projects`, `project_memories`, `project_sessions`, `session_project_map`
   - Auto-detect projects from tip domains
   - Map sessions to projects by keyword matching
2. **Prompt fragment Elo tournaments**:
   - Table: `prompt_fragments(id, fragment, fragment_type, elo, matches)`
   - Judge: `llm_judge.compare_prompt_fragments()` via DeepSeek V4 Pro
   - Batch: `cortex_flywheel_v2.run_prompt_fragment_tournament()`
3. **Live dashboard**:
   - File: `~/subconscious/hermes_dashboard.py`
   - Tool: `hermes_dashboard(refresh=30)`
   - Shows: Tips, Elo, survival, tool rankings, projects

### Phase 5: TRAINING DATA EXPORT
1. **Export tip corpus**: High-confidence tips with Elo ratings → JSONL
2. **Export tool patterns**: Historical calls with success/failure labels → JSONL
3. **Generate curriculum**: Sort by Elo, create easy/medium/hard/expert levels
4. **Estimated tokens**: ~1.7M tokens for Qwen fine-tuning

## Key Files Created/Modified

| File | Purpose |
|------|---------|
| `~/subconscious/predictive_router.py` | Tool routing by success rate |
| `~/.hermes/tools/predictive_router_tool.py` | Hermes tool registration |
| `~/subconscious/hermes_dashboard.py` | Live cognitive dashboard |
| `~/subconscious/cortex_flywheel_v2.py` | Prompt fragment Elo tournaments |
| `~/.hermes/plugins/distillation/__init__.py` | Tip survival + adversarial hooks |
| `~/.hermes/cerebrum_memory.db` | New tables: tip_survival, tip_adversarial, prompt_fragments, projects, session_project_map |
| `~/.hermes/tool_intelligence.db` | New table: tool_performance_summary |
| `~/qwen-training-data/` | Exported training corpus |

## Results

| Metric | Before | After |
|--------|--------|-------|
| Active modules | 530 (91% dead) | 80 active, 453 archived |
| Registered tools | 1 | 10 |
| Plugins enabled | 32 | 35 |
| Empty DBs | 12 ghosts | Deleted |
| Tip survival tracking | None | 1902 tips tracked |
| Projects | None | 11 auto-detected |
| Training data | None | 1.7M tokens |

## Pitfalls Learned

1. **Patch tool loop**: When patch fails 3+ times with "path required" or "old_string not found", switch immediately to `write_file` + `terminal("python3 /tmp/script.py")`. Don't keep retrying patch.
2. **Method injection order**: When appending methods to a class file, ensure they're INSIDE the class body, not after `if __name__ == "__main__"`. We accidentally appended `compare_prompt_fragments` after `main()`, making it a module-level function that wasn't accessible.
3. **Force module reload**: When testing newly added methods, `del sys.modules['module_name']` before re-importing. Otherwise Python uses cached bytecode without the new method.
4. **Tool registration path**: Custom tools must be in `~/.hermes/tools/` with `@register_tool` decorator. The `register_tool` import must be `from hermes.core.tools import register_tool`.
5. **DB path confusion**: Always use `os.path.expanduser("~/.hermes/cerebrum_memory.db")`, not `~/subconscious/cerebrum_memory.db` (which is a 4KB stub).

## User Style Notes

During this session, user said:
- "yea pls" — wants immediate action without preamble
- "we can push after training finishes" — defers training data push, wants enhancement now
- "right now I just want you enhancing your hermes harness/kimi hands" — focus on self-improvement, not external tasks
- Short commands, no explanation expected, action-oriented throughout
