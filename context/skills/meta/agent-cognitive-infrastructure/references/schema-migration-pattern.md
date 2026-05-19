# Database Schema Migration Pattern

## Session: Enhancement Cycle 6, 2026-05-09

## Problem

Building new cognitive systems that need new tables/columns, but the existing database was created by earlier code with different schemas. INSERTs fail with missing columns.

## Example Failure

```python
# SessionEndExtractor.save_lessons() tries:
c.execute("""
    INSERT INTO rapid_learnings (lesson, category, source, created_at)
    VALUES (?, ?, ?, strftime('%s', 'now'))
""", (lesson["lesson"], lesson["category"], lesson["source"]))

# Error:
sqlite3.OperationalError: table rapid_learnings has no column named category
```

Actual schema: `id, session_id, trigger_tool, trigger_args, outcome, lesson, confidence, applied_count, created_at`
Expected by code: `..., category, source`

## Fix Pattern

```python
import sqlite3
from pathlib import Path

db_path = Path.home() / '.hermes' / 'cerebrum_memory.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 1. Check existing columns
cursor.execute("PRAGMA table_info(rapid_learnings)")
cols = [c[1] for c in cursor.fetchall()]

# 2. Add missing columns dynamically
for col in ['category', 'source']:
    if col not in cols:
        cursor.execute(f"ALTER TABLE rapid_learnings ADD COLUMN {col} TEXT")
        print(f"Added column: {col}")

conn.commit()
conn.close()
```

## Prevention

1. **Always check schema before INSERTing** — use `PRAGMA table_info()`
2. **Use `INSERT OR IGNORE` with explicit column lists** — fails gracefully
3. **Version your schema** — add a `schema_version` table to track migrations
4. **Create tables with `IF NOT EXISTS`** — safe for repeated runs

## Migration Utility

```python
def ensure_columns(db_path: str, table: str, columns: dict):
    """Ensure table has required columns. Add if missing.
    
    columns: {column_name: sqlite_type}
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    existing = {col[1] for col in c.fetchall()}
    
    for col_name, col_type in columns.items():
        if col_name not in existing:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
            print(f"[MIGRATION] Added {col_name} {col_type} to {table}")
    
    conn.commit()
    conn.close()

# Usage:
ensure_columns("cerebrum_memory.db", "rapid_learnings", {
    "category": "TEXT",
    "source": "TEXT"
})
```

## When This Happens

- Adding new cognitive systems that write to existing tables
- Refactoring table schemas across enhancement cycles
- Multiple code paths writing to same table with different assumptions
- Plugin code that expects columns added by other plugins
