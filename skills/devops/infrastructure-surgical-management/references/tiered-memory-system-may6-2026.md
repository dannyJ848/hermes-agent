# Tiered Memory System — May 6, 2026

## Problem

The `memory` tool has a 2,500-character hard limit. When full, it rejects new entries. No overflow, no offloading, no cascade to other persistence layers existed.

## Solution: Three-Tier Memory with Auto-Flow

```
HOT   ~/.hermes/memory.json          (2,500ch limit, immediate context)
WARM  ~/.hermes/cerebrum_memory.db   (SQLite, distilled tips awaiting evaluation)
COLD  cortex PostgreSQL/SQLite       (Full archive, Elo-rated, vector searchable)
```

## Auto-Flow Rules

1. **Overflow**: HOT ≥ 80% → distill oldest low-priority entries → WARM staging
2. **Evaluation**: WARM accumulates tips → heuristic scoring (actionability, specificity, conditions) → quality ≥ 0.6 → COLD archive with Elo 1200
3. **Promotion**: COLD tips with Elo > 1300 + high access → promoted to HOT as "golden rules"
4. **Demotion**: HOT entries unused 30 days → staged to WARM for re-evaluation

## Files

- `hermes_cli/subconscious/tiered_memory.py` — Three-tier engine
- `hermes_cli/subconscious/memory_daemon.py` — Background maintenance daemon

## Usage

```python
from tiered_memory import TieredMemory
tm = TieredMemory()
tm.add("key", "value", priority=10, tags=["critical"])
tm.check_overflow()  # Auto-offload if needed
stats = tm.get_stats()
```

## Daemon Commands

```bash
python3 hermes_cli/subconscious/memory_daemon.py --once --verbose   # Single run
python3 hermes_cli/subconscious/memory_daemon.py --stats             # Show state
python3 hermes_cli/subconscious/memory_daemon.py --interval 300      # Daemon mode
```

## Integration

Wired into `instant_context.py` for CLI visibility:

```
[TIERED MEMORY]
  HOT   [██████████████░░░░░░] 72.4% (1809/2500)
        8 entries — immediate context
  WARM  0 unrated tips awaiting evaluation
  COLD  fallback SQLite
        0 high-performer memories
```

## Key Insight

The learning pipeline is already tiered (raw → distill → evaluate → skills). The memory system should match this flow: hot for immediate context, warm for staging, cold for archive. Simple offloading breaks the pipeline by losing the "recently distilled but not yet evaluated" stage.
