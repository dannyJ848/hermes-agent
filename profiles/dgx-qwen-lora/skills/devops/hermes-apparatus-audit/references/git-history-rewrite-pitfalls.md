# Pitfall: Git History Rewrite Reverts Interactive Fixes

## Problem

After using `git filter-branch` to remove large files/secrets from history, and then cherry-picking or soft-resetting to rebuild a clean commit, **interactive-only fixes can be lost**.

## What Happened (2026-05-18)

1. `agent/cognitive_systems_plugin.py` was interactively rewritten with correct class names
2. `git filter-branch` removed secrets from history
3. `git reset --soft origin/main` + cherry-pick rebuilt the commit
4. The cherry-pick pulled the OLD version of `cognitive_systems_plugin.py` from the pre-filter commit
5. Result: The file reverted to broken class names (`AgentScorecard`, `ToolHealthMonitor`, `ErrorMiner`, etc.)

## Prevention

**Always commit fixes BEFORE any history rewrite.**

```bash
# WRONG order:
git filter-branch --index-filter '...'   # rewrites history
# ... now try to recover your fixes from the old branch — fragile

# CORRECT order:
git add agent/cognitive_systems_plugin.py
git commit -m "fix: correct cognitive system class names"
git filter-branch --index-filter '...'   # your fix is now in the rewritten history
```

## Detection

After any history rewrite, verify critical files:

```bash
# Check that your fixes survived
git diff HEAD~1 -- agent/cognitive_systems_plugin.py
# Should show the corrected imports, not the old broken ones

# Quick smoke test
python -c "import agent.cognitive_systems_plugin as csp; print(dir(csp))"
```

## Recovery (If Already Lost)

If fixes were lost during rewrite:

```bash
# Find the fix in reflog
git reflog | grep "cognitive\|class\|fix"

# Extract the good version
git show <ref>:agent/cognitive_systems_plugin.py > /tmp/fixed.py

# Apply to current tree
cp /tmp/fixed.py agent/cognitive_systems_plugin.py
git add agent/cognitive_systems_plugin.py
git commit --amend --no-edit
```

## Related

- `session-2026-05-18-class-name-mismatches.md` — the actual class name fixes that were lost
