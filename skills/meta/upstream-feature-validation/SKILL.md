---
name: upstream-feature-validation
version: 1.0
created: 2026-04-30
description: |
  Validate that features merged from upstream (origin/main) are actually operational
  in the local environment, not just present in the codebase. Covers: code presence
  check, gateway/runtime wiring verification, trigger logic validation, state file
  audit, and first-run simulation. Prevents "ghost features" — code that exists but
  never executes due to missing state, incompatible Python versions, or silent
  gating conditions.
triggers:
  - After merging a large upstream commit (e.g., 400+ commits from origin/main)
  - When a feature is mentioned in release notes but produces no observable effect
  - When checking if a newly merged subsystem (curator, daemon, new learning module) has ever run
  - When the user says "is X actually working?" about a recently merged feature
  - Before declaring a post-merge environment "fully integrated"
---

# Upstream Feature Validation

## Problem Class

After merging hundreds of commits from upstream, new features appear in the codebase
but may be **ghost features** — present but never executed due to:
- Missing state files (first-run never triggered)
- Gateway wiring exists but gating conditions never satisfied
- Python version incompatibility (e.g., `|` union syntax requires 3.10+)
- No data exists for the feature to process (empty tables, no agent-created skills)
- Silent `except Exception: pass` swallowing all errors

## The Validation Pattern

### Phase 0: Verify-Before-Apply (Diverged Forks)

When a fork has massively diverged from upstream (no merge base, thousands of conflicting files):

```bash
# DON'T cherry-pick blindly — every commit will conflict
# DO check if upstream changes are ALREADY in your fork

# Check specific patterns from upstream commits
for pattern in "grok-4.3" "deepseek-v4-pro" "trinity-large-thinking"; do
    grep -q "$pattern" hermes_cli/models.py && echo "✓ $pattern already present"
done

# Check if functions already exist
grep -n "_compression_threshold_for_model" agent/auxiliary_client.py  # ✓ present?
grep -n "update_mode" plugins/memory/hindsight/__init__.py            # ✓ present?
```

**Why this matters**: The user's fork often already contains upstream changes via manual patches, parallel development, or earlier cherry-picks. Blindly applying creates redundant work and risks overwriting custom modifications.

### Phase 1: Code Presence Check

```bash
# 1. Find the feature's code
find ~/hermes-agent/agent -name '*<feature>*' -type f

# 2. Check if module imports cleanly
python3 -c "from agent.<module> import <MainClass>" 2>&1

# 3. Check gateway/runtime wiring
grep -rn "<feature>\|maybe_run_<feature>" gateway/run.py run_agent.py
```

**Common finding**: Module exists but import fails due to Python version issues.
**Common finding**: Gateway calls `maybe_run_*()` but the function is gated and never returns True.

### Phase 2: State File Audit

```bash
# Check if the feature has persistent state
ls -la ~/.hermes/<feature>*/ 2>/dev/null
ls -la ~/.hermes/skills/.<feature>_state 2>/dev/null

# Read state if it exists
python3 -c "
import json
from pathlib import Path
state_file = Path.home() / '.hermes' / 'skills' / '.<feature>_state'
if state_file.exists():
    print(json.load(state_file.open()))
else:
    print('NEVER RUN')
"
```

**Critical finding**: State file missing = feature has never run, even if code exists.

### Phase 3: Trigger Logic Validation

```bash
# Check the feature's should-run logic
python3 -c "
from agent.<module> import should_run_now
print(f'should_run_now(): {should_run_now()}')
"
```

**If import fails due to Python version:**
```bash
# Check available Python versions
python3 --version  # System default
python3.12 --version 2>/dev/null || python3.11 --version 2>/dev/null || echo "No modern Python"

# Test with correct version
python3.12 -c "from agent.<module> import should_run_now; print(should_run_now())"
```

**Fake-state test** (verify trigger logic works):
```python
# Write a fake state showing last run was 8 days ago
from pathlib import Path
import json
from datetime import datetime, timezone, timedelta

state_file = Path.home() / '.hermes' / 'skills' / '.<feature>_state'
state_file.parent.mkdir(parents=True, exist_ok=True)
old_run = datetime.now(timezone.utc) - timedelta(days=8)
json.dump({'last_run_at': old_run.isoformat(), 'paused': False}, state_file.open('w'))

# Now test should_run_now()
python3.12 -c "from agent.<module> import should_run_now; print(should_run_now())"  # Should print True

# CLEAN UP: Remove fake state after test
state_file.unlink()
```

### Phase 4: Configuration Audit

```bash
# Check config for feature settings
python3 -c "
import yaml
from pathlib import Path
config = yaml.safe_load((Path.home() / '.hermes' / 'config.yaml').open())
feature_cfg = config.get('<feature>', {})
print(f'Enabled: {feature_cfg.get(\"enabled\", True)}')
print(f'Interval: {feature_cfg.get(\"interval_hours\", 168)} hours')
"
```

### Phase 5: Data Availability Check

```bash
# Check if there's anything for the feature to process
# For curator: count agent-created skills
python3 -c "
from pathlib import Path
skills_dir = Path.home() / '.hermes' / 'skills'
agent_created = sum(1 for d in skills_dir.iterdir() if d.is_dir() and 'agent_created: true' in (d/'SKILL.md').read_text())
print(f'Agent-created skills: {agent_created}')
"

# For learning modules: check DB tables
python3 -c "
import sqlite3
from pathlib import Path
db = sqlite3.connect(Path.home() / '.hermes' / 'cerebrum_memory.db')
cur = db.cursor()
cur.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
for row in cur.fetchall():
    count = cur.execute(f'SELECT COUNT(*) FROM {row[0]}').fetchone()[0]
    print(f'{row[0]}: {count} rows')
"
```

### Phase 6: Full Smoke Test

```bash
# Run the feature's full workflow if possible
# For curator: force a run with fake state and verify output
python3.12 -c "
from agent.curator import maybe_run_curator, load_state
# Fake state already written
result = maybe_run_curator(idle_for_seconds=float('inf'))
print(f'Result: {result}')
"
```

## Common Pitfalls

1. **Python version incompatibility**: `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` — the `|` union syntax requires Python 3.10+. The system default is 3.8 but 3.12 is available.
   → **Fix**: Always test imports with `python3.12` first, then fall back to `python3`.

2. **Missing state file = never run**: The feature's `should_run_now()` returns False because `last_run_at` is None.
   → **Fix**: Write fake state to verify trigger logic, then remove it.

3. **Empty data = silent no-op**: Curator has 0 agent-created skills, so even if it runs, it has nothing to do.
   → **Fix**: Create test data (fake agent-created skill) to verify the full workflow.

4. **Gateway poll rate vs actual interval**: `CURATOR_EVERY = 60` ticks means poll every hour, but the real interval is 7 days. The feature won't run for a week even though the gateway checks hourly.
   → **Fix**: Document this clearly; don't expect immediate execution.

5. **Config defaults vs explicit config**: Feature is enabled by default but user hasn't set any config. The feature should work with defaults.
   → **Fix**: Verify defaults are sensible and documented.

6. **Diverged fork with "already applied" upstream changes**: When a fork diverges massively from upstream, many upstream commits may already be present via parallel development or earlier manual patches. Blindly cherry-picking creates conflicts on files that already have the changes.
   → **Fix**: Use `grep` to verify patterns exist before attempting to apply. See Phase 0 above.
   → **Fix**: Skip low-value changes when risk exceeds benefit. Document what was skipped and why.

## Verification Checklist

- [ ] Feature code exists in expected location
- [ ] Module imports cleanly with correct Python version
- [ ] Gateway/runtime wiring exists and is reachable
- [ ] State file exists OR trigger logic can be validated with fake state
- [ ] Config is present (explicit or defaults)
- [ ] Feature has data to process OR can be tested with fake data
- [ ] Full workflow can be simulated end-to-end
- [ ] No silent `except Exception: pass` swallowing all errors
- [ ] Clean up fake state/test data after validation

## Files to Check

| File | What |
|------|------|
| `agent/<feature>.py` | Core module code |
| `gateway/run.py` | Gateway wiring (search for `maybe_run_*` or `CURATOR_EVERY`) |
| `~/.hermes/config.yaml` | Feature configuration |
| `~/.hermes/skills/.<feature>_state` | Persistent state file |
| `~/.hermes/logs/<feature>/` | Log directory |

## Example: Hermes Curator Validation

```bash
# 1. Code presence
find ~/hermes-agent/agent -name '*curator*' -type f
# → agent/curator.py

# 2. Import test (fails on 3.8, works on 3.12)
python3.12 -c "from agent.curator import CuratorOrchestrator; c=CuratorOrchestrator(); print('OK')"

# 3. State file check
ls -la ~/.hermes/skills/.curator_state  # → No such file

# 4. Config check
grep -A5 "curator:" ~/.hermes/config.yaml
# → enabled: true, interval_hours: 168

# 5. Trigger logic validation
# Write fake state (8 days ago)
python3 -c "
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
state = {'last_run_at': (datetime.now(timezone.utc) - timedelta(days=8)).isoformat(), 'paused': False}
Path('~/.hermes/skills/.curator_state').expanduser().write_text(json.dumps(state))
"
# Test
python3.12 -c "from agent.curator import should_run_now; print(should_run_now())"  # → True
# Clean up
rm ~/.hermes/skills/.curator_state

# 6. Data check
# 0 agent-created skills, 0 pinned — curator has nothing to curate

# CONCLUSION: Curator is fully operational but has never run due to:
#   - Fresh state (no previous run)
#   - 7-day interval gating
#   - No agent-created skills exist to curate
# It will auto-trigger after 7 days when conditions are met.
```
