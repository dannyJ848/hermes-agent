# YantrikDB as Hermes Memory Provider

**Date:** 2026-05-16
**Status:** Experimental — not yet integrated into Hermes' official memory provider plugin system

## Overview

YantrikDB is a cognitive memory engine (Rust + Python bindings) with:
- Bundled embedders (no external dependencies)
- Graph relationships between memories
- Async ingest queue with auto-consolidation
- `think()` for conflict detection and pattern mining

It can complement or replace Cerebrum/Hindsight for semantic memory storage.

## Comparison with Existing Providers

| Feature | YantrikDB | Holographic | Hindsight | Cerebrum |
|---------|-----------|-------------|-----------|----------|
| Storage | Local SQLite | Local SQLite | PostgreSQL | Local SQLite |
| Embedder | Bundled (potion) | Built-in HRR | External LLM | None (text search) |
| Graph relations | Yes | No | Yes (knowledge graph) | No |
| Async ingest | Yes (256 queue) | No | No | No |
| Consolidation | `think()` | Trust scoring | `hindsight_reflect` | None |
| Cost | Free | Free | Free (local) | Free |

## Integration Path

### Current: Standalone Script

YantrikDB is NOT yet a Hermes memory provider plugin. Use it via standalone scripts:

```python
import sys
sys.path.insert(0, '/Users/dannygomez/.hermes/plugins/yantrikdb/src')
from yantrikdb import YantrikDB

ydb = YantrikDB.with_default("~/.hermes/yantrikdb.db")
# ... use directly, not through Hermes memory manager
```

### Future: Plugin Wrapper

To make YantrikDB a first-class Hermes memory provider, create:

```
~/hermes-agent/plugins/memory/yantrikdb/
├── __init__.py          # YantrikDBProvider class
├── plugin.yaml          # Metadata
└── README.md            # Setup docs
```

The `__init__.py` must implement:
- `__init__(self, config=None)` — set up with config dict
- `initialize(self, session_id, **kwargs)` — deferred init with `hermes_home`
- `record()`, `recall()`, `relate()`, `think()` methods
- `is_available()` — health check

See `hermes-memory-providers` skill for full provider ABC requirements.

## Migration from Cerebrum

See `yantrikdb-integration` skill for complete migration playbook including:
- Reading from `cerebrum_memory.db` `distilled_tips` table
- Transforming to YantrikDB record format
- Batch import with queue management (`think()` flush every 100 records)
- Verification via `recall()` and `list_memories()`

## Key Pitfalls

- **Ingest queue limit (256 ops):** Batch imports will fail without `think()` flush
- **No Hermes integration yet:** Must use standalone scripts, not `memory.provider` config
- **Graph index empty until `think()`:** `stats()` shows `edges: 0` until consolidation
- **Async processing:** Immediate `recall()` may miss just-recorded items

## Related

- `yantrikdb-integration` skill — Full integration guide
- `cerebrum-memory` skill — Source system being migrated
- `hermes-memory-providers` skill — Official provider system
