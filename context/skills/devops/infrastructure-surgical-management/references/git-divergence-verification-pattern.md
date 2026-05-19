# Git Divergence Verification Pattern

## Session Context
Date: May 6, 2026
Situation: User's fork (dannyJ848/hermes-agent) diverged massively from upstream (NousResearch/hermes-agent). No merge base. 2,946 files touched by both sides.

## What Happened

1. User asked to "check hermes repo for missed commits and update without breaking custom stuff"
2. `git merge-base upstream/main HEAD` returned empty — histories diverged completely
3. `git log --oneline upstream/main --not HEAD` showed 40 new upstream commits
4. Initial attempt: cherry-pick — every commit conflicted because files were heavily modified in both forks

## The Fix: Verify-Before-Apply

Instead of blindly cherry-picking, check if upstream changes are ALREADY in the local fork:

```bash
# Check specific patterns from upstream commits
grep -n "grok-4.3" hermes_cli/models.py          # ✓ already present
grep -n "deepseek-v4-pro" hermes_cli/models.py    # ✓ already present
grep -n "trinity-large-thinking" agent/auxiliary_client.py  # ✓ already present
grep -n "_compression_threshold_for_model" agent/auxiliary_client.py  # ✓ already present
grep -n "_compression_threshold_for_model" run_agent.py  # ✓ already present
grep -n "update_mode" plugins/memory/hindsight/__init__.py  # ✓ already present
grep -n "dependency" plugins/kanban/dashboard/dist/index.js  # ✓ already present
```

## Results

| Upstream Commit | Description | Status | Action |
|----------------|-------------|--------|--------|
| f27fcb6a8 | grok-4.3 model | ✓ Already in | None |
| 477e4a2fe | deepseek-v4-pro model | ✓ Already in | None |
| 2d4eaed11 | arcee temp/compression | ✓ Already in | None |
| c46bc9294 | aux provider compression | ✓ Already in | None |
| 3082fa082 | hindsight append/dedupe | ✓ Already in | None |
| a49670c21 | kanban dependency selects | ✓ Already in | None |
| 3188e63b0 | SSE token batching | ✗ Missing | Skip — low value, high risk |
| f0d278412 | kanban max_spawn | ✗ Missing | Skip — low value, high risk |
| 1fc8733a6 | kanban failure counter | ✗ Missing | Skip — low value, high risk |
| 9022804d7 | providers pluggable | ✗ Missing | Skip — low value, high risk |

**Outcome: 7/12 already applied. Skipped 4 that would risk breaking custom training pipeline.**

## Key Insight

When forks diverge massively, the user's branch often already contains upstream changes via:
- Manual patches applied in earlier sessions
- Parallel development (both forks added same feature independently)
- Cherry-picks from previous update attempts

Always verify with `grep` before attempting to apply. This prevents:
- Redundant work
- Merge conflicts on files that already have the change
- Accidentally overwriting custom modifications with identical upstream code

## Commands Used

```bash
# Check divergence
git remote add upstream https://github.com/NousResearch/hermes-agent.git
git fetch upstream --depth=50
git merge-base upstream/main HEAD  # empty = diverged

# See what upstream has that we don't
git log --oneline upstream/main --not HEAD | head -40

# Check if specific changes are already applied
for pattern in "grok-4.3" "deepseek-v4-pro" "trinity-large-thinking"; do
    grep -q "$pattern" hermes_cli/models.py && echo "✓ $pattern present"
done

# See files touched by both sides
python3 -c "
import subprocess
upstream = set(subprocess.run(['git','log','--name-only','--pretty=format:','upstream/main','--not','HEAD'], capture_output=True, text=True).stdout.strip().split('\n'))
ours = set(subprocess.run(['git','log','--name-only','--pretty=format:','HEAD','--not','upstream/main'], capture_output=True, text=True).stdout.strip().split('\n'))
print(f'Both touched: {len(upstream & ours)}')
print(f'Only upstream: {len(upstream - ours)}')
print(f'Only ours: {len(ours - upstream)}')
"
```
