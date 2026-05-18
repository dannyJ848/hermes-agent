# DeepSeek API Key Location Pattern

## Where the key is stored

The `DEEPSEEK_API_KEY` is stored in `~/.hermes/.env` (not in shell configs like `.zshrc` or `.bashrc`).

Format:
```
DEEPSEEK_API_KEY=sk-7ab7950...
```

## How to load it

```bash
# Export from .env file
export DEEPSEEK_API_KEY=$(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)

# Verify it's set
echo "Key: ${DEEPSEEK_API_KEY:0:15}..."

# Test API
curl -s https://api.deepseek.com/v1/models -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

## Why this matters for daemons

- The `llm_judge.py` loads `.env` at import time, but daemon processes started via `nohup` or background jobs may not inherit the parent's environment
- Always export `DEEPSEEK_API_KEY` before starting the cortex daemon or scheduler daemon
- The `cortex_daemon.py` does NOT load `.env` — it relies on the environment variable being set

## Common failure mode

If `DEEPSEEK_API_KEY` is not set:
- `llm_judge.compare_tips()` hangs for 15+ seconds per call (timeout on auth retry)
- Flywheel eval cycles never complete (stuck in `status='running'`)
- 14+ cycles accumulate as "running" but never finish
- Daemon appears alive but makes no progress

## Fix for stuck cycles after key is loaded

```python
import psycopg2
conn = psycopg2.connect('postgresql://hindsight:hindsight@localhost:5432/cortex')
cur = conn.cursor()
cur.execute("UPDATE cortex_flywheel SET status = 'killed' WHERE status = 'running'")
print(f'Killed {cur.rowcount} stuck cycles')
conn.commit()
conn.close()
```

## Performance note

- DeepSeek v4 Pro API calls take ~15 seconds per tip comparison
- Sequential judging of 50 pairs = ~750 seconds (12+ minutes)
- Use `use_llm_every=50` in flywheel config so only 2% of evals use LLM (spot-checks)
- Heuristic judging takes <1 second per pair
