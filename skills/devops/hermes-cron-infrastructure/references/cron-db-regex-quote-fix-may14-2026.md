# Cron Database Corruption: Regex-Based Quote Fixing

## Problem

Cron job prompts containing unescaped double quotes inside JSON strings corrupt the `~/.hermes/cron/jobs.json` file. This happens when prompts contain shell commands with quoted arguments, e.g.:

```json
{"prompt": "Run Evey's integrated brain cycle. Execute: cd ~/hermes-agent && venv/bin/python -c \"from agent.brain import ParallelBrain; ParallelBrain().run_cycle()\"."}
```

The nested `"` breaks the JSON parser with:
```
json.decoder.JSONDecodeError: Expecting ',' delimiter: line 202 column 103 (char 10545)
```

## Detection

```bash
python3 -c "import json; json.load(open('/Users/dannygomez/.hermes/cron/jobs.json')); print('JSON valid')"
```

If this raises `JSONDecodeError`, the DB is corrupted.

## Root Cause Analysis

Find all lines with unescaped quotes in prompt fields:
```bash
python3 -c "
import json
with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    content = f.read()
lines = content.split('\n')
for i, line in enumerate(lines):
    if '\"prompt\":' in line and line.count('\"') > 4:
        print(f'Line {i+1}: {line[:150]}')
"
```

## Fix: Regex-Based Bulk Replacement (May 14, 2026)

The most reliable fix for multiple corrupted prompts is regex replacement:

```python
import json, re

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    content = f.read()

# Replace python -c \"...\" with python -c '...'
# This handles the most common case: shell commands in prompts
content = re.sub(r'python3? -c \\\"(.*?)\\\"', r"python -c '\1'", content)

# Write back
with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    f.write(content)

# Verify
json.loads(content)
print('Fixed and validated')
```

## Alternative Fixes (in order of preference)

### 1. Restore from backup (fastest)
```bash
cp /Users/dannygomez/.hermes/cron/jobs.json.backup /Users/dannygomez/.hermes/cron/jobs.json
```

### 2. Manual line-by-line fix (for single corrupted job)
```python
import json

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    content = f.read()

lines = content.split('\n')
for i, line in enumerate(lines):
    if 'brain-cycle-alpha' in line:  # or whatever job name
        # Fix next line (the prompt line)
        prompt_line = lines[i+1]
        fixed = prompt_line.replace('\"from agent.brain', "'from agent.brain").replace('run_cycle()\"', "run_cycle()'")
        lines[i+1] = fixed
        break

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    f.write('\n'.join(lines))
```

### 3. JSON repair library (for complex corruption)
```bash
pip install json-repair
python3 -c "
from json_repair import repair_json
import json

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    raw = f.read()

fixed = repair_json(raw)
data = json.loads(fixed)

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)
"
```

## Prevention

1. **Escape nested quotes when creating cron jobs:**
   ```python
   # Before writing prompt to jobs.json, escape nested quotes
   safe_prompt = prompt.replace('"', '\\"')
   ```

2. **Use single quotes in shell commands:**
   ```bash
   # BAD: python -c "from agent.brain import run_cycle()"
   # GOOD: python -c 'from agent.brain import run_cycle()'
   ```

3. **Validate JSON after every cron creation:**
   ```python
   import json
   json.load(open('/Users/dannygomez/.hermes/cron/jobs.json'))
   ```

4. **Keep backups:**
   ```bash
   cp /Users/dannygomez/.hermes/cron/jobs.json /Users/dannygomez/.hermes/cron/jobs.json.backup
   ```

## Related

- See `references/cron-database-corruption-recovery-may13-2026.md` for the general corruption recovery pattern
- See `references/unified-daemon-manual-triggers-pattern.md` for replacing cron with daemons entirely
