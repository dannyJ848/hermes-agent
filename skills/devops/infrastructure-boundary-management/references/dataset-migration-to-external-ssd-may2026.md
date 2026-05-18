# Dataset Migration to External SSD — May 15 2026

## Session Context

MacBook internal drive at 99% full (886G/926G). User believed datasets were already on external SSD connected to DGX. They were not — only partial data existed on SSD.

## Storage Breakdown (MacBook)

| Location | Size | Contents |
|----------|------|----------|
| `~/datasets/tier2-reasoning/` | 150G | Llama-Nemotron-PT (66G), AM-DeepSeek-R1-0528 (64G), AgentNet (12G), etc. |
| `~/datasets/tier3-health/` | 133G | Synthea synthetic health records |
| `~/datasets/tier1-reasoning/` | 54G | Various reasoning datasets |

## SSD State (DGX /mnt/bigssd)

| Location | Size | Status |
|----------|------|--------|
| `/mnt/bigssd/datasets/tier1-reasoning/` | 51G | Already present |
| `/mnt/bigssd/datasets/tier2-reasoning/` | 15M | Nearly empty — needs full transfer |
| `/mnt/bigssd/datasets/tier3-health/` | 1.8M | Nearly empty — needs full transfer |

## Discovery Commands

```bash
# Check if SSD is mounted
ssh djg6228@spark-85e8.local 'df -h | grep bigssd'

# Check SSD contents
ssh djg6228@spark-85e8.local 'du -sh /mnt/bigssd/datasets/* 2>/dev/null | sort -rh'

# Check local contents
du -sh ~/datasets/* 2>/dev/null | sort -rh
```

## exFAT Mount Permission Fix

The SSD was exFAT but mounted with root ownership, causing `chown` failures:

```bash
# WRONG — default mount gives root ownership
sudo mount /dev/sda2 /mnt/bigssd
# → chown fails: Operation not permitted

# RIGHT — mount with user ownership
sudo umount /mnt/bigssd 2>/dev/null
sudo mount -t exfat -o uid=$(id -u djg6228),gid=$(id -g djg6228),umask=0022 /dev/sda2 /mnt/bigssd

# Verify
ls -la /mnt/bigssd  # → djg6228:djg6228
```

## Transfer Commands

```bash
# Start tier2 (150G) — long running, use background process
rsync -avh --progress ~/datasets/tier2-reasoning/ djg6228@spark-85e8.local:/mnt/bigssd/datasets/tier2-reasoning/ > /tmp/rsync-tier2.log 2>&1

# Start tier3 (133G) — parallel
rsync -avh --progress ~/datasets/tier3-health/ djg6228@spark-85e8.local:/mnt/bigssd/datasets/tier3-health/ > /tmp/rsync-tier3.log 2>&1

# Monitor
tail -f /tmp/rsync-tier2.log
tail -f /tmp/rsync-tier3.log
```

## Transfer Speeds Observed

- tier2-reasoning: ~11-26 MB/s (varies by file size)
- tier3-health: ~15-23 MB/s
- Estimated total time: ~1.5-2 hours for 283GB

## Verification

```bash
# Compare sizes on both ends
ssh djg6228@spark-85e8.local 'du -sh /mnt/bigssd/datasets/*'
du -sh ~/datasets/*

# Check specific files
ssh djg6228@spark-85e8.local 'ls -la /mnt/bigssd/datasets/tier2-reasoning/AM-DeepSeek-R1-0528/README.md'
```

## Post-Transfer Cleanup

```bash
# Once verified, remove local copies
rm -rf ~/datasets/tier2-reasoning ~/datasets/tier3-health

# Symlink local path to SSD (optional, for scripts that expect ~/datasets)
# ln -s /mnt/bigssd/datasets ~/datasets  # on DGX only
```

## Key Lesson

When user says "I thought we already moved X", verify BOTH locations before assuming. Partial transfers are common — the user may have started but not completed, or transferred one tier but not others.
