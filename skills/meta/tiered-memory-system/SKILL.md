---
name: tiered-memory-system
version: 1.0
description: Three-tier memory with automatic overflow, distillation, and promotion for Hermes Agent learning pipeline.
trigger: When memory hits 2,500 char limit, when building learning systems, when managing agent memory lifecycle.
---

# Tiered Memory System

Three-tier memory architecture: HOT (immediate context) → WARM (staging for evaluation) → COLD (long-term archive).

## Architecture

```
HOT (~/.hermes/memory.json, 2,500ch) → WARM (SQLite staging) → COLD (Cortex PostgreSQL)
```

## Auto-flow Rules

1. **Overflow**: HOT ≥ 80% → distill oldest → WARM staging table
2. **Evaluation**: WARM batch ≥ 50 → heuristic scoring → quality ≥ 0.6 → COLD archive (Elo 1200)
3. **Promotion**: COLD Elo > 1300 + high access → HOT as "golden rules"
4. **Demotion**: HOT unused 30 days → WARM re-evaluation

## Files

- `hermes_cli/subconscious/tiered_memory.py` — Core engine (HotTier, WarmTier, ColdTier)
- `hermes_cli/subconscious/memory_daemon.py` — Background maintenance daemon
- `hermes_cli/subconscious/memory_cortex_bridge.py` — Auto-offload bridge (detects pressure → scores → offloads → removes)

## Usage

### TieredMemory (full system)
```python
from tiered_memory import TieredMemory
tm = TieredMemory()
tm.add("key", "value", priority=10, tags=["critical"])
tm.check_overflow()  # Auto-handle overflow
stats = tm.get_stats()  # Full system state
```

### MemoryCortexBridge (auto-offload only)
```python
from memory_cortex_bridge import MemoryCortexBridge, pre_tool_call_hook, memory_add_hook

bridge = MemoryCortexBridge()

# Check and offload if needed
result = bridge.offload_if_needed()  # Returns action summary

# Wire into agent loop
agent_state = pre_tool_call_hook(agent_state)

# Wire into memory add
if memory_add_hook("new_key", "new_value"):
    memory.add("new_key", "new_value")
```

## CLI

```bash
# Daemon (full tiered system)
python3 hermes_cli/subconscious/memory_daemon.py --once --verbose
python3 hermes_cli/subconscious/memory_daemon.py --stats
python3 hermes_cli/subconscious/memory_daemon.py --interval 300

# Bridge (auto-offload only)
python3 hermes_cli/subconscious/memory_cortex_bridge.py --check     # Check pressure, offload if needed
python3 hermes_cli/subconscious/memory_cortex_bridge.py --stats     # Show current stats
python3 hermes_cli/subconscious/memory_cortex_bridge.py --search "query"  # Search offloaded memories
python3 hermes_cli/subconscious/memory_cortex_bridge.py --force     # Force offload (ignore cooldown)
```

## Integration

Wired into `instant_context.py` for visibility:
```
[TIERED MEMORY]
  HOT   [██████████████░░░░░░] 72.4% (1809/2500)
        8 entries — immediate context
  WARM  0 unrated tips awaiting evaluation
  COLD  fallback SQLite
        0 high-performer memories
```

### Hook Wiring

**pre_tool_call hook** — checks memory pressure before every tool call:
```python
from memory_cortex_bridge import pre_tool_call_hook
# In agent loop:
agent_state = pre_tool_call_hook(agent_state)
```

**memory_add hook** — ensures space before adding:
```python
from memory_cortex_bridge import memory_add_hook
if memory_add_hook("key", "value"):
    memory.add("key", "value")
```

## Key Design Decisions

- **Heuristic scoring** (not LLM) for speed: actionability, specificity, conditions, concrete details
- **CortexDB integration** with SQLite fallback for portability
- **Access tracking** on every get() call for promotion/demotion
- **Priority-based eviction** — low priority + old + low access offloaded first

## Bridge Design Decisions

- **Pressure threshold**: 2,400 chars (96% of 2,500 limit) — start offloading before hard limit
- **Batch size**: 3 entries per offload — aggressive enough to matter, small enough to be safe
- **Age gate**: Don't offload entries younger than 1 hour — prevents thrashing on fresh data
- **Score formula**: `priority * -2 + age_hours * 0.5 + access_count * -1` — lower = more offloadable
- **Cooldown**: 60 seconds between checks — prevents loop thrashing
- **Fallback chain**: CortexDB → cerebrum SQLite → skip (never crash the agent)
