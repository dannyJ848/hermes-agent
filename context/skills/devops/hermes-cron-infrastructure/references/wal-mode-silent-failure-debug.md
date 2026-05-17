# WAL Mode Silent Failure — Debug Technique

## Symptom

SQLite insert appears to succeed (no exception, `conn.commit()` returns) but `SELECT COUNT(*)` returns 0 rows. Happens when:
- Code runs in `execute_code` sandbox
- SQLite is in WAL mode (`PRAGMA journal_mode = WAL`)
- Multiple connections open/close rapidly

## Root Cause

WAL (Write-Ahead Logging) writes changes to `.db-wal` file before checkpointing to main `.db`. If the checking connection doesn't handle WAL properly, or if the sandbox exits before checkpoint, data appears "lost".

## Verification

```bash
# Check WAL files
ls -la ~/.hermes/cerebrum_memory.db*
# Should show: .db, .db-shm, .db-wal

# Check journal mode
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA journal_mode;"
# Returns: wal

# Force checkpoint and query
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA wal_checkpoint(TRUNCATE); SELECT COUNT(*) FROM table_name;"
```

## Fix Patterns

### Pattern 1: Checkpoint Before Query (Python)

```python
conn = sqlite3.connect(DB_PATH, isolation_level=None)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM table_name")
count = c.fetchone()[0]
```

### Pattern 2: Use Terminal for Verification

Terminal `sqlite3` command handles WAL correctly. Use it instead of `execute_code` for post-insert verification:

```bash
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA wal_checkpoint(TRUNCATE); SELECT * FROM table_name LIMIT 5;"
```

### Pattern 3: Disable WAL (if not needed)

```python
conn.execute("PRAGMA journal_mode=DELETE")
```

Trade-off: WAL allows concurrent reads during writes. DELETE mode locks the whole DB.

## When This Fires

- Governor logging verification
- Tip injection attempt counting
- Any DB write followed by immediate read in sandbox

## Prevention

Always verify DB writes via terminal command, not `execute_code`, when WAL mode is active.
