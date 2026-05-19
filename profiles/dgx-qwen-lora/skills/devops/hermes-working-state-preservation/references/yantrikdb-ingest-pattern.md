# YantrikDB Ingest Pattern — Copying Cortex/Cerebrum Memories

## Date: 2026-05-16

## Problem

User wants to copy (not migrate) distilled tips from `cerebrum_memory.db` into YantrikDB for experimentation. YantrikDB requires an embedder and has a 256-item ingest queue that fills quickly under rapid insertion.

## Prerequisites

1. YantrikDB plugin installed at `~/.hermes/plugins/yantrikdb/`
2. Rust extension built for correct architecture (see hub-integration-pattern.md for arch mismatch fix)
3. Ollama running locally with an embedding model (e.g., `nomic-embed-text`)

## Initialization

```bash
cd ~/.hermes/plugins/yantrikdb && PYTHONPATH=src python3 -c "
from yantrikdb import YantrikDB

# Use bundled embedder (downloads ~8M-128M model on first use)
ydb = YantrikDB.with_default('/path/to/yantrikdb.db')

# Alternative: use named embedder (built-in: potion-base-8M, potion-base-32M, potion-multilingual-128M)
# ydb.set_embedder_named('potion-base-32M')
"
```

**Key finding:** `YantrikDB(path)` without `with_default()` requires an explicit embedder. The `with_default()` class method bundles a default embedder. `set_embedder_named()` only takes a name string, not kwargs.

## Ingestion Protocol

### The Queue Problem

YantrikDB has an async ingest queue (max 256 pending ops). Rapid `record()` calls fill it and raise:
```
RuntimeError: ingest queue full (256 pending ops, max=256); retry after 50ms
```

**Solutions (in order of preference):**

1. **Slow insertion with sleep** (most reliable):
```python
for i, tip in enumerate(tips):
    ydb.record(text=..., memory_type='semantic', ...)
    time.sleep(0.02)  # 20ms between records
    if (i + 1) % 100 == 0:
        time.sleep(1.0)  # longer flush every 100
```

2. **Retry with backoff** (when queue fills):
```python
for attempt in range(20):
    try:
        ydb.record(...)
        break
    except RuntimeError as e:
        if 'ingest queue full' in str(e) and attempt < 19:
            time.sleep(0.1 * (attempt + 1))
            continue
        raise
```

3. **Batch with explicit flush** (if API available):
Check `ydb.apply_ops()` or `ydb.extract_ops_since()` for batching APIs. The queue is internal to the Rust layer and may not expose explicit flush.

### Recommended Approach for 1000+ Items

```bash
cd ~/.hermes/plugins/yantrikdb && PYTHONPATH=src python3 -c "
import os, time, sqlite3
from yantrikdb import YantrikDB

home = os.path.expanduser('~')
ydb = YantrikDB.with_default(os.path.join(home, '.hermes', 'yantrikdb_copy.db'))

cerebrum_path = os.path.join(home, '.hermes', 'cerebrum_memory.db')
conn = sqlite3.connect(cerebrum_path)
c = conn.cursor()
c.execute('SELECT id, tip_type, condition, recommendation, rationale, tool_name, domain, confidence, upvotes, downvotes, frequency, source_ids FROM distilled_tips')
tips = c.fetchall()
conn.close()

print(f'Copying {len(tips)} tips...')

for i, tip in enumerate(tips):
    tip_id, tip_type, condition, recommendation, rationale, tool_name, domain, confidence, upvotes, downvotes, frequency, source_ids = tip
    
    text = f'[{tip_type}] {domain or \"general\"} | {tool_name or \"\"}\\n'
    text += f'CONDITION: {condition}\\n'
    text += f'RECOMMENDATION: {recommendation}\\n'
    if rationale:
        text += f'RATIONALE: {rationale}\\n'
    text += f'Confidence: {confidence:.4f} | Votes: +{upvotes}/-{downvotes} | Freq: {frequency}'
    
    metadata = {
        'cerebrum_id': tip_id,
        'tip_type': tip_type,
        'tool_name': tool_name or '',
        'domain': domain or 'general',
        'source_ids': source_ids or '',
        'upvotes': upvotes,
        'downvotes': downvotes,
        'frequency': frequency,
        'original_db': 'cerebrum_memory.db'
    }
    
    importance = min(1.0, (confidence or 0.5) * (1 + (upvotes or 0) * 0.1))
    
    ydb.record(
        text=text,
        memory_type='semantic',
        importance=importance,
        metadata=metadata,
        namespace='cerebrum_tips',
        domain=domain or 'general',
        source='cerebrum_copy',
        certainty=confidence or 0.5
    )
    
    # Critical: sleep to let queue drain
    time.sleep(0.02)
    
    if (i + 1) % 100 == 0:
        print(f'  {i+1}/{len(tips)}')
        time.sleep(1.0)

print(f'Done! Copied {len(tips)} tips')
stats = ydb.stats()
print(f'Stats: {stats}')

# Verify
result = ydb.recall(query='tool usage patterns', top_k=3, namespace='cerebrum_tips')
for mem in result[:3]:
    print(mem.get('text', '')[:70] + '...')

ydb.close()
"
```

## Field Mapping

| Cerebrum Column | YantrikDB Field | Notes |
|-----------------|-----------------|-------|
| `tip_type` | `metadata.tip_type` | Also used in text prefix |
| `condition` | Text body | Core content |
| `recommendation` | Text body | Core content |
| `rationale` | Text body | Optional content |
| `tool_name` | `metadata.tool_name`, text | Empty string if null |
| `domain` | `domain`, text | Default 'general' |
| `confidence` | `certainty`, `importance` | importance = min(1.0, confidence * (1 + upvotes*0.1)) |
| `upvotes` | `metadata.upvotes` | Also boosts importance |
| `downvotes` | `metadata.downvotes` | |
| `frequency` | `metadata.frequency` | |
| `source_ids` | `metadata.source_ids` | |
| `id` | `metadata.cerebrum_id` | Preserve original ID for cross-reference |

## Verification

After copy, check:
```python
stats = ydb.stats()
print(f"Active memories: {stats['active_memories']}")
print(f"Vec index entries: {stats['vec_index_entries']}")

# Should match number of tips copied
assert stats['active_memories'] == len(tips), "Mismatch!"
```

## Pitfalls

- **No embedder = no work:** `YantrikDB(path)` without `with_default()` fails on first `record()`
- **Queue fills silently:** Without sleep between records, queue hits 256 and raises RuntimeError
- **Terminal timeouts:** Large batches (>500 items with sleep) exceed 600s terminal timeout — run as background script instead
- **list_memories returns strings:** `ydb.list_memories()` may return string representations, not dicts — check type before accessing `.get()`
- **Namespace filtering:** `recall(namespace='X')` filters by namespace; omit for global search
- **Memory type:** Use `'semantic'` for distilled tips (knowledge), `'episodic'` for session events

## Background Execution for Large Datasets

For 1000+ items, write a script file and run it detached:

```bash
cat > /tmp/yantrik_ingest.py << 'PYEOF'
# ... full script ...
PYEOF

# Run in background, log to file
nohup python3 /tmp/yantrik_ingest.py > /tmp/yantrik_ingest.log 2>&1 &
echo $! > /tmp/yantrik_ingest.pid

# Check progress
tail -f /tmp/yantrik_ingest.log
```

## Why "Copy" Not "Migrate"

The user explicitly said "copy over not migrate" — this means:
- Keep original `cerebrum_memory.db` intact
- Create a new YantrikDB file (`yantrikdb_copy.db`)
- Both databases coexist
- YantrikDB is experimental/secondary, not replacement
