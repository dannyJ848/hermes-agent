# Unified Context System — May 6, 2026 Session

## What Was Built

Complete unified context system for instant CLI handoff and live session tracking.

## Files Created

| File | Purpose |
|------|---------|
| `~/.hermes/unified_context.db` | Central SQLite database with all context |
| `hermes_cli/instant_context.py` | New CLI startup — shows everything at once |
| `hermes_cli/context_updater.py` | Live updates during sessions |
| `setup_unified_context.py` | One-time database setup script |

## Database Schema

### cli_context
```sql
CREATE TABLE cli_context (
    key TEXT PRIMARY KEY,
    category TEXT,
    value TEXT,
    priority INTEGER DEFAULT 5,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Priority 1 = critical (training PID, branch, judge status)
Priority 2-5 = decreasing importance

### tool_intelligence_snapshot
```sql
CREATE TABLE tool_intelligence_snapshot (
    tool_name TEXT PRIMARY KEY,
    success_rate REAL,
    total_calls INTEGER,
    avg_latency_ms REAL,
    circuit_state TEXT,  -- 'OPEN' or 'CLOSED'
    last_failure TEXT,
    recommendation TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### session_continuity
```sql
CREATE TABLE session_continuity (
    session_id TEXT PRIMARY KEY,
    start_time TIMESTAMP,
    last_activity TIMESTAMP,
    active_tasks TEXT,     -- JSON array
    decisions_made TEXT,   -- JSON array
    files_modified TEXT,   -- JSON array
    status TEXT
);
```

### error_registry
```sql
CREATE TABLE error_registry (
    signature TEXT PRIMARY KEY,
    tool_name TEXT,
    root_cause TEXT,
    fix TEXT,
    occurrences INTEGER DEFAULT 1,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP
);
```

## Usage

### New CLI Session Startup
```bash
python3 hermes_cli/instant_context.py
```

Output:
```
[CRITICAL]
  training_step: 220/4000 (5.5%)
  training_status: running - healthy
  training_loss: 2.087 (CE:1.764 D:1.504 SAE:0.604)
  training_gpu: 85.3GB / 130GB
  branch: qwen27b-training-artifacts-may3-2026
  deepseek_judge: deepseek-v4-pro active

[TOOL INTELLIGENCE — ROUTE AROUND WEAK]
  ✓ web_search: 96% (300 calls)
  ✓ browser_console: 95% (100 calls)
  ✓ web_extract: 94% (200 calls)
  ✓ execute_code: 93% (600 calls)
  ✓ write_file: 87% (500 calls)
  ✗ AVOID patch: 59% (402 calls)
  ✗ AVOID skill_manage: 51% (380 calls)
  ✗ AVOID cronjob: 13% (31 calls)

[RECENT ERRORS — LEARN FROM]
  ! execute_code: unterminated string literal → Escape quotes or use write_file
  ! execute_code: IndentationError → Use write_file for multi-line code
  ! patch: old_string identical → Verify uniqueness

[ACTIVE SESSION]
  Session: session_20260506_134119
  Tasks: Qwen 27B training restart, Hermes source enhancement, Self-improvement cycle
  → Use write_file over patch
  → Centralize subconscious
  → Build loop guard
```

### Live Updates During Session
```python
from hermes_cli.context_updater import ContextUpdater
updater = ContextUpdater()

# After tool call
updater.update_tool_result('write_file', success=True, latency_ms=150)

# After error
updater.record_error('patch', 'identical strings', 'Use write_file instead')

# After task/decision
updater.update_session('session_id', task='new task', decision='use X over Y')

# Set arbitrary context
updater.set_context('new_key', 'new_value', priority=1)
```

## Key Design Decisions

1. **SQLite over JSON** — Queryable, transactional, handles concurrent access
2. **Snapshots over logs** — Current state is what matters for handoff, not full history
3. **Priority system** — Critical info (training PID) surfaces first
4. **Circuit breaker states** — Tools marked OPEN/closed for instant routing decisions
5. **Error signatures** — Pattern matching for recurring errors, not just raw messages
6. **Session continuity** — Tasks, decisions, files all tracked for context preservation

## Practice Run Results

All systems tested and working:
- instant_context.py: ✓ Shows full context in 1 command
- context_updater.py: ✓ Updates all tables correctly
- Database: ✓ All 4 tables populated with real data
- Training status: ✓ Updated from step 0 to step 220 during session

## Commit

`15b76e55a` in `qwen27b-training-artifacts-may3-2026`
