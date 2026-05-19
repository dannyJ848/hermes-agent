# YantrikDB Migration Session Findings — May 17, 2026

## Session Context

Migrating 1,282 cerebrum tips from `cerebrum_memory.db` to YantrikDB (`yantrikdb_copy.db`). Discovered critical bugs in YantrikDB plugin queue management.

## Key Findings

### 1. Ingest Queue Permanently Stuck (Plugin Bug)

**Symptoms:**
- `RuntimeError: ingest queue full (256 pending ops, max=256); retry after 50ms`
- Occurs even with batches of 50 and 2-second delays between them
- `think()` takes 18+ seconds but queue depth stays at 256
- `stats()` shows `operations` count not increasing between `think()` calls

**Root cause:** Rust background thread (`_yantrikdb_rust.cpython-38-darwin.so`) deadlocked or exited silently. Not a usage error.

**Workaround:** Direct SQLite insertion using `db.embed()` for embeddings + `struct.pack()` for blob format. Full script in `yantrikdb-integration/references/direct-sqlite-insert.md`.

### 2. `record_batch()` Signature Quirk

- `record_batch([{'text': 'x', 'namespace': 'foo'}])` — works (namespace inside dict)
- `record_batch(batch, namespace='foo')` — fails: "unexpected keyword argument 'namespace'"
- Contrast: `record(text='x', namespace='foo')` — works (namespace as kwarg)

### 3. `recall()` SQLite Parameter Limit

`recall('', namespace='cerebrum_tips', top_k=2000)` fails on large databases:
```
RuntimeError: variable number must be between ?1 and ?32766
```

Internal query generates `SELECT ... WHERE rid IN (?1, ?2, ...)` with thousands of params. Use `top_k <= 500` for large DBs.

### 4. Plugin Registration Gap

YantrikDB exists in `~/.hermes/plugins/yantrikdb/` and Python import works, but does NOT appear in `hermes plugins list`. This means:
- Skills referencing YantrikDB work (via direct Python import)
- Hermes plugin registry doesn't know about it
- No plugin-level hooks, events, or lifecycle management

**Verification:**
```bash
ls ~/.hermes/plugins/ | grep -E "yantrik|paperclip"  # directories exist
hermes plugins list | grep -E "yantrik|paperclip"    # NOT registered
```

### 5. Migration Result

- 1,282 distinct cerebrum tips migrated to YantrikDB
- 1,308 total records (26 duplicates from interrupted prior attempts)
- Semantic search working: `recall('cron job debugging', top_k=3)` returns relevant tips
- Database size: 5.3MB

### 6. `embed()` Works Even When Queue Is Stuck

The `db.embed(text)` method (used for generating embeddings) continues to work even when the ingest queue is at 256/256. This is what enables the direct SQLite workaround.

## Commands Used

```bash
# Verify YantrikDB health
cd ~/.hermes/plugins/yantrikdb && PYTHONPATH=src python3 -c "
from yantrikdb import YantrikDB
db = YantrikDB.with_default('~/.hermes/yantrikdb_copy.db')
print(db.stats())
print(db.recall('test', namespace='cerebrum_tips', top_k=3))
db.close()
"

# Direct SQLite verification
sqlite3 ~/.hermes/yantrikdb_copy.db "
SELECT COUNT(*) FROM memories WHERE namespace = 'cerebrum_tips';
SELECT COUNT(DISTINCT json_extract(metadata, '$.cerebrum_id')) 
FROM memories WHERE namespace = 'cerebrum_tips';
"
```

## Related

- `yantrikdb-integration/SKILL.md` — Main YantrikDB skill (updated with these findings)
- `yantrikdb-integration/references/direct-sqlite-insert.md` — Full workaround script
- `yantrikdb-integration/references/sqlite-in-clause-limit.md` — Parameter limit details
