# DB Path Migration Reference

## Problem

After migrating cognitive systems from `~/subconscious/` into `~/hermes-agent/agent/`, some modules retain hardcoded DB paths pointing to `~/hermes-agent/*.db` instead of `~/.hermes/*.db`.

## Root Cause

During migration, standalone scripts used paths relative to their development directory (`~/hermes-agent/` or `~/subconscious/`). The integrated Hermes codebase uses `~/.hermes/` as the canonical data directory via `get_hermes_home()`.

## Affected Patterns

| Wrong Path | Correct Path | Files Found (May 2026) |
|------------|------------|------------------------|
| `~/hermes-agent/tool_capability.db` | `~/.hermes/tool_capability.db` | `agent/tool_misuse_prevention.py`, `agent/brain_to_toolintel.py`, `agent/agent_scorecard.py` |
| `~/hermes-agent/skill_rewards.db` | `~/.hermes/skill_rewards.db` | `agent/tip_system/impact_analyzer.py` |
| `~/hermes-agent/knowledge_compiler.db` | `~/.hermes/knowledge_compiler.db` | `agent/knowledge_compiler.py`, `agent/save_finding.py` |
| `~/hermes-agent/memory_consolidation.db` | `~/.hermes/memory_consolidation.db` | `agent/memory_consolidation.py` |
| `~/hermes-agent/self_eval.db` | `~/.hermes/self_eval.db` | `agent/self_eval_loop.py` |
| `~/hermes-agent/tool_sequences.db` | `~/.hermes/tool_sequences.db` | `agent/tool_sequences.py` |
| `~/hermes-agent/training_gym.db` | `~/.hermes/training_gym.db` | `agent/training_gym.py` |
| `~/hermes-agent/tip_decay_snapshots.db` | `~/.hermes/tip_decay_snapshots.db` | `agent/tip_system/decay_monitor.py` |
| `~/hermes-agent/tool_stats.db` | `~/.hermes/tool_stats.db` | `agent/tip_system/condition_rewriter.py` |

## Detection

```bash
# Find all wrong paths in agent/
grep -r "hermes-agent.*\.db" ~/hermes-agent/agent/*.py ~/hermes-agent/agent/tip_system/*.py 2>/dev/null | grep -v ".pyc"
```

## Fix Pattern

Replace three common patterns:

```python
# Pattern 1: Path.home() / "hermes-agent" / "*.db"
Path.home() / ".hermes" / "*.db"

# Pattern 2: os.path.expanduser("~/hermes-agent/.../*.db")
os.path.expanduser("~/.hermes/*.db")

# Pattern 3: str(Path.home() / "hermes-agent" / "*.db")
str(Path.home() / ".hermes" / "*.db")
```

## Data Migration

If the old DB has data that needs preserving:

```python
import sqlite3, shutil

old_db = os.path.expanduser("~/subconscious/tool_capability.db")
new_db = os.path.expanduser("~/.hermes/tool_capability.db")

# Backup
shutil.copy2(new_db, new_db + ".backup")

# Migrate table by table
old_conn = sqlite3.connect(old_db)
new_conn = sqlite3.connect(new_db)
# ... INSERT from old to new ...
```

## Verification

```bash
# Check DB exists in correct location
ls -la ~/.hermes/*.db

# Check schema and row counts
source ~/hermes-agent/venv/bin/activate && python3 -c "
import sqlite3, os
db = os.path.expanduser('~/.hermes/tool_capability.db')
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
for (t,) in c.fetchall():
    c.execute(f'SELECT COUNT(*) FROM {t}')
    print(f'{t}: {c.fetchone()[0]} rows')
"
```
