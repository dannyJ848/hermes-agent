# Cron Database Corruption Recovery (May 13, 2026)

## Symptom
```
Cron database corrupted and unrepairable: Expecting ',' delimiter: line 171 column 103 (char 9387)
```

All cron operations fail — list, create, remove, etc.

## Root Cause
A job prompt contains nested quotes that break JSON parsing:
```json
"prompt": "Run Evey's integrated brain cycle. Execute: cd ~/hermes-agent && venv/bin/python -c \"from agent.brain import ParallelBrain; ParallelBrain().run_cycle()\". This runs..."
```

The `"from agent.brain` inner quotes aren't escaped, corrupting the JSON structure.

## Recovery Steps

### 1. Restore from backup
```bash
cp ~/.hermes/cron/jobs.json.backup ~/.hermes/cron/jobs.json
```

### 2. If backup also corrupt, fix manually
```python
with open('/Users/dannygomez/.hermes/cron/jobs.json', 'r') as f:
    content = f.read()

# Find the problematic area
pos = 9387  # from error message
print(repr(content[pos-50:pos+50]))

# Fix: replace nested quotes with escaped versions or simplify
old = 'python -c \"from agent.brain import ParallelBrain; ParallelBrain().run_cycle()\"'
new = 'python -c \\\"from agent.brain import ParallelBrain; ParallelBrain().run_cycle()\\\"'
content = content.replace(old, new)

with open('/Users/dannygomez/.hermes/cron/jobs.json', 'w') as f:
    f.write(content)
```

### 3. Verify JSON is valid
```python
import json
with open('/Users/dannygomez/.hermes/cron/jobs.json') as f:
    data = json.load(f)
print(f"Valid: {len(data['jobs'])} jobs")
```

### 4. Prevention
When creating cron jobs via `cronjob(action='create')`, avoid prompts with:
- Shell commands containing `"` quotes
- Complex multi-line strings
- Unescaped backslashes

**Workaround:** Put complex logic in a shell script file, then reference it:
```bash
# Create script
echo '#!/bin/bash\npython3 -c "from agent.brain import ParallelBrain; ParallelBrain().run_cycle()"' > ~/brain_cycle.sh
chmod +x ~/brain_cycle.sh

# Cron prompt becomes simple:
# "Run brain cycle: bash ~/brain_cycle.sh"
```
