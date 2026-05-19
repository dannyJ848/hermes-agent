# Autobrowse Live Verification — 2026-05-09

## What We Verified

After applying the hook signature fix (**kwargs + defaults for all 4 hook functions), we ran a full end-to-end smoke check.

## Discovery: Dual Database Architecture

The autobrowse pipeline writes to **TWO** different databases:

### 1. `tool_intelligence.db` — LIVE CAPTURE (1,907 calls)
- **Path**: `~/.hermes/tool_intelligence.db`
- **Table**: `tool_calls` (cols: id, tool_name, success, duration_ms, tokens_in, tokens_out, error_type, error_message, context, session_id, timestamp)
- **Written by**: `_record_tool_call_cortex()` in distillation plugin `_on_post_tool_call` hook
- **Status**: ACTIVE — latest entry 2026-05-09 11:45:38 (terminal call)
- **Recent web_search**: 2026-05-09 11:43:16, success=1, dur=0ms

### 2. `cerebrum_memory.db` — OLD SYNC PATH (492 rows, STALE)
- **Path**: `~/.hermes/cerebrum_memory.db`
- **Table**: `tool_call_log` (cols: id, tool_name, status, speed_ms, args, created_at)
- **Last entry**: 2026-05-05 12:34:49 (id=4095, write_file)
- **Status**: STALE — no writes since May 5 despite heavy session activity

**Implication**: Checking `cerebrum_memory.db` alone will falsely report a dead pipeline. Always check `tool_intelligence.db` for live status.

## Full Pipeline Smoke Test Results

```
=== TRACER ===
traces: 5 (3x web_search + read_file + delegate_task)

=== ANALYZER ===
patterns: 2
  redundant_loop: sev=0.60 conf=0.85
  suboptimal_model: sev=0.60 conf=0.85

=== SYNTHESIZER ===
tips: 2
  [efficiency] WHEN about to call the same tool (trace) with similar input...
  [cost_optimization] WHEN selecting a model for simple information retrieval...
CortexDB.insert_node error: duplicate key value violates unique constraint "cortex_active_tip_md5_uniq"
  → EXPECTED: tips already exist from live pipeline

=== GRADUATOR ===
tracked: 2, activated: 0, moduled: 0

=== STRATEGY UPDATE ===
strategy.md exists: True, size: 16,835 bytes

=== CORTEX PERSIST ===
all traces persisted

=== FULL PIPELINE: PASS ===
```

## Method Name Reference (Verified Live)

| Module | Correct Method | Wrong Assumption | Error if Wrong |
|--------|---------------|------------------|----------------|
| Tracer | `record_call(tool_name, model_used, input_data, output_data, execution_time_ms, status, ...)` | `record_tool_call` | `AttributeError` |
| Analyzer | `analyze_traces(traces)` | `analyze_recent_traces(hours=24)` | `AttributeError` |
| Synthesizer | `generate_tips(patterns)` | `synthesize_from_patterns` | `AttributeError` |
| Graduator | `record_application(tip_id: str, success: bool)` | `evaluate_tip(tip)` or `record_application(tip, success=True, context='...')` | `TypeError` |

## Hook Fix Verification

Current signature in `~/.hermes/plugins/distillation/__init__.py`:
```python
def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                        status: str = "", error: str = "", **kwargs) -> Optional[dict]:
```

**Confirmed working**: `**kwargs` + default params prevent `TypeError` when Hermes core passes unexpected kwargs (`task_id`, `session_id`, `tool_call_id`, `duration_ms`).

## Quick Health Check Commands

```bash
# Live capture status (tool_intelligence.db)
python3 -c "
import sqlite3, time
conn = sqlite3.connect('/Users/dannygomez/.hermes/tool_intelligence.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM tool_calls WHERE timestamp > ?', (time.time()-86400,))
print('live calls 24h:', c.fetchone()[0])
c.execute('SELECT tool_name, timestamp FROM tool_calls ORDER BY timestamp DESC LIMIT 3')
for row in c.fetchall():
    from datetime import datetime
    print(f'  {row[0]}: {datetime.fromtimestamp(row[1]).strftime(\"%H:%M:%S\")}')
conn.close()
"

# Cerebrum sync status (may be stale — check both)
python3 -c "
import sqlite3
conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
c = conn.cursor()
c.execute(\"SELECT COUNT(*) FROM tool_call_log WHERE created_at > datetime('now', '-24 hours')\")
print('cerebrum calls 24h:', c.fetchone()[0])
c.execute(\"SELECT COUNT(*) FROM distilled_tips WHERE created_at > datetime('now', '-24 hours')\")
print('new tips 24h:', c.fetchone()[0])
conn.close()
"
```
