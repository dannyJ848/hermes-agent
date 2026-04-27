# KIMI HARNESS ENHANCEMENT MANIFEST v2.3
## Background Self-Improvement Daemon

**Date:** 2026-04-26
**Status:** DEPLOYED

---

## WHAT CHANGED FROM v2.2

v2.2 predicted tool needs.
v2.3 **improves while idle** — runs background tasks between sessions.

---

## ARCHITECTURE

### Task Types

| Type | Trigger | Action |
|------|---------|--------|
| `review` | 2+ errors of same type in 24h | Extract lessons from error patterns |
| `research` | 3+ queries on same topic in 7d | Flag topic for deep research |
| `practice` | Tool success rate < 70% | Suggest practice exercises |
| `consolidate` | 10+ unused memories in 7d | Suggest memory cleanup |
| `skill_update` | New knowledge discovered | Update skill instructions |

### Cycle

1. **Generate tasks** → Scan Cortex for improvement opportunities
2. **Prioritize** → Score by urgency and impact
3. **Execute** → Run top-N tasks (default 3 per cycle)
4. **Record** → Store results in `improvement_tasks` table

---

## SCHEMA

```sql
CREATE TABLE improvement_tasks (
    id UUID PRIMARY KEY,
    task_type TEXT NOT NULL,
    priority FLOAT,
    description TEXT,
    context TEXT,
    status TEXT,  -- pending, in_progress, completed, failed
    result TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER
);

CREATE TABLE session_reviews (
    id UUID PRIMARY KEY,
    session_id TEXT,
    review_type TEXT,
    findings JSONB,
    created_at TIMESTAMP
);
```

---

## FILES

### New
- `agent/self_improvement_daemon.py` — Background improvement engine

---

## HOW IT WORKS

1. **Idle detected** → Daemon runs `run_daemon_cycle()`
2. **Scan Cortex** → Looks for errors, unused memories, weak tools
3. **Generate tasks** → Creates prioritized improvement tasks
4. **Execute** → Runs top tasks (review errors, flag research, etc.)
5. **Record** → Stores findings for next session

---

## INTEGRATION

Can be wired as:
- **Cron job** → Run every 5 minutes of idle time
- **Gateway hook** → Run on session end
- **Manual trigger** → `/improve` command

---

## FUTURE ENHANCEMENTS

1. **Auto-research** → Actually execute web_search for flagged topics
2. **Skill auto-update** → Rewrite skill files based on new knowledge
3. **Error auto-fix** → Apply known resolutions without human intervention
4. **Capability growth** → Learn new tools by watching successful usage
5. **Self-assessment** → Regular evaluation of overall performance

---

## TESTING

```python
from agent.self_improvement_daemon import SelfImprovementDaemon

daemon = SelfImprovementDaemon()

# Run one cycle
result = daemon.run_daemon_cycle(max_tasks=3)
print(f"Executed {result['tasks_executed']} tasks")

# Get report
report = daemon.get_improvement_report(days=7)
print(f"Total improvements: {report['total_tasks']}")
```
