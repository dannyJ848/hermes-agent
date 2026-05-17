# YantrikDB Integration Pitfalls — May 2026

## Discovery Context

Attempted to migrate 1,282 cerebrum tips to YantrikDB as a secondary memory store. Hit multiple queue/performance issues.

## Key Findings

### 1. Embedder Required — No Text-Only Mode

YantrikDB **requires** an embedder. `record()` throws `RuntimeError: No embedder configured` even for text-only use.

**Solution:** Use `YantrikDB.with_default(path)` which loads the bundled `potion-base-2M` embedder (~7MB, dim=64):
```python
from yantrikdb import YantrikDB
ydb = YantrikDB.with_default("/path/to/db")
```

**Wrong approaches that fail:**
- `YantrikDB(path)` — no embedder, fails on first `record()`
- `ydb.set_embedder_named('ollama', ...)` — wrong signature, only takes name string
- `ydb.set_embedder('ollama')` — requires object with `.encode()` method

### 2. Ingest Queue Size Limit: 256 ops

`record()` and `record_batch()` both hit an async ingest queue with max 256 pending operations.

**Error:** `RuntimeError: ingest queue full (256 pending ops, max=256); retry after 50ms`

**Queue flush mechanism:** Call `ydb.think()` periodically to flush/consolidate:
```python
ydb.think()  # Flushes queue, runs consolidation
```

### 3. Batch Size Tuning

| Batch Size | Sleep Between | Result |
|-----------|---------------|--------|
| 100 | 0s | FAIL at chunk 3 (queue full) |
| 50 | 1s | FAIL at chunk 6 (queue full) |
| 25 | 3s | FAIL at chunk 8 (queue full) |
| 20 | 5s | Timeout (600s limit) |

**Conclusion:** For 1,200+ records, batch approach within a single process is unreliable. The queue fills faster than `think()` can flush it.

### 4. Recommended Migration Pattern

For bulk migration of >1000 records:

**Option A: Background script (no timeout)**
```python
# Run outside Hermes terminal (no 600s limit)
import time
from yantrikdb import YantrikDB

ydb = YantrikDB.with_default("memory.db")

for i, record in enumerate(all_records):
    ydb.record(**record)
    if (i + 1) % 50 == 0:
        ydb.think()  # flush queue
        time.sleep(2)

ydb.think()
ydb.close()
```

**Option B: Chunked with process restart**
```python
# Process 200 records, close DB, reopen fresh
# Resets queue state
```

**Option C: Accept partial copy**
- ~200-250 records get through before queue fills
- Remaining accumulate organically via normal usage
- Use `list_memories(namespace=...)` to check what's already there

### 5. Verification

```python
# Check stats
stats = ydb.stats()
print(f"Active: {stats['active_memories']}")

# Check specific namespace
existing = ydb.list_memories(namespace="cerebrum_tips")
print(f"In namespace: {len(existing)}")

# Sample recall
results = ydb.recall("tool usage patterns", top_k=5, namespace="cerebrum_tips")
```

### 6. Namespace Isolation

`list_memories(namespace=...)` returns memories filtered by namespace. Metadata fields (like `cerebrum_id`) are stored but not queryable — they're for application-level filtering after recall.

## Files

- YantrikDB plugin: `~/.hermes/plugins/yantrikdb/`
- Migration script (incomplete): `/tmp/yantrik_copy.py`
- Target DB: `~/.hermes/yantrikdb_copy.db`
