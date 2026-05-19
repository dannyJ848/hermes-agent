---
name: sqlite-wal-lock-contention
description: Fix SQLite WAL-mode database lock contention when multiple processes (Hermes gateway, subconscious controller, cron jobs) share the same DB. Covers diagnosis, graceful degradation, and the JSONL bridge pattern.
version: 1.0
created: 2026-04-10
tags: [sqlite, wal, lock, contention, hermes, gateway, database]
---

# SQLite WAL Lock Contention — Diagnosis & Fix

## When to Use
- A script crashes with `sqlite3.OperationalError: database is locked`
- Multiple processes share the same SQLite database (gateway + cron + controller)
- The Hermes gateway holds a long-lived write lock via its distillation plugin

## Root Cause

The Hermes gateway (PID visible in `ps aux | grep gateway`) opens `cerebrum_memory.db` and other subconscious DBs in WAL mode with a long-lived write connection. Any other process trying to write gets `database is locked`, even with `busy_timeout` set high. The gateway never releases the lock because it's always processing.

**Key insight:** WAL mode allows concurrent reads but NOT concurrent writes. Only one writer at a time.

## Diagnosis Steps

1. **Check which DB is locked** — look at the traceback for the `sqlite3.connect()` path
2. **Verify gateway holds it** — `ps aux | grep gateway` should show a running process
3. **Confirm reads work** — try a SELECT; if it works, it's a write-lock issue:
   ```python
   conn = sqlite3.connect(db_path, timeout=5)
   conn.execute("SELECT count(*) FROM some_table").fetchone()  # works
   conn.execute("UPDATE some_table SET x=1")  # FAILS with "database is locked"
   ```
4. **Check WAL size** — large `-wal` file = uncommitted data, active writer:
   ```bash
   ls -la path/to/db.db-wal
   ```

## Fix Pattern 1: Graceful Lock Detection (preferred for audit/controller scripts)

Probe for write access before attempting writes. Skip write-dependent phases cleanly.

```python
import sqlite3

def run_with_graceful_lock_handling(conn):
    """Detect if DB is write-locked and degrade gracefully."""
    enforce_skipped = False
    
    # Initialize defaults for all enforcement results
    trust_fix = {"capped": 0}
    stale_preds = {"resolved": 0}
    
    # Probe: can we write?
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.rollback()  # release immediately — just testing
    except sqlite3.OperationalError:
        enforce_skipped = True
    
    if not enforce_skipped:
        trust_fix = enforce_trust_caps(conn)
        stale_preds = enforce_resolve_stale(conn)
    else:
        trust_fix["skipped"] = True
        stale_preds["skipped"] = True
    
    # ... rest of audit with read-only data
```

**Critical:** When skipping enforcement, you MUST:
1. Initialize all result variables with defaults BEFORE the if/else
2. Handle `KeyError` in report section — skipped results won't have all keys
3. Log clearly that phases were skipped and why

## Fix Pattern 2: JSONL Bridge (for daemons)

See `hermes-cron-to-daemon` skill for the full JSONL write + merge pattern.

## Fix Pattern 3: Connection Tuning

If lock contention is intermittent (not a permanent gateway lock):

```python
conn = sqlite3.connect(str(db_path), timeout=60)  # 60s wait
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=55000")  # 55s internal timeout
```

## Pitfalls

1. **Increasing timeout doesn't help** if the gateway holds an indefinite write lock. 60s timeout still fails if the gateway never releases.
2. **Removing `-wal`/`-shm` files is dangerous** — can corrupt the DB if a writer is active.
3. **`PRAGMA wal_checkpoint(TRUNCATE)` also blocks** if another writer holds the lock.
4. **Variable scoping** — when skipping enforcement with `if/else`, all result dicts must be initialized before the branch, or you get `NameError` in the report section.
5. **KeyError in report** — skipped enforcement results may not have keys like `verdict`, `distilled` that the report expects. Use `.get()` with defaults or conditional logging.
6. **The 0-byte DB file** — if you see a DB file that's 0 bytes, it was created but never initialized. The actual DB may be at a different path (e.g., `cerebrum_memory.db` not `subconscious.db`).
7. **WAL mode makes verification deceptive** — inserts commit to the WAL file (`*.db-wal`), not the main DB. A new `sqlite3.connect()` may see stale data until the WAL is checkpointed. If your script reports "0 rows" after inserts "succeeded", the data is in WAL. Verify with `PRAGMA wal_checkpoint(TRUNCATE)` before querying, or query from the same connection that wrote.

### WAL Verification Pitfall — Full Pattern

**Symptom:** `INSERT` reports success, `conn.commit()` returns, but `SELECT COUNT(*)` returns 0 from a new connection.

**Root cause:** WAL mode writes to `*.db-wal` first. The writer's connection sees the data, but a NEW connection only sees checkpointed data. If no checkpoint occurred, the new connection sees an empty table.

**Detection:**
```bash
ls -la ~/.hermes/cerebrum_memory.db*  # Look for .db-wal file
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA journal_mode;"  # Returns "wal"
```

**Fix — checkpoint before verifying:**
```python
conn = sqlite3.connect(db_path, isolation_level=None)
conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM tip_injection_attempts")
count = c.fetchone()[0]  # Now accurate
```

**Fix — verify from same connection:**
```python
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("INSERT INTO ...")
conn.commit()
c.execute("SELECT COUNT(*) FROM ...")  # Same conn sees WAL data
count = c.fetchone()[0]
```

**Anti-pattern — never do this:**
```python
# WRONG: separate connections, second sees stale data
conn1 = sqlite3.connect(db_path)
conn1.execute("INSERT ..."); conn1.commit(); conn1.close()
conn2 = sqlite3.connect(db_path)  # NEW connection
conn2.execute("SELECT COUNT(*)")  # Returns 0! Data is in WAL.
```

## Files Modified (2026-04-10 controller.py fix)

- `~/subconscious/controller.py`:
  - `get_conn()`: timeout 15→60s, busy_timeout 10s→55s
  - `run_full_audit()`: added `BEGIN IMMEDIATE` lock probe, graceful skip of phases 2-4
  - Report section: conditional logging for skipped calibration/distillation
