# Memory-Cortex Bridge Pattern

Session: May 6, 2026 — built to solve memory tool at 99% (2,477/2,500 chars)

## Problem

Hermes memory tool has hard 2,500 char limit. When full, agent must manually replace entries. This breaks autonomous operation.

## Solution

Auto-offload bridge: detect pressure → score entries → move to CortexDB → free space.

## Architecture

```
MEMORY.md (2,500ch limit)
    ↓ pressure ≥ 2,400 chars
MemoryCortexBridge.offload_if_needed()
    ↓ score entries (priority, age, access)
    ↓ select bottom 3
CortexDB.insert_node() or cerebrum SQLite fallback
    ↓ remove from MEMORY.md
Space freed → agent continues
```

## Scoring Formula

```python
score = priority * -2 + age_hours * 0.5 + access_count * -1
```

Lower score = more offloadable. Priority 10 (critical) resists offloading. Age rewards old entries. Access count rewards frequently used.

## Key Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| MEMORY_LIMIT | 2,500 | Hermes hard limit |
| MEMORY_PRESSURE_THRESHOLD | 2,400 | 96% — act before crisis |
| OFFLOAD_BATCH_SIZE | 3 | Aggressive but safe |
| MIN_ENTRY_AGE_HOURS | 1 | Don't thrash fresh data |
| COOLDOWN | 60s | Prevent check loops |

## Hook Integration

### pre_tool_call hook
```python
from memory_cortex_bridge import pre_tool_call_hook
agent_state = pre_tool_call_hook(agent_state)  # Auto-offloads if needed
```

### memory_add hook
```python
from memory_cortex_bridge import memory_add_hook
if memory_add_hook("key", "value"):
    memory.add("key", "value")
```

## Fallback Chain

1. CortexDB (PostgreSQL/SQLite via `subconscious/cortex_access.py`)
2. Cerebrum SQLite (`~/.hermes/cerebrum_memory.db` with `memory_units` table)
3. Skip offload (never crash agent)

## Testing Results

- Before: 2,477 chars (99.1%)
- After offload: 1,898 chars (75.9%)
- Freed: 584 chars, 3 entries
- Node IDs: 1039, 1040, 1041 in CortexDB

## Files

- `hermes_cli/subconscious/memory_cortex_bridge.py` — Full implementation
- `hermes_cli/subconscious/tiered_memory.py` — Three-tier engine
- `hermes_cli/subconscious/memory_daemon.py` — Background daemon
