# SQLite `.recover` Extraction Technique

**Date:** May 16, 2026
**Session:** Cerebrum schema disaster recovery
**Use case:** When `PRAGMA integrity_check` fails, `.dump` fails, and table-by-table copy fails due to malformed schema

## Problem

All standard recovery methods fail on severely corrupted databases:
- `sqlite3 db .dump` → `database disk image is malformed`
- `sqlite3 db .schema` → `malformed database schema`
- Table-by-table `SELECT * FROM table` → `database disk image is malformed`
- Even `iterdump()` fails with the same error

## The `.recover` Command

SQLite 3.27+ includes a `.recover` dot-command that scans the raw database file page-by-page, bypassing the normal schema parser. It extracts valid rows even when the schema is corrupted.

```bash
# Extract all recoverable data as SQL INSERT statements
sqlite3 corrupted.db ".recover" > /tmp/recovered.sql

# The output is raw SQL — filter for specific tables
grep "INSERT INTO \"distilled_tips\"" /tmp/recovered.sql > /tmp/table_specific.sql

# Count recovered rows
grep -c "INSERT INTO \"distilled_tips\"" /tmp/recovered.sql
```

## Real-World Recovery (May 16, 2026)

**Scenario:** `cerebrum_memory.db` had a new-schema `distilled_tips` table (13 columns) that replaced the old-schema version (15 columns). All code expected the old schema. All backups were also corrupted.

**Recovery process:**

```bash
# Step 1: Attempt standard recovery — all fail
sqlite3 ~/.hermes/cerebrum_memory.db.corrupt_backup ".dump" 2>&1 | head -5
# → Error: database disk image is malformed

# Step 2: Use .recover
sqlite3 ~/.hermes/cerebrum_memory.db.corrupt_backup ".recover" > /tmp/cerebrum_recover.sql
# → Success: 1,279 INSERT statements extracted

# Step 3: Filter for the target table
grep "INSERT INTO \"distilled_tips\"" /tmp/cerebrum_recover.sql > /tmp/tips_recover.sql

# Step 4: Count and verify
grep -c "INSERT INTO \"distilled_tips\"" /tmp/tips_recover.sql
# → 1279

# Step 5: Create clean database with CORRECT schema
# Export all OTHER tables from current (working) DB
sqlite3 ~/.hermes/cerebrum_memory.db ".dump" | grep -v "INSERT INTO \"distilled_tips\"" > /tmp/all_other_tables.sql

# Step 6: Create old-schema table definition
sqlite3 /tmp/new_cerebrum.db << 'EOF'
CREATE TABLE distilled_tips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tip_type TEXT,
    condition TEXT,
    recommendation TEXT,
    rationale TEXT,
    tool_name TEXT,
    domain TEXT,
    confidence REAL,
    upvotes INTEGER,
    downvotes INTEGER,
    frequency INTEGER,
    source_ids TEXT,
    created_at REAL,
    last_seen REAL,
    last_used REAL
);
EOF

# Step 7: Import recovered data
sqlite3 /tmp/new_cerebrum.db < /tmp/tips_recover.sql

# Step 8: Import all other tables
sqlite3 /tmp/new_cerebrum.db < /tmp/all_other_tables.sql

# Step 9: Verify
sqlite3 /tmp/new_cerebrum.db "SELECT COUNT(*) FROM distilled_tips"
# → 1279
sqlite3 /tmp/new_cerebrum.db "PRAGMA integrity_check"
# → ok
```

## Key Differences from Standard Repair

| Method | When it works | When it fails |
|--------|-------------|---------------|
| `.dump` | Minor corruption, intact schema | Malformed schema |
| Table-by-table copy | Readable tables | Schema parser errors |
| `.recover` | **Always** — bypasses schema parser | Only when raw pages are physically damaged |

## Limitations

- `.recover` extracts raw row data but NOT constraints, indexes, or triggers
- You must recreate the schema (CREATE TABLE, CREATE INDEX) manually
- Foreign key constraints may be violated if referenced tables weren't recovered
- Some rows may be partially corrupted — `.recover` skips unrecoverable pages

## Prevention: Schema Migration Safety

**The root cause of this disaster:** A script rebuilt `distilled_tips` with a new schema without checking all consumers.

**Mandatory pre-migration checklist:**

```bash
# 1. Identify ALL consumers of the table
grep -rn "distilled_tips" ~/hermes-agent/ ~/.hermes/plugins/ ~/subconscious/

# 2. Document current schema
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA table_info(distilled_tips)"

# 3. Create migration script (NOT just DROP/CREATE)
# Migration should: add new columns, migrate data, THEN drop old columns

# 4. Test migration on copy
# 5. Verify all consumers still work
# 6. Only then apply to production
```

**Golden rule:** Never `DROP TABLE` without a migration plan. Always `ALTER TABLE ADD COLUMN` first, migrate data, then optionally drop old columns after all consumers are updated.
