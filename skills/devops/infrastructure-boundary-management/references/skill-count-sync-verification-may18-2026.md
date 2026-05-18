# Skill Count Sync Verification — May 18, 2026

**Scenario:** After copying skills from `hermes-agent/skills/` to `~/.hermes/skills/`, the CLI shows different counts on different machines. Need to verify sync and reconcile discrepancies.

## The Discrepancy Pattern

| Location | Claimed | Actual SKILL.md | Actual `hermes skills list` |
|----------|---------|-----------------|---------------------------|
| MacBook | 384 | 384 | 384 |
| DGX source repo | 161 (old context) | 78-90 | N/A (no venv) |
| DGX ~/.hermes/skills/ | 136 entries | 388 | N/A |

**Root causes:**
1. DGX source repo `skills/` has only 25 top-level directories (category umbrellas), but 78-90 SKILL.md files at depth 3
2. DGX `~/.hermes/skills/` had 136 entries including non-skill files (databases, markdown, test dirs)
3. The "161 skills" from another CLI context was likely counting differently (builtin + some local)

## Verification Commands

```bash
# Count SKILL.md files at depth 2 (individual skills under umbrellas)
find skills/ -name "SKILL.md" -maxdepth 2 | wc -l

# Count SKILL.md files at depth 3 (includes sub-skills like devops/hermes-backup/)
find skills/ -name "SKILL.md" -maxdepth 3 | wc -l

# Count top-level directories (category umbrellas)
find skills/ -type d -maxdepth 1 | wc -l

# Hermes CLI count (may differ due to builtin vs local split)
hermes skills list | wc -l
```

**Depth matters:** 
- `maxdepth 2` catches `skills/devops/SKILL.md` (category index) and `skills/devops/hermes-backup/SKILL.md` (individual skill)
- `maxdepth 3` catches deeply nested skills like `skills/software-development/hermes-deployment/SKILL.md`

## Sync Workflow

```bash
# 1. Verify source has skills
ls hermes-agent/skills/ | wc -l  # → 25 category directories
find hermes-agent/skills/ -name "SKILL.md" -maxdepth 3 | wc -l  # → 384

# 2. Copy to ~/.hermes/skills/
cp -r hermes-agent/skills/* ~/.hermes/skills/

# 3. Verify
find ~/.hermes/skills/ -name "SKILL.md" -maxdepth 3 | wc -l  # → 384
hermes skills list | wc -l  # → 384

# 4. Commit and push
git add skills/
git commit -m "Install 305 source skills"
git push origin main

# 5. On target machine (DGX)
git pull origin main
rm -rf ~/.hermes/skills/*
cp -r /data/SpecForge/hermes-agent/skills/* ~/.hermes/skills/
find ~/.hermes/skills/ -name "SKILL.md" -maxdepth 3 | wc -l  # → 384
```

## Cross-Machine Verification

```bash
# MacBook
find ~/.hermes/skills/ -name "SKILL.md" -maxdepth 3 | wc -l

# DGX (via SSH)
ssh djg6228@spark-85e8.local 'find ~/.hermes/skills/ -name "SKILL.md" -maxdepth 3 | wc -l'

# Should match. If not:
# 1. Check git commit match
# 2. Check for .DS_Store or temp files
# 3. Re-copy from source
```

## Pitfall: `~/.hermes/skills/` vs `hermes-agent/skills/`

The Hermes CLI reads skills from `~/.hermes/skills/` (or config `skills.external_dirs`), NOT from the source repo `hermes-agent/skills/`. After `git pull` updates the source repo, you must ALSO update `~/.hermes/skills/`.

**Two locations to keep in sync:**
1. `hermes-agent/skills/` — source of truth in git
2. `~/.hermes/skills/` — runtime location used by CLI

## Pitfall: Non-skill files in skills directory

`~/.hermes/skills/` may accumulate non-skill files:
- `skill_hits.db` — SQLite database
- `skill_memory.db` — SQLite database  
- `system_status_check.md` — temp file
- `test/`, `test-skill/` — test directories

These inflate directory counts but not SKILL.md counts. Always verify with `find -name SKILL.md`, not `ls`.
