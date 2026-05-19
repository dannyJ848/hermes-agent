---
name: cortex-daemon-diagnostic
version: 1.0
created: 2026-04-14
description: Diagnose and fix stuck cortex_daemon processes, stalled flywheel cycles, and perform clean restarts.
trigger: When cortex_daemon appears stuck, flywheel cycles show 'running' but never complete, or daemon needs restart.
---

# Cortex Daemon Diagnostic & Restart

## Quick Health Check (run these first)

```bash
# 1. Is daemon alive?
pgrep -fl cortex_daemon

# 2. Recent activity in structured log
tail -5 ~/subconscious/cortex_daemon.jsonl | python3 -c "import sys,json; [print(json.loads(l)['region'], json.loads(l)['detail'][:60]) for l in sys.stdin]"

# 3. Last DB flywheel entries
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
import psycopg2
conn = psycopg2.connect('postgresql://hindsight:hindsight@localhost:5432/cortex')
cur = conn.cursor()
cur.execute(\"SELECT cycle_type, status, started_at FROM cortex_flywheel ORDER BY started_at DESC LIMIT 8\")
for r in cur.fetchall():
    print(f'  {r[0]:15s} {r[1]:12s} {r[2]}')
conn.close()
"
```

## DeepSeek API Key Discovery & Verification

When `DEEPSEEK_API_KEY` is missing from environment but needed for flywheel:

**Location**: Check `~/.hermes/.env` first:
```bash
grep DEEPSEEK_API_KEY ~/.hermes/.env
# Output: DEEPSEEK_API_KEY=sk-7ab7950...
```

**Export for current session**:
```bash
export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)
```

**Add to shell profile for persistence**:
```bash
echo "export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)" >> ~/.zshrc
```

**Verify API works**:
```bash
curl -s -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  https://api.deepseek.com/models | jq '.data[].id'
# Should show: deepseek-v4-pro, deepseek-v4-flash, etc.
```

**Verify judge function**:
```python
cd ~/hermes-agent && source venv/bin/activate
python3 -c "
from llm_judge import compare_tips
result = compare_tips('tip A', 'tip B', 'test')
print(result)
"
# Should return JSON with winner, confidence, reasoning in ~10s
```

## Diagnosing Stuck Cycles

**Symptom**: Flywheel entries show `status=running` for hours, never `completed`.

**Root causes found so far**:
1. **Missing `complete_flywheel_cycle()` call** — `llm_judge.py` `run_llm_eval_sweep()` never called it. Compare with `cortex_flywheel.py` `run_eval_sweep()` which does call it. Check ALL cycle-type functions for this.
2. **LLM API timeout / 401 auth failure** — `call_llm_judge` uses `urllib.request.urlopen(req, timeout=15)`. If DeepSeek API key is missing or invalid, calls hang indefinitely (no timeout on auth retry loop). **Check `env | grep DEEPSEEK_API_KEY` before starting flywheel.** See `references/deepseek-api-key-missing-2026-05-03.md`.
3. **Daemon stopped but process alive** — daemon threads are `daemon=True`, so when main loop exits (`_running=False`), threads die but the process can linger on DB connections.

**Fix for stuck records**:
```python
import psycopg2
conn = psycopg2.connect('postgresql://hindsight:hindsight@localhost:5432/cortex')
cur = conn.cursor()
cur.execute("UPDATE cortex_flywheel SET status = 'completed', completed_at = NOW() WHERE status = 'running'")
print(f"Fixed {cur.rowcount} stuck records")
conn.commit()
conn.close()
```

## Clean Daemon Restart

**CRITICAL GOTCHA**: Shell commands containing `cortex_daemon` in their text get matched by `pkill -f`, killing the terminal command itself. Must use a script file approach.

### Automated Watchdog (cron-based)

Use the provided watchdog script at `scripts/cortex_watchdog.sh` for 24/7 daemon monitoring:

```bash
# Install: copy to ~/.hermes and add to crontab
cp ~/.hermes/skills/devops/cortex-daemon-diagnostic/scripts/cortex_watchdog.sh ~/.hermes/cortex_watchdog.sh
chmod +x ~/.hermes/cortex_watchdog.sh

# Add to crontab (runs every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * bash /Users/dannygomez/.hermes/cortex_watchdog.sh") | crontab -
```

The watchdog:
- Reads PID from `~/.hermes/cortex_daemon.pid`
- Verifies process is alive with `ps -p`
- Checks if log is stale (>10 min old)
- Restarts daemon silently if dead/stale
- Logs only when action taken (no spam)

### Manual Restart

**Step 1**: Create restart script at `/tmp/restart_daemon.sh`:
```bash
#!/bin/bash
# Kill only python processes, NOT this bash script
while IFS= read -r pid; do
    [ -n "$pid" ] && kill -9 "$pid" 2>/dev/null
done < <(pgrep -f 'venv/bin/python3.*cortex_daemon' 2>/dev/null || true)
while IFS= read -r pid; do
    [ -n "$pid" ] && kill -9 "$pid" 2>/dev/null
done < <(pgrep -f '^python3 .*cortex_daemon' 2>/dev/null || true)
sleep 2
rm -f ~/subconscious/cortex_daemon.pid
> /tmp/cortex_daemon.log

cd ~/hermes-agent && source venv/bin/activate
nohup python3 -u ~/subconscious/cortex_daemon.py >> /tmp/cortex_daemon.log 2>&1 &
NEW_PID=$!
sleep 5
if kill -0 "$NEW_PID" 2>/dev/null; then
    echo "Daemon $NEW_PID ALIVE"
else
    echo "Daemon $NEW_PID DEAD"
fi
```

**Step 2**: Run it: `bash /tmp/restart_daemon.sh`

**Step 3**: Verify:
```bash
pgrep -fl cortex_daemon | wc -l  # Should be exactly 1
tail -3 ~/subconscious/cortex_daemon.jsonl
```

## DB Health Checks

### Column name gotchas
- `pg_stat_user_indexes`: column is **`indexrelname`**, NOT `indexname`
- `cortex_flywheel`: timestamp column is **`started_at`**, NOT `created_at`
- Elo is in **dedicated columns** (`elo`, `elo_matches`, `elo_wins`, `elo_losses`), NOT in `metadata` JSONB

### Key queries
```sql
-- Dead tuples and vacuum status
SELECT relname, n_live_tup, n_dead_tup,
       ROUND(n_dead_tup::numeric / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2) as dead_pct,
       last_autovacuum
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC;

-- Flywheel 24h summary
SELECT cycle_type, COUNT(*) as total,
       SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
       SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed
FROM cortex_flywheel WHERE started_at > NOW() - INTERVAL '24 hours'
GROUP BY cycle_type;

-- Stuck cycles
SELECT cycle_type, COUNT(*) FROM cortex_flywheel 
WHERE status = 'running' GROUP BY cycle_type;
```

## Architecture Reference

**Daemon threads** (4+1):
- `flywheel_loop`: 15s cycles — eval (500 pairs) + repair + consolidate (every 5th) + normalize (every 10th) + research (every 20th). Every 3rd cycle uses LLM judge (300 pairs, 50 LLM calls). Experience Elo every 3rd.
- `training_gym_loop`: 20s cycles — rate 30 tips + quality sweep (15 tips) + experience rating (every 3rd) + metacog self-improvement (every 5th)
- `perf_monitor_loop`: 300s cycles — DB latency checks + node counts + monthly 3-DB sync + circuit_breaker auto-purge (1hr TTL)
- `heartbeat`: 30s cycles — writes PID + timestamp to heartbeat file
- `main()`: supervision loop — auto-restarts daemon on SIGTERM (5s delay)

**AUTO-RESTART MECHANISM** (added Apr 15):
- SIGTERM triggers auto-restart via supervision loop in `main()`. Daemon catches SIGTERM, sets `_restart_requested=True`, exits, then `main()` respawns after 5s delay.
- This prevents daemon death from macOS SIGTERM during logout/restart.
- **STOP FILE PROTOCOL**: `touch ~/subconscious/DAEMON_STOP` BEFORE killing to prevent auto-restart. Without STOP file, `kill` (SIGTERM) triggers respawn → race condition with manual restart = DUPLICATE INSTANCES.
- Clean restart: `touch ~/subconscious/DAEMON_STOP; pkill -f cortex_daemon; sleep 3; rm -f ~/subconscious/DAEMON_STOP; cd ~/hermes-agent && source venv/bin/activate && rm -rf ~/subconscious/__pycache__; nohup python3 ~/subconscious/cortex_daemon.py >> /tmp/cortex_daemon.log 2>&1 &`
- **KILL ONLY**: `pkill -9` bypasses signal handler entirely — use only for truly stuck processes.

**DEAD MECHANISMS** (killed Apr 15 — do NOT re-enable):
- `launchctl` service `com.hermes.cortex-daemon` — was macOS system service. Removed with `launchctl remove`.
- These were the ROOT CAUSE of duplicate daemon instances before the STOP file protocol existed.

**SENTINEL (re-activated)**:
- `cortex_sentinel.py` runs as a standalone cron health checker (not a daemon supervisor).
- It checks 13 health dimensions: PG connectivity, embedding server, disk space, memory, CPU, active nodes, dead tuples, cache hit, embedding coverage, PG locks, PG connections, PG replication, and process liveness.
- Returns JSON with `overall` (ok/warn/crit), individual check statuses, and a formatted report.
- Run with: `python3 ~/subconscious/cortex_sentinel.py --status`
- The sentinel daemon process should be running in background: `nohup python3 -u ~/subconscious/cortex_sentinel.py --verbose >> /tmp/cortex_sentinel.log 2>&1 &`

**Logs**: Structured → `~/subconscious/cortex_daemon.jsonl`. Debug prints → `/tmp/cortex_daemon.log`.

## Full 16-Point Diagnostic

Run this when doing a comprehensive cortex health check:

### Group 1: Database (5 checks)
1. **Connectivity** — `psycopg2.connect(dsn)` — verify Postgres version (18.0+)
2. **Table structure** — `SELECT count(*) FROM information_schema.tables WHERE table_schema='public'` — expect 24 tables
3. **Node counts** — `SELECT node_type, count(*) FROM cortex_nodes WHERE is_active=true GROUP BY node_type` — expect 30K+ active
4. **Elo stats** — `SELECT count(*), avg(elo), min(elo), max(elo), stddev(elo) FROM cortex_nodes WHERE elo IS NOT NULL AND elo > 0` — use dedicated columns, NOT metadata JSONB
5. **Dead tuples + vacuum** — `SELECT relname, n_dead_tup, last_autovacuum FROM pg_stat_user_tables ORDER BY n_dead_tup DESC` — VACUUM ANALYZE if >5% dead

### Group 2: Flywheel (3 checks)
6. **Stuck cycles** — `SELECT count(*) FROM cortex_flywheel WHERE status='running'` — should be 0
7. **K factor** — default `k=40.0` in `update_elo_pair()` (line 35), tie override `k=8` (line 136). NOT a bug if you see both.
8. **Recent activity** — `SELECT cycle_type, status, started_at FROM cortex_flywheel ORDER BY started_at DESC LIMIT 8`

### Group 3: Indexes (1 check)
9. **Index usage** — `SELECT indexrelname, idx_scan FROM pg_stat_user_indexes ORDER BY idx_scan` — column is `indexrelname` NOT `indexname`. Zero unused indexes is normal.

### Group 4: Code (3 checks)
10. **Module imports** — `python3 -c "import cortex_access, cortex_flywheel, cortex_daemon, cortex_elasticsearch, llm_judge, failure_exemplar_bank, trajectory_intel, cortex_quick_stats"` — all should import clean
11. **CortexDB methods** — CortexDB has 22 instance methods. `get_connection()` is MODULE-LEVEL (line 33), NOT an instance method. `cortex_cursor` is also module-level. NOT a bug.
12. **llm_judge fix** — verify `complete_flywheel_cycle()` is called at line ~173 of `run_llm_eval_sweep()`

### Group 5: Daemon (4 checks)
13. **Process count** — `pgrep -fl cortex_daemon | wc -l` — must be exactly 1
14. **Sentinel check** — `pgrep -fl cortex_sentinel` — should be 1+ (re-activated as cron health checker). Run `python3 ~/subconscious/cortex_sentinel.py --status` to see full report.
15. **launchctl check** — `launchctl list | grep cortex` — should be empty (removed)
16. **Thread wiring** — check daemon log for 4 threads: flywheel_loop, training_gym_loop, perf_monitor_loop, heartbeat

### Common False Alarms
- "Missing method CortexDB.get_connection" → It's module-level, not instance
- "K factor wrong, shows 8 not 40" → k=8 is only for tie overrides, default is k=40
- "No CortexDB.cortex_cursor" → Module-level function
- "Sentinel not found" → Intentionally killed. Daemon runs standalone.

### Embedding Server Recovery (port 8083)

**Symptom**: Sentinel reports `embedding_server: CRIT — unreachable`, `process_embedding_server: warn — not responding on port 8083`.

**Root cause**: The embedding server (Nomic Embed) expects an OpenAI-compatible `/v1/embeddings` endpoint on port 8083. If the server process dies, there's no auto-restart mechanism — `local_inference.py` only checks liveness, never starts it.

**Quick fix — Ollama proxy** (if Ollama is running with `nomic-embed-text`):
Ollama already exposes an OpenAI-compatible endpoint at port 11434. Create a lightweight Python proxy script that forwards port 8083 → Ollama 11434. The proxy handles:
- `GET /v1/models` → returns `nomic-embed-text`
- `GET /health` → returns `{"status": "ok"}`
- `POST /v1/embeddings` → converts OpenAI format to Ollama `/api/embeddings`, returns OpenAI-format response

Start: `nohup python3 -u /tmp/embed_proxy.py 8083 >> /tmp/embed_proxy.log 2>&1 &`

**Verify**: Re-run `python3 ~/subconscious/cortex_sentinel.py --status` — embedding_server should be OK.

**Alternative**: Set `EMBED_URL=http://127.0.0.1:11434` env var (used by `value_retriever.py`) and update any code calling port 8083 directly.

### Disk Space Recovery

**Symptom**: Sentinel reports `disk_space: CRIT — Disk free X% < 10%`.

**Quick wins**: Clean up temp browser profiles and test artifacts in `/tmp/`. Investigate `~/Library/Caches`, `~/Library/Application Support`, `~/Library/Developer` for large directories. Consider `brew cleanup` and Docker pruning if applicable.

### Schema Mismatch Bug (found May 3 2026)

**Symptom**: Daemon log shows `Flywheel error: column "pairs_evaluated" of relation "cortex_flywheel" does not exist`

**Root cause**: The `cortex_flywheel` table was created with an older schema that lacks columns expected by `complete_flywheel_cycle()`. The daemon starts cycles but cannot complete them.

**Fix**: Add missing columns to PostgreSQL:
```python
import psycopg2
conn = psycopg2.connect('postgresql://hindsight:hindsight@localhost:5432/cortex')
cur = conn.cursor()

# Check current schema
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'cortex_flywheel' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]

# Add any missing columns
missing = []
for col, dtype in [('pairs_evaluated', 'INTEGER DEFAULT 0'), ('tips_repaired', 'INTEGER DEFAULT 0'), 
                    ('tips_consolidated', 'INTEGER DEFAULT 0'), ('duration_ms', 'INTEGER DEFAULT 0')]:
    if col not in cols:
        cur.execute(f"ALTER TABLE cortex_flywheel ADD COLUMN {col} {dtype}")
        missing.append(col)

conn.commit()
conn.close()
print(f'Added columns: {missing}')
```

**Verification**: After fix, `complete_flywheel_cycle()` should succeed and cycles should show `status='completed'` instead of hanging in `status='running'`.

### INSERT Schema Mismatch (found May 5 2026)

**Symptom**: `cortex_access.py` `insert_node()` fails with `column "tip_type" of relation "cortex_nodes" does not exist` or `column "last_seen" of relation "cortex_nodes" does not exist`.

**Root cause**: Code INSERTs columns that don't exist in the actual Postgres schema. This happens when:
1. Schema evolved (columns renamed/removed) but INSERT wasn't updated
2. SQLite schema (development) differs from Postgres schema (production)
3. `ON CONFLICT` clause references a unique constraint that was never created

**Diagnosis**:
```python
import psycopg2
conn = psycopg2.connect('postgresql://hindsight:hindsight@localhost:5432/cortex')
cur = conn.cursor()

# 1. Check actual columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'cortex_nodes'")
actual_cols = [r[0] for r in cur.fetchall()]
print(f'Actual columns: {actual_cols}')

# 2. Check constraints
cur.execute("""
    SELECT conname, pg_get_constraintdef(oid) 
    FROM pg_constraint 
    WHERE conrelid = 'cortex_nodes'::regclass
""")
constraints = [r[0] for r in cur.fetchall()]
print(f'Constraints: {constraints}')

conn.close()
```

**Fix**: Patch `cortex_access.py` `insert_node()` method:

1. **Merge tip fields into metadata before JSON serialization** (around line 134):
```python
# Merge tip fields into metadata (cortex_nodes schema doesn't have dedicated columns)
meta = metadata or {}
if tip_type: meta["tip_type"] = tip_type
if condition: meta["condition"] = condition
if recommendation: meta["recommendation"] = recommendation
if rationale: meta["rationale"] = rationale
if tool_name: meta["tool_name"] = tool_name
metadata_json = json.dumps(meta)
```

2. **Remove non-existent columns from INSERT** — keep only: `node_type, text, domain, confidence, elo, provenance, source_ids, metadata, content_md5, embedding, created_at, updated_at`

3. **Remove broken `ON CONFLICT` clause** if no unique constraint on `content_md5`:
```python
# WRONG — will error if constraint doesn't exist
ON CONFLICT (content_md5) WHERE content_md5 IS NOT NULL AND is_active = TRUE DO NOTHING

# CORRECT — simple INSERT without conflict handling
INSERT INTO cortex_nodes (...) VALUES (...) RETURNING id
```

4. **Use `updated_at` NOT `last_seen`** — `last_seen` column does not exist in current schema. Both `created_at` and `updated_at` exist and are auto-managed.

**Verification**:
```python
from cortex_access import CortexDB
db = CortexDB()
nid = db.insert_node(
    text='WHEN testing cortex fix, THEN verify insert works',
    node_type='tip', domain='mlops', confidence=0.85,
    tip_type='strategy', condition='WHEN testing',
    recommendation='THEN verify', rationale='Test insert',
    metadata={'source': 'cortex_fix_may5'}
)
assert nid is not None, "INSERT FAILED"
print(f"OK: node_id={nid}")
```

**Result after fix**: Daemon runs flywheel cycles, injects tips, 7060+ active nodes, Elo avg ~1336.

### Common Real Bugs (found Apr 15 audit)
- **Method exists but never called**: `world_model_r27.py` has `simulate()` method, but the plugin only called `record_outcome()` (post) and `build_injection()` (pre). The simulation gate showed 0% rate. Fix: search for all methods defined in a module and verify each is called from the plugin's hook paths.
- **Singleton not shared across processes**: `intrinsic_metacognition.py` creates `_INSTANCE` singleton, but daemon and agent run in separate processes. Round history shows 0 in agent even when daemon has 10+ rounds. Use DB persistence for cross-process state.
- **Circuit breaker node bloat**: Plugin creates circuit_breaker nodes for operational tracking. 12K+ accumulated with 0 knowledge value. Add TTL auto-purge (1hr) in perf_monitor_loop.
- **Uppercase domain leak**: `DOMAIN_MAP` in tip_normalizer catches most variants but new code can still insert uppercase domains. Add `LOWER()` in INSERT or enforcement in `_normalize_domain()`.

## Flywheel API Reconciliation

When `cortex_flywheel.py` crashes with `AttributeError` against `CortexDB`, or reports `total_nodes: 0` despite data existing, use this section.

### Empty SQLite Red Herring

The flywheel may read from `~/hermes-agent/cortex_unified.db` (zero-byte SQLite) instead of PostgreSQL. Always cross-check with direct Postgres query:
```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
import sys; sys.path.insert(0, str(__import__('pathlib').Path.home() / 'subconscious'))
from cortex_access import CortexDB; import json
print(json.dumps(CortexDB().get_stats(), indent=2, default=str))
"
```

### Known Schema Drift (flywheel code vs actual DB)

| Flywheel References | Actual Column/Table | Fix |
|---|---|---|
| `type` | `node_type` | Use `node_type` |
| `phase` | `cycle_type` | Use `cycle_type` |
| `node_id_a` / `node_id_b` | `node_a_id` / `node_b_id` | No `_id` suffix on node part |
| `flywheel_cycles` table | `cortex_flywheel` | Use actual table name |
| `tip_evaluations` table | `cortex_eval_history` | Use actual table name |
| `round_id` | `cycle_id` (uuid) | Use `cycle_id` |

### bool/isinstance Gotcha

Python `bool` subclasses `int`. Always check `bool` BEFORE `(int, float)`:
```python
def update_elo(self, node_a_id, node_b_or_elo, k_or_is_winner=32):
    if isinstance(k_or_is_winner, bool):  # CHECK BOOL FIRST
        self.set_elo(node_a_id, node_b_or_elo, k_or_is_winner)
        return
    # ... classic logic ...
```

### psycopg2 % Escaping

Any literal `%` in SQL text must be `%%`:
```sql
-- WRONG → IndexError: tuple index out of range
AND text NOT LIKE '{"action_hash":%}'
-- CORRECT
AND text NOT LIKE '{"action_hash":%%}'
```

### Manual Phase Execution Fallback

If flywheel hangs silently, execute phases manually:

**Phase 1 — EVAL:**
```python
import sys, random; sys.path.insert(0, '/Users/USER/subconscious')
from cortex_access import CortexDB
db = CortexDB(); tips = db.get_tips_for_eval(limit=100)
random.shuffle(tips)
# Heuristic scoring + Elo update + record_eval with CORRECT column names
```

**Phase 2 — REPAIR:** Deactivate tips with `elo < 950 AND elo_matches >= 10`.

**Phase 3 — CONSOLIDATE:** Merge duplicate MD5s, create `similar_elo` edges.

**Phase 4 — STATS:** `SELECT COUNT(*) ... FROM cortex_nodes` — never trust flywheel JSON alone.

## Sentinel Status Check

Run `python3 ~/subconscious/cortex_sentinel.py --status` for a 13-dimension health report:
- PG connectivity, embedding server (port 8083), disk space, memory, CPU
- Active nodes, dead tuples, cache hit ratio, embedding coverage
- PG locks, connections, replication, process liveness

Returns JSON with `overall: ok/warn/crit` and per-check status.

### Embedding Server Recovery (port 8083)

If sentinel reports `embedding_server: CRIT`, the Nomic Embed server is down. Quick fix: proxy Ollama's OpenAI-compatible endpoint (port 11434) to port 8083 with a lightweight Python proxy.

### Memory-cortex wiring gap

There is NO automatic offloading from the 2,500-char `memory` tool to the cortex database. When memory fills up, new entries are rejected. If you need a tiered memory system (hot→warm→cold), build it explicitly — do not assume it exists. The `memory` tool, `cortex_memory.db`, and `cortex` PostgreSQL are three separate systems with no native cascade.
