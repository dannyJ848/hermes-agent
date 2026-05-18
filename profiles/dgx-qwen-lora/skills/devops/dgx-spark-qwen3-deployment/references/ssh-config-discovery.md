# SSH Config Discovery — DGX Spark

## Lesson: ALWAYS Check NVIDIA Sync SSH Config First

**Date**: May 8, 2026
**Context**: Failed multiple SSH attempts to DGX Spark because I checked `~/.ssh/config` which only had an `Include` directive, not the actual host entries.

## The Pattern

On MacBooks with NVIDIA Sync installed, the DGX Spark SSH config lives in:
```
~/Library/Application Support/NVIDIA/Sync/config/ssh_config
```

NOT in `~/.ssh/config`.

## What `~/.ssh/config` Actually Contains

```
Include "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/ssh_config"
```

That's it. The real host entries are in the included file.

## The Real Config

```
Host spark-85e8.local
  Hostname spark-85e8.local
  User djg6228
  Port 22
  IdentityFile "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key"
```

## Critical Details

| Field | Value | Where I Failed |
|-------|-------|----------------|
| Username | `djg6228` | Guessed `danny`, `root`, `ubuntu` — all wrong |
| Key path | `~/Library/Application Support/NVIDIA/Sync/config/nvsync.key` | Tried default `~/.ssh/id_*` keys — all wrong |
| Hostname | `spark-85e8.local` (mDNS) | Also resolves to `10.0.0.171` via ping |

## Correct Connection Command

```bash
ssh -i "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key" djg6228@spark-85e8.local
```

Or using IP:
```bash
ssh -i "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key" djg6228@10.0.0.171
```

## Verification Steps (Before Wasting Time)

1. **Check if NVIDIA Sync config exists**:
   ```bash
   ls ~/Library/Application\ Support/NVIDIA/Sync/config/ssh_config
   ```

2. **Read the included config**:
   ```bash
   cat ~/Library/Application\ Support/NVIDIA/Sync/config/ssh_config
   ```

3. **Verify key exists**:
   ```bash
   ls ~/Library/Application\ Support/NVIDIA/Sync/config/nvsync.key
   ```

4. **Test connection**:
   ```bash
   ssh -o ConnectTimeout=5 -i <key_path> <user>@<hostname> "echo connected"
   ```

## User Frustration Signal

> "omg look thorugh the master doc and prior sessions"

This means: **The information is discoverable. Stop guessing and look in the obvious places.**

## Related

- `references/ssh-timeout-under-training-load.md` — SSH unresponsiveness during training
- `references/access-troubleshooting-and-recovery.md` — Full access recovery playbook
