# Cron + Flywheel Debug Session — May 3, 2026

## Incident Summary
During a comprehensive self-audit and optimization session, multiple infrastructure issues were discovered and fixed. This reference documents the debugging patterns and fixes.

## Issues Found & Fixed

### 1. Broken `cronjob` Tool Loop
- **Symptom:** `cronjob(action='list')` returned `{'error': "'id'", 'success': False}` repeatedly
- **Agent behavior:** Called the broken tool 3+ times without switching strategy
- **Root cause:** The `cronjob` tool has a bug where it expects an 'id' field that's missing
- **Fix:** Stop using the broken tool; read `~/.hermes/cron/jobs.json` directly
- **File:** `~/.hermes/cron/jobs.json` contains all job definitions

### 2. Scheduler Bug — `KeyError: 'id'`
- **Location:** `cron/jobs.py` line 845
- **Code:** `if rj["id"] == job["id"]:`
- **Fix:** `if rj.get("id") == job.get("id"):`
- **Impact:** Scheduler `tick()` couldn't run due to missing 'id' field on some jobs

### 3. Python Version Mismatch
- **System Python:** 3.8.8 (too old for `|` union syntax)
- **Venv Python:** 3.11.14 (correct)
- **Fix:** Always activate venv before running scheduler: `source venv/bin/activate`

### 4. DeepSeek API Key Not Loaded
- **Location:** `~/.hermes/.env` — `DEEPSEEK_API_KEY=sk-7ab7950...`
- **Problem:** Key exists in file but not in environment variable
- **Daemon impact:** LLM judge couldn't authenticate, causing flywheel cycles to hang
- **Fix:** Export before starting daemon: `export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)`
- **Verification:** `curl -s https://api.deepseek.com/v1/models -H "Authorization: Bearer $DEEPSEEK_API_KEY"`

### 5. Stuck Flywheel Cycles
- **Symptom:** 14 cycles in "running" state, some since April 15 (18+ days)
- **Impact:** New cycles couldn't start due to database contention
- **Fix:** Kill all stuck cycles: `UPDATE cortex_flywheel SET status = 'killed' WHERE status = 'running'`
- **Result:** 19 cycles killed, flywheel resumed

### 6. DeepSeek Timeout on Bulk Evals
- **Symptom:** 1-pair eval works (~27s), 3+ pairs timeout
- **Root cause:** Each DeepSeek API call takes ~15s, sequential execution
- **Fix:** Set `use_llm_every=50` in daemon config — only 2% of evals use LLM
- **File:** `cortex_daemon.py` line 99: `run_eval_sweep(num_pairs=50, use_llm_every=50)`

## Key Commands

```bash
# Check cron jobs directly
cat ~/.hermes/cron/jobs.json | python3 -m json.tool

# Kill all cron jobs (mass disable)
python3 -c "
import json
with open('/Users/dannygomez/.hermes/cron/jobs.json') as f:
    data = json.load(f)
for j in data['jobs']:
    j['enabled'] = False
    j['state'] = 'paused'
with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f)
"

# Start scheduler daemon
export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)
cd ~/hermes-agent && source venv/bin/activate
python3 /tmp/hermes_scheduler_daemon.py

# Kill stuck flywheel cycles
psql -d cortex -U hindsight -c "UPDATE cortex_flywheel SET status = 'killed' WHERE status = 'running'"

# Test flywheel eval
python3 -c "from cortex_flywheel import CortexFlywheel; fw = CortexFlywheel(); print(fw.run_eval_sweep(num_pairs=2, use_llm_every=1))"
```

## User Preference Signal
User prefers surgical precision: kill everything first, then selectively re-enable only what matters. When they see 42 cron jobs, they want them all dead immediately — no review, no nuance.
