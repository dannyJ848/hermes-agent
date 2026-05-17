---
name: sqlite-corruption-repair
description: Repair corrupted SQLite databases by table-by-table copy to clean file. Use when PRAGMA integrity_check fails or database disk image is malformed.
version: 1.0
category: devops
---

# SQLite Database Corruption Repair

Repair corrupted SQLite databases by dumping and rebuilding into a clean file.

## Trigger
- `sqlite3.OperationalError: database is locked` that persists after clearing WAL/SHM
- `sqlite3.DatabaseError: database disk image is malformed`
- `PRAGMA integrity_check` returns anything other than `ok`

## Steps

### 1. Diagnose
```python
conn = sqlite3.connect(db_path)
result = conn.execute("PRAGMA integrity_check").fetchone()
print(result[0])  # "ok" or corruption details with page numbers
conn.close()
```

### 2. Clear WAL/SHM lock files first (simplest fix)
```bash
rm -f <db_path>-shm <db_path>-wal
```
Retry the operation. If it still fails, proceed to full repair.

### 3. Full Repair — Table-by-Table Copy

**CRITICAL**: `conn.iterdump()` will ALSO fail on corruption. Do NOT use it.

Instead, copy CREATE statements + row-by-row INSERT. Write the repair script to a file first (shell escaping of nested Python f-strings is fragile):

```python
import sqlite3, shutil, os

db_path = "/path/to/corrupted.db"
backup_path = db_path + ".corrupt_backup"
new_path = db_path + ".repaired"

shutil.copy2(db_path, backup_path)  # Always backup first

old_conn = sqlite3.connect(db_path)
new_conn = sqlite3.connect(new_path)

# Copy schema — CREATE TABLE
for name, sql in old_conn.execute(
    "SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
).fetchall():
    try:
        new_conn.execute(sql)
    except Exception:
        pass  # Skip sqlite_sequence and similar

# Copy schema — CREATE INDEX
for name, sql in old_conn.execute(
    "SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
).fetchall():
    try:
        new_conn.execute(sql)
    except Exception:
        pass

new_conn.commit()

# Copy data — table by table, row by row with INSERT OR IGNORE
failed_tables = []
for table_name, _ in tables:
    try:
        rows = old_conn.execute(f"SELECT * FROM [{table_name}]").fetchall()
        if not rows:
            continue
        cols = [d[0] for d in old_conn.execute(f"SELECT * FROM [{table_name}] LIMIT 0").description]
        placeholders = ", ".join(["?"] * len(cols))
        col_str = ", ".join(f"[{c}]" for c in cols)
        for row in rows:
            try:
                new_conn.execute(f"INSERT OR IGNORE INTO [{table_name}] ({col_str}) VALUES ({placeholders})", row)
            except Exception:
                pass
    except Exception as e:
        failed_tables.append(table_name)

new_conn.commit()
new_conn.close()
old_conn.close()
```

### 4. Verify and Swap
```python
test_conn = sqlite3.connect(new_path)
integrity = test_conn.execute("PRAGMA integrity_check").fetchone()
assert integrity[0] == "ok"
test_conn.close()

# Atomic swap
shutil.move(db_path, db_path + ".pre_repair")
shutil.move(new_path, db_path)
for ext in ["-shm", "-wal"]:
    p = db_path + ext
    if os.path.exists(p):
        os.remove(p)
```

### 5. Recreate lost tables
For any tables that failed to recover, recreate the structure:
```python
conn = sqlite3.connect(db_path)
conn.execute("CREATE TABLE IF NOT EXISTS lost_table (id INTEGER PRIMARY KEY, ...)")
conn.commit()
conn.close()
```

## Pitfalls
- **DO NOT use `iterdump()`** — it fails on corrupted databases with the same `DatabaseError`
- **Always backup first** before any repair attempt
- **FTS5 virtual tables** may error on recreation if shadow tables exist — drop shadow tables first or skip FTS recreation
- **`sqlite_sequence`** is auto-managed by SQLite — skip it during schema copy
- On macOS, `timeout` command is not available — use Python's signal alarm or rely on the terminal tool timeout parameter
- **Write repair scripts to a file first** then execute — shell escaping nested Python f-strings is fragile and will cause syntax errors
- **When querying unknown databases, discover schema first** — see `references/schema-discovery-pattern.md` for the safe pattern that prevents `no such table` and `no such column` errors
- **`.recover` for schema-level corruption** — When the schema itself is malformed (not just data), `.dump` and table-by-table copy both fail. Use `sqlite3 db ".recover"` to extract raw INSERT statements page-by-page, bypassing the schema parser. See `references/sqlite-recover-extraction.md` for the full technique.
