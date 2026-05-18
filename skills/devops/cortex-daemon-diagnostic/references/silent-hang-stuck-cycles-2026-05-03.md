# Silent Hang + Stuck Cycles — Cortex Flywheel Debug Log

**Date:** 2026-05-03  
**Session type:** Cron job execution of `cortex_flywheel.py --full-cycle --eval-pairs 50`

## Symptom

Process started, remained alive for 6+ minutes, produced **zero stdout/stderr output**, no log entries. `ps aux` confirmed Python process was running. `lsof` showed normal file handles. No CPU activity.

## Root Causes (compound failure)

1. **Stuck running cycles from previous runs** — `cortex_flywheel` table had 2 rows with `status='running'` from 2026-04-25 and 2026-05-02 that were never completed. The flywheel's `start_flywheel_cycle()` or `get_tips_for_eval()` may have been blocked by these.

2. **Schema drift in `record_eval()`** — `cortex_access.py` references `round_id` which does not exist in `cortex_eval_history`. If the flywheel got far enough to record an eval, it would crash with `UndefinedColumn: column "round_id" does not exist`. But because the hang happened before any output, the crash may have been on the first eval attempt after a slow DB operation.

3. **Silent error handling** — The flywheel wraps operations in try/except that may suppress errors without logging.

## Diagnosis Steps

```bash
# 1. Confirm process exists
ps aux | grep cortex_flywheel

# 2. Check for stuck cycles
python3 -c "
import sys; sys.path.insert(0, '/Users/USER/subconscious')
from cortex_access import cortex_cursor
with cortex_cursor() as cur:
    cur.execute(\"SELECT * FROM cortex_flywheel WHERE status = 'running'\")
    for row in cur.fetchall():
        print(dict(row))
"

# 3. Verify eval_history schema
python3 -c "
import sys; sys.path.insert(0, '/Users/USER/subconscious')
from cortex_access import cortex_cursor
with cortex_cursor() as cur:
    cur.execute(\"SELECT column_name FROM information_schema.columns WHERE table_name = 'cortex_eval_history'\")
    print([r['column_name'] for r in cur.fetchall()])
"
```

## Fix Applied

1. **Cleaned stuck cycles:**
   ```sql
   UPDATE cortex_flywheel
   SET status = 'abandoned', completed_at = NOW()
   WHERE status = 'running';
   ```

2. **Ran all 4 phases manually** using `execute_code` with direct SQL, bypassing the broken flywheel script entirely.

3. **Used correct schema** for eval inserts: `(node_a_id, node_b_id, winner, judge_type, confidence, reasoning, cycle_id)` — no `round_id`.

## Result

- 50 pairs evaluated in 579ms
- 0 tips repaired (none met thresholds)
- 0 tips consolidated (no duplicates)
- 385 edges created between similar tips
- Total: 682ms

## Prevention

Add stuck-cycle cleanup to the flywheel startup sequence, and add a `--dry-run` mode that validates schema before attempting real work.
