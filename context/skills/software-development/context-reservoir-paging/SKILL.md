---
name: context-reservoir-paging
version: 2.0
created: 2026-04-05
updated: 2026-04-05
category: software-development
description: "Build a verbatim demand-paging system for LLM context windows. Replace lossy summarization with evict-to-reservoir pattern. Based on Pichay (arXiv 2603.09023)."
tags: [context, paging, memory, llm, reservoir, evict]
---

# Context Reservoir: Demand Paging for LLM Context Windows

## When to Use
- When context window fills up and compression (summarization) would lose important data
- When building long-running agents that need to preserve full conversation history
- When reasoning quality degrades from context loss (not just context rot)

## Core Insight (from Danny)
> "Why not create a massive store of the context instead of deleting huge chunks during compression? Transfer old context to a massive reservoir that is chronological and wired in but keeps the main context window low."

## Architecture: 4-Tier Memory Hierarchy

```
L1 (Context Window)  → Active working memory, <35% fill
L2 (Eviction Buffer) → Recent evictions, verbatim, fast recall, auto-pruned at 100
L3 (Reservoir)       → Full chronological archive, verbatim, NEVER deleted
L4 (Honcho/Cerebrum) → Consolidated semantic memory (existing)
```

Key principle: **Context window = L1 cache, not memory.** (Pichay arXiv 2603.09023)

## Research Foundation

**Pichay (arXiv 2603.09023)** - Demand paging for LLM context windows:
- Context window is L1 cache, the field treats it as entire memory system
- 21.8% of context is structural waste (tool defs, system prompts, stale results)
- Their system: 93% context reduction (5,038KB → 339KB)
- Page fault rate: 0.0254% (almost never needs to bring evicted content back)
- Eviction NOT compression -- MOVE verbatim, don't summarize
- Retrieval handles as small anchors left in context

## Implementation

### Core Module: ~/subconscious/context_reservoir.py
- DB: ~/.hermes/context_reservoir.db (SQLite)
- Tables: eviction_buffer (L2), reservoir (L3), retrieval_handles, page_faults

### 4 Key Operations

1. **evict(role, content, session_id, token_estimate)**
   - Moves content from L1 to L2+L3 verbatim
   - Returns retrieval handle (tiny pointer for context)
   - Handle = first 80 chars + hash, NOT a summary

2. **fault_in(handle_id, reason)**
   - Brings content back from reservoir on demand
   - Logs page fault for working set detection
   - Auto-pins content after 3+ faults (Denning working set theory)

3. **search_reservoir(query, limit)**
   - Text search across full archive
   - Could upgrade to semantic search later

4. **get_handles_for_context(limit=20)**
   - Returns small anchors to inject into L1
   - Format: `[handle_id] preview... (faults: N)`

### Gotchas from Implementation

1. **Schema columns**: retrieval_handles needs `last_fault_at` column. The ORDER BY in get_handles must use `created_at` not `timestamp` (that column doesn't exist in retrieval_handles).
2. **SQLite locking**: Use separate DB for reservoir, not cerebrum_memory.db. Avoids lock contention with the gateway.
3. **Test with clean DB**: Delete .db file between schema changes during development.

## Wiring into Hermes

### Step 1: Intercept Compression (DONE)
The interception point is `plugins/memory/cerebrum/provider.py` method `on_pre_compress()`.

**How compression works in Hermes:**
1. `run_agent.py` line ~5480: `_compress_context()` is called when context exceeds threshold (40%)
2. Line 5492: `self._memory_manager.on_pre_compress(messages)` fires BEFORE compression
3. Line 5496: `self.context_compressor.compress(messages)` does the lossy summarization

**The patch** adds a Phase 1 (verbatim eviction) BEFORE Phase 2 (existing salience extraction):
- Phase 1: Loop all messages, call `reservoir.evict()` for each -> saves verbatim to L3
- Phase 2: Existing high-salience fact extraction into episodic/semantic memory (unchanged)
- Wrapped in try/except so reservoir failure doesn't break compression
- Uses `sys.path.insert` to lazy-import from ~/subconscious/

**Key discovery**: `on_pre_compress` is a MemoryProvider hook, not a plugin hook. It lives in the memory provider class hierarchy (`agent/memory_provider.py` ABC -> Cerebrum provider override). The `MemoryManager` in `agent/memory_manager.py` line 258 dispatches it to the active provider.

**Important**: Patch takes effect only after gateway restart (Python caches modules). Must also restart cron sessions.

### Step 2: Inject retrieval handles (DONE)
In `system_prompt_block()` (line ~251), added a "Paged-Out Context" section that calls `_get_reservoir().get_handles_for_context()`. Shows model what's been paged out with handle_ids for recall.

### Step 3: Expose fault_in as Hermes tool (DONE)

**Three-spot change pattern for adding Cerebrum actions (all in provider.py):**

1. **CEREBRUM_SCHEMA** (line ~50): Add action to enum, add new params (e.g. `handle_id`), update description string
2. **Handler dispatch dict** (line ~455): Add `"reservoir_recall": self._action_reservoir_recall` to the dict
3. **Handler methods** (end of class): Add `def _action_reservoir_recall(self, args: Dict) -> str:` methods

**4 actions added:**
- `reservoir_recall` — Page fault: calls `reservoir.fault_in(handle_id)`, returns verbatim content
- `reservoir_search` — Text search across L3 archive, calls `reservoir.search_reservoir(query)`
- `reservoir_status` — Stats + recent handles, calls `reservoir.get_stats()` + `reservoir.get_handle_list()`
- `reservoir_release` — Cooperative release, calls `reservoir.cooperative_release(handle_id)`

**Lazy import pattern** (avoids import errors at module load — DO NOT cache instance, safer for DB locks):
```python
def _get_reservoir(self):
    try:
        import sys
        sub_path = str(Path.home() / "subconscious")
        if sub_path not in sys.path:
            sys.path.insert(0, sub_path)
        from context_reservoir import ContextReservoir
        return ContextReservoir()
    except Exception as e:
        logger.warning("Cerebrum: Failed to load reservoir: %s", e)
        return None
```

**VERIFICATION PATTERN (cannot use Python imports due to relative imports):**
```bash
# Verify schema has actions
grep "reservoir_recall" provider.py
# Verify dispatch wired
grep -A 5 '"reservoir_recall":' provider.py
# Verify methods exist
grep -c "_action_reservoir" provider.py  # Should be 8 (4 dispatch + 4 methods)
# Compile check
python3 -c "import py_compile; py_compile.compile('provider.py', doraise=True)"
```

**Integration test pattern** (run from execute_code):
```python
import sys, json
sys.path.insert(0, '/Users/dannygomez/subconscious')
from context_reservoir import ContextReservoir
r = ContextReservoir()
# 1. Evict -> 2. Search -> 3. Fault-in -> 4. Status -> 5. Release -> 6. Verify L3 permanent
# 7. Dead tool GC -> 8. Pressure zones
handle = r.evict(role="tool", content="...", session_id="test", token_count=25, page_type="tool_result", tool_name="test", source_turn=3)
results = r.search_reservoir("query")
fault = r.fault_in(handle["handle_id"], reason="test")
stats = r.get_stats()
released = r.cooperative_release(handle["handle_id"])
# After release, search_reservoir still finds it (L3 is permanent)
```

**PITFALL: Context degradation during implementation.** At high context fill, the model generates syntactically invalid Python (mixed prose/code, undefined variables, missing colons). ALWAYS validate edits with `python3 -c "import ast; ast.parse(open('provider.py').read())"` after ANY edit. The patch tool's lint checker will catch syntax errors too.

**PITFALL: Gateway restart.** `hermes_cli.main gateway restart` sometimes stops but doesn't start. Fall back to manual: `nohup ./venv/bin/python -m hermes_cli.main gateway run &`. Verify with `ps aux | grep hermes_cli.main`.

### Step 4: Tool Schema Stubbing (DONE — 54% reduction per stubbed tool)

**Patches `memory_manager.py` in two places:**

1. **`get_all_tool_schemas()`** (line ~185): After collecting schemas from all providers, calls `_apply_tool_stubbing(schemas)`. This registers each tool's full+stub schema with the reservoir, then swaps full schemas for stubs on stale tools.

2. **`handle_tool_call()`** (line ~282): Records `reservoir.record_tool_call(tool_name)` so the stubbing logic knows which tools were recently active. Wrapped in try/except — never breaks dispatch.

**`_apply_tool_stubbing()` method:**
- Registers all tool schemas with reservoir (full + stub pair)
- For each tool, asks reservoir whether to use full or stub
- Fresh tools (<5 min since last call) get full schema
- Stale tools get minimal stub: `{name, "[Stub] short desc", empty params}`
- Model can still call stubbed tools — handle_tool_call restores full schema on next get_all_tool_schemas()

**CRITICAL BUG FIX in `get_tool_schema()` (context_reservoir.py):**
The original logic had `if not last_called: return full_schema, False` which meant tools registered with a stub but never called would NEVER get stubbed. Fixed to: `if not last_called and not stub_schema: return full_schema, False`. Now: registered-but-never-called tools DO get stubbed (they have a stub_schema). Only truly unknown tools (no registration at all) get full schema as safety fallback.

**Safety guarantees:**
- `_apply_tool_stubbing` wrapped in try/except at call site — if reservoir fails, full schemas returned
- `record_tool_call` wrapped in try/except — if reservoir fails, tool dispatch unaffected
- Never cache reservoir instances (create fresh each call for SQLite lock safety)

## File Locations
- Module: ~/subconscious/context_reservoir.py
- DB: ~/.hermes/context_reservoir.db
- Eviction log: ~/.hermes/workspace/eviction_log.jsonl
- Research: ~/.hermes/knowledge/context-reservoir-demand-paging-2026.md
