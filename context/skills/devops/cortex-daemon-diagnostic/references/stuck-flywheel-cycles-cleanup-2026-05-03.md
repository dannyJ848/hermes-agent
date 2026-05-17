# Stuck Flywheel Cycles Cleanup — May 3, 2026

## Problem
The Cortex flywheel had 14 cycles stuck in "running" state, some for 18+ days (since April 15). These blocked new cycles from starting due to database contention.

## Detection
```bash
# Check for stuck cycles
psql -d cortex -U hindsight -c "
  SELECT status, COUNT(*), MIN(started_at), MAX(started_at) 
  FROM cortex_flywheel 
  GROUP BY status
"
```

## Root Cause
When `run_eval_sweep()` hangs (e.g., DeepSeek API unavailable), the cycle never completes. New cycles check for existing "running" cycles and wait indefinitely.

## Fix
Kill all stuck "running" cycles:
```bash
psql -d cortex -U hindsight -c "
  UPDATE cortex_flywheel 
  SET status = 'killed' 
  WHERE status = 'running'
"
```

## Prevention
1. Set `use_llm_every=50` in daemon config — only 2% of evals use LLM judge
2. Export `DEEPSEEK_API_KEY` before starting daemon
3. Add timeout to `run_eval_sweep()` (e.g., max 300s per cycle)
4. Monitor `cortex_flywheel` table for cycles stuck >1 hour

## Verification After Fix
```bash
# Test with small sweep
python3 -c "from cortex_flywheel import CortexFlywheel; fw = CortexFlywheel(); print(fw.run_eval_sweep(num_pairs=2, use_llm_every=1))"
# Should return: {'status': 'completed', 'pairs_evaluated': 2, 'llm_calls': 2, 'duration_ms': ~30000}
```

## DeepSeek API Key Pattern
Key is stored in `~/.hermes/.env` but must be exported before daemon starts:
```bash
export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)
```
