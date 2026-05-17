# cerebrum-schema-disaster-may-2026

*Researched: 2026-05-16 12:19 CDT*

# Cerebrum Schema Disaster — May 2026

## Incident Summary

On May 16, 2026, the cerebrum knowledge base (`~/.hermes/cerebrum_memory.db`) was discovered to have a corrupted `distilled_tips` table schema. The table had been rebuilt with a new 3-column schema (`judge_score`, `content`, `tags`) while all code (evey-rag plugin, distillation pipeline) expected the canonical 15-column schema. This caused all knowledge retrieval queries to fail with "no such column" errors, rendering the semantic memory system non-functional.

## Root Cause

1. **Schema change without migration plan**: The `distilled_tips` table was dropped and recreated with a new schema without checking all consumers
2. **No consumer audit**: Code querying the table (evey-rag `__init__.py`, distillation pipeline) was not updated to match the new schema
3. **Backup available but not used**: A corrupt backup (`cerebrum_memory.db.corrupt_backup`) existed with the old schema but was not initially leveraged

## Impact

- **1,279 tips lost** from the corrupted table (only 3 tips in new schema remained)
- evey-rag `knowledge_search` tool returned empty results for all queries
- Agent could not recall past learnings, configurations, or patterns
- Distillation pipeline could not insert new tips

## Recovery Process

### Phase 1: Diagnosis
```bash
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA table_info(distilled_tips)"
# → Showed wrong columns: judge_score, content, tags
```

### Phase 2: Data Recovery
```bash
# Used SQLite .recover to extract maximum data from corrupt backup
sqlite3 ~/.hermes/cerebrum_memory.db.corrupt_backup ".recover" > /tmp/cerebrum_recover.sql
# → 16MB SQL dump with 1,279 INSERT statements
```

### Phase 3: Schema Rebuild
1. Exported all other tables from current DB (20 tables, 516KB)
2. Created new DB with canonical 15-column `distilled_tips` schema
3. Imported recovered data + 3 new tips migrated from wrong schema

### Phase 4: Verification
- DB integrity check: `ok`
- Tip count: 1,282 (1,279 recovered + 3 migrated)
- Avg confidence: 0.86
- evey-rag queries execute successfully

## Key Lessons

1. **Never DROP TABLE without migration plan**: Always create migration scripts, check all consumers, and maintain backward compatibility
2. **Always verify schema before inserting**: Use `PRAGMA table_info()` before any data operation
3. **Keep `.recover` output as backup**: SQLite's `.recover` command can extract data even from severely corrupted files
4. **The canonical schema has 15 columns**: `tip_type`, `condition`, `recommendation`, `rationale`, `tool_name`, `domain`, `confidence`, `upvotes`, `downvotes`, `frequency`, `source_ids`, `created_at`, `last_seen`, `last_used`
5. **Cerebrum fallback is the primary knowledge path**: Even when Hindsight appears "down", the evey-rag plugin falls back to cerebrum SQLite

## Prevention

- Created `cerebrum-schema-recovery` skill with full recovery pipeline
- Added schema verification to `cortex-flywheel-diagnostics` skill
- Updated SOUL.md with schema mismatch detection heuristics
- All future schema changes must include consumer audit (`grep` all code referencing the table)

## Current State

| Component | Status | Details |
|-----------|--------|---------|
| Cerebrum SQLite | ONLINE | 1,282 tips, canonical schema |
| evey-rag fallback | ONLINE | SQL queries match schema |
| Hindsight API | Not active | Cortex is configured as memory provider |
| Knowledge retrieval | FUNCTIONAL | Via cerebrum fallback |


## Sources

- Internal system audit May 16 2026
- SQLite .recover documentation
- evey-rag plugin source code
