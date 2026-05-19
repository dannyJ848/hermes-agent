---
name: cerebrum-memory
version: 1.0
description: |
  Cerebrum Memory System — biologically-inspired 4-tier memory architecture.
  Manages episodic, semantic, procedural, and working memory for the agent.
trigger: |
  When configuring memory providers, troubleshooting memory issues,
  or setting up the Cerebrum knowledge base.
---

# Cerebrum Memory System

## Overview
Cerebrum is a 4-tier memory system inspired by human cognition:
1. **Working Memory**: Active session context (LCM)
2. **Episodic Memory**: Past session logs (`~/.hermes/memory/`)
3. **Semantic Memory**: Distilled tips (`cerebrum_memory.db`)
4. **Procedural Memory**: Skills (`~/.hermes/skills/`)

## Database Schema
The canonical `distilled_tips` table has 15 columns:
- `tip_type`, `condition`, `recommendation`, `rationale`
- `tool_name`, `domain`, `confidence`
- `upvotes`, `downvotes`, `frequency`
- `source_ids`, `created_at`, `last_seen`, `last_used`

## Key Operations
```python
# Query tips
import sqlite3
conn = sqlite3.connect(os.path.expanduser("~/.hermes/cerebrum_memory.db"))
c = conn.cursor()
c.execute("SELECT * FROM distilled_tips WHERE domain=? ORDER BY confidence DESC", (domain,))

# Insert tip
c.execute("""
    INSERT INTO distilled_tips 
    (tip_type, condition, recommendation, rationale, tool_name, domain, confidence, upvotes, downvotes, frequency, source_ids, created_at, last_seen)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, 1, ?, ?, ?)
""", (tip_type, condition, recommendation, rationale, tool_name, domain, confidence, source_ids, now, now))
```

## Maintenance
- Run `PRAGMA table_info(distilled_tips)` before schema changes
- Backup before any ALTER/DROP operations
- Verify all consumers after schema changes

## YantrikDB Integration
YantrikDB is a Rust-based cognitive memory engine with vector search, graph relations, and async ingest. It uses a bundled `potion-base-2M` embedder (~7MB) via `YantrikDB.with_default(path)`.

**Migration from Cerebrum to YantrikDB:**
- Cerebrum tips can be copied as `semantic` memories with `namespace='cerebrum_tips'`
- **Critical pitfall:** YantrikDB's async ingest queue has a hard max of 256 pending ops. Bulk migration of 1,000+ tips will saturate it.
- **Workaround:** Use `record_batch()` with chunk_size=10, call `think()` every 3 chunks to flush, and accept that very large migrations may need to run in a standalone background script (not within Hermes's 600s terminal timeout).
- See `references/yantrikdb-migration.md` for full details.

## Current State
- 1,282 tips in distilled_tips
- 22 tables in cerebrum_memory.db
- Schema validated: 15 columns match canonical
- YantrikDB migration: partially complete (queue saturation issue documented)
