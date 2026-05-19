# DGX Iteration Pipeline Fix: Distillation Daemon Stuck (May 14, 2026)

## Problem

The distillation daemon was running but producing ZERO new tips for 2+ hours.

**Root cause:** 238 of 247 experiences had NO lessons extracted. The daemon filters for `frequency >= 3 AND lesson != ''`, so only 7 experiences qualified. All 7 were already processed at startup.

**Why lessons were missing:**
- Learning system only extracted lessons from failures/regressions
- 240 of 247 experiences had `result='success'`
- Success experiences never got lessons → never distilled → no tips

## The Fix

### 1. Backfill Missing Lessons

Extract lessons from ALL experiences (successes AND failures):

```python
def backfill_missing_lessons():
    """Extract lessons for experiences that don't have them."""
    conn = sqlite3.connect(str(DB_PATH), timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    
    cursor = conn.execute(
        """SELECT id, action_type, result, error_pattern, action_detail
           FROM experiences 
           WHERE lesson = '' OR lesson IS NULL"""
    )
    
    updated = 0
    for row in cursor.fetchall():
        exp_id, action_type, result, error_pattern, action_detail = row
        
        if result == 'regression' or error_pattern:
            lesson = extract_lesson_from_failure(action_type, error_pattern, result)
        else:
            lesson = extract_lesson_from_success(action_type, action_detail, result)
        
        if lesson:
            conn.execute(
                "UPDATE experiences SET lesson = ? WHERE id = ?",
                (lesson, exp_id)
            )
            updated += 1
    
    conn.commit()
    conn.close()
    return updated
```

### 2. Success-Pattern Lesson Extraction

Heuristic-based lessons for common tools:

```python
def extract_lesson_from_success(action_type, action_detail, result):
    lessons = {
        'terminal': 'Use terminal for shell commands, builds, git. Set timeout=300+ for long tasks.',
        'execute_code': 'Use execute_code for Python scripts with 3+ tool calls. Print final result.',
        'skill_view': 'Load skills proactively with skill_view(name) before matching tasks.',
        'skill_manage': 'Save successful workflows as skills. Patch existing skills when pitfalls found.',
        'read_file': 'Use read_file instead of cat/head/tail. Use offset/limit for large files.',
        'write_file': 'Use write_file instead of echo/heredoc. Auto-runs syntax checks.',
        'patch': 'Use patch for targeted edits. Include enough context for uniqueness.',
        'search_files': 'Use search_files instead of grep/find. Use target=files for directory listing.',
        'delegate_task': 'Delegate reasoning-heavy subtasks. Provide full context.',
        'delegate_with_model': 'Use cheap models for simple tasks. Route code to qwen-coder-free.',
        'web_search': 'Use web_search for current info, fact verification.',
        'web_extract': 'Use web_extract for articles, docs. Use max_chars to limit output.',
        'browser_navigate': 'Use browser_navigate first, then click/type/scroll.',
        'memory': 'Save user preferences, environment facts, tool quirks to memory.',
        'learn_from_interaction': 'Call after delegation, research, or non-trivial tool use.',
        'status_check': 'Call status_check FIRST every session. Free - shows bridge, costs, cron.',
        'cost_check': 'Check cost_check BEFORE expensive operations.',
    }
    return lessons.get(action_type, f'{action_type} worked successfully - note pattern for reuse')
```

### 3. Lower Frequency Threshold

Changed from `freq >= 3` to `freq >= 2`:

```python
def distill_experiences(min_freq=2):  # Was 3
    cursor = conn.execute(
        """SELECT action_type, result, lesson, frequency, action_detail
           FROM experiences 
           WHERE frequency >= ? AND lesson != '' AND lesson IS NOT NULL
           ORDER BY frequency DESC""",
        (min_freq,)
    )
```

## Results

| Metric | Before | After |
|--------|--------|-------|
| Experiences with lessons | 9 | 247 (+238) |
| Distilled tips | 7 | 59 (+52) |
| Daemon status | Stuck | Running |

## Updated Daemon Script

Location: `/data/SpecForge/hermes-agent/scripts/dgx_distillation_daemon.py`

Key changes:
1. `backfill_missing_lessons()` runs on startup
2. `extract_lesson_from_success()` for success patterns
3. `min_freq=2` instead of 3
4. Auto-distills every 5 minutes
5. Exports training data hourly to `/data/SpecForge/custom_dflash/datasets/hermes_sessions/`

## Verification

```bash
# Check daemon status
sudo systemctl status dgx-learning

# Check tip count
cd /data/SpecForge/hermes-agent
venv/bin/python -c "
import sqlite3
from pathlib import Path
conn = sqlite3.connect(str(Path.home() / '.hermes' / 'cerebrum_memory.db'))
print(f'Experiences with lessons: {conn.execute(\"SELECT COUNT(*) FROM experiences WHERE lesson != \'\'\").fetchone()[0]}')
print(f'Distilled tips: {conn.execute(\"SELECT COUNT(*) FROM distilled_tips\").fetchone()[0]}')
"
```

## Key Insight

**A learning system that only learns from failures is blind to 97% of experiences.** Success patterns are equally valuable - they tell you what WORKS, not just what to avoid.
