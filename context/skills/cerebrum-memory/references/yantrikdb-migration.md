# YantrikDB Migration Notes

## Problem: Ingest Queue Saturation

When bulk-migrating from Cerebrum SQLite to YantrikDB, the async ingest queue (max 256 ops) fills rapidly and throws:

```
RuntimeError: ingest queue full (256 pending ops, max=256); retry after 50ms
```

## What Does NOT Work

- `record()` one-by-one with retry/sleep — too slow for 1,000+ tips
- `record_batch()` with 50-100 items — still overflows queue
- `record_batch()` with retry backoff — queue never drains fast enough
- Calling `think()` between batches — helps slightly but not enough for large sets

## What DOES Work (Partial)

- `record_batch()` with chunk_size=20 + `think()` flush every 5 chunks
- BUT: still fails around chunk 5-6; queue drains slower than fills

## Root Cause

YantrikDB's async processing is designed for interactive use (a few records per turn), not bulk ETL. The bundled embedder (`potion-base-2M`) processes embeddings in background threads. With 1,282 tips, queue depth exceeds capacity.

## Workaround: Hybrid Approach

1. **Copy high-value subset first** — filter by `confidence > 0.8` or `upvotes > 2`
2. **Use smaller chunks** — chunk_size=10 with think() every 3 chunks
3. **Run in background** — nohup script with generous sleeps (not via Hermes terminal)
4. **Accept partial copy** — organic accumulation via normal usage

## Verified API

```python
from yantrikdb import YantrikDB

# Must use with_default() for bundled embedder
ydb = YantrikDB.with_default("/path/to/db")

# Available methods
ydb.record(text, memory_type='semantic', importance=0.5, metadata={}, namespace='default')
ydb.record_batch([{text, memory_type, importance, metadata, namespace}])
ydb.recall(query, top_k=5, namespace='default')
ydb.think()  # consolidate + flush queue
ydb.stats()  # active_memories, operations, etc.
ydb.close()
```

## Current Status

- 1,282 cerebrum tips total
- ~24,000 active memories in YantrikDB (from partial runs)
- Only ~3 with proper `cerebrum_tips` namespace metadata
- Migration: INCOMPLETE — blocked on queue saturation
