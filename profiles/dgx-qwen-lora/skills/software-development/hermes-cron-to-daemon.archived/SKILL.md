---
name: hermes-cron-to-daemon
description: Convert Hermes cron jobs to persistent background daemons with 24/7 autonomous operation. Production-proven with cortex_daemon.py (4 threads, JSONL logging, heartbeat, graceful shutdown). Includes Postgres performance patterns and SQLite→Postgres migration gotchas.
version: 2.0
created: 2026-04-05
updated: 2026-04-13
tags: [hermes, cron, daemon, postgres, cortex, distillation, performance]
---

# Converting Cron Jobs to Background Daemons

## When to Use
- Cron jobs are blocking each other (max_workers bottleneck)
- You need sub-2-minute intervals for continuous operation
- You want 24/7 autonomous loops (training, eval, consolidation)
- SQLite lock contention is blocking daemon writes

## Production Architecture (cortex_daemon.py)

```
DAEMON: ~/subconscious/cortex_daemon.py (PID-managed, 24/7)
├── Thread: flywheel (30s cycle) — Elo eval + repair + consolidate
├── Thread: training_gym (60s cycle) — rate unrated tips + quality sweep
├── Thread: perf_monitor (5min cycle) — continuous benchmarks
├── Thread: heartbeat (30s) — writes PID + cycle count
├── Log: ~/subconscious/cortex_daemon.jsonl (append-only)
├── PID: ~/subconscious/cortex_daemon.pid
└── Heartbeat: ~/subconscious/cortex_daemon.heartbeat

PERFORMANCE (proven):
  Fetch by UUID:    0.09ms
  FTS search:       0.9ms   (GIN index)
  ILIKE search:     1.0ms   (pg_trgm GIN)
  Edge traversal:   0.1ms   (indexed joins)
  Eval 100 pairs:   1.1s    (11ms/pair)
  Consolidation:    56ms    (was 65,000ms before optimization!)
  Full cycle:       1.2s
  Max throughput:   3,393 pairs/hr
```

## Daemon Template (copy this pattern)

```python
#!/usr/bin/env python3
"""
daemon_name.py — 24/7 persistent daemon.
Runs continuously with graceful shutdown.
"""
import sys, os, time, json, signal, threading, traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.home() / "subconscious"))

LOG_FILE = Path.home() / "subconscious" / "daemon_name.jsonl"
PID_FILE = Path.home() / "subconscious" / "daemon_name.pid"
HEARTBEAT_FILE = Path.home() / "subconscious" / "daemon_name.heartbeat"

_running = True
_cycle_count = 0

def handle_signal(signum, frame):
    global _running
    _running = False
    log("daemon", "shutdown", 0, f"Signal {signum}")

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

def log(region, status, duration_ms, detail=""):
    """Append-only JSONL — lock-free, no DB contention."""
    entry = {
        "ts": datetime.now().isoformat(),
        "region": region,
        "status": status,
        "duration_ms": round(duration_ms),
        "detail": detail[:200]
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def heartbeat():
    while _running:
        HEARTBEAT_FILE.write_text(json.dumps({
            "pid": os.getpid(),
            "ts": datetime.now().isoformat(),
            "cycles": _cycle_count
        }))
        time.sleep(30)

def worker_loop_1():
    """Your main work loop."""
    global _cycle_count
    while _running:
        _cycle_count += 1
        try:
            t0 = time.time()
            # ... do work ...
            log("worker_1", "ok", (time.time()-t0)*1000, "result summary")
            time.sleep(30)  # Cycle interval
        except Exception as e:
            log("worker_1", "error", 0, traceback.format_exc()[:200])
            time.sleep(60)  # Back off on error

def main():
    PID_FILE.write_text(str(os.getpid()))
    threads = [
        threading.Thread(target=worker_loop_1, daemon=True),
        threading.Thread(target=heartbeat, daemon=True),
    ]
    for t in threads:
        t.start()
    while _running:
        time.sleep(1)

if __name__ == "__main__":
    main()
```

## Start / Stop / Restart Commands

```bash
# Start
cd ~/hermes-agent && source venv/bin/activate
nohup python3 ~/subconscious/cortex_daemon.py >> /tmp/cortex_daemon.log 2>&1 &

# Stop gracefully
kill $(cat ~/subconscious/cortex_daemon.pid)

# Check status
cat ~/subconscious/cortex_daemon.heartbeat | python3 -m json.tool
tail -20 ~/subconscious/cortex_daemon.jsonl

# After reboot, restart:
cd ~/hermes-agent && source venv/bin/activate
nohup python3 ~/subconscious/cortex_daemon.py >> /tmp/cortex_daemon.log 2>&1 &
```

## Postgres Performance Optimization (CRITICAL — learned the hard way)

### 1. md5 Hash Dedup (1000x speedup over similarity())

**Problem**: `similarity(a.text, b.text) > 0.7` JOIN on 388K edges takes 65 SECONDS.
**Solution**: `md5(a.text) = md5(b.text)` takes 56 MILLISECONDS.

```sql
-- BEFORE (65 seconds):
SELECT a.id, b.id FROM cortex_nodes a
JOIN cortex_nodes b ON a.id < b.id AND similarity(a.text, b.text) > 0.7
WHERE a.node_type = 'tip' AND a.is_active = TRUE;

-- AFTER (56ms):
SELECT a.id, b.id FROM cortex_nodes a
JOIN cortex_nodes b ON a.id < b.id AND a.node_type = b.node_type AND md5(a.text) = md5(b.text)
WHERE a.is_active = TRUE AND b.is_active = TRUE AND a.node_type = 'tip';

-- Index for this:
CREATE INDEX idx_nodes_text_hash ON cortex_nodes(md5(text)) WHERE is_active = TRUE;
```

**Why it works**: md5 is a deterministic hash computed once per row, indexable. similarity() is a trigram comparison computed for every pair — O(n²) even with a GIN index. Use md5 for exact dedup, reserve similarity() for manual spot-checks only.

### 2. Index Strategy for Knowledge Graph DB (19 indexes proven)

```sql
-- Node lookups
CREATE INDEX idx_nodes_type_active ON cortex_nodes(node_type, is_active);
CREATE INDEX idx_nodes_elo ON cortex_nodes(elo DESC) WHERE is_active = TRUE;
CREATE INDEX idx_nodes_elo_matches ON cortex_nodes(elo_matches) WHERE is_active = TRUE;
CREATE INDEX idx_nodes_domain ON cortex_nodes(domain) WHERE is_active = TRUE;

-- Full-text search (GIN)
CREATE INDEX idx_nodes_fts ON cortex_nodes
  USING GIN(to_tsvector('english', coalesce(text, ''))) WHERE is_active = TRUE;

-- Trigram similarity (GIN)
CREATE INDEX idx_nodes_trgm ON cortex_nodes
  USING GIN(text gin_trgm_ops) WHERE is_active = TRUE AND node_type = 'tip';

-- Edge traversal (388K rows — CRITICAL)
CREATE INDEX idx_edges_source ON cortex_edges(source_id);
CREATE INDEX idx_edges_target ON cortex_edges(target_id);
CREATE INDEX idx_edges_source_target ON cortex_edges(source_id, target_id);

-- Covering index for eval queries
CREATE INDEX idx_nodes_tip_eval ON cortex_nodes(elo, elo_matches, is_active)
  WHERE node_type = 'tip' AND is_active = TRUE;

-- ALWAYS run ANALYZE after creating indexes
ANALYZE cortex_nodes;
ANALYZE cortex_edges;
```

### 3. pg_trgm Gotcha

**The GIN index helps ILIKE `%pattern%` but does NOT help similarity() function.**
The similarity() function still does a sequential scan over all matching rows even with the GIN index. Only use it for small result sets (<100 rows), never for JOINs.

### 4. Edge GROUP BY with OR is Slow

```sql
-- SLOW (394ms) — OR prevents index use:
SELECT n.node_type, COUNT(DISTINCT e.id) FROM cortex_nodes n
JOIN cortex_edges e ON (e.source_id = n.id OR e.target_id = n.id)
GROUP BY n.node_type;

-- FAST — split into two queries:
SELECT 'outgoing' as direction, n.node_type, COUNT(*) FROM cortex_nodes n
JOIN cortex_edges e ON e.source_id = n.id GROUP BY n.node_type;
SELECT 'incoming' as direction, n.node_type, COUNT(*) FROM cortex_nodes n
JOIN cortex_edges e ON e.target_id = n.id GROUP BY n.node_type;
```

## Elo Flywheel Tuning

### K-Factor Selection
- **K=40**: Fast convergence, good for initial rating (spreads tips quickly)
- **K=32**: Standard, slower convergence
- **K=20**: Stable, for mature systems where you don't want Elo to swing much
- Use K=40 until spread > 100, then consider lowering to K=32

### Elo Spread Target
- **stddev < 20**: Tips not differentiating — raise K-factor or improve judge
- **stddev 30-50**: Good — clear quality tiers emerging
- **stddev > 80**: May have bimodal distribution — check for bad tips dragging down

## SQLite→Postgres Migration Gotchas

1. **CREATE TABLE order matters** — must order by FK dependencies (referenced tables first)
2. **DROP DATABASE** must connect to 'postgres' DB, not the target DB itself
3. **SQLite timestamps** can be int, float, string, ISO, or milliseconds — need robust converter
4. **SQLite empty strings** in numeric columns → Postgres type errors — need clean() that converts "" to None
5. **SQLite booleans** are 0/1 ints — wrap with bool() for Postgres
6. **fetchall() consumes cursor** — double-fetching returns empty rows
7. **psycopg2 kwargs** must match function signature — unknown kwargs throw TypeError
8. **After modifying plugins**: MUST `rm -rf __pycache__/` or changes silently ignored
9. **UUID columns**: Always generate with `str(uuid.uuid4())` — PostgreSQL validates format strictly

## Cron Jobs as Backup

Keep cron jobs running alongside the daemon as a safety net:

```
d9d790021dd1  cortex-flywheel-baseline   every 2h   (backup for daemon flywheel)
ece3733a111c  cortex-consolidation       daily 4am  (deep consolidation)
54efd7ef8bf6  cortex-dojo                daily 3am  (self-improvement report)
fca05291425c  cortex-quality-sweep       every 2h   (quality audit)
```

If the daemon dies, cron picks up the slack. If daemon is running, cron runs add extra cycles (harmless — operations are idempotent).

## Dual-Write Adapter Pattern

When migrating from SQLite to Postgres while keeping the old system running:

```python
# cortex_compat.py — intercepts writes, mirrors to Cortex
try:
    from cortex_compat import cortex_sync
    _CORTEX_SYNC = True
except Exception:
    _CORTEX_SYNC = False

# After every SQLite INSERT:
if _CORTEX_SYNC:
    try:
        cortex_sync('insert', 'distilled_tips', {...})
    except Exception:
        pass  # Non-blocking — SQLite is source of truth during migration
```

Key points:
- Sync is non-blocking — if Cortex is down, SQLite still works
- Read path: try Cortex first, fall back to SQLite
- Write path: write to both, ignore Cortex errors
- Eventually: switch reads to Cortex-only, retire SQLite
