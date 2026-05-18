---
name: ml-workspace-cleanup
description: Audit and clean machine learning workspace bloat — HuggingFace caches, training datasets, model weights, package manager caches, and Docker images. Reclaim 100GB+ safely by identifying duplicates and unused artifacts.
trigger: When disk is running low, ML training artifacts have accumulated, or the user explicitly asks to clean model/dataset bloat from their machine.
category: devops
---

# ML Workspace Bloat Cleanup

## Quick Audit (run first)

Check the common bloat locations in order of typical size:

```bash
# 1. HuggingFace Hub cache (models + datasets)
du -sh ~/.cache/huggingface/hub/* 2>/dev/null | sort -rh | head -20
du -sh ~/.cache/huggingface/datasets/* 2>/dev/null | sort -rh | head -10

# 2. Training data / project folders (often the biggest)
du -sh ~/training-data ~/datasets ~/models ~/dgx-spark-prep 2>/dev/null | sort -rh

# 3. Package manager caches
du -sh ~/.cache/uv ~/.cache/pip ~/.conda/pkgs 2>/dev/null | sort -rh

# 4. Docker
docker system df 2>/dev/null

# 5. Downloads
du -sh ~/Downloads 2>/dev/null
```

## Safe Deletion Targets

**Always confirm with user before deleting.** These are typically safe if duplicates exist on remote storage or training servers:

| Target | What it is | Typical Size |
|--------|-----------|--------------|
| `~/.cache/huggingface/hub/models--*` | Downloaded HF models | 1-50GB each |
| `~/.cache/huggingface/datasets/` | Cached datasets | 100MB-10GB |
| `*/training-data/` | Local training datasets | 10-300GB |
| `~/.cache/uv/` | UV package cache | 2-10GB |
| `~/.cache/pip/` | pip wheel cache | 1-5GB |
| `~/Downloads/*.dmg` | Installer images | 100MB-1GB each |
| Docker images/volumes | Container artifacts | 10-100GB |

## Dataset Migration (Before Deletion)

When datasets are large (100GB+) and the user believes they should be on external storage, **verify both locations** before deleting:

```bash
# Check local
ls -la ~/datasets/
du -sh ~/datasets/* 2>/dev/null | sort -rh

# Check external SSD (example: DGX /mnt/bigssd)
ssh djg6228@spark-85e8.local 'du -sh /mnt/bigssd/datasets/* 2>/dev/null | sort -rh'

# Compare — if external has partial data, user may have started but not completed transfer
```

**If external is missing data, migrate before deleting local:**
```bash
# Ensure SSD mounted with user perms (exFAT needs explicit uid/gid)
ssh djg6228@spark-85e8.local 'sudo mount -t exfat -o uid=$(id -u),gid=$(id -g),umask=0022 /dev/sda2 /mnt/bigssd'

# Rsync to external
rsync -avh --progress ~/datasets/tier2-reasoning/ djg6228@spark-85e8.local:/mnt/bigssd/datasets/tier2-reasoning/
```

**Pitfall — User says "I thought we already moved the datasets"**: This signals partial or incomplete transfer. Always verify BOTH locations with `du -sh` before concluding.

### Background Rsync with Progress Tracking

For large transfers (100GB+), run rsync in background with log files:

```bash
# Terminal 1: Start background rsync
rsync -avh --progress ~/datasets/tier2-reasoning/ djg6228@spark-85e8.local:/mnt/bigssd/datasets/tier2-reasoning/ > /tmp/rsync-tier2.log 2>&1 &

# Terminal 2: Monitor progress
tail -f /tmp/rsync-tier2.log | grep -E "^[0-9]|%|sent"

# Check if still running
ps aux | grep "rsync.*tier2" | grep -v grep

# Verify completion
grep -E "sent|total size" /tmp/rsync-tier2.log | tail -2
```

**Critical**: Do NOT delete local copies until BOTH of these are true:
1. `ps aux | grep rsync` shows no active process
2. `grep "speedup 1.00" /tmp/rsync-*.log` confirms completion
3. Remote verification: `ssh user@host "du -sh /remote/path"` matches local size

**Pitfall**: rsync may appear complete in the log (showing 100%) but the process may still be finalizing. Always check `ps aux` to confirm the process has exited before deleting local files.
## What to KEEP

- Active project code and configs
- Small embedding models used for local RAG (BGE, MiniLM, etc.)
- Models under active development (< 5GB)
- `.git` repos (obviously)
- Virtual environments for active projects

## One-Liner Reclaim Commands

```bash
# Delete specific large HF models (replace MODEL-NAME)
rm -rf ~/.cache/huggingface/hub/models--MODEL-NAME

# Nuke all HF datasets cache
rm -rf ~/.cache/huggingface/datasets

# Nuke UV cache
rm -rf ~/.cache/uv

# Docker deep clean (containers, networks, volumes, images)
docker system prune -a --volumes

# Clean pip cache
pip cache purge
```

## Verification

After cleanup, check disk usage:
```bash
df -h /
```

## Safety Rules

1. **Never delete training data that only exists locally** — always verify remote/backup copies first
2. **Never delete `.git` directories** unless explicitly asked
3. **Never delete `~/.ssh`, `~/.gnupg`, or credential stores**
4. **Never delete active virtual environments**
5. **When in doubt, `du -sh` first, delete second**
