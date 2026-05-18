---
name: cortex-flywheel-diagnostics
description: Diagnose and fix the Cortex continuous learning flywheel. Identifies injection bottlenecks, broken subsystems, dead R-modules, and efficiency gaps. Based on real diagnostics from a 2.4% efficiency system.
version: 1.0.0
metadata:
  hermes:
    tags: [cortex, diagnostics, flywheel, debugging, self-improvement]
    related_skills: [cortex-flywheel-operation, distillation-quality-debug, plugin-integration-audit]
---

# Cortex Flywheel Diagnostics

Real-world diagnostic methodology for the Cortex learning apparatus. Identifies what's actually working vs what's just wired.

## When to Use

- User says "why isn't my agent learning", "tips aren't helping", "flywheel broken"
- After tip injection shows low hit rates
- When daemon logs show errors or zero metacognition rounds
- Periodic health check (weekly recommended)

## Quick Diagnostic Scan

Run these checks in order. Full SQL queries available in `references/diagnostic-queries.sql`.

### 1. Injection Effectiveness
```sql
-- What % of tips have ever been accessed?
SELECT 
  COUNT(CASE WHEN access_count > 0 THEN 1 END) * 100.0 / COUNT(*) as hit_rate,
  COUNT(*) as total_tips
FROM distilled_tips;
```

**Healthy:** >20% hit rate  
**Critical:** <5% hit rate

### 2. Elo Distribution
```sql
SELECT 
  CASE 
    WHEN elo < 1000 THEN 'garbage'
    WHEN elo < 1200 THEN 'bad'
    WHEN elo < 1400 THEN 'weak'
    WHEN elo < 1600 THEN 'ok'
    WHEN elo < 1800 THEN 'good'
    ELSE 'strong'
  END as tier,
  COUNT(*) as count
FROM distilled_tips
GROUP BY tier;
```

**Healthy:** Most tips in 1600+ range  
**Critical:** Most tips <1200

### 3. Injection Budget
```python
# Check how many injection calls are dropped per turn
# Look for "governor dropped X lines" in logs
# Or count build_injection calls vs actual injected tips
```

**Healthy:** <50% drop rate  
**Critical:** >80% drop rate (97.6% seen in field)

### 4. World Model Simulation
```python
# Check if simulate() ever fires
# Look for "simulating" in logs
# Or check simulation_gate actual_rate vs target_rate
```

**Healthy:** 5-15% simulation rate  
**Critical:** 0% (gate too strict)

### 5. Metacognition Rounds
```sql
SELECT COUNT(*) as completed_rounds FROM metacog_predictions WHERE round_completed = 1;
```

**Healthy:** >0 rounds/week  
**Critical:** 0 rounds ever

### 6. Episodic Memory Retrieval
```sql
-- Check salience filter
SELECT COUNT(*) as meaningful FROM experiences WHERE elo > 1200 AND confidence > 0.5;
SELECT COUNT(*) as total FROM experiences;
```

**Healthy:** >10% meaningful  
**Critical:** 0% retrieved (salience filter rejects all)

### 7. DB Schema Staleness (Cortex Flywheel)
**Symptom:** Orchestrator reports "no such column: node_type" or similar schema errors.
**First check:** The error may be from STALE CACHED SCHEMA, not the actual DB.

```bash
# Verify actual schema BEFORE attempting ALTER
sqlite3 ~/.hermes/cortex.db ".schema cortex_nodes"
```

**If the column already exists:** The orchestrator's cached schema info is stale. Restart the gateway or the cognitive orchestrator process to refresh.

**If the column is actually missing:** The table was created with an incomplete schema. Add the missing columns:
```sql
ALTER TABLE cortex_nodes ADD COLUMN node_type TEXT DEFAULT 'generic';
ALTER TABLE cortex_nodes ADD COLUMN priority INTEGER DEFAULT 5;
ALTER TABLE cortex_nodes ADD COLUMN tags TEXT DEFAULT '[]';
ALTER TABLE cortex_nodes ADD COLUMN source TEXT DEFAULT 'cortex';
```

**Pitfall — "Missing column" on DGX cognitive orchestrator (May 2026):**
The DGX cognitive orchestrator reported `node_type` missing from `cortex_nodes`, but SSH verification showed the column already existed. The orchestrator's schema cache was stale from an earlier incomplete initialization.

**Fix pattern:**
```bash
# 1. Verify actual schema via SSH (don't trust orchestrator error)
ssh djg6228@spark-85e8.local "sqlite3 /home/djg6228/.hermes/cortex.db '.schema cortex_nodes'"
# → Shows node_type column exists

# 2. Reinitialize the orchestrator (not ALTER the DB)
ssh djg6228@spark-85e8.local "cd /data/SpecForge/hermes-agent && venv/bin/python -c 'from plugins.cognitive_orchestrator import CognitiveOrchestrator; co = CognitiveOrchestrator(); co.initialize_all_subsystems()'"
# → 20/20 subsystems active
```

**Key lesson:** When a cognitive orchestrator reports schema errors, always verify the ACTUAL database schema first. The error may be from cached/stale schema info, not the DB itself. Reinitializing the orchestrator refreshes its schema cache without touching the database.

**Pitfall:** Don't assume the DB is wrong just because the error says so. Always verify with `.schema` first. This saves time and prevents unnecessary schema migrations.

### 8. Cerebrum Schema Mismatch (Cerebrum SQLite)
**Symptom:** evey-rag fallback queries fail with "no such column" errors, or `knowledge_search` returns empty results despite tips existing.
**Root cause:** The `distilled_tips` table schema was changed (e.g., rebuilt with wrong columns) but code still queries the old schema.

**Diagnostic:**
```bash
# Check actual schema
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA table_info(distilled_tips)"

# Check if evey-rag queries match
# The canonical schema has 15 columns:
# tip_type, condition, recommendation, rationale, tool_name, domain, confidence, upvotes, downvotes, frequency, source_ids, created_at, last_seen, last_used
```

**Fix pattern (May 2026 — full recovery):**
```bash
# 1. Backup current DB
cp ~/.hermes/cerebrum_memory.db ~/.hermes/cerebrum_memory.db.pre_fix

# 2. Recover data from corrupt backup using SQLite .recover
sqlite3 ~/.hermes/cerebrum_memory.db.corrupt_backup ".recover" > /tmp/cerebrum_recover.sql

# 3. Export other tables from current DB
sqlite3 ~/.hermes/cerebrum_memory.db ".dump" > /tmp/cerebrum_current.sql

# 4. Create new DB with correct schema
sqlite3 ~/.hermes/cerebrum_memory.db.new < /tmp/cerebrum_correct_schema.sql

# 5. Import recovered data
sqlite3 ~/.hermes/cerebrum_memory.db.new < /tmp/cerebrum_recover.sql

# 6. Verify
sqlite3 ~/.hermes/cerebrum_memory.db.new "PRAGMA integrity_check"
sqlite3 ~/.hermes/cerebrum_memory.db.new "SELECT COUNT(*) FROM distilled_tips"

# 7. Replace
cp ~/.hermes/cerebrum_memory.db.new ~/.hermes/cerebrum_memory.db
```

**Prevention:**
- Never `DROP TABLE` without migration plan
- Always `grep` all consumers before schema changes
- Keep `.recover` output as backup before any schema change
- The evey-rag plugin uses these exact columns: `tip_type`, `condition`, `recommendation`, `rationale`, `tool_name`, `domain`, `confidence`, `upvotes`, `downvotes`, `frequency`, `source_ids`, `created_at`, `last_seen`, `last_used`

## Known Failure Modes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| 97.6% tips never accessed | Injection budget too tight (1500 chars / 5 tips / 56 modules competing) | Lower confidence threshold, expand budget, or reduce module count |
| simulate() never fires | should_simulate gate too strict | Lower uncertainty threshold or use fixed 10% random sampling |
| 0 metacog rounds | No session context in daemon | Move metacog to plugin hook or feed session snapshots |
| episodic always empty | Salience filter rejects all | Lower salience threshold or bypass for high-elo experiences |
| skill_rewards missing | Table referenced but never created | CREATE TABLE skill_rewards (tip_id, outcome, reward) |
| 138 injection calls dropped/turn | Governor silently truncates | Log drops, add negative feedback signal |

## Zombie Module Audit

```python
# Which R-modules produce 0 attributable tips?
for module in r_modules:
    tips = query("SELECT COUNT(*) FROM distilled_tips WHERE source LIKE ?", f"%{module}%")
    if tips == 0:
        flag_for_removal(module)
```

**Target:** <20% zombie modules. Each dead module adds import time, injection computation, and code complexity.

## Redundancy Check

| Component | SPOF? | Fallback | Action if Down |
|-----------|-------|----------|----------------|
| Postgres | YES | Agent runs blind | Restart Postgres, daemon reconnects |
| Daemon | NO | Tips ossify but agent works | Restart daemon |
| Plugin | YES | Agent becomes static | Plugin reload |
| Embedding model | NO | Falls back to text search | Disable until reload |

## Fix Priority

1. **Injection bottleneck** — highest impact, affects all tips
2. **World model gate** — enables simulation-based learning
3. **Metacognition** — enables self-directed improvement
4. **Episodic memory** — enables long-term experience reuse
5. **Credit assignment** — enables outcome correlation
6. **Zombie cleanup** — reduces code complexity

## Verification

After fixes, re-run the 6 diagnostic checks. Target state:
- Injection hit rate: >20%
- Elo: 70%+ in 1600+ range
- Simulation: 5-15% rate
- Metacog: >1 round/week
- Episodic: >5% meaningful retrieved
- Zombies: <20% of modules
