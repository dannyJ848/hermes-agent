# DeepSeek API Key Missing — Flywheel Hang Incident (2026-05-03)

## Symptom
- Flywheel eval cycles show `status=running` for hours, never complete
- `cortex_flywheel.run_eval_sweep()` hangs even with 1 pair
- LLM judge calls timeout after 15s+ per call
- 14+ cycles stuck in "running" state

## Root Cause
`DEEPSEEK_API_KEY` was present in `~/.hermes/.env` but NOT loaded into environment variables. The `llm_judge.py` module reads the key from `.env`, but daemon processes (scheduler, cortex_daemon) didn't inherit it. API calls to DeepSeek returned 401/auth errors, causing indefinite retries/timeouts.

## Fix

### 1. Find the key
```bash
grep DEEPSEEK_API_KEY ~/.hermes/.env
# Output: DEEPSEEK_API_KEY=sk-7ab7950...
```

### 2. Export before starting any daemon
```bash
export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)
```

### 3. Kill all stuck cycles
```python
import psycopg2
conn = psycopg2.connect('postgresql://hindsight:hindsight@localhost:5432/cortex')
cur = conn.cursor()
cur.execute("UPDATE cortex_flywheel SET status = 'killed' WHERE status = 'running'")
print(f"Killed {cur.rowcount} stuck cycles")
conn.commit()
conn.close()
```

### 4. Restart scheduler with key exported
```bash
export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)
cd ~/hermes-agent && source venv/bin/activate && python3 /tmp/hermes_scheduler_daemon.py
```

## Verification
Test LLM judge directly:
```bash
export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)
cd ~/subconscious && python3 -c "
from llm_judge import LLMJudge
judge = LLMJudge()
result = judge.compare_tips('Use list comprehensions.', 'Use for loops.')
print(f'Winner: {result[\"winner\"]}, Confidence: {result[\"confidence\"]}')
"
```

## Prevention
- Always check `env | grep DEEPSEEK_API_KEY` before starting flywheel
- The daemon wrapper MUST export the key before importing llm_judge
- Consider adding `os.environ['DEEPSEEK_API_KEY'] = ...` at top of `cortex_daemon.py`

## Performance Note
DeepSeek v4 Pro API calls take ~15s each. The flywheel does them sequentially.
- 1 pair: ~27s (works)
- 2 pairs: ~30s (works)
- 3+ pairs: >120s (times out)

**Recommendation:** Use `use_llm_every=50` (heuristic for 98% of evals, DeepSeek spot-check for 2%). This keeps bulk evals fast while maintaining quality calibration.
