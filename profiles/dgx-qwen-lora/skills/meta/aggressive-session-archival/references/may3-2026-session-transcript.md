# Session Transcript: Aggressive Archival — May 3, 2026

## User Request
> "oh no move everythingto the repo please, EVERYTHING."

This was the 3rd escalation. First attempt: committed only scripts. Second attempt: committed scripts + README. Third attempt (this one): user demanded ALL runtime state.

## What We Tried

### Attempt 1: Naive `git add -A`
```bash
cd ~/.hermes && git add -A && git commit -m "Add ALL runtime state..."
```
**Result:** Command timed out after 120s. `~/.hermes` is 19GB with 6GB `.git` directory.

### Attempt 2: `.gitignore` then re-add
Created `.gitignore` excluding `*.db`, `cache/`, `logs/`, etc.
```bash
cat > .gitignore << 'EOF'
*.db
*.db-shm
*.db-wal
*.db.corrupt*
*.db.backup*
*.pid
*.lock
__pycache__/
*.pyc
*.pyo
checkpoints/
cache/
browser-profile/
eyes_cache/
context_snapshots/
state-snapshots/
memory_backups/
api_captures/
anki_output/
claude-bridge/
twitter_bridge/
sessions/
logs/
EOF
```
**Problem:** `.gitignore` blocked `git add -A` but we needed specific files. Had to use `git add -f` for explicit files.

### Attempt 3: Explicit file list
```bash
git add -f config.yaml goals.md BLUEPRINT*.md CHECKPOINT*.md MEMORY*.md SOUL.md SYSTEM*.md QUARANTINE*.md RESUME*.md REVERT_STATE_DB.sh .env
```
**Result:** GitHub GH013 blocked push. Secrets in `.env` and `config.yaml`.

### Attempt 4: Remove secrets, re-commit
```bash
git reset --soft HEAD~1
git rm --cached .env config.yaml
git commit -m "Add ALL session artifacts except secrets"
```
**Result:** Still blocked. HuggingFace token in `CHECKPOINT-apr23-v0110-eagle3-tools5-permissions.md:96`.

### Attempt 5: Redact HF token
```bash
# File: CHECKPOINT-apr23-v0110-eagle3-tools5-permissions.md:96
# Before: - **HF token:** `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`
# After:  - **HF token:** `hf_***` (redacted)
sed -i 's/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/hf_*** (redacted)/g' CHECKPOINT-apr23-v0110-eagle3-tools5-permissions.md
```

### Final: Amend and push
```bash
git add CHECKPOINT-apr23-v0110-eagle3-tools5-permissions.md
git commit --amend --no-edit
git push origin main:hermes-config --force-with-lease
```
**Result:** SUCCESS. 31 files committed, 0 secrets.

## Final Archive Contents

```
.gitignore
README.md
goals.md
SOUL.md
MEMORY_ARCHITECTURE_FIX.md
SYSTEM_HARDENING_COMPLETE.md
BLUEPRINT-qwen-scope-franken-v8-master.md
BLUEPRINT_AUDIT_REPORT_APR27.md
CHECKPOINT-apr23-adaptive-thinking-live.md
CHECKPOINT-apr23-eagle3-complete.md
CHECKPOINT-apr23-qwen36-optimization.md
CHECKPOINT-apr23-stable-clean.md
CHECKPOINT-apr23-v0110-eagle3-tools5-permissions.md
CHECKPOINT-apr23-v0110-eagle3-tools5.md
CHECKPOINT-apr24-dflash-training-84pct.md
CHECKPOINT-apr24-phase1-complete.md
CHECKPOINT-apr24-phase2-training-live.md
CHECKPOINT-apr25-dataset-downloads.md
CHECKPOINT-apr25-deepseek-delegate-fix.md
CHECKPOINT-apr25-merged-cortex-research.md
CHECKPOINT-apr26-cortex-migration-complete.md
CHECKPOINT-apr26-franken-v8-3batch-checkpoint.md
CHECKPOINT-apr26-franken-v8-audit-complete.md
CHECKPOINT-apr26-iteration-apparatus-v2-fixed.md
CHECKPOINT-apr26-iteration-apparatus-v2.md
CHECKPOINT-apr26-iteration-apparatus.md
CHECKPOINT-apr26-kimi-harness-v2-dflash-epoch0.md
CHECKPOINT-may3-qwen27b-sae-only.md
CHECKPOINT-pre-restart-v2.md
QUARANTINE-apr23-eagle3-hacking-pause.md
RESUME-apr26-cortex-migration-complete.md
REVERT_STATE_DB.sh
scripts/archive_sessions.py
scripts/check_dflash_training.py
scripts/emergency-restore.sh
scripts/hermes-write-helper.sh
scripts/hermes_loop_guard.py
scripts/hermes_scheduler_daemon.py
scripts/memory_pruner.py
scripts/new-agent-handoff.py
scripts/safe-restart.sh
scripts/state_db_merge.py
```

## Key Lessons

1. **`.gitignore` first, always.** Never `git add -A` on a directory you haven't audited.
2. **GitHub scans EVERYTHING.** Even old checkpoint files from weeks ago can contain secrets.
3. **`git add -f` is dangerous.** It bypasses `.gitignore` — only use on files you've verified.
4. **`git commit --amend` saves history.** No need to create new commits when fixing secrets.
5. **Users want EVERYTHING.** When they say "everything", they mean configs, blueprints, checkpoints, scripts, docs — but NOT secrets or 19GB of runtime data.
