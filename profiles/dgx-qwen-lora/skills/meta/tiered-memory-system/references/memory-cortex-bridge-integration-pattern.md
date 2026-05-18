# Memory Cortex Bridge Integration Pattern

**Session:** May 6, 2026 — Built after discovering the other CLI had documented but never coded the auto-offload bridge.

## The Problem

The tiered memory system had HOT/WARM/COLD tiers and a daemon skeleton, but no actual bridge code to:
1. Detect when memory approaches 2,500 char limit
2. Select lowest-importance entries for transfer
3. Insert into CortexDB
4. Remove from active memory store
5. Wire into the agent's pre_tool_call hook

## The Solution

### 1. Bridge Module (`memory_cortex_bridge.py`)

```python
class MemoryCortexBridge:
    def __init__(self):
        self.cortex = CortexDBBridge()  # CortexDB with SQLite fallback
        self.parser = MemoryParser()     # Parse MEMORY.md into scored entries
    
    def offload_if_needed(self, force=False) -> Dict:
        # 1. Check pressure (>2,400 chars)
        # 2. Score entries: priority * -2 + age * 0.5 + access * -1
        # 3. Select bottom 3 candidates (age > 1 hour)
        # 4. Store in CortexDB → get node_id
        # 5. Remove from MEMORY.md
        # 6. Return action summary
```

**Key design decisions:**
- Pressure threshold: 2,400 chars (96%) — start before hard limit
- Batch size: 3 entries — aggressive enough, safe enough
- Age gate: 1 hour minimum — prevents thrashing fresh data
- Cooldown: 60 seconds between checks
- Fail-open: Exception in bridge never blocks tool calls

### 2. Hook Wiring (`plugins.py`)

```python
def get_pre_tool_call_block_message(tool_name, args, ...):
    # Memory pressure check — auto-offload before tool calls
    try:
        from memory_cortex_bridge import MemoryCortexBridge
        bridge = MemoryCortexBridge()
        result = bridge.offload_if_needed()
        if result.get('status') == 'offloaded':
            logger.info("Memory offloaded: %s entries freed...")
    except Exception:
        pass  # Fail-open
    
    # ... rest of hook logic
```

**Critical:** The bridge must be fail-open. Never let memory management errors block actual work.

### 3. Integration Test Pattern

```python
# Phase 1: Individual module tests
for mod in [bridge, miner, validator, guard, gate, monitor, watcher]:
    assert mod.get_stats()  # Each module loads

# Phase 2: Hook tests
pre_tool_call_hook({})       # Returns agent_state
memory_add_hook("k", "v")    # Returns bool
post_tool_call_hook("tool", "error")  # Records error

# Phase 3: Full workflow test
# 1. Record error → 2. Validate plan → 3. Check memory → 4. Validate tip → 5. Monitor process → 6. Check training
```

## Bug Found During Integration

**Issue:** `post_tool_call_hook` received `context={}` (dict from **kwargs) but tried to slice it as string.

**Fix:** `context[:500] if isinstance(context, str) else str(context)[:500]`

**Lesson:** Always type-check before slicing in hook interfaces — kwargs can pass unexpected types.

## Files

- `hermes_cli/subconscious/memory_cortex_bridge.py` — 465 lines, full bridge
- `hermes_cli/plugins.py` — Hook wired into `get_pre_tool_call_block_message`
