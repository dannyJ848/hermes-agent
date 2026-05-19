---
name: sqlite-to-postgres-shim
description: Build a connection-level SQLite-to-PostgreSQL proxy shim that intercepts sqlite3.connect() calls and transparently routes queries to Postgres. Handles schema mismatches, column remapping, and E2E testing. Use when migrating a Python codebase from SQLite to Postgres without rewriting all queries.
version: 1.0
tags: [sqlite, postgres, migration, shim, monkey-patch, schema-remap]
---

# SQLite-to-PostgreSQL Connection-Level Shim

## When to Use
- Migrating a large Python codebase (50+ modules) from SQLite to PostgreSQL
- Can't rewrite every SQL query in every module
- Need transparent interception at the `sqlite3.connect()` level
- Source SQLite tables have different schemas than target Postgres tables

## Architecture

### Core Pattern: Monkey-patch sqlite3.connect
```python
import sqlite3 as _sq

# Save the REAL connect function at MODULE LEVEL before patching
_ORIGINAL_CONNECT = _sq.connect

def patch_sqlite3():
    """Replace sqlite3.connect with CortexConnection factory."""
    _sq.connect = _patched_connect

def _patched_connect(database, *args, **kwargs):
    # Detect if this is a database we want to intercept
    if 'cerebrum_memory.db' in str(database):
        return CortexConnection(database, *args, **kwargs)
    return _ORIGINAL_CONNECT(database, *args, **kwargs)
```

### The Three Critical Problems (and fixes)

#### 1. Infinite Recursion
**Problem**: `CortexConnection.__init__` creates a SQLite fallback connection. If you call `sqlite3.connect()` inside it, you hit the patched version → infinite recursion.

**Fix**: Save `_ORIGINAL_CONNECT` at MODULE level (not inside `patch_sqlite3()`):
```python
# CORRECT — module-level
_ORIGINAL_CONNECT = _sq.connect

def patch_sqlite3():
    _sq.connect = _patched_connect  # uses _ORIGINAL_CONNECT via closure
```

#### 2. INSERT Schema Mismatch
**Problem**: SQLite `INSERT INTO distilled_tips (condition, recommendation, domain) VALUES (?, ?, ?)` — but Postgres `cortex_nodes` has columns `text, domain, metadata` (no `condition` column).

**Fix**: Parse SQL into column/value dicts, then use schema-aware insert:
```python
def _insert_to_cortex(self, sql, params, table):
    data = self._parse_sql_to_dict(sql, params)  # {condition: 'x', recommendation: 'y'}
    # Map to cortex_nodes schema
    insert_data = {
        'node_type': self._infer_node_type(table),
        'domain': data.get('domain', 'general'),
        'confidence': data.get('confidence', 0.5),
    }
    # Remaining fields → metadata JSONB
    metadata = {k: v for k, v in data.items() if k not in core_fields}
    insert_data['text'] = json.dumps(data, default=str)[:500]
    insert_data['metadata'] = json.dumps(metadata)
    # Use cortex_access.insert_node() — NOT raw SQL translation
```

**Key insight**: Raw SQL translation (`REPLACE INTO cortex_nodes (...)`) FAILS when column sets differ. Must go through an ORM-like layer.

#### 3. SELECT Column Remapping
**Problem**: `SELECT condition FROM distilled_tips WHERE condition = ?` — `condition` doesn't exist in `cortex_nodes`. Data is in `metadata->>'condition'`.

**Fix**: Regex remap column names in the translated SQL:
```python
_col_remap = [
    ('condition', "metadata->>'condition'"),
    ('recommendation', "metadata->>'recommendation'"),
    ('tip_type', "metadata->>'tip_type'"),
]
for _old, _new in _col_remap:
    sql_pg = re.sub(
        r'(?<!>)(?<!\w)\b' + _old + r'\b',
        _new, sql_pg, flags=re.IGNORECASE
    )
```

**DOUBLE-REMAP GOTCHA**: After replacing `condition` → `metadata->>'condition'`, the word `condition` appears INSIDE the replacement text. A second pass would produce `metadata->>'metadata->>'condition''`.

**Fix**: Use negative lookbehind `(?<!>)` — this prevents matching `condition` when preceded by `>` (as in `->>'condition'`).

**DO NOT USE variable-length lookbehind** like `(?<!>'\w)` — Python's `re` module doesn't support it. Only fixed-length lookbehinds work.

## E2E Testing Pattern

Always test all three phases:

```python
# Phase 1: Write through shim (simulates app code)
conn = sqlite3.connect('cerebrum_memory.db')  # intercepted by shim
cur = conn.cursor()
cur.execute("INSERT INTO distilled_tips (condition, domain) VALUES (?, ?)",
            ('test condition', 'testing'))
conn.commit()
conn.close()

# Phase 2: Verify in Postgres DIRECTLY (bypasses shim)
import psycopg2
pg = psycopg2.connect('postgresql://user:pass@localhost:5432/db')
pc = pg.cursor()
pc.execute("SELECT id, text FROM cortex_nodes WHERE text LIKE '%test condition%'")
assert pc.fetchone() is not None, "Write didn't land in Postgres!"

# Phase 3: Read back through shim (simulates app code)
conn2 = sqlite3.connect('cerebrum_memory.db')
cur2 = conn2.cursor()
cur2.execute("SELECT condition FROM distilled_tips WHERE condition = ?",
             ('test condition',))
assert cur2.fetchone() is not None, "Read through shim returned nothing!"
```

## Table Mapping Strategy

When multiple SQLite tables map to one Postgres table (e.g., `distilled_tips`, `semantic_facts`, `predictions` → `cortex_nodes`):

1. **Inject `node_type` filter on SELECT**: Every `SELECT FROM distilled_tips` gets `WHERE node_type = 'tip'` prepended
2. **Inject `node_type` on INSERT**: Every `INSERT INTO distilled_tips` gets `node_type = 'tip'` added
3. **Map via lookup dict**: `{'distilled_tips': 'cortex_nodes', 'semantic_facts': 'cortex_nodes'}`
4. **Unmapped tables → KV store**: For tables without a clear mapping, store as JSON in a generic `cortex_kv_store` table

## Deployment Checklist

1. Write shim module (`cortex_compat_shim.py`)
2. Add one-liner import to each target file:
   ```python
   from cortex_compat_shim import patch_sqlite3; patch_sqlite3()
   ```
3. Place import AFTER `import sqlite3` in each file
4. `rm -rf __pycache__/` before testing (stale .pyc silently ignores changes)
5. Run E2E test (write → direct verify → read-back)
6. Check for unmapped tables falling through to SQLite fallback

## Audit Findings (Apr 13 comprehensive audit)

After running a 10-audit marathon against a live Cortex DB (15,815 nodes), 4 shim bugs were found:

### ALL 4 ORIGINAL BUGS RESOLVED (Apr 15 fix gauntlet):
- Bug 1 (WHERE =): Fixed — WHERE clause now works for all mapped tables
- Bug 2 (condition/recommendation = None): FIXED — Added text field fallback regex. ~78% of tips had condition/recommendation merged into `text` (IF...THEN format) not metadata. The column remap now uses `COALESCE(metadata->>'condition', CASE WHEN text ~* '^IF\s+' THEN substring...)` to extract from text when metadata is empty.
- Bug 3 (INSERT-then-SELECT): Was already working — false alarm from test path not matching 'cerebrum'
- Bug 4 (predictions NoneType): Was already working — predictions SELECT/INSERT both work fine

### Additional fixes applied Apr 15:
- **regex escape bug**: Column remap SQL strings containing `\s` were interpreted by re.sub. Fixed by using `lambda m: _new` instead of passing `_new` directly as replacement.
- **f-string SQL injection**: All 6 INSERT/UPDATE/DELETE f-strings now validated through `_safe_col()` and `_safe_table()` which reject non-alphanumeric-underscore characters.
- **DELETE handler**: Now injects node_type filter and remaps condition/recommendation in WHERE clause (was missing).
- **File permissions**: Shim tightened to 600 (was 644).
- **WHERE LIKE expansion**: When `condition`/`recommendation` appear in WHERE with LIKE/ILIKE/=, adds `OR text ILIKE %s` to also match the 78% of tips where condition is in text.

### REMAINING WARNS (non-critical):
- 10 nodes with NULL created_at (migration artifacts)
- 1 node with future timestamp (clock skew during insert)
- ~48% nodes without embeddings (circuit_breakers at 13.7%)
- 1 line with DSN in shim (password masked with ***)

## Pitfalls

- **Variable-length lookbehind**: Python `re` only supports fixed-length lookbehinds. Use `(?<!>)` not `(?<!>'\\w)`.
- **fetchall() consumes cursor**: Calling `fetchall()` twice on same cursor returns empty on second call.
- **psycopg2 transaction abort cascade**: One failed INSERT aborts ALL subsequent commands until `rollback()`. Roll back after EVERY failed insert in a loop.
- **SQLite booleans**: Stored as 0/1 ints — must wrap with `bool()` for Postgres.
- **SQLite timestamps**: Mixed format (int, float, ISO string, milliseconds). Need robust converter.
- **Empty strings in numeric columns**: SQLite stores `""` in float columns — must convert to `None` for Postgres.
- **Shell quoting**: For complex Python scripts, write to `/tmp/file.py` then `python3 /tmp/file.py`. Never inline in terminal commands.
- **sqlite3.connect() returns connection, not cursor**: Must call `.cursor()` before `.execute()`. Passing the connection directly to execute causes AttributeError.
- **Numeric columns can't compare with `= ''`**: Postgres rejects `WHERE confidence = ''` for real-type columns. Use `IS NULL` only for numeric checks.
- **Table may not exist in SQLite**: `episodic_memory` table was renamed to `experiences`. Always check `sqlite_master` for actual table names before querying.
- **No content_hash column**: If dedup was expected via content_hash, check actual schema — it may use text-based comparison instead. Always verify column existence with `information_schema.columns`.
