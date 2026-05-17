# Hermes Upstream Sync Check

Quick workflow to check if your Hermes fork is behind upstream.

## Prerequisites

Your fork must have upstream configured:
```bash
cd ~/hermes-agent
git remote add upstream https://github.com/NousResearch/hermes-agent.git
```

Verify:
```bash
git remote -v
# Should show: upstream  https://github.com/NousResearch/hermes-agent.git (fetch)
```

## One-Liner Sync Check

```bash
cd ~/hermes-agent && git fetch upstream main 2>&1 && echo "---COMMITS BEHIND---" && git log --oneline HEAD..upstream/main | head -20
```

## Detailed Diff Stats

```bash
cd ~/hermes-agent && git diff HEAD..upstream/main --stat | tail -20
```

## Critical Files to Check

```bash
# Core agent loop changes
git diff HEAD..upstream/main -- run_agent.py | head -50

# CLI changes
git diff HEAD..upstream/main -- cli.py | head -50

# Tool registry changes
git diff HEAD..upstream/main -- tools/registry.py | head -50
```

## What to Look For

**High-priority upstream fixes:**
- `fix(cache)` — context/prompt caching issues
- `fix(gateway)` — messaging platform stability
- `fix(agent)` — core loop bugs
- `fix(cli)` — command-line issues
- `feat(providers)` — new model providers or renamed ones

**Danger signs (merge ASAP):**
- Changes to `run_agent.py` main loop
- Changes to tool dispatch (`model_tools.py`)
- Security fixes (`fix(approval)`, `fix(security)`)
- Breaking changes in config format

## Safe Merge Strategy

```bash
cd ~/hermes-agent

# 1. Stash your changes
git stash

# 2. Fetch and merge
git fetch upstream
git merge upstream/main

# 3. Resolve conflicts (if any)
# - Prefer upstream for core files (run_agent.py, cli.py)
# - Keep your changes for cognitive systems (agent/brain.py, etc.)

# 4. Test
cd ~/hermes-agent && source venv/bin/activate && python3 -c "import run_agent"

# 5. Restart Hermes
```

## Post-Merge Verification

```bash
# Check your cognitive modules still import
python3 -c "
import sys
sys.path.insert(0, '.')
from agent.iteration_engine import IterationEngine
from agent.cortex_learning import get_learning_engine
print('Core cognitive modules OK')
"

# Check tool registration
python3 -c "
import sys
sys.path.insert(0, '.')
from tools.registry import registry
print(f'Tools registered: {len(registry._tools)}')
"
```

## Automation

Add to your daily cron or daemon:
```bash
#!/bin/bash
cd ~/hermes-agent
BEHIND=$(git rev-list HEAD..upstream/main --count 2>/dev/null || echo "?")
if [ "$BEHIND" -gt 10 ]; then
    echo "WARNING: $BEHIND commits behind upstream"
    # Send notification via hermes gateway or log
fi
```
