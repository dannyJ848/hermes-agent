---
name: brain-cycle
description: "Evey's parallel cognitive brain — 3-region ThreadPoolExecutor architecture with epistemic guard and iteration engine. 3.8x speedup over sequential."
version: 5.1
created: 2026-04-03
updated: 2026-04-04
triggers:
  - "run brain"
  - "brain cycle"
  - "parallel brain"
  - "consciousness"
  - "self-improvement"
---

# Evey's Parallel Brain v4.0

## Architecture

```
Thalamus (orchestrator) — parallel_brain.py
├── Temporal Lobe → Connect + Intuit (pattern finding)
├── Prefrontal Cortex → Reflect (validation, identity)
├── Motor Cortex → Grow (execution, synthesis)
└── Shared: cerebrum_memory.db, iteration_engine, epistemic_guard
```

## Files

| File | Purpose |
|------|---------|
| `~/subconscious/parallel_brain.py` | Main parallel brain (2.5x faster) |
| `~/subconscious/brain.py` | Sequential fallback (v3.0) |
| `~/subconscious/epistemic_guard.py` | Trust ring enforcement |
| `~/subconscious/iteration_engine.py` | Instant experiential learning |
| `~/.hermes/cerebrum_memory.db` | Shared nervous system (all regions R/W) |

## Key Design Decisions

1. **Parallel execution via ThreadPoolExecutor** — Connect, Intuit, and Reflect run simultaneously. The total time is the max(slowest), not the sum.
2. **Thread-safe DB access** — Each thread gets its own SQLite connection. The main thread's `self.db` is never used inside thread workers.
3. **Epistemic guard hardwired** — All model-generated facts capped at trust 0.3. No fact enters memory without being assigned a trust ring.
4. **Iteration engine** — `before_action()` retrieves lessons in sub-ms. `after_action()` records every success/failure. Detects regressions.

## DB Schema Notes

- `semantic_facts` columns: id, content, source, provenance, category, trust, salience, access_count, consolidation_count, created_at, last_accessed, last_consolidated, entities, tags, session_id
- **No `source_class` column** — use `source` and `provenance` instead. Model-generated content has `source='model-generate'`.
- `predictions` columns: id (TEXT PK), timestamp, session_id, task_type, task_summary, predicted_difficulty, predicted_approach, predicted_iterations, predicted_outcome, confidence, actual_difficulty, actual_iterations, actual_outcome, actual_approach, difficulty_error, outcome_error, iteration_error, calibration_score, resolved. **Note**: The main text field is `task_summary`, NOT `prediction`.
- `self_model` columns: key (TEXT PK), value (TEXT). Key entries: `maslow_level`, `knowledge_count`, `prediction_count`, `last_reflection`, `intuition_accuracy`.
- `brain_dispatch` table — inter-region task queue for squad dispatch
- `life_events` columns: id (TEXT PK), timestamp (REAL), event_type (TEXT), title (TEXT), description (TEXT), emotional_valence (REAL), significance (REAL), lessons (TEXT), related_events (TEXT), chapter (TEXT). Event types: `intuition_confirmed`, `intuition_corrected`. These track when the Reflect phase validates or corrects past intuitions — the highest-value output for self-improvement reporting.
- `experiences` columns: id (INTEGER), action_hash (TEXT), action_type (TEXT), action_detail (TEXT), action_fingerprint (TEXT), result (TEXT), error_pattern (TEXT), error_snippet (TEXT), lesson (TEXT), approach (TEXT), fix_command (TEXT), iterations (INTEGER), frequency (INTEGER), speed_ms (INTEGER), last_seen (REAL), created_at (REAL), context_tags (TEXT). **Note**: No `status` column — the `ITERATE` log line (e.g., `Total: 433 | Resolved: 192 | Session: 0`) tracks resolution separately in the iteration engine, not via a DB column. Query `result` field for success/failure patterns.

## Running

```bash
# Parallel brain (primary)
cd ~/subconscious && python3 parallel_brain.py

# Sequential brain (fallback)
cd ~/subconscious && python3 brain.py

# Quick iteration engine stats
cd ~/subconscious && python3 -c "from iteration_engine import IterationEngine; print(IterationEngine().get_learning_stats())"

# Epistemic audit
cd ~/subconscious && python3 epistemic_guard.py

# Status check
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT key, value FROM self_model"
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM predictions"
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT CASE WHEN trust>=0.7 THEN 'ground' WHEN trust>=0.4 THEN 'derived' ELSE 'speculative' END as ring, COUNT(*), ROUND(AVG(trust),3) FROM semantic_facts GROUP BY ring"

# Category distribution (useful for spotting knowledge imbalances)
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT category, COUNT(*) as cnt, ROUND(AVG(trust),2) as avg_trust FROM semantic_facts GROUP BY category ORDER BY cnt DESC LIMIT 15"

# Recent intuitions (most actionable brain output)
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT substr(task_summary,1,80), predicted_outcome, confidence, resolved FROM predictions ORDER BY timestamp DESC LIMIT 5"

# Trust distribution (spot low-quality knowledge)
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT substr(content,1,100), trust, category FROM semantic_facts WHERE trust < 0.15 ORDER BY trust ASC LIMIT 10"
```

## Post-Cycle Analysis & Reporting (for cron jobs)

After running a cycle, analyze and report the results:

### 1. Check cycle output files
```bash
# Latest run history (SUMMARY ONLY — counts/timings, no detailed content)
cat ~/subconscious/run-history/$(ls -t ~/subconscious/run-history/ | head -1) | python3 -m json.tool

# Latest brain state (detailed state snapshots — but only from brain.py sequential runner)
cat ~/subconscious/brain-state/$(ls -t ~/subconscious/brain-state/ | head -1) | python3 -m json.tool

# Latest governance audit (BEST SOURCE for diagnostic depth — facts, predictions, tool perf, violations)
cat ~/subconscious/audits/$(ls -t ~/subconscious/audits/ | head -1) | python3 -m json.tool
```

> **Note**: run-history JSONs contain only summary metrics (cycle_id, elapsed, maslow_level, counts of connections/intuitions/research, grounded_pct, parallel_speedup, timings). They do NOT contain the actual text content of intuitions, connections, or research insights. For meaningful reporting, the `audits/` files are the primary source — they include fact breakdowns, prediction stats, tool performance verdicts, and violation lists.

### 1b. Quick content retrieval for cron reports (single Python snippet)
The run-history JSONs only have counts. For the ACTUAL text of connections, intuitions, and research from the latest cycle, query `semantic_facts` directly:

```python
import sqlite3, os
db = sqlite3.connect(os.path.expanduser('~/.hermes/cerebrum_memory.db'))
db.row_factory = sqlite3.Row
c = db.cursor()

# Latest connections, intuitions, research
for cat in ['connection', 'intuition', 'research']:
    c.execute("SELECT id, trust, substr(content,1,200) FROM semantic_facts WHERE category=? ORDER BY id DESC LIMIT 3", (cat,))
    rows = c.fetchall()
    print(f'\n=== {cat.upper()} ({len(rows)} latest) ===')
    for r in rows:
        print(f'  [{r[0]}] trust={r[1]:.2f}  {r[2]}')

# Trust distribution
c.execute("SELECT CASE WHEN trust>=0.7 THEN 'grounded' WHEN trust>=0.4 THEN 'derived' ELSE 'speculative' END as ring, COUNT(*), ROUND(AVG(trust),3) FROM semantic_facts GROUP BY ring")
for r in c.fetchall(): print(f'  {r[0]}: {r[1]} facts (avg trust {r[2]})')
db.close()
```

This is the fastest path from "cycle finished" to "readable report with actual content."

### 2. Trend analysis across recent cycles
```bash
# Use a Python script to avoid shell quoting issues with $f inside Python f-strings
python3 -c "
import json, glob
for f in sorted(glob.glob('$HOME/subconscious/run-history/*.json')):
    d = json.load(open(f))
    print(f\"{d['cycle_id']} L{d['maslow_level']} conn={d['connections']} int={d['intuitions']} res={d['research']} ground={d['grounded_pct']}% time={d['elapsed']:.0f}s speedup={d['parallel_speedup']:.1f}x\")
" | tail -20
```

### 2b. Daily stats aggregation (useful for cron reports)
```python
import json, glob, os
from collections import Counter

files = sorted(glob.glob(os.path.expanduser('~/subconscious/run-history/2026-04-04_*.json')))
levels = Counter()
grounded = []
for f in files:
    try:
        d = json.load(open(f))
        levels[d.get('maslow_level', 0)] += 1
        grounded.append(d.get('grounded_pct', 0))
    except: pass

print(f'Today: {len(files)} cycles')
print(f'Maslow levels: {dict(sorted(levels.items()))}')
if grounded:
    print(f'Grounded %: min={min(grounded):.1f} avg={sum(grounded)/len(grounded):.1f} max={max(grounded):.1f}')

# Last 10 cycles for trend
for f in files[-10:]:
    d = json.load(open(f))
    print(f"  {d['cycle_id']}  L{d['maslow_level']}  grounded={d.get('grounded_pct',0):.1f}%  conns={d.get('connections',0)}  intuit={d.get('intuitions',0)}  research={d.get('research',0)}  trust={d.get('trust_adjustments',0)}")
```

### 3. Key metrics to report
- **Cycle stats**: maslow level, elapsed time, parallel speedup, connections/intuitions/research counts
- **Epistemic quality**: grounded % (watch for steady decline — signals speculative fact explosion)
- **Phase timings**: reflect, intuit, connect, research, grow — identify bottlenecks
- **Governance audit grade & violations**: prediction backlog, duplicate clusters, fact explosion rate, tool performance verdict

### 4. Red flags to escalate
- **Grounded % declining monotonically** across cycles → speculative facts overwhelming grounded ones. **Quantify with first-10 vs last-10 cycle averages**: if the gap exceeds 10 percentage points (e.g., 40% → 26%), the system is in a speculation spiral — generating speculative facts faster than grounded ones compound. Each cycle adds ~2-3 speculative facts per grounded fact, so the ratio worsens over time without intervention.
- **Maslow level regression** (e.g., Level 5 → Level 1 sustained for 3+ cycles) → Grow phase stuck as no-op, escalation logic stalled in a local minimum. Compare against the most recent brain-state JSON in `~/subconscious/brain-state/` to see when it was last healthy.
- **Maslow stuck at Level 1 across ALL run-history entries** → `parallel_brain.py` may lack the Maslow advancement gate that `brain.py` had. The brain-state/ directory tracks `brain.py` runs (which DO progress 1→3→4), while run-history/ tracks `parallel_brain.py` runs. If run-history shows perpetual Level 1 but brain-state shows higher levels, the parallel runner is missing escalation logic. Check `controller.py` for the advancement function and verify it's called from `parallel_brain.py`.
- **Maslow stuck at Level 1 despite adequate semantic_facts (≥1500)** → Check for stale prediction backlog. The `_determine_maslow()` function forces Level 1 when `unresolved predictions > 200`. Predictions with NULL timestamps can NEVER be resolved by the Reflect phase. **Fix**: `sqlite3 ~/.hermes/cerebrum_memory.db "UPDATE predictions SET resolved = 1 WHERE timestamp IS NULL AND resolved = 0"` — then re-run the cycle. With facts ≥ 1500 and predictions < 200, Maslow jumps to Level 5 immediately.
- **Grow phase completes in 0.0s** → Motor cortex is a no-op at Level 1, meaning the cycle never escalates. Investigate `controller.py` escalation logic or `parallel_brain.py` grow phase.
- **0 items resolved in Reflect** → Prefrontal found nothing to resolve, suggests iteration engine backlog is stale or empty.
- **Prediction backlog > 50** → predictions generated faster than resolved
- **Fact explosion > 100/hr** → needs consolidation/pruning pass
- **Tool performance verdict = "degrading"** → brain growth not translating to real-world tool use
- **Composite score < 2.0 or grade F** → systemic issues need intervention
- **Audit grade F but calibration = "IMPROVING"** → common discrepancy. The audit penalizes speculative fact ratio (75%+ speculative) and prediction backlog size, while the calibration tracker measures actual recent tool-use success rate (typically 90%+). When calibration contradicts audit, trust calibration for operational health and note the audit violations for long-term cleanup.

### 4b. Grounded % collapse — diagnostic procedure
When grounded % drops sharply (>10pp in a single cycle), run this diagnostic:

```python
cd ~/subconscious && python3 << 'PYEOF'
from epistemic_guard import EpistemicGuard
import json, glob

guard = EpistemicGuard()

# 1. Find the exact transition cycle
runs = sorted(glob.glob('run-history/*2026-04-04*.json'))  # adjust date
prev_g = None
for i, r in enumerate(runs):
    d = json.load(open(r))
    g = d.get('grounded_pct')
    if prev_g is not None and prev_g > 5 and g is not None and g <= 1:
        print(f"TRANSITION at index {i}: {r}")
        print(f"  Before: {prev_g}% -> After: {g}%")
        break
    if g is not None:
        prev_g = g

# 2. Trust distribution (the real health check)
rows = guard.conn.execute("""
    SELECT CASE WHEN trust>=0.7 THEN 'ground' WHEN trust>=0.4 THEN 'derived' ELSE 'speculative' END as ring,
           COUNT(*), ROUND(AVG(trust),3)
    FROM semantic_facts GROUP BY ring
""").fetchall()
total = sum(r[1] for r in rows)
print(f"\nTrust distribution (total={total}):")
for ring, count, avg in rows:
    print(f"  {ring}: {count} ({100*count/total:.1f}%) avg_trust={avg}")

# 3. Fact creation rate by period (finds bulk ingestion)
rows2 = guard.conn.execute("""
    SELECT CASE
        WHEN created_at > strftime('%s','now') - 3600 THEN 'last_hour'
        WHEN created_at > strftime('%s','now') - 14400 THEN 'last_4h'
        WHEN created_at > strftime('%s','now') - 86400 THEN 'today'
        ELSE 'older'
    END as period, COUNT(*), ROUND(AVG(trust),3)
    FROM semantic_facts WHERE created_at IS NOT NULL
    GROUP BY period ORDER BY MIN(created_at)
""").fetchall()
print("\nFacts by creation period:")
for period, count, avg_trust in rows2:
    print(f"  {period}: {count} facts (avg trust: {avg_trust})")
PYEOF
```

**Typical finding**: A batch of new facts was ingested at trust ~0.25 (speculative), diluting the grounded/total ratio. The fix options are: (1) reduce speculative fact ingestion rate, (2) accelerate trust promotion, or (3) add decay/pruning for low-trust unused facts. If speculative exceeds 80%, the knowledge base quality is degraded.

### 4c. Cliff-drop grounded% (not gradual) — 0-byte target DB

When grounded% drops from ~40% to <1% in a **single cycle** (not gradual), the root cause is usually a 0-byte or empty target DB (`~/.hermes/cerebrum_memory.db`). The cycle's perceive phase classifies knowledge files via LLM inference, generating speculative fact counts (e.g., "3250 speculative, 544 derived, 109 grounded") that have no DB backing. The grounded_pct becomes 109/(109+544+3250) ≈ 0.4%.

**Quick binary search for regression point** (faster than iterating all runs):
```python
import json, glob
runs = sorted(glob.glob('~/subconscious/run-history/*DATE*.json'))
lo, hi = 0, len(runs) - 1
while lo < hi:
    mid = (lo + hi) // 2
    d = json.load(open(runs[mid]))
    if d.get('grounded_pct', 0) > 5:
        lo = mid + 1  # still healthy, look later
    else:
        hi = mid       # already degraded, look earlier
# lo is the first degraded run
print(f"Regression at: {runs[lo]}")
```

**Diagnostic triage** (run these in order):
```bash
# 1. Check target DB size (0 bytes = never initialized)
ls -la ~/.hermes/cerebrum_memory.db

# 2. Check if tables exist at all
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT name FROM sqlite_master WHERE type='table'"

# 3. If tables exist but are empty vs if DB is truly 0 bytes
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT count(*) FROM semantic_facts"

# 4. Compare against working brain.db
sqlite3 ~/subconscious/brain.db "SELECT count(*) FROM semantic_facts"
```

**Finding pattern**: If `cerebrum_memory.db` is 0 bytes but `brain.db` has facts, the cycle is reading from brain.db but writing to the empty cerebrum_memory.db. The cycle "works" (connections=3, intuitions=2) but all output is silently lost because the write target has no schema. Fix: ensure `parallel_brain.py`'s `__init__` creates tables in `cerebrum_memory.db` (see Pitfall #8).

### 5. File locations
| Path | Contents |
|------|----------|
| `~/subconscious/run-history/` | Per-cycle JSON summaries |
| `~/subconscious/brain-state/` | Detailed state snapshots |
| `~/subconscious/audits/` | Governance audit reports with grades |
| `~/subconscious/tool_capability.db` | Tool performance DB (call counts, success rates, confidence, recipes) |
| `~/subconscious/ideas/` | Generated ideas (JSONL) |
| `~/subconscious/debates/` | Adversarial debates (JSONL) |
| `~/subconscious/synthesis/` | Synthesized insights |

### 5b. Tool capability queries (enrich cycle reports)
```bash
# Top tools by usage and confidence
sqlite3 ~/subconscious/tool_capability.db "SELECT tool_name, total_calls, successes, failures, ROUND(confidence,2) as conf FROM tool_stats ORDER BY total_calls DESC LIMIT 15;"

# Recent tool failures
sqlite3 ~/subconscious/tool_capability.db "SELECT tool_name, error_pattern, lesson, datetime(timestamp, 'unixepoch', 'localtime') FROM call_log WHERE result_status='failure' ORDER BY timestamp DESC LIMIT 10;"

# Successful tool recipes (sequences that worked)
sqlite3 ~/subconscious/tool_capability.db "SELECT tool_name, task_signature, success_count, sequence FROM tool_recipes ORDER BY success_count DESC LIMIT 10;"
```

**Schema**: `tool_stats` (tool_name PK, total_calls, successes, failures, partials, avg_speed_ms, confidence), `call_log` (id, tool_name, args_preview, result_status, speed_ms, error_pattern, lesson, turn_context, timestamp), `tool_recipes` (id, tool_name, task_signature, args_shape, sequence, success_count, last_used, created_at).

## Execution Method (Updated Apr 5 2026)

**Brain daemon** (replaces cron jobs): `~/subconscious/brain_daemon.py`
- 3 threads (alpha/bravo/charlie) staggered by 40s
- Writes cycle results to `~/subconscious/brain_cycles.jsonl`
- Controller cron (hourly) merges JSONL into `tool_capability.db`
- Log: `/tmp/brain_daemon.log`

**Why daemon instead of cron**: Brain cycles take 60-80s each. With 3 cron jobs every 2min on `max_workers=1`, they blocked the AGI cron entirely. Daemon runs independently, freeing the scheduler.

**Paused cron jobs** (kept as fallback):
- brain-cycle-alpha (cd005dde53af): paused
- brain-cycle-bravo (07e231ad644b): paused
- brain-cycle-charlie (eaedcb13a4f4): paused

**Distillation chain is intact**: `parallel_brain.py` → `cerebrum_memory.db` (via IterationEngine quick_before/quick_after) → `controller.py` hourly distillation. The cron wrapper was never part of this chain — it only added trivial `terminal: success, 440ms` entries to tool_capability.db. The real iteration tracking happens inside parallel_brain.py's 241+ think_json experiences.

**JSONL bridge for tool-intelligence**: `~/subconscious/brain_to_toolintel.py` writes cycle results to `brain_cycles.jsonl`. Controller's `merge_brain_cycles()` function merges into `tool_capability.db` hourly. This avoids SQLite lock contention — the gateway holds tool_capability.db open with 9+ file handles.

## Squad Sync

When updating subconscious files, sync to all 3 profiles:
```bash
for p in soma-coder soma-researcher soma-tester; do
  cp ~/subconscious/parallel_brain.py ~/.hermes/profiles/$p/workspace/subconscious/
  cp ~/subconscious/epistemic_guard.py ~/.hermes/profiles/$p/workspace/subconscious/
  cp ~/subconscious/iteration_engine.py ~/.hermes/profiles/$p/workspace/subconscious/
done
```

## Pitfalls

### 1. Patch tool mangles escaped quotes in triple-quoted f-strings
When using the `patch` tool on `"""..."""` strings with internal escaped quotes like `\"supported\"`, the tool double-escapes them to `\\\"supported\\\"`, causing SyntaxError.

**Fix**: Replace triple-quoted f-strings containing escaped quotes with parenthesized string concatenation:
```python
# BAD — patch tool will mangle:
prompt = f"""Answer only: \"supported\" or \"contradicted\"."""

# GOOD — use parenthesized concatenation:
prompt = (
    f'Earlier, Evey had this intuition: "{pred[1]}"\n'
    f'The predicted test was: "{pred[2]}"\n'
    'Answer only: "supported", "contradicted", or "unchanged".'
)
```

### 2. Thread safety with SQLite
SQLite connections are NOT thread-safe. Each thread function must create its own `sqlite3.connect()`. Never use `self.db` (the main thread's connection) inside a ThreadPoolExecutor worker. The parallel brain's `_research_phase()` demonstrates the fix.

### 3. EpistemicGuard has no store_fact method
The guard validates trust levels but doesn't store facts. Use direct `db.execute(INSERT INTO semantic_facts ...)` with trust=0.3 for model-generated content. The guard's `validate()` returns a trust assessment, not a storage method.

### 4. API key loading from .env
The parallel brain's `DirectModel` loads `GLM_API_KEY` from `~/.hermes/.env` since cron jobs don't inherit shell environment. Always include this fallback:
```python
self.api_key = os.environ.get("GLM_API_KEY", "")
if not self.api_key:
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GLM_API_KEY="):
                self.api_key = line.split("=", 1)[1].strip()
                break
```

### 5. Timing measurement for parallel tasks
Measure from `t_submit = time.time()` BEFORE submitting to pool, then `elapsed = time.time() - t_submit` in each result callback. Measuring inside the callback gives near-zero since the work is already done.

### 6. brain-state/ vs run-history/ track DIFFERENT runners
`brain-state/` contains state snapshots from `brain.py` (sequential runner) which includes Maslow level progression. `run-history/` contains summaries from `parallel_brain.py` which may lack advancement logic. When diagnosing stuck Maslow levels, check BOTH directories — they tell different stories. The iteration engine's `ITERATE` log line (e.g., `Total: 246 | Resolved: 85 | Session: 0`) also tracks global vs session resolution separately.

### 7. Stale predictions with NULL timestamps block Maslow advancement
Predictions are generated during the Intuit phase but older cycles stored them without timestamps. The Reflect phase can only resolve predictions it can match against recent activity — predictions with `NULL` timestamps accumulate forever. Since `_determine_maslow()` returns Level 1 (Survival) when unresolved predictions exceed 200, this silently caps the brain's growth regardless of how many semantic facts exist.

**Diagnostic**: `sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM predictions WHERE resolved = 0 AND timestamp IS NULL"` — if > 0, these are permanent blockers.

**Fix**: `sqlite3 ~/.hermes/cerebrum_memory.db "UPDATE predictions SET resolved = 1 WHERE timestamp IS NULL AND resolved = 0"`

**Prevention**: Consider adding a periodic cleanup to the brain cycle that auto-resolves predictions older than 30 days or with NULL timestamps.

### 8. parallel_brain.py __init__ must create ALL required tables (not just brain_dispatch)

As of 2026-04-04, `parallel_brain.py`'s `__init__` was only creating `brain_dispatch` but querying `semantic_facts`, `predictions`, and `self_model`. These tables were created externally (by Cerebrum's init or other tooling). If the external creation hasn't run or the DB is fresh, all queries silently return empty results — the brain runs but operates at Level 1 with 0.5% grounded because it sees no facts.

**Fix applied**: Patched `__init__` to include `CREATE TABLE IF NOT EXISTS` for all 4 tables (`brain_dispatch`, `semantic_facts`, `predictions`, `self_model`). The `IF NOT EXISTS` makes this idempotent — safe to run even when tables already exist.

**Diagnostic**: If the brain runs but `_get_knowledge()` returns 0 facts despite `cerebrum_memory.db` having thousands:
```bash
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('semantic_facts','predictions','self_model')"
```
If empty, the schema was never created. Re-run `parallel_brain.py` after patching.

### 9. Multiple identical model.call() lines need context for patching
When patching `self.model.think_json(prompt)` calls, always include 3-5 lines of surrounding prompt text to make the match unique. There are typically 5-7 identical `self.model.think` lines in brain.py.

### 10. Brain cycle outputs go to DB, not files
The cycle does NOT write intuition/connection/research text to `outputs/`, `ideations/`, `insights/`, or any markdown files. All content goes into the `semantic_facts` table in `~/.hermes/cerebrum_memory.db` with categories `connection`, `intuition`, `research`, `synthesis`. The `run-history/` JSONs contain only summary counts and timings. To get actual content, query the DB directly (see Section 1b above).

**Don't waste time searching for output files.** The reflex to `find ~/subconscious -name "*.md" -mmin -5` will always return nothing useful. Skip directly to the DB query in Section 1b.

**Two separate databases**:
1. `~/.hermes/cerebrum_memory.db` — The full Cerebrum system DB (3,336+ facts, multiple provenance types). This is what the broader Hermes memory system uses.
2. `~/subconscious/brain.db` — The parallel brain's own working DB (100-200 facts, all `provenance='ground'`). This is what `parallel_brain.py` reads/writes during cycles.

The brain cycle queries `brain.db` for its knowledge, NOT `cerebrum_memory.db`. When the cycle reports "109 facts absorbed" or "0.4% grounded", it's measuring against `brain.db`, not the full 3,336-fact Cerebrum DB. For a complete picture, query both databases.

**Schema discovery shortcut**: If unsure about column names, use `PRAGMA table_info(table_name)` on the SQLite DB. Common gotcha: `predictions` uses `task_summary` not `prediction` or `content` as the main text field.

**brain.db schema (simpler than cerebrum_memory.db)**: `semantic_facts` columns are: `id` (INTEGER PK), `content` (TEXT), `source` (TEXT, default 'unknown'), `category` (TEXT, default 'general'), `trust` (REAL, default 0.5), `salience` (REAL, default 0.5), `provenance` (TEXT, default 'derived'), `created_at` (REAL, default 0), `last_accessed` (REAL, default 0). Note: **no** `access_count`, `consolidation_count`, `entities`, `tags`, or `session_id` columns — those exist only in `cerebrum_memory.db`. Using `sqlite3.Row` with brain.db column names from the Cerebrum schema will cause `IndexError`. Always `PRAGMA table_info()` first if unsure.

### 11. Audit tool_performance dict structure is inconsistent
When parsing `audits/*.json` tool_performance, not all sub-dicts have a `successes` key. The `brain_internal` entry reports `success_rate` but may lack `successes`/`failures` individually. Always use `.get('successes', 0)` and check for key existence before iterating:

```python
for cat, val in tp.items():
    if isinstance(val, dict) and 'success_rate' in val:
        sr = val.get('successes', 'N/A')
        tot = val.get('total', '?')
        print(f'  {cat}: {sr}/{tot} ({val["success_rate"]*100:.0f}%)')
```

### 12. Intuitions not persisted as predictions — broken feedback loop
The Intuit phase generates hunches (confidence, test, why) but `parallel_brain.py` does NOT insert them into the `predictions` table. The predictions table remains empty, so the Reflect phase has nothing to resolve, and trust never gets updated from prediction validation. This means:
- All 109 facts in `brain.db` stay at exactly trust=0.70 (never promoted or demoted)
- The "3 trust adjustments" logged each cycle are computed but not persisted
- The grounded percentage is purely based on provenance tagging, not empirical validation

**Diagnostic**: `sqlite3 ~/subconscious/brain.db "SELECT COUNT(*) FROM predictions WHERE resolved=0"` — if 0, the predict→observe→learn loop is broken.

### 13. identity_state table must exist for synthesize to work
The `synthesize()` phase inserts into `identity_state` (self_narrative, last_updated) but the table was missing from the `__init__` CREATE TABLE block until 2026-04-04. Without it, the synthesize phase crashes silently (caught by the outer try/except), which means **ALL cycle outputs are lost** — no connections, intuitions, predictions, or research get stored. The cycle reports success (connections=3, intuitions=2) but the DB remains unchanged.

**Diagnostic**: `sqlite3 ~/.hermes/cerebrum_memory.db "SELECT name FROM sqlite_master WHERE type='table' AND name='identity_state'"` — if empty, synthesize is silently failing every cycle.

**Fix**: Ensure `CREATE TABLE IF NOT EXISTS identity_state (key TEXT PRIMARY KEY, value TEXT DEFAULT '')` is in the schema init block alongside `self_model`.

**Key insight**: The synthesize phase is NOT atomic — it does connections first, then intuitions, then identity, then self_model. If identity INSERT fails, the prior connection/intuition INSERTs are lost too because `self.db.commit()` happens after the identity block. One missing table invalidates the entire cycle's output.

### 14. DB_PATH points to cerebrum_memory.db, NOT brain.db
`parallel_brain.py` uses `DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"`. All writes from the cycle (connections, intuitions, research) go to THIS database. When debugging or checking cycle output, always query `~/.hermes/cerebrum_memory.db`, not `~/subconscious/brain.db`. The brain.db file is a separate working DB with different schema and content.

**Time-saving rule**: After a cycle completes, go straight to:
```bash
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT id, category, trust, substr(content,1,150) FROM semantic_facts WHERE created_at > $(date -v-5M +%s) ORDER BY id DESC"
```
Do NOT search for output files, do NOT check brain.db, do NOT look in outputs/ directories.

### 15. call_log result_status is mostly 'partial', not 'success'
The brain cycle's own tool introspection logs nearly all calls as `result_status='partial'` because it captures output mid-stream before the full result is processed. This means querying `call_log WHERE result_status='failure'` will show very few rows, and `tool_stats.partials` is heavily inflated. For meaningful failure analysis, use `tool_stats.last_error` and `tool_stats.last_lesson` columns instead, or filter by `error_pattern IS NOT NULL AND error_pattern != ''` on call_log.
