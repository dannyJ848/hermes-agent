---
name: cerebrum-schema-recovery
description: Recover from cerebrum schema disasters — when distilled_tips table is corrupted, rebuilt with wrong columns, or dropped entirely. Full recovery pipeline from backup extraction to schema verification.
version: 1.0.0
metadata:
  hermes:
    tags: [cerebrum, schema, recovery, sqlite, distillation, memory]
    related_skills: [cortex-flywheel-diagnostics, distillation-manual-tip-insertion, distillation-quality-debug]
---

# Cerebrum Schema Recovery

Complete recovery pipeline for when the cerebrum_memory.db `distilled_tips` table schema is corrupted, rebuilt with wrong columns, or accidentally dropped.

## When to Use

- `knowledge_search` returns empty results despite tips existing
- evey-rag plugin throws "no such column" errors
- `distilled_tips` table has wrong columns (e.g., `judge_score` instead of `confidence`)
- Table was dropped and recreated with incomplete schema
- Any schema mismatch between code queries and actual DB columns

## The Canonical Schema

The evey-rag plugin and all distillation code expect this 15-column schema:

| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER PRIMARY KEY | Auto-increment |
| tip_type | TEXT | 'strategy', 'recovery', 'optimization', 'heuristic' |
| condition | TEXT | IF-clause describing trigger |
| recommendation | TEXT | THEN-clause describing action |
| rationale | TEXT | Why this tip works |
| tool_name | TEXT | Associated tool (optional) |
| domain | TEXT | Domain tag (e.g., 'devops', 'training') |
| confidence | REAL | 0.0-1.0 quality score |
| upvotes | INTEGER | Positive feedback count |
| downvotes | INTEGER | Negative feedback count |
| frequency | INTEGER | Observation count |
| source_ids | TEXT | Session/trace references |
| created_at | REAL | Unix timestamp |
| last_seen | REAL | Unix timestamp |
| last_used | REAL | Unix timestamp |

## Quick Diagnostic

```bash
# 1. Check if DB exists and is writable
ls -la ~/.hermes/cerebrum_memory.db

# 2. Check actual schema
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA table_info(distilled_tips)"

# 3. Check tip count
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM distilled_tips"

# 4. Test evey-rag query
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT tip_type, condition, recommendation, confidence, source_ids FROM distilled_tips WHERE confidence > 0.7 LIMIT 3"
```

**If step 4 fails with "no such column" → schema mismatch confirmed. Proceed to recovery.**

## Recovery Pipeline

### Phase 1: Preserve Everything

```bash
# Create timestamped backup directory
BACKUP_DIR="$HOME/.hermes/backups/schema_recovery_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup current DB (even if corrupt)
cp ~/.hermes/cerebrum_memory.db "$BACKUP_DIR/cerebrum_memory.db.current"

# Check for corrupt backup (from previous failed recovery)
if [ -f ~/.hermes/cerebrum_memory.db.corrupt_backup ]; then
    cp ~/.hermes/cerebrum_memory.db.corrupt_backup "$BACKUP_DIR/cerebrum_memory.db.corrupt_backup"
fi

# List all backups
ls -lt ~/.hermes/cerebrum_memory.db.* 2>/dev/null | head -10
```

### Phase 2: Extract Data from Corrupt Backup

```bash
# Use SQLite .recover to extract maximum data from corrupt backup
sqlite3 ~/.hermes/cerebrum_memory.db.corrupt_backup ".recover" > "$BACKUP_DIR/cerebrum_recover.sql"

# Check how much data was recovered
wc -l "$BACKUP_DIR/cerebrum_recover.sql"
grep -c "INSERT INTO distilled_tips" "$BACKUP_DIR/cerebrum_recover.sql"
```

**If .recover produces 0 INSERTs:** The backup is too damaged. Try:
- Check older backups: `ls -lt ~/.hermes/cerebrum_memory.db.*`
- Use `.dump` instead of `.recover` if the file is readable but has integrity issues
- Check if the data exists in other tables (staging_tips, experiences)

### Phase 3: Export Other Tables from Current DB

```bash
# Dump all tables EXCEPT distilled_tips from current DB
sqlite3 ~/.hermes/cerebrum_memory.db ".dump" | grep -v "INSERT INTO distilled_tips" > "$BACKUP_DIR/cerebrum_current_other_tables.sql"
```

### Phase 4: Build Correct Schema

```bash
# Create schema file
cat > "$BACKUP_DIR/cerebrum_correct_schema.sql" << 'EOF'
-- Drop wrong table if exists
DROP TABLE IF EXISTS distilled_tips;

-- Create with canonical schema
CREATE TABLE distilled_tips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tip_type TEXT NOT NULL,
    condition TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    rationale TEXT DEFAULT '',
    tool_name TEXT DEFAULT '',
    domain TEXT DEFAULT '',
    confidence REAL DEFAULT 0.5,
    upvotes INTEGER DEFAULT 1,
    downvotes INTEGER DEFAULT 0,
    frequency INTEGER DEFAULT 1,
    source_ids TEXT DEFAULT '',
    created_at REAL DEFAULT (strftime('%s', 'now')),
    last_seen REAL DEFAULT (strftime('%s', 'now')),
    last_used REAL DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_distilled_tips_domain ON distilled_tips(domain);
CREATE INDEX IF NOT EXISTS idx_distilled_tips_confidence ON distilled_tips(confidence);
CREATE INDEX IF NOT EXISTS idx_distilled_tips_tip_type ON distilled_tips(tip_type);
EOF
```

### Phase 5: Assemble New Database

```bash
# Create new DB with correct schema
sqlite3 ~/.hermes/cerebrum_memory.db.new < "$BACKUP_DIR/cerebrum_correct_schema.sql"

# Import other tables from current DB
sqlite3 ~/.hermes/cerebrum_memory.db.new < "$BACKUP_DIR/cerebrum_current_other_tables.sql"

# Import recovered distilled_tips data
sqlite3 ~/.hermes/cerebrum_memory.db.new < "$BACKUP_DIR/cerebrum_recover.sql"
```

### Phase 6: Verify and Migrate New Tips

```bash
# Check integrity
sqlite3 ~/.hermes/cerebrum_memory.db.new "PRAGMA integrity_check"

# Check tip count
sqlite3 ~/.hermes/cerebrum_memory.db.new "SELECT COUNT(*) FROM distilled_tips"

# Check for tips in wrong schema (from current DB that had new schema)
# These will have columns like judge_score, content, tags instead of confidence, condition, recommendation
sqlite3 ~/.hermes/cerebrum_memory.db.new "SELECT COUNT(*) FROM distilled_tips WHERE condition IS NULL OR condition = ''"

# If there are tips with empty condition, they were in the wrong schema
# Migrate them manually:
```

### Phase 7: Migrate Tips from Wrong Schema

If the current DB had tips in a wrong schema (e.g., `judge_score`, `content`, `tags` columns), migrate them:

```python
import sqlite3

# Connect to new DB
conn = sqlite3.connect('~/.hermes/cerebrum_memory.db.new')
c = conn.cursor()

# Find tips with empty condition (indicates wrong schema)
c.execute("SELECT id, tip_type, condition, recommendation, confidence FROM distilled_tips WHERE condition IS NULL OR condition = '' OR condition = 'NULL'")
wrong_schema_tips = c.fetchall()

for tip_id, tip_type, condition, recommendation, confidence in wrong_schema_tips:
    # These tips were stored with different column names
    # Get the actual data from the recovered SQL or old DB
    # For tips that came from the new-schema DB:
    # - judge_score maps to confidence
    # - content maps to recommendation (or condition + recommendation combined)
    # - tags maps to domain
    
    # You'll need to inspect the old schema to know exact mappings
    # For now, flag them for manual review:
    c.execute("UPDATE distilled_tips SET condition = 'MIGRATION_NEEDED: Review and fix this tip' WHERE id = ?", (tip_id,))

conn.commit()
conn.close()
```

### Phase 8: Replace and Final Verify

```bash
# Backup current DB one more time
cp ~/.hermes/cerebrum_memory.db ~/.hermes/cerebrum_memory.db.pre_rebuild_backup

# Replace with new DB
cp ~/.hermes/cerebrum_memory.db.new ~/.hermes/cerebrum_memory.db

# Final verification
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA integrity_check"
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) as total, ROUND(AVG(confidence),2) as avg_conf FROM distilled_tips"
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT tip_type, condition, recommendation, confidence, source_ids FROM distilled_tips WHERE confidence > 0.7 LIMIT 3"
```

## Prevention Checklist

- [ ] Never `DROP TABLE` without migration plan
- [ ] Always `grep` all consumers before schema changes
- [ ] Run `PRAGMA table_info()` before any INSERT
- [ ] Keep `.recover` output as backup before schema changes
- [ ] Test evey-rag queries after any schema change
- [ ] Document schema version in DB comment or metadata table

## Common Schema Variants

| Variant | Columns | Used By |
|---------|---------|---------|
| Canonical (old) | 15 columns: tip_type, condition, recommendation, rationale, tool_name, domain, confidence, upvotes, downvotes, frequency, source_ids, created_at, last_seen, last_used | evey-rag, distillation pipeline |
| New (broken) | 3 columns: judge_score, content, tags | Incorrect rebuild |
| staging_tips | 8 columns: content, content_hash, source_key, source_tier, priority, tags, distilled_at | Some distillation pipelines |

**Always verify which variant your installation uses before inserting data.**

## One-Liner Health Check

```bash
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT CASE WHEN COUNT(*) > 0 THEN 'HEALTHY: ' || COUNT(*) || ' tips' ELSE 'EMPTY' END FROM distilled_tips;" && sqlite3 ~/.hermes/cerebrum_memory.db "SELECT CASE WHEN COUNT(*) > 0 THEN 'CONFIDENCE_OK' ELSE 'NO_HIGH_CONF' END FROM distilled_tips WHERE confidence > 0.7;"
```
