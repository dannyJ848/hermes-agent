---
name: hermes-backup
description: Daily backup system for Hermes Agent — git commits for instant rollback + tar.gz snapshots for disaster recovery. 7-day retention, cron-automated.
version: 1.0
created: 2026-04-15
---

# Hermes Agent Daily Backup

## What It Protects

| Path | Size | Why |
|------|------|-----|
| `~/hermes-agent/run_agent.py` | ~2MB | Most edited file, highest corruption risk |
| `~/hermes-agent/config.yaml` | ~50KB | Provider keys, model config |
| `~/hermes-agent/.env` | ~1KB | API keys |
| `~/hermes-agent/plugins/` | ~5MB | Custom context/memory plugins |
| `~/subconscious/` | ~30MB | All cortex modules (daemon, flywheel, judge, etc.) |
| `~/.hermes/skills/` | ~17MB | Learned procedural skills |
| `~/.hermes/memory/` | small | Agent memory store |
| `~/.hermes/cron/` | ~62MB | Scheduled jobs |
| `~/.hermes/knowledge/` | varies | Research findings |

## What It Skips (too large, regeneratable)

- `~/.hermes/sessions/` — 1.3GB, chat history
- `~/.hermes/checkpoints/` — 660MB, session checkpoints
- `~/.hermes/browser-profile/` — 37MB, browser cache
- `~/.hermes/logs/` — 30MB, log files
- `~/hermes-agent/venv/` — Python venv, regeneratable

## Setup

1. Script is at `~/hermes-backup.sh` (chmod +x)
2. Cron job `hermes-daily-backup` runs at 3am daily
3. First run initializes git repos in `~/subconscious/` and `~/.hermes/` if needed

## Rollback

### Single file (from git — instant)
```bash
cd ~/hermes-agent
git log --oneline -10              # find the good commit
git checkout <hash> -- run_agent.py  # restore just that file
```

Works for any tracked file across all 3 repos:
- `~/hermes-agent/` — agent core
- `~/subconscious/` — cortex modules
- `~/.hermes/` — skills/memory/cron

### Full disaster recovery (from tar)
```bash
mkdir ~/restore && cd ~/restore
tar xzf ~/.hermes-backups/hermes_backup_YYYYMMDD*.tar.gz
# Then copy files back to their locations
```

## Pitfalls Learned

1. **~/.hermes is 4.2GB** — MUST exclude sessions/, checkpoints/, browser-profile/, logs/ or tar takes 60+ seconds and times out. Only backup skills/, memory/, cron/, knowledge/.

2. **nohup in hermes_tools terminal()** — running `nohup cmd &` inside a terminal() call spawns TWO processes (one from bash eval, one from nohup). For process management, use a Python script file with `subprocess.Popen(start_new_session=True)` instead.

3. **Git repos for 3 directories** — hermes-agent already has git, but ~/subconscious/ and ~/.hermes/ need `git init` on first run. The backup script handles this automatically.

4. **Duplicate memory entries** — When saving to Hermes memory, check for duplicates before adding. If you save twice, use `memory(action='remove', old_text='...')` with the stale entry's text.

5. **Daemon restart race** — Killing cortex_daemon processes and restarting in the same terminal() call is unreliable. Kill in one call, verify in a second, then start in a third.

## Verification Checklist

After setup, verify with:
```bash
# Run backup manually
bash ~/hermes-backup.sh

# Check tar contents
tar tzf ~/.hermes-backups/hermes_backup_*.tar.gz | head -20

# Check git history
cd ~/hermes-agent && git log --oneline -5
cd ~/subconscious && git log --oneline -5

# Check backup size and count
ls -lh ~/.hermes-backups/
```

Expected: ~96MB tar, 8,500+ files, completes in ~5 seconds.
