---
name: agent-self-audit
version: 1.0
description: |
  Comprehensive self-audit methodology for AI agent learning apparatus health checks.
  Covers Cortex/Cerebrum database inspection, daemon health verification, module wiring
  effectiveness analysis, tip quality assessment, and skill ecosystem audits.
trigger: |
  When the user asks for a self-audit, health check, or review of the learning system.
  When the agent needs to diagnose why tips aren't improving, modules aren't firing,
  or the distillation pipeline seems stalled.
---

# Agent Self-Audit Protocol

Run this audit monthly or when the user asks for a learning apparatus health check. It exposes daemon status, module wiring gaps, domain balance, and tip survival rates.

## Quick Health Check (30 seconds)

```bash
# 1. Is the daemon running?
pgrep -f cortex_daemon || echo "DAEMON OFFLINE"

# 2. When was the last flywheel cycle?
cd ~/subconscious && python3 -c "
import psycopg2
conn = psycopg2.connect('postgresql://hindsight:hindsight@localhost:5432/cortex')
cur = conn.cursor()
cur.execute(\"SELECT MAX(started_at) FROM cortex_flywheel\")
print('Last cycle:', cur.fetchone()[0])
conn.close()
"

# 3. How many modules are orphaned?
cd ~/subconscious && python3 -c "
import os, re
with open(os.path.expanduser('~/.hermes/plugins/distillation/__init__.py')) as f:
    imports = set(re.findall(r'from\s+(\w+)\s+import', f.read()))
files = [f[:-3] for f in os.listdir('.') if f.endswith('.py') and not f.startswith('_')]
wired = [f for f in files if f in imports]
print(f'Wired: {len(wired)}/{len(files)} ({len(wired)/len(files)*100:.1f}%)')
"
```

## Full Audit Script

```python
#!/usr/bin/env python3
"""Hermes Learning Apparatus Self-Audit — run from ~/subconscious/"""
import sys, os, subprocess
sys.path.insert(0, '.')
from cortex_access import CortexDB
import psycopg2

db = CortexDB()
conn = psycopg2.connect(db.dsn)
cur = conn.cursor()

print("=== CORTEX DATABASE ===")
stats = db.get_stats()
for k, v in stats.items():
    print(f"  {k}: {v}")

print("\n=== TIP QUALITY TIERS ===")
report = db.get_tip_quality_report()
for k, v in report.items():
    print(f"  {k}: {v}")

print("\n=== ELO DISTRIBUTION ===")
cur.execute('''
    SELECT 
        percentile_cont(0.1) WITHIN GROUP (ORDER BY elo) as p10,
        percentile_cont(0.25) WITHIN GROUP (ORDER BY elo) as p25,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY elo) as p50,
        percentile_cont(0.75) WITHIN GROUP (ORDER BY elo) as p75,
        percentile_cont(0.9) WITHIN GROUP (ORDER BY elo) as p90,
        AVG(elo_matches) as avg_matches
    FROM cortex_nodes WHERE node_type='tip' AND is_active=true
''')
p10, p25, p50, p75, p90, avg_m = cur.fetchone()
print(f"  P10: {p10:.0f} | P25: {p25:.0f} | P50: {p50:.0f} | P75: {p75:.0f} | P90: {p90:.0f}")
print(f"  Avg matches: {avg_m:.1f}")

print("\n=== DOMAIN BALANCE ===")
cur.execute('''
    SELECT domain, COUNT(*) as cnt, AVG(elo) as avg_elo, AVG(confidence) as avg_conf
    FROM cortex_nodes WHERE node_type='tip' AND is_active=true
    GROUP BY domain ORDER BY cnt DESC
''')
for d, c, e, conf in cur.fetchall():
    quality = 'EXCELLENT' if e > 1800 else 'GOOD' if e > 1500 else 'AVERAGE' if e > 1200 else 'WEAK'
    print(f"  {d}: {c} tips | elo={e:.0f} | conf={conf:.2f} | {quality}")

print("\n=== DAEMON HEALTH ===")
result = subprocess.run(['pgrep', '-f', 'cortex_daemon'], capture_output=True, text=True)
if result.stdout.strip():
    print("  RUNNING")
else:
    print("  STOPPED — restart with: python3 ~/subconscious/cortex_daemon.py &")

cur.execute("SELECT COUNT(*), MAX(started_at) FROM cortex_flywheel")
cycles, last = cur.fetchone()
print(f"  Flywheel cycles: {cycles}")
print(f"  Last cycle: {last}")

print("\n=== MODULE WIRING ===")
plugin_path = os.path.expanduser('~/.hermes/plugins/distillation/__init__.py')
with open(plugin_path) as f:
    content = f.read()
lines = content.split('\n')
import re
imports = re.findall(r'from\s+(\w+)\s+import', content)
unique_imports = set(imports)
sub_files = [f[:-3] for f in os.listdir('.') if f.endswith('.py') and not f.startswith('_')]
wired = [f for f in sub_files if f in unique_imports]
orphaned = [f for f in sub_files if f not in unique_imports and len(f) > 3]
print(f"  Total .py files: {len(sub_files)}")
print(f"  Wired: {len(wired)} ({len(wired)/len(sub_files)*100:.1f}%)")
print(f"  Orphaned: {len(orphaned)} ({len(orphaned)/len(sub_files)*100:.1f}%)")

conn.close()
```

## Critical Health Thresholds

| Check | Healthy Threshold | Critical If |
|-------|-------------------|-------------|
| Daemon running | PID exists | No PID for > 1 hour |
| Recent flywheel | < 1 hour ago | Last cycle > 24 hours ago |
| Active tips | > 1000 | < 500 |
| Orphan ratio | > 50% wired | < 30% wired |
| Domain balance | Max domain < 60% | One domain > 80% |
| Elo spread | > 400 points | < 200 points |
| Avg matches per tip | > 5 | < 2 |

## Audit Red Flags

1. **Daemon offline > 24h** — continuous learning stopped. Restart immediately.
2. **Orphan ratio > 50%** — modules built but never wired. Bulk wiring needed.
3. **One domain > 80% of tips** — "general" dumping ground. Reclassify tips.
4. **Avg matches < 5** — tips not being evaluated. Flywheel may be stuck.
5. **No tips created in 7 days** — research/distillation pipeline stalled.

## Post-Audit Action Matrix

| Finding | Priority | Action |
|---------|----------|--------|
| Daemon offline | CRITICAL | `python3 ~/subconscious/cortex_daemon.py &` |
| Orphaned modules | CRITICAL | Bulk wire top 50 modules via V3 script |
| Domain imbalance | HIGH | Reclassify 500+ "general" tips |
| Low Elo spread | HIGH | Increase K-factor or run more tournaments |
| Hermes behind upstream | HIGH | `git fetch && git merge origin/main` |
| No recent benchmarks | MEDIUM | Run testing_gym full suite |
| Stale skills | MEDIUM | Run hermes-dojo analysis |

## Cognitive Apparatus Enhancement Cycle (May 9, 2026)

When the user says "execute to completion, test it, audit, keep running enhancement cycles until you can't enhance anymore":

**This is a systematic cleanup + enhancement protocol, not a single task.**

### Phase 1: Audit (5 min)
1. Count subconscious modules → identify orphans (0 imports)
2. Count registered tools → identify invisible tools (no @register_tool)
3. Count databases → identify empty ghosts (0 bytes, 0 rows)
4. Count plugins → identify disabled high-value plugins
5. Run dashboard → baseline metrics

### Phase 2: Cleanup (30 min)
1. **Archive orphans**: Move 400+ dead modules to `~/subconscious/archive/`
2. **Delete empty DBs**: Remove 0-byte schema ghosts
3. **Register tools**: Add `@register_tool` to top 10 most valuable orphaned tools
4. **Enable plugins**: `hermes plugins enable <name>` for dormant high-value plugins

### Phase 3: Enhance (1-2 hours)
1. **Tip survival tracking**: Create `tip_survival` table, wire to post_tool_call hook
2. **Adversarial validation**: Add `_adversarial_validate_tip()` using LLM judge
3. **Project clustering**: Auto-detect projects from tip domains
4. **Predictive tool selection**: Build `tool_performance_summary` from call_log
5. **Prompt optimization**: Track prompt fragment Elo ratings
6. **Training data export**: Convert tips + tool patterns to structured JSONL

### Phase 4: Test (15 min)
1. Run dashboard → verify all new systems report data
2. Check tool registration → `hermes tools list` shows new tools
3. Verify plugin hooks → check logs for hook firing
4. Test adversarial validation → run on sample tip

### Phase 5: Repeat
1. Re-run audit → check for new gaps
2. If gaps found → return to Phase 2
3. If no gaps → report "enhancement saturated"

### Key Metrics to Track

| Metric | Before | After Cycle 1 | Target |
|--------|--------|---------------|--------|
| Active modules | 530 | 78 | <100 |
| Registered tools | 1 | 10 | All valuable tools |
| Empty DBs | 12 | 0 | 0 |
| Plugins enabled | 32 | 35 | All high-value |
| Tip survival tracked | 0 | 1902 | 100% |
| Projects detected | 0 | 10 | Auto-detect |
| Tool success rankings | None | 38 tools | All tools |

### User Style for This Protocol

- "yea execute to completion" → Start immediately, no preamble
- "test it" → Run verification after each phase
- "audit and keep running" → Loop until no more improvements possible
- "until you can't enhance anymore" → Stop when audit shows zero gaps

**DO NOT:**
- Explain what you're about to do before doing it
- Ask for confirmation on each step
- Show dry runs or previews
- Stop after one cycle unless explicitly told

**DO:**
- Execute immediately
- Report concise metrics after each phase
- Loop automatically
- Report final state when saturated

## CortexDB Query Pitfalls

- **CortexDB.conn attribute doesn't exist** — use `db.get_stats()` and `db.search_text()`, not raw `db.conn.execute()`
- **Flywheel table uses `started_at` not `created_at`** — check `information_schema.columns` before querying
- **RealDictCursor returns dict-like objects** — access via `r['column_name']` not `r[0]`
- **Plugin import grep catches non-module imports** — filter to only `~/subconscious/*.py` filenames
- **Daemon may have no log files** — check process existence with `pgrep`, not log presence

## Cortex Schema Mismatch Pitfall (May 4, 2026)

**The daemon may connect to a DIFFERENT database than you expect.**

Symptom: Flywheel crashes with `column "content_md5" does not exist` even after you "fixed" it.

Root cause: Multiple databases exist (`cortex`, `hindsight`, `cerebrum_memory.db`) and the daemon's `cortex_cursor()` connects to whichever one is configured in its module — not necessarily the one you were inspecting.

**Diagnostic:**
```python
with cortex_flywheel.cortex_cursor() as cur:
    cur.execute("SELECT current_database()")
    print("Database:", dict(cur.fetchone()))
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='cortex_nodes'")
    cols = [dict(r)['column_name'] for r in cur.fetchall()]
    print("Columns:", cols)
    print("content_md5 exists:", 'content_md5' in cols)
```

**Fix pattern:**
1. Check `current_database()` to confirm WHICH DB the daemon uses
2. Add `content_md5` to THAT database's `cortex_nodes` table
3. Populate MD5 for all existing tips: `hashlib.md5(f"{node_type}|{text}".encode()).hexdigest()`
4. Clear Python bytecode cache (`find . -name "*.pyc" -delete`) to prevent stale compiled code
5. Restart daemon

**Key lesson:** Always verify the database connection string the daemon actually uses, not the one you assume. Check `cortex_access.py` or `cortex_flywheel.cortex_cursor()` source for the real DSN.

## New Module Schema Mismatch Pitfall (May 6, 2026)

**New standalone modules assume a schema, but the existing DB has different columns.**

Symptom: Module imports cleanly, but functional tests fail with `sqlite3.OperationalError: no such column: input_tokens`. The module was written with `input_tokens` / `output_tokens` / `timestamp` columns, but `cerebrum_memory.db` (the existing unified memory store) uses `tokens_in` / `tokens_out` / `created_at`.

Root cause: When building new learning apparatus, you create a fresh schema in the module's `_ensure_table()`. But if the module connects to an EXISTING database (e.g., `cerebrum_memory.db` which already has 80+ tables from prior systems), the `_ensure_table()` may create the table OR may find it already exists with different columns. The code then queries the columns it expects, not the columns that exist.

**Diagnostic — always run this BEFORE declaring a module ready:**
```python
import sqlite3
conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
c = conn.cursor()
c.execute("PRAGMA table_info(token_usage)")  # or whatever table the module uses
print("Actual columns:", [col[1] for col in c.fetchall()])
conn.close()
```

**Fix pattern:**
1. **Inspect actual schema** — `PRAGMA table_info(table_name)` on the EXISTING DB
2. **Align code to reality** — Change queries to use actual column names (`tokens_in` not `input_tokens`)
3. **Make `_ensure_table()` schema-aware** — Check existing columns before creating, add missing ones with `ALTER TABLE`, don't assume a blank slate:
   ```python
   def _ensure_table(self):
       c = self.conn.cursor()
       c.execute("PRAGMA table_info(token_usage)")
       existing = [col[1] for col in c.fetchall()]
       if not existing:
           # Create fresh
           c.execute("CREATE TABLE token_usage (...)")
       else:
           # Add missing columns to existing table
           if 'session_id' not in existing:
               c.execute("ALTER TABLE token_usage ADD COLUMN session_id TEXT")
           if 'tokens_in' not in existing:
               c.execute("ALTER TABLE token_usage ADD COLUMN tokens_in INTEGER DEFAULT 0")
       self.conn.commit()
   ```
4. **Use `sqlite3.Row` factory** for dict-like access that adapts to whatever columns exist
5. **Test with the REAL DB**, not an in-memory mock

**Key lesson:** New modules must be schema-adaptive when connecting to existing databases. Never assume column names match your `_ensure_table()` definition. Always `PRAGMA table_info()` first.

## Table Rebuild Without Code Update Pitfall (May 16, 2026)

**A table is rebuilt with a new schema, but ALL dependent code still references old columns.**

Symptom: `sqlite3.OperationalError: no such column: confidence` when calling `knowledge_stats()`. The `distilled_tips` table was rebuilt with a simplified schema (`content`, `content_hash`, `source_key`, `source_tier`, `priority`, `tags`, `distilled_at`, `evaluated`, `judge_score`, `judge_feedback`, `sent_to_cortex`, `cortex_node_id`) but the evey-rag plugin, distillation plugin, and tip injection scripts all query old columns (`tip_type`, `condition`, `recommendation`, `rationale`, `tool_name`, `domain`, `confidence`, `upvotes`, `downvotes`, `frequency`, `created_at`, `last_seen`, `source_ids`).

Root cause: During an audit or cleanup, someone ran `DROP TABLE distilled_tips; CREATE TABLE distilled_tips (...)` with a new schema. The new schema was simpler but incompatible. No code was updated to match. Result: 1,279 tips lost (old backup has them, current DB has 3), all knowledge queries fail.

**Diagnostic:**
```python
import sqlite3
conn = sqlite3.connect(os.path.expanduser("~/.hermes/cerebrum_memory.db"))
c = conn.cursor()

# Check actual schema
c.execute("PRAGMA table_info(distilled_tips)")
actual_cols = [col[1] for col in c.fetchall()]
print("Actual columns:", actual_cols)

# Check what code expects (grep for column references)
# In evey-rag plugin:
#   "SELECT tip_type, condition, recommendation, confidence, source_ids FROM distilled_tips"
# In distillation plugin:
#   "UPDATE distilled_tips SET confidence = 0.1, status = 'under_review' WHERE id=?"
# In tip injection scripts:
#   "INSERT INTO distilled_tips (tip_type, condition, recommendation, ...) VALUES (...)"

# Check for backups with old schema
import glob, os
backups = sorted(glob.glob(os.path.expanduser("~/.hermes/cerebrum_memory.db*backup*")))
for b in backups:
    c2 = sqlite3.connect(b)
    c2.execute("PRAGMA table_info(distilled_tips)")
    old_cols = [col[1] for col in c2.fetchall()]
    c2.execute("SELECT COUNT(*) FROM distilled_tips")
    count = c2.fetchone()[0]
    print(f"{b}: {len(old_cols)} cols, {count} rows, columns: {old_cols[:5]}...")
    c2.close()

conn.close()
```

**Fix pattern:**
1. **STOP** — do not rebuild tables without a migration plan
2. **Inspect ALL consumers** — grep every `.py` file that references the table:
   ```bash
   find ~/.hermes -name "*.py" | xargs grep -l "distilled_tips" 2>/dev/null
   ```
3. **Compare schemas** — `PRAGMA table_info()` on current vs backup vs what code expects
4. **Choose direction:**
   - **Restore old schema** (recommended if old schema is richer and all code expects it)
   - **Migrate all code** (only if new schema is strictly better AND you update every consumer)
5. **If restoring:**
   ```bash
   # Backup current (even if broken)
   cp ~/.hermes/cerebrum_memory.db ~/.hermes/cerebrum_memory.db.broken_schema
   # Restore from old backup
   cp ~/.hermes/cerebrum_memory.db.corrupt_backup ~/.hermes/cerebrum_memory.db
   # Migrate any new tips from broken schema to restored schema
   ```
6. **If migrating code:** Update EVERY query in EVERY file that references the table. One missed file = broken system.

**Prevention:**
- Never `DROP TABLE` on production data without a backup
- Always run `PRAGMA table_info()` AND grep all code before schema changes
- Use `ALTER TABLE ADD COLUMN` for additive changes, not `DROP+CREATE`
- Maintain a schema version in a `_meta` table:
  ```sql
  CREATE TABLE IF NOT EXISTS _schema_version (table_name TEXT PRIMARY KEY, version INTEGER, migrated_at REAL);
  ```

**Key lesson:** Schema changes are code changes. Changing a table without updating all queries is like changing a function signature without updating callers. The database IS an API.

## Table Rebuild Without Code Update Pitfall (May 16, 2026)

**A table is rebuilt with a new schema, but ALL dependent code still references old columns.**

Symptom: `sqlite3.OperationalError: no such column: confidence` when calling `knowledge_stats()`. The `distilled_tips` table was rebuilt with a simplified schema (`content`, `content_hash`, `source_key`, `source_tier`, `priority`, `tags`, `distilled_at`, `evaluated`, `judge_score`, `judge_feedback`, `sent_to_cortex`, `cortex_node_id`) but the evey-rag plugin, distillation plugin, and tip injection scripts all query old columns (`tip_type`, `condition`, `recommendation`, `rationale`, `tool_name`, `domain`, `confidence`, `upvotes`, `downvotes`, `frequency`, `created_at`, `last_seen`, `source_ids`).

Root cause: During an audit or cleanup, someone ran `DROP TABLE distilled_tips; CREATE TABLE distilled_tips (...)` with a new schema. The new schema was simpler but incompatible. No code was updated to match. Result: 1,279 tips lost (old backup has them, current DB has 3), all knowledge queries fail.

**Diagnostic:**
```python
import sqlite3
conn = sqlite3.connect(os.path.expanduser("~/.hermes/cerebrum_memory.db"))
c = conn.cursor()

# Check actual schema
c.execute("PRAGMA table_info(distilled_tips)")
actual_cols = [col[1] for col in c.fetchall()]
print("Actual columns:", actual_cols)

# Check what code expects (grep for column references)
# In evey-rag plugin:
#   "SELECT tip_type, condition, recommendation, confidence, source_ids FROM distilled_tips"
# In distillation plugin:
#   "UPDATE distilled_tips SET confidence = 0.1, status = 'under_review' WHERE id=?"
# In tip injection scripts:
#   "INSERT INTO distilled_tips (tip_type, condition, recommendation, ...) VALUES (...)"

# Check for backups with old schema
import glob, os
backups = sorted(glob.glob(os.path.expanduser("~/.hermes/cerebrum_memory.db*backup*")))
for b in backups:
    c2 = sqlite3.connect(b)
    c2.execute("PRAGMA table_info(distilled_tips)")
    old_cols = [col[1] for col in c2.fetchall()]
    c2.execute("SELECT COUNT(*) FROM distilled_tips")
    count = c2.fetchone()[0]
    print(f"{b}: {len(old_cols)} cols, {count} rows, columns: {old_cols[:5]}...")
    c2.close()

conn.close()
```

**Fix pattern:**
1. **STOP** — do not rebuild tables without a migration plan
2. **Inspect ALL consumers** — grep every `.py` file that references the table:
   ```bash
   find ~/.hermes -name "*.py" | xargs grep -l "distilled_tips" 2>/dev/null
   ```
3. **Compare schemas** — `PRAGMA table_info()` on current vs backup vs what code expects
4. **Choose direction:**
   - **Restore old schema** (recommended if old schema is richer and all code expects it)
   - **Migrate all code** (only if new schema is strictly better AND you update every consumer)
5. **If restoring:**
   ```bash
   # Backup current (even if broken)
   cp ~/.hermes/cerebrum_memory.db ~/.hermes/cerebrum_memory.db.broken_schema
   # Restore from old backup
   cp ~/.hermes/cerebrum_memory.db.corrupt_backup ~/.hermes/cerebrum_memory.db
   # Migrate any new tips from broken schema to restored schema
   ```
6. **If migrating code:** Update EVERY query in EVERY file that references the table. One missed file = broken system.

**Prevention:**
- Never `DROP TABLE` on production data without a backup
- Always run `PRAGMA table_info()` AND grep all code before schema changes
- Use `ALTER TABLE ADD COLUMN` for additive changes, not `DROP+CREATE`
- Maintain a schema version in a `_meta` table:
  ```sql
  CREATE TABLE IF NOT EXISTS _schema_version (table_name TEXT PRIMARY KEY, version INTEGER, migrated_at REAL);
  ```

**Key lesson:** Schema changes are code changes. Changing a table without updating all queries is like changing a function signature without updating callers. The database IS an API.

## Hermes Repo Audit

```bash
cd ~/hermes-agent  # or wherever hermes-agent is cloned
git log --oneline -5
git status -sb  # shows ahead/behind
git log --oneline --since="2026-04-01" --until="2026-05-03" | wc -l
```

## Session Reference

This protocol was developed during the May 3, 2026 self-audit session. Live metrics captured:
- Cortex: 66,310 nodes, 2,405 active tips, 203,045 evals
- Daemon: OFFLINE (last cycle Apr 22, 256 hours ago)
- Modules: 529 total, 124 wired (23.4%), 405 orphaned (76.6%)
- Domain skew: 90.7% "general" tips, specialized domains starved
- Hermes: 247 commits behind upstream

See `references/may3-2026-audit-results.md` for full session transcript.
See `references/may6-2026-smoke-test-script.py` for a reusable smoke test script that verifies all brain modules import, function, and integrate correctly — including schema alignment checks against `cerebrum_memory.db`.
