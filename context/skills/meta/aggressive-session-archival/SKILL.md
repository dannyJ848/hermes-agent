---
name: aggressive-session-archival
description: "Archive an entire CLI session's state — code, configs, checkpoints, blueprints, scripts, documentation — into a git repo branch for perfect reproducibility. Handles secret redaction, .gitignore management, and GitHub push protection (GH013)."
trigger: "When the user says 'save everything', 'move to repo', 'archive session', 'checkpoint all', or wants to close a CLI with full history preserved."
---

# Aggressive Session Archival

## When to Use
- User is closing a CLI session and wants ALL state preserved
- User says "move everything to the repo" or "archive this"
- Multi-hour session produced configs, scripts, blueprints, checkpoints that must survive context window death
- Need perfect reproducibility: another CLI instance should resume exactly where this one left off

## What Gets Archived

| Category | Examples | Git Strategy |
|----------|----------|-------------|
| **Scripts** | `*.py`, `*.sh`, daemon files | `git add scripts/` |
| **Configs** | `config.yaml`, `.env` | `.env` → **EXCLUDE** (secrets). `config.yaml` → redact or exclude |
| **Blueprints** | `BLUEPRINT-*.md` | `git add BLUEPRINT*.md` |
| **Checkpoints** | `CHECKPOINT-*.md` | `git add CHECKPOINT*.md` |
| **Documentation** | `README.md`, `SOUL.md`, `goals.md` | `git add` |
| **Runtime data** | `*.db`, `*.pid`, `*.lock`, caches | **EXCLUDE** via `.gitignore` |
| **Secrets** | API keys, tokens, passwords | **NEVER commit**. Redact in docs, exclude files |

## Step-by-Step Process

### Step 1: Identify the target repo and branch

```bash
# Determine where to archive
cd TARGET_DIR          # Usually ~/.hermes or project root
git branch -a          # Check existing branches
```

Common patterns:
- `main` branch for code changes
- `hermes-config` branch for dotfiles/session artifacts
- Feature branches for specific experiments

### Step 2: Create/update .gitignore

**CRITICAL:** `.gitignore` must be in place BEFORE adding files, or secrets will be committed.

```bash
cat > .gitignore << 'EOF'
# Secrets — NEVER commit
.env
*.env
secrets/

# Runtime data
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

# Large directories
checkpoints/
cache/
logs/
sessions/
browser-profile/
eyes_cache/
context_snapshots/
state-snapshots/
memory_backups/
api_captures/
anki_output/
claude-bridge/
twitter_bridge/
EOF
git add .gitignore
git commit -m "Update .gitignore for session archival"
```

### Step 3: Add all safe files

```bash
# Add everything that .gitignore allows
git add -A

# Explicitly add files that .gitignore might block but are safe
git add -f README.md goals.md SOUL.md
```

### Step 4: Handle secrets (GitHub GH013 protection)

**Scan for secrets BEFORE committing:**

```bash
# Quick scan for common secret patterns
grep -rE "(sk-[a-zA-Z0-9]{20,}|hf_[a-zA-Z0-9]{30,}|ghp_[a-zA-Z0-9]{30,}|AKIA[0-9A-Z]{16})" . \
  --include="*.md" --include="*.yaml" --include="*.yml" --include="*.py" --include="*.sh" \
  --exclude-dir=.git --exclude-dir=__pycache__
```

**If secrets found in files that MUST be committed (e.g., checkpoint docs):**

```bash
# Redact the secret
sed -i 's/sk-[a-zA-Z0-9]\{20,\}/YOUR_API_KEY_HERE/g' FILE.md
sed -i 's/hf_[a-zA-Z0-9]\{30,\}/YOUR_HF_TOKEN/g' FILE.md

# Verify
git diff FILE.md
```

**If `.env` or `config.yaml` contain secrets and user wants them archived:**
- **Option A:** Exclude from git, document in README how to recreate
- **Option B:** Create redacted template (`config.yaml.example`)
- **Option C:** Commit to private repo (if available) — still risky

### Step 5: Commit with descriptive message

```bash
git commit -m "Session archive: DATE — brief description of what was done"
```

### Step 6: Push and handle GH013

```bash
git push origin main:BRANCH_NAME --force-with-lease
```

**If GH013 (secret scanning) blocks push:**

```bash
# 1. Identify which file has the secret
git log --oneline -1          # Note the commit hash

# 2. Remove secret from commit
git reset --soft HEAD~1       # Unstage everything
git rm --cached .env config.yaml   # Remove secret files from staging
# OR redact secrets in committed files:
sed -i 's/SECRET/REDACTED/g' FILE.md
git add FILE.md

# 3. Re-commit
git commit -m "Session archive: DATE — secrets redacted"

# 4. Re-push
git push origin main:BRANCH_NAME --force-with-lease
```

### Step 7: Verify the archive

```bash
# Check what's in the repo
git ls-files | wc -l          # Count of archived files
git ls-files                  # List all archived files

# Verify no secrets leaked
grep -rE "(sk-[a-zA-Z0-9]{20,}|hf_[a-zA-Z0-9]{30,})" $(git ls-files) || echo "No secrets found ✓"
```

### Step 8: Document resume procedure

Add to README.md or a new CHECKPOINT file:

```markdown
## Resume Procedure

```bash
# 1. Pull the archive branch
git clone -b BRANCH_NAME https://github.com/USER/REPO.git /tmp/config
cp -r /tmp/config/* ~/.hermes/

# 2. Recreate secrets (NOT in repo)
export DEEPSEEK_API_KEY="your-key-here"
# Or: cp ~/secure/.env ~/.hermes/.env

# 3. Start daemons
python3 ~/.hermes/scripts/hermes_scheduler_daemon.py &
cd ~/subconscious && python3 cortex_daemon.py start
```
```

## Pitfalls

| Pitfall | Why It Happens | Prevention |
|---------|---------------|------------|
| GH013 push rejection | Committed `.env` or `config.yaml` with API keys | Scan with `grep` before commit; use `.gitignore` |
| `.gitignore` doesn't protect already-tracked files | `git add -f` overrides `.gitignore` | Never use `-f` on files you haven't scanned for secrets |
| Committing 19GB of runtime data | `git add -A` includes `.db` files | `.gitignore` must list `*.db` BEFORE any `git add` |
| Redacting only in working tree, not in commit | `sed` changes file but commit still has secret | `git commit --amend` or `git reset --soft HEAD~1` |
| Forgetting to document how to recreate secrets | Next session can't find API keys | README must have "Recreate secrets" section |
| Pushing to wrong branch | Confusion between `main` and `hermes-config` | Always check `git branch -a` first |

## Secret Redaction Patterns

| Service | Pattern | Redaction |
|---------|---------|-----------|
| OpenRouter | `sk-or-v1-...` | `YOUR_OPENROUTER_KEY` |
| HuggingFace | `hf_...` | `YOUR_HF_TOKEN` |
| GitHub PAT | `ghp_...` | `YOUR_GITHUB_TOKEN` |
| DeepSeek | `sk-...` | `YOUR_DEEPSEEK_KEY` |
| AWS | `AKIA...` | `YOUR_AWS_KEY` |
| OpenAI | `sk-...` | `YOUR_OPENAI_KEY` |
| Anthropic | `sk-ant-...` | `YOUR_ANTHROPIC_KEY` |

## Session Example: May 3, 2026

**Context:** 8+ hour session on DGX Spark Qwen 27B training, cron scheduler fixes, flywheel restart.

**What was archived:**
- 31 checkpoint files (Apr 23–May 3)
- 2 blueprint files
- 9 scripts (loop guard, scheduler daemon, archive, restore, etc.)
- README.md with setup instructions
- goals.md, SOUL.md, MEMORY_ARCHITECTURE_FIX.md

**What was excluded:**
- `.env` (OpenRouter key)
- `config.yaml` (multiple API keys)
- All `.db` files (runtime state)
- Large directories (checkpoints, cache, logs)

**GH013 incident:** HuggingFace token found in `CHECKPOINT-apr23-v0110-eagle3-tools5-permissions.md:96`. Fixed with `sed` redaction and `git commit --amend`.

**Result:** 43 files in `hermes-config` branch, 0 secrets, perfect resume capability.
