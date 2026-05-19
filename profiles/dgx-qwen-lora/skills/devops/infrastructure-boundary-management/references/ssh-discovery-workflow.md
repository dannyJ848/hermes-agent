# SSH Discovery Workflow — When `ssh dgx` Fails

## Problem
The DGX Spark SSH host is NOT in standard `~/.ssh/config`. It's managed by NVIDIA Sync with a non-obvious Include path, non-default user, and key location.

## Discovery Steps

```bash
# Step 1: Check main config for Includes
cat ~/.ssh/config
# Output: Include "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/ssh_config"

# Step 2: Follow the Include
cat "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/ssh_config"
# Output:
#   Host spark-85e8.local
#     Hostname spark-85e8.local
#     User djg6228
#     Port 22
#     IdentityFile "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key"

# Step 3: SSH with discovered credentials
ssh spark-85e8.local 'ps aux | grep train'
```

## Common Failures

| Failure | Cause | Fix |
|---------|-------|-----|
| `ssh dgx: nodename nor servname provided` | No `Host dgx` entry | Use `spark-85e8.local` from NVIDIA Sync config |
| `ssh 192.168.1.100: Operation timed out` | Wrong IP | Use `spark-85e8.local` hostname |
| `Permission denied (publickey,password)` | Wrong user | Must be `djg6228`, not `root` or default |
| `Permission denied` with correct user | Key not loaded | NVIDIA Sync key is auto-managed, but verify path |

## Training Log Discovery

Training logs are NOT at a fixed path. The training process writes to whatever path it was started with. To find the active log:

```bash
# Find log via process file descriptors
ssh spark-85e8.local 'ls -la /proc/443609/fd | grep log'
# Output: l-wx------ 1 djg6228 djg6228 64 May 9 11:07 1 -> /mnt/bigssd/train_r256_final.log

# Or check cwd
ssh spark-85e8.local 'ls -la /proc/443609/cwd'
# Output: /proc/443609/cwd -> /data/SpecForge/custom_dflash
```

## Never Do These
- Try `root@spark-85e8.local` — wrong user, will fail
- Try `ssh dgx` or `ssh 192.168.1.100` — these are not configured
- Assume log path is `~/qwen-training/checkpoints/` — that's not where training runs
- Run MacBook-only code through the SSH session — DGX is training-only
