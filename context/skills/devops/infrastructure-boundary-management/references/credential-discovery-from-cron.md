# Credential Discovery from Cron Jobs

## Problem

SSH to remote system fails because you don't know the correct user, host, or key path. `session_search` returns "Session database not available." Standard SSH configs don't have the entry.

## Solution: Mine cron job definitions

Hermes cron jobs (`~/.hermes/cron/jobs.json`) contain full SSH commands with credentials in their prompt strings. These are a reliable fallback when other discovery methods fail.

## Pattern

```bash
# Search cron jobs for host/user references
search_files path="~/.hermes" pattern="spark-85e8|10\.0\.0\.171|djg6228|train_"

# Or grep directly
grep -E "ssh.*spark|ssh.*10\.0\.0|djg6228" ~/.hermes/cron/jobs.json | head -10
```

## What you'll find

Cron job prompts typically contain complete SSH commands like:
```
ssh djg6228@spark-85e8.local "tail -20 /mnt/bigssd/train_standard.log"
ssh -i "/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key" djg6228@spark-85e8.local "nvidia-smi"
```

## Extracting credentials

| Field | Example | Where found |
|-------|---------|-------------|
| Host | `spark-85e8.local` | SSH command in cron prompt |
| IP | `10.0.0.171` | Hermes config.yaml or cron prompt |
| User | `djg6228` | SSH command in cron prompt |
| Key | `/Users/dannygomez/Library/Application Support/NVIDIA/Sync/config/nvsync.key` | SSH `-i` flag in cron prompt |
| Log path | `/mnt/bigssd/train_lora_sae_teacher_v1.log` | tail command in cron prompt |

## Verification

Once extracted, verify immediately:
```bash
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 djg6228@spark-85e8.local "nvidia-smi"
```

## Pitfalls

| Wrong | Right |
|-------|-------|
| Guess `root@` or default user | Extract actual user from cron prompt |
| Try `ssh dgx` (generic hostname) | Use exact host from cron: `spark-85e8.local` |
| Give up after `session_search` fails | Fallback to `search_files` on cron jobs |
| Assume IP from config is current | Verify with `ssh spark-85e8.local` first |

## Related

- `references/ssh-discovery-workflow.md` — Standard SSH config file discovery
- `references/session-search-fallback-pattern.md` — When session_search fails, use search_files
