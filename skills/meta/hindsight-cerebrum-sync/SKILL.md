---
name: hindsight-cerebrum-sync
description: SUPERSDED by Cortex Unified DB. The old cerebrum SQLite + Hindsight Postgres sync is obsolete. Use cortex_access.py instead. This skill now documents the unified Cortex database architecture.
version: 2.0
created: 2026-04-11
updated: 2026-04-13
superseded_by: cortex_access.py + cortex_flywheel.py
---

# CORTEX UNIFIED DATABASE (Supersedes Old Sync)

## What Changed (Apr 13)
All data from cerebrum SQLite + Hindsight Postgres + training gym was merged into a single
PostgreSQL database called `cortex` on localhost:5432. The old two-system sync is obsolete.

## Architecture
- **Database**: `cortex` on PostgreSQL localhost:5432, owned by `hindsight` user
- **Extensions**: pgvector(384), pg_trgm, uuid-ossp
- **23 tables**: cortex_nodes, cortex_edges, cortex_entities, cortex_documents, cortex_chunks,
  cortex_tool_calls, cortex_predictions, cortex_debug_sessions, cortex_token_usage,
  cortex_calibration, cortex_circuit_breakers, cortex_reasoning, cortex_step_rewards,
  cortex_eval_history, cortex_flywheel, cortex_life_events, cortex_identity,
  cortex_epistemic_facts, cortex_exploration, cortex_mastery, cortex_node_entities,
  cortex_entity_cooccurrences, cortex_migration_log

## Key Files
- `~/subconscious/cortex_access.py` — CortexDB class, single access point for ALL operations
- `~/subconscious/cortex_flywheel.py` — Autonomous eval+repair+consolidate loop
- `~/subconscious/cortex_schema_design.py` — Schema SQL + design doc

## Quick Usage
```python
from cortex_access import CortexDB
db = CortexDB()

# Insert a tip
tip_id = db.insert_node("When X happens, do Y", node_type="tip", domain="terminal")

# Get tips for Elo evaluation
tips = db.get_tips_for_eval(domain="terminal", limit=50)

# Update Elo rating
db.update_elo(tip_id, new_elo=1250.0, won=True)

# Search
results = db.search_text("terminal error recovery", node_type="tip")

# Stats
stats = db.get_stats()
```

## Connection String
```
postgresql://hindsight:hindsight@localhost:5432/cortex
```

## Data Counts (post-migration Apr 13)
- 13,933 nodes (tips: 1,869, experiences: 8,157, facts: 1,080, observations: 1,618, world: 1,008, etc.)
- 388,104 edges
- 4,369 entities
- 6,414 documents
- 5,251 predictions
- Elo: 1,322 rated tips, range 1124-1288, avg 1200

## Flywheel (cortex_flywheel.py)
Autonomous cycle: eval (Elo tournaments) -> repair (deactivate low-Elo) -> consolidation (merge dupes)
Run: `python3 ~/subconscious/cortex_flywheel.py`
Wired to cron d9d790021dd1 (every 2h).

## Migration Lessons Learned

### 1. SQL Schema Must Respect FK Dependency Order
Tables with foreign keys MUST be created AFTER the tables they reference.
cortex_entities before cortex_entity_cooccurrences. cortex_nodes before cortex_edges.
Always create leaf tables first, then tables that reference them.

### 2. SQLite to Postgres Type Conversion Is Fragile
- Timestamps can be int (unix), float (unix with decimals), string (ISO), or None
- Numeric fields can contain empty strings '' that cause "invalid input syntax for type double"
- Boolean fields in SQLite are stored as int (0/1), need bool() cast for Postgres
- Solution: write a robust `clean()` function that handles '' -> None, 'None' -> None

### 3. psycopg2 Cursor.fetchall() Consumes the Cursor
```python
# BUG: double fetchall() returns empty on second call
hc.execute("SELECT ... FROM memory_units")
rows = hc.fetchall()  # consumes cursor
for row in hc.fetchall():  # EMPTY!
```
Always assign to a variable ONCE: `rows = hc.fetchall()`, then iterate `rows`.

### 4. API Mismatches Between Layers
When building a flywheel that calls CortexDB methods, verify every method signature
matches before running. Common mismatches: extra kwargs (metrics=), wrong column names
(created_at vs started_at), missing error_message parameter.
Pattern: write the access layer FIRST, then write consumers that strictly match its API.

### 5. pgvector Dimension Must Match Embedding Model
BAAI/bge-small-en-v1.5 produces 384-dim vectors. The vector(384) column type must match.
If using a different model, change the dimension accordingly.

## Dual-Write Adapter (cortex_compat.py)
Gradual migration strategy: the distillation plugin still writes to SQLite, but `cortex_compat.py`
mirrors every write to Cortex in parallel. This avoids a risky big-bang rewrite.

**Integration points in `~/.hermes/plugins/distillation/__init__.py`:**
1. Import at module level: `from cortex_compat import cortex_sync as _cortex_sync`
2. After EACH `cer.commit()` that INSERTs a tip (3 locations ~L667, ~L1968, ~L2041):
   ```python
   if _CORTEX_SYNC:
       try: _cortex_sync('insert', 'distilled_tips', {...})
       except Exception: pass
   ```
3. After upvote/downvote UPDATE (~L2123): `_cortex_sync('upvote'|'downvote', ...)`
4. pre_llm_call READ path (~L2733): queries Cortex first via `cdb.search_text()`,
   falls back to SQLite if cortex is unavailable. The `_use_cortex` flag gates this.

**CRITICAL**: After ANY change to the distillation plugin:
```bash
rm -rf ~/.hermes/plugins/distillation/__pycache__
```
Python silently uses cached .pyc files — stale cache = changes ignored.

## Cron Jobs Wired to Cortex
| Job ID    | Name                    | Schedule      | Purpose                              |
|-----------|-------------------------|---------------|--------------------------------------|
| d9d790021dd1 | cortex-flywheel-baseline | every 2h    | Elo eval (50 pairs) + repair + consolidate |
| ece3733a111c | cortex-consolidation     | daily 4am   | Trust decay + promotion + merge      |
| 54efd7ef8bf6 | Cortex Dojo              | daily 3am   | Stats report + improvement analysis  |
| fca05291425c | Cortex Quality Sweep     | every 2h    | Tip tier audit + edge density check  |

## Old Data (Preserved As Backup)
- Cerebrum SQLite: `~/.hermes/cerebrum_memory.db` (13MB, 80+ tables) — READ ONLY, do not modify
- Hindsight Postgres: `localhost:5432/hindsight` (pid 50151) — READ ONLY, do not modify
- Migration log in cortex_migration_log table tracks every row migrated
