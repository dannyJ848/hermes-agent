# WAL Mode Silent Failure — Debug Pattern

## Symptom

Governor `log_attempt()` reports "INSERT OK" but `SELECT COUNT(*)` returns 0.

## Root Cause

SQLite WAL mode writes to `.db-wal` file before checkpointing to main DB. Different connections see different states.

## Verification Steps

```bash
# Check WAL files exist
ls -la ~/.hermes/cerebrum_memory.db*
# Expected: .db, .db-shm, .db-wal

# Force checkpoint and verify
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA wal_checkpoint(TRUNCATE); SELECT COUNT(*) FROM tip_injection_attempts;"

# Check journal mode
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA journal_mode;"
# Expected: wal
```

## Python Fix

When querying from Python, use `PRAGMA wal_checkpoint` before SELECT:

```python
conn = sqlite3.connect(db_path, isolation_level=None)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM table_name")
```

## In Sandboxes

`execute_code` runs in temp sandbox. WAL writes may not persist across script invocations. Use terminal with `sqlite3` CLI for verification.

## Prevention

- Don't rely on immediate SELECT after INSERT in WAL mode
- Use `conn.commit()` + `conn.close()` + reopen for verification
- Or use `PRAGMA wal_checkpoint(TRUNCATE)` after batch inserts
