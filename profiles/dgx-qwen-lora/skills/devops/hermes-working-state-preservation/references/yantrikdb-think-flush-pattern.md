# YantrikDB think() Queue Flush Pattern

## Date: 2026-05-16

## Discovery

During live migration of 1,282 cerebrum tips to YantrikDB, the ingest queue repeatedly filled at ~250 records despite various retry/sleep strategies. After 122+ loop detection failures, discovered that `ydb.think()` triggers consolidation which processes pending ingest ops, effectively flushing the queue.

## The Pattern

```python
BATCH_SIZE = 20
FLUSH_EVERY = 5  # batches

for i in range(0, len(records), BATCH_SIZE):
    batch = records[i:i + BATCH_SIZE]
    ydb.record_batch(batch)
    
    # Flush queue every N batches
    if (i // BATCH_SIZE + 1) % FLUSH_EVERY == 0:
        ydb.think()  # Consolidates and frees queue space
        time.sleep(1.0)
    
    time.sleep(3.0)  # Between batches
```

## Why This Works

- YantrikDB's ingest queue is async (background thread processes embeddings)
- Max queue depth: 256 ops
- `record()` and `record_batch()` enqueue but don't block
- `think()` runs consolidation which processes pending ops
- Without `think()`, queue fills regardless of sleep time (queue drains slower than enqueue rate)

## Stats Before/After think()

```python
stats_before = ydb.stats()
# {'active_memories': 29290, 'operations': 5899, ...}

ydb.think()

stats_after = ydb.stats()
# {'active_memories': 29286, 'consolidated_memories': 5, 'operations': 5908, ...}
# Note: active_memories may decrease (consolidation merges duplicates)
# operations increases (pending ops processed)
```

## Anti-Patterns That Failed

1. **Retry with exponential backoff** — Queue never drains fast enough, infinite retry loops
2. **Sleep between individual records** — Still fills queue at ~250 (enqueue rate > drain rate)
3. **Large batches (100+)** — Fills queue immediately on first batch
4. **nohup background script** — Hermes terminal rejects shell-level backgrounding

## Related

- `yantrikdb-integration` skill — Full YantrikDB integration guide
- `references/yantrikdb-ingest-pattern.md` — Original ingest pattern (pre-think() discovery)
