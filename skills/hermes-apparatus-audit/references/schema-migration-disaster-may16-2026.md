# Schema Migration Disaster — May 16, 2026

## Incident Summary

The `distilled_tips` table in `~/.hermes/cerebrum_memory.db` was rebuilt with a new schema during an audit/cleanup, but ALL dependent code still referenced the old schema. Result: 1,279 tips lost, all knowledge queries failing.

## Timeline

1. **Original schema** (pre-Apr 9): `tip_type`, `condition`, `recommendation`, `rationale`, `tool_name`, `domain`, `confidence`, `upvotes`, `downvotes`, `frequency`, `source_ids`, `created_at`, `last_seen`, `last_used`
2. **Backup created** (Apr 9): `cerebrum_memory.db.corrupt_backup` — 1,279 tips, old schema
3. **Table rebuilt** (sometime between Apr 9-May 16): New schema with `content`, `content_hash`, `source_key`, `source_tier`, `priority`, `tags`, `distilled_at`, `evaluated`, `judge_score`, `judge_feedback`, `sent_to_cortex`, `cortex_node_id`
4. **Current state** (May 16): Only 3 tips in new schema, all code queries old columns

## Affected Consumers

| File | Query Pattern | Status |
|------|--------------|--------|
| `~/.hermes/plugins/evey-rag/__init__.py` | `SELECT tip_type, condition, recommendation, confidence, source_ids FROM distilled_tips` | BROKEN |
| `~/.hermes/plugins/distillation/__init__.py` | `UPDATE distilled_tips SET confidence = 0.1, status = 'under_review' WHERE id=?` | BROKEN |
| `~/.hermes/tip_queue/r112_distill.py` | `INSERT INTO distilled_tips (tip_type, condition, recommendation, ...)` | BROKEN |
| `~/.hermes/skills/mlops/qwen27b-training-pipeline/scripts/dgx_distillation_daemon.py` | `SELECT condition, recommendation, confidence FROM distilled_tips` | BROKEN |

## Detection Commands

```bash
# Check actual schema
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA table_info(distilled_tips)"

# Check all consumers
find ~/.hermes -name "*.py" | xargs grep -l "distilled_tips" 2>/dev/null

# Check backup row counts
for f in ~/.hermes/cerebrum_memory.db*backup*; do
    echo -n "$f: "
    sqlite3 "$f" "SELECT COUNT(*) FROM distilled_tips" 2>/dev/null || echo "N/A"
done

# Check current row count
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM distilled_tips"
```

## Recovery Options

### Option A: Restore Old Schema (Recommended)
```bash
# Backup current broken state
cp ~/.hermes/cerebrum_memory.db ~/.hermes/cerebrum_memory.db.new_schema_backup

# Restore from old backup (has 1,279 tips)
cp ~/.hermes/cerebrum_memory.db.corrupt_backup ~/.hermes/cerebrum_memory.db

# Migrate the 3 new tips from new schema to old schema
# (manual INSERT with old column names)
```

### Option B: Migrate All Code (High Risk)
- Update evey-rag plugin queries
- Update distillation plugin queries  
- Update all tip injection scripts
- Update any other files referencing old columns
- Risk: missing one file = broken system

## Prevention Checklist

- [ ] Before any `DROP TABLE`, create a named backup
- [ ] After schema change, run `find` to identify ALL consumers
- [ ] Verify each consumer's queries match new schema
- [ ] Use `ALTER TABLE ADD COLUMN` for additive changes
- [ ] Maintain `_schema_version` meta table
- [ ] Run full system test after schema migration

## Related

- See `agent-self-audit` skill: "Table Rebuild Without Code Update Pitfall (May 16, 2026)"
- See `hermes-apparatus-audit` skill: Database Layer verification commands
