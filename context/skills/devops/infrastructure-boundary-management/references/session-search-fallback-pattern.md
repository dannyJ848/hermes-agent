# Session Search Fallback Pattern

## Problem

`session_search` tool may return "Session database not available" when trying to retrieve previous session context, including DGX credentials, training status, or other cross-session state.

## Fallback: search_files in ~/.hermes/cron/jobs.json

When session_search fails and you need DGX access credentials:

```bash
# Search for DGX-related entries in cron jobs (contains SSH commands with full credentials)
search_files path="~/.hermes" pattern="DGX|dgx|spark-85e8|djg6228|train_.*log"
```

The cron job definitions contain explicit SSH commands like:
```json
"ssh djg6228@spark-85e8.local \"tail -20 /mnt/bigssd/train_ultimate_v3_final.log\""
```

From these you can extract:
- **Host:** `spark-85e8.local` (resolves to `10.0.0.171`)
- **User:** `djg6228`
- **Log paths:** `/mnt/bigssd/train_standard.log`, `/mnt/bigssd/train_r256_final.log`, etc.

## Why This Works

Cron jobs are stored as JSON in `~/.hermes/cron/jobs.json` — this is a regular file that `search_files` can read even when the session database is down. The cron definitions contain the exact SSH commands used for monitoring, including hosts, users, and file paths.

## Verification

After extracting credentials, verify immediately:
```bash
ssh djg6228@spark-85e8.local "hostname"
# Should return: spark-85e8.local
```

## Also Check

- `~/.ssh/config` and included configs for host aliases
- `~/.hermes/CHECKPOINT-*.md` files for system state snapshots
- `~/.hermes/config.yaml` for provider definitions (spark-bf16, spark-fp8)
