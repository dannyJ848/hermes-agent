---
name: git-large-file-cleanup
description: "Clean up git repositories with large files exceeding GitHub's 100MB limit, including history rewriting and .gitignore setup."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [git, github, cleanup, large-files, filter-branch, history-rewrite]
---

# Git Large File Cleanup

When a git repository contains files larger than GitHub's 100MB hard limit (or 50MB soft limit), pushes will be rejected with `pre-receive hook declined` errors. Simply removing files from the working tree is NOT enough — they remain in git history and will block pushes.

## Common Error Pattern

```
remote: error: File backups/20260517_213115/lcm.db is 315.10 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: GH001: Large files detected. You may want to try Git Large File Storage - https://git-lfs.github.com.
To https://github.com/user/repo.git
 ! [remote rejected]     main -> main (pre-receive hook declined)
```

## Quick Fix: History Rewrite

### Step 1: Remove files from index (NOT enough alone)

```bash
git rm -r --cached backups/ checkpoints/ state.db *.db
git commit --amend -m "chore: Remove large files from index"
```

**This is NOT sufficient** — files still exist in older commits.

### Step 2: Rewrite history to remove files completely

Use `git filter-branch` (or `git filter-repo` if available):

```bash
# Remove directories and specific files from ALL history
git filter-branch --force --index-filter \
  'git rm -rf --cached --ignore-unmatch \
    backups/ checkpoints/ \
    state.db lcm.db unified_context.db \
    cerebrum_memory.db skill_tracker.db \
    *.db *.db-shm *.db-wal' \
  --prune-empty --tag-name-filter cat -- --all
```

**Pitfall:** `filter-branch` creates a `.git-rewrite` directory. If interrupted, clean up:
```bash
git filter-branch --abort 2>/dev/null
rm -rf .git-rewrite
```

### Step 3: Clean up and verify

```bash
# Remove original refs
git reflog expire --expire=now --all
git gc --aggressive --prune=now

# Verify no large files remain in history
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '$1 == "blob" && $3 > 50000000 {print $3, $4}' | sort -rn
```

### Step 4: Update .gitignore to prevent recurrence

```gitignore
# Runtime databases and state
*.db
*.db-shm
*.db-wal
*.log
*.lock
*.pid

# Backup and checkpoint directories
backups/
checkpoints/
sessions/
telemetry/
state/

# Named database files
state.db
lcm.db
unified_context.db
cerebrum_memory.db
skill_tracker.db
live_learning.db
memory_store.db
agent-mesh.db
cortex.db
distillation_buffer.db
kanban.db
```

### Step 5: Force push the cleaned history

```bash
git push origin main --force-with-lease
```

## Alternative: Fresh Orphan Branch

If history rewrite is too complex, create a clean branch:

```bash
# Save current state
git branch backup-main

# Create orphan branch with current files
git checkout --orphan clean-main
git add -A
git commit -m "chore: Fresh start with clean history"

# Replace main
git branch -M main
git push origin main --force-with-lease
```

## Key Pitfalls

1. **`.git-rewrite` cleanup:** If `filter-branch` is interrupted, stale `.git-rewrite` prevents re-running. Always `rm -rf .git-rewrite` before retrying.

2. **Session files in history:** Auto-generated session JSON files (10-20MB each) accumulate quickly. Add `sessions/` to `.gitignore` early.

3. **Pack files:** Git packfiles can exceed 100MB even if individual objects don't. Run `git gc --aggressive` after rewrite.

4. **Backup branches:** Always create a backup branch before force-pushing: `git branch backup-before-rewrite`.

5. **Collaborators:** Force-push rewrites shared history. Coordinate with team members or use `--force-with-lease` for safety.

## When filter-branch times out

For very large repos, `filter-branch` may take hours. Options:
- Run in a `screen` or `tmux` session
- Use `git filter-repo` (much faster, may need `pip install git-filter-repo`)
- Use BFG Repo-Cleaner for simple file removal: `java -jar bfg.jar --delete-files '*.db'`
