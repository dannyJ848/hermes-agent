# SQLite Schema Discovery — Query Unknown Databases Safely

## Problem

You query a SQLite database assuming standard table/column names, but get:
```
sqlite3.OperationalError: no such table: training_rounds
sqlite3.OperationalError: no such column: status
```

This happens when:
- The database was created by a different module with different schema
- Schema evolved but old code references old names
- You're querying a database you didn't create (training gym, distillation buffer, etc.)

## Pattern: Always Discover Schema First

```python
import sqlite3

conn = sqlite3.connect(db_path)

# 1. List all tables
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()
print(f"Tables: {[t[0] for t in tables]}")

# 2. For each table, get column info
for table in tables:
    table_name = table[0]
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    print(f"\n{table_name} columns:")
    for col in cols:
        print(f"  {col[1]} ({col[2]})")  # name, type

# 3. Sample rows
for table in tables:
    table_name = table[0]
    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"\n{table_name}: {count} rows")
    if count > 0:
        sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
        print(f"  Sample: {sample}")

conn.close()
```

## Real Schema Examples

### training_gym.db
```
Tables: ['attempts', 'exercises', 'personal_records', 'sqlite_sequence', 'tier_progress']

exercises columns:
  id (INTEGER)
  name (TEXT)
  description (TEXT)
  tier (INTEGER)
  created_at (TEXT)

attempts columns:
  id (INTEGER)
  exercise_id (INTEGER)
  score (REAL)
  timestamp (TEXT)
  # NO "status" column — just score
```

### distillation_buffer.db
```
Tables: ['tips', 'tip_evaluations', 'tip_lineage', 'elo_history']

tips columns:
  id (INTEGER)
  content (TEXT)
  elo_score (REAL)
  created_at (TEXT)
  # NO "status" column
```

## Safe Query Pattern

Instead of assuming columns exist:

```python
# WRONG — will crash if column doesn't exist
cursor.execute("SELECT status FROM attempts")

# RIGHT — check columns first, query dynamically
cols = [c[1] for c in conn.execute("PRAGMA table_info(attempts)").fetchall()]
if 'status' in cols:
    result = conn.execute("SELECT status FROM attempts").fetchall()
else:
    # Fallback: use what exists
    result = conn.execute("SELECT score, timestamp FROM attempts").fetchall()
```

## Pitfalls

| Wrong | Right |
|-------|-------|
| Assume `training_rounds` table exists | Check `.tables` first |
| Assume `status` column exists | Run `PRAGMA table_info()` first |
| Hardcode schema from memory | Discover dynamically each session |
| Guess table names from module names | Check actual tables in the DB file |

## When to Use

- Any database in `~/.hermes/*.db` that you didn't create yourself
- Databases created by plugins or cron jobs
- Any query that fails with `no such table` or `no such column`
