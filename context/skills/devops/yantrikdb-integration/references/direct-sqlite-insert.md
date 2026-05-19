# YantrikDB Direct SQLite Insertion — Reference

## Problem

The YantrikDB ingest queue (max 256 pending ops) can become permanently stuck — the background thread stops draining, and `think()` calls take 18+ seconds without reducing queue depth. This blocks all `record()` and `record_batch()` operations.

## Symptoms

- `RuntimeError: ingest queue full (256 pending ops, max=256); retry after 50ms` even with batches of 50 and 2-second delays between them
- `stats()` shows `operations` count not increasing between `think()` calls
- `think()` takes 10-20 seconds per call but queue stays at 256
- Terminal commands timeout because the migration script hangs on `think()`

## Root Cause

The Rust-based background processing thread in `_yantrikdb_rust.cpython-38-darwin.so` appears to deadlock or exit silently. This is a plugin-level bug, not a usage error.

## Workaround: Direct SQLite Insertion

Bypass the YantrikDB API entirely and insert directly into the SQLite database it manages.

### Prerequisites

1. YantrikDB database file exists (create via `YantrikDB.with_default(path)` first)
2. The `memories` table has been initialized by YantrikDB
3. You have access to the `embed()` method via a live YantrikDB instance (for generating embeddings)

### Full Working Script

```python
import sqlite3, struct, time, json
from yantrikdb import YantrikDB

def migrate_cerebrum_to_yantrikdb(cerebrum_path, yantrik_path, namespace='cerebrum_tips'):
    """Migrate cerebrum tips to YantrikDB, bypassing the broken ingest queue."""
    
    # Open cerebrum source
    cerebrum = sqlite3.connect(cerebrum_path)
    cerebrum.row_factory = sqlite3.Row
    cursor = cerebrum.cursor()
    
    # Open YantrikDB for embeddings only
    ydb = YantrikDB.with_default(yantrik_path)
    
    # Open YantrikDB SQLite directly for insertion
    conn = sqlite3.connect(yantrik_path)
    ycursor = conn.cursor()
    
    # Get already migrated IDs
    ycursor.execute("SELECT DISTINCT json_extract(metadata, '$.cerebrum_id') "
                    "FROM memories WHERE namespace = ?", (namespace,))
    migrated_ids = set()
    for row in ycursor.fetchall():
        if row[0]:
            try: migrated_ids.add(int(row[0]))
            except: pass
    
    print(f'Already migrated: {len(migrated_ids)}')
    
    # Fetch remaining tips
    cursor.execute('SELECT * FROM distilled_tips ORDER BY id')
    all_tips = [dict(row) for row in cursor.fetchall()]
    remaining = [t for t in all_tips if t['id'] not in migrated_ids]
    print(f'Remaining: {len(remaining)}')
    
    migrated = 0
    for tip in remaining:
        memory_text = f"[{tip['tip_type']}] {tip['condition']}\n"
        memory_text += f"Recommendation: {tip['recommendation']}"
        if tip.get('rationale'):
            memory_text += f"\nRationale: {tip['rationale']}"
        if tip.get('tool_name'):
            memory_text += f"\nTool: {tip['tool_name']}"
        if tip.get('domain'):
            memory_text += f"\nDomain: {tip['domain']}"
        
        importance = min(0.95, max(0.3, 
            tip['confidence'] * 0.5 + (tip.get('frequency') or 0) * 0.1))
        
        # Generate embedding via YantrikDB API
        emb = ydb.embed(memory_text)
        emb_blob = struct.pack(f'{len(emb)}f', *emb)
        
        rid = f"cerebrum_{tip['id']:08d}"
        now = time.time()
        
        ycursor.execute('''
            INSERT INTO memories (rid, type, text, embedding, created_at, updated_at,
                                importance, half_life, last_access, access_count, valence,
                                consolidation_status, storage_tier, metadata, namespace,
                                certainty, domain, source, created_at_unix_micros)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rid, 'semantic', memory_text, emb_blob, now, now, importance,
            604800.0, now, 0, 0.0, 'active', 'hot',
            json.dumps({'tip_type': tip['tip_type'], 'cerebrum_id': tip['id']}),
            namespace, 0.8, tip.get('domain') or 'general', 'cerebrum_migration',
            int(now * 1e6)
        ))
        
        migrated += 1
        if migrated % 100 == 0:
            conn.commit()
            print(f'Migrated {migrated}/{len(remaining)}', end='\r')
    
    conn.commit()
    print(f'\nDone: {migrated} migrated')
    
    # Verify
    ycursor.execute("SELECT COUNT(*) FROM memories WHERE namespace = ?", (namespace,))
    total = ycursor.fetchone()[0]
    print(f'Total in namespace: {total}')
    
    conn.close()
    ydb.close()
    cerebrum.close()
    
    return migrated

# Usage
migrate_cerebrum_to_yantrikdb(
    '~/.hermes/cerebrum_memory.db',
    '~/.hermes/yantrikdb_copy.db'
)
```

### Key Points

- **Embeddings must be generated via YantrikDB's `embed()` method** — the vector index expects the exact same embedding model and dimension that YantrikDB was initialized with
- **Embedding blob format:** `struct.pack(f'{len(emb)}f', *emb)` — array of 32-bit floats
- **RID format:** Any unique string works; `cerebrum_{id:08d}` is readable and deterministic
- **Commit every 100 records:** SQLite WAL mode performs best with periodic commits
- **Metadata as JSON string:** The `metadata` column stores JSON text, not a parsed dict

### Post-Migration: Rebuild Vector Index

After direct insertion, the vector index may be stale. Rebuild it:

```python
from yantrikdb import YantrikDB

db = YantrikDB.with_default('~/.hermes/yantrikdb_copy.db')
# Verify method exists before calling (availability varies by YantrikDB version)
if hasattr(db, 'rebuild_vec_index'):
    db.rebuild_vec_index()
else:
    # Fallback: close and reopen to trigger index refresh
    db.close()
    db = YantrikDB.with_default('~/.hermes/yantrikdb_copy.db')
db.close()
```

Without this step, `recall()` may return incomplete results for newly inserted records. In practice, YantrikDB's HNSW vector index often picks up new records on the next `recall()` call without explicit rebuilding — verify with a test query before assuming rebuild is needed.

## Verification

```python
from yantrikdb import YantrikDB
import sqlite3

db = YantrikDB.with_default('~/.hermes/yantrikdb_copy.db')

# Test semantic search
result = db.recall('self-improvement', namespace='cerebrum_tips', top_k=5)
print(f'Found {len(result)} results')

# Check via SQLite
conn = sqlite3.connect('~/.hermes/yantrikdb_copy.db')
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM memories WHERE namespace = 'cerebrum_tips'")
print(f'Total records: {c.fetchone()[0]}')
c.execute("SELECT COUNT(DISTINCT json_extract(metadata, '$.cerebrum_id')) "
          "FROM memories WHERE namespace = 'cerebrum_tips'")
print(f'Distinct IDs: {c.fetchone()[0]}')
conn.close()
```

## When NOT to Use This Workaround

- When the ingest queue is working normally (use standard `record()` / `record_batch()`)
- When you need graph relationships (`relate()`, `get_edges()`) — direct insertion skips graph index updates
- When you need conflict detection or consolidation — direct insertion bypasses these features

## Related

- `yantrikdb-integration/SKILL.md` — Main skill with queue management patterns
- `yantrikdb-integration/references/queue-debug.md` — Diagnosing stuck queues
