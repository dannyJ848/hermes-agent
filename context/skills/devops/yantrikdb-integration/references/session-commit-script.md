# Session Context Commit Script

## Problem

The user wants all persistence layer context files (MEMORY.md, SOUL.md, USER.md, MASTER.md) backed up to the git repo after every session. These files live in `~/.hermes/` which is outside the repo. They must be copied into the repo and committed, but credentials (`.env`, `auth.json`, `config.yaml`, DBs) must NEVER be committed.

## Solution: `scripts/session-commit.sh`

Created at: `/Users/dannygomez/hermes-agent/scripts/session-commit.sh`

### What it does

1. Copies `~/.hermes/{MEMORY.md,SOUL.md,USER.md,MASTER.md}` → `docs/context/` in the repo
2. Only commits if files actually changed (`git diff --quiet` check)
3. Never touches `.env`, `auth.json`, `config.yaml`, or any `.db` files
4. Generates a descriptive commit with timestamp

### Usage

```bash
# After any session where context files changed:
bash /Users/dannygomez/hermes-agent/scripts/session-commit.sh
```

### Safety

- The script is **manual only** — respects user's explicit constraint against autonomous processes without permission
- No cron, no daemon, no automatic trigger
- Frictionless: one command, idempotent (no-op if no changes)

### Directory structure

```
hermes-agent/
  docs/context/
    MEMORY.md    ← copied from ~/.hermes/
    SOUL.md      ← copied from ~/.hermes/
    USER.md      ← copied from ~/.hermes/
    MASTER.md    ← copied from ~/.hermes/
  scripts/
    session-commit.sh
```

### Git ignore considerations

Add to `.gitignore` (if not already):
```
# Never commit credentials or DBs
docs/context/*.db
docs/context/.env
docs/context/auth.json
docs/context/config.yaml
```

## Session Reference

- Date: 2026-05-17
- User request: "I want the repo to be the living reservoir of ALL the changes and learning from every session"
- Constraint: User rejects autonomous agents without explicit permission
- Resolution: Manual script, not automatic, respects constraint
- Status: ✅ COMPLETED — script created, context files committed to `qwen27b-training-artifacts-may3-2026`
