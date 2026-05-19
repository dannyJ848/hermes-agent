---
name: hermes-unified-restart
description: Unified Hermes restart with 7-contingency safety net. Manual kill + restart flow with checkpoint/marker recovery, multiple escape hatches, and new-agent handoff.
version: "3.0"
---

# Hermes Unified Restart (with Safety Net)

## Quick Usage

```bash
# Safe restart with full safety net (recommended)
bash ~/.hermes/scripts/safe-restart.sh

# Dry run first (validates patches, backs up, copies context to clipboard)
bash ~/.hermes/scripts/safe-restart.sh --dry-run

# Emergency restore (works with no gateway running)
bash ~/.hermes/scripts/emergency-restore.sh [checkpoint_label]

# Give to a new agent if everything fails
bash ~/.hermes/scripts/new-agent-handoff.sh
```

## CRITICAL FACTS (learned the hard way)

1. **`hermes gateway restart --all` DOES NOT EXIST.** The previous session designed `_unified_restart()` and `--all` flag but they were never merged into the running codebase. Do NOT rely on them.
2. **The restart flow is MANUAL:** kill processes via Python → `hermes gateway restart` (no `--all`) → verify.
3. **Git stash is a trap:** Running `safe-restart.sh` stashes your working tree. After ANY failure, you MUST `git stash pop` to get patches back. The `--dry-run` mode ALSO stashes!
4. **SAFETY_NET directory blocks `git stash pop`:** Always `rm -rf ~/hermes-agent/SAFETY_NET/` before popping stash.
5. **The running gateway caches Python modules:** After patching files on disk, you MUST restart the gateway for patches to take effect. `hermes gateway restart` (without `--all`) does this.

## What the Safe Restart Does (in order)

1. **STASH** git working state for instant rollback
2. **VALIDATE** all patched files compile (syntax check)
3. **BACKUP** all checkpoints to 3 independent locations
4. **COPY** checkpoint context to clipboard (your last-resort safety net)
5. **LAUNCH** 60-second watchdog (detects gateway failure, attempts manual restart)
6. **KILL** all Hermes processes via Python (not CLI flag)
7. **START** gateway fresh with `hermes gateway run --replace &`
8. **VERIFY** via watchdog

## Files That ACTUALLY Exist

- `~/.hermes/scripts/safe-restart.sh` — Full safety net orchestration script (the real restart mechanism)
- `~/.hermes/scripts/emergency-restore.sh` — Standalone restore (no gateway needed)
- `~/.hermes/scripts/new-agent-handoff.sh` — Complete diagnostic + context dump for a fresh agent
- `gateway/run.py` — Restart-marker detection block (inserted after auto-reset handling, ~line 2313). Runs for ALL sessions. Cron guard included.
- `cli.py` — Yellow warning after welcome banner if unconsumed marker exists
- `hermes_cli/gateway.py` — `_save_pre_restart_checkpoint()` and `_clear_all_pycache()` DO exist. `_unified_restart()` and `_kill_all_hermes_processes()` DO NOT.

## Files That DO NOT Exist (despite earlier claims)

- `_unified_restart()` function in `hermes_cli/gateway.py` — was designed but never merged
- `_kill_all_hermes_processes()` in `hermes_cli/gateway.py` — same
- `--all` flag for `hermes gateway restart` — never wired into `hermes_cli/main.py`
- `hermes_cli/main.py` restart subparser `--all` argument — never added

The kill logic is inlined in `safe-restart.sh` as a Python one-liner instead.

## Patching Details

### Patch A: Marker check ungated (gateway/run.py ~line 2313)
The marker check block was INSERTED (not replacing existing code) between the auto-reset handling and auto-load skill sections. Key design: runs for ALL sessions, not gated by `_is_new_session`.

### Patch B: Cron guard (inside Patch A block)
Only sessions with `source.platform.value in ("cli", "telegram", "discord", "matrix")` can consume (delete) the marker. Cron/automated sessions log but don't delete.

### Patch C: CLI fallback (cli.py ~line 6876)
After `self.console.print(f"[{_welcome_color}]{_welcome_text}[/]")`, added marker file check with yellow warning.

## 7 Failure Modes → 7 Contingencies

| # | Failure | Contingency |
|---|---------|-------------|
| 1 | Patch has syntax error | Syntax check BEFORE restart; auto-rollback via git stash |
| 2 | Checkpoint corrupted/deleted | Triple backup in 3 locations (~/.hermes/workspace/checkpoint-backups/, /tmp/hermes-checkpoint-backup/, ~/hermes-agent/SAFETY_NET/) |
| 3 | Context totally lost | Clipboard pre-loaded BEFORE restart happens |
| 4 | Marker injection fails | CLI prints yellow warning on startup if marker exists |
| 5 | Cron eats marker first | Cron guard — only interactive sessions consume marker |
| 6 | Gateway dies, won't restart | 60s watchdog detects, attempts manual restart |
| 7 | Total catastrophe | `new-agent-handoff.sh` — full diagnostics + context for a fresh agent |

## Escape Hatches (if things go wrong)

```bash
# Give to new agent — runs ALL diagnostics automatically
bash ~/.hermes/scripts/new-agent-handoff.sh

# Read your checkpoint without gateway
bash ~/.hermes/scripts/emergency-restore.sh

# Revert all patches (remove SAFETY_NET first!)
rm -rf ~/hermes-agent/SAFETY_NET/
cd ~/hermes-agent && git stash pop

# Start gateway manually
cd ~/hermes-agent && source venv/bin/activate && hermes gateway run --replace &

# Restart gateway (picks up patched code on disk)
hermes gateway restart
```

## GATEWAY INJECTION IS BROKEN — USE CLIENT-SIDE INJECTION

**The gateway-side marker injection in `run.py` (~line 2314) DOES NOT FIRE for CLI sessions.** Confirmed across 3 separate attempts with debug logging. The `_handle_message_with_agent` code path is reached but the marker check never logs — likely the CLI uses a different dispatch path through the API server that bypasses the patched code.

**Working approach (client-side injection in `cli.py`):**
1. Write restore context to `~/.hermes/.restore-context.txt` (plain text, self-contained)
2. Patch `cli.py`'s `chat()` method to check for this file on every call
3. If found, prepend the full restore context to the user's first message: `message = restore_ctx + "\n\nUser says: " + message`
4. Clean up both `restore-context.txt` AND `restart-marker` after injection
5. This works because it runs in the CLI process, not the gateway

**The CLI warning (Patch C) DOES work** — the yellow "RESTART MARKER DETECTED" banner appears correctly. It's just the gateway injection that fails silently.

## Pitfalls

- **Gateway injection does NOT work for CLI**: The `context_prompt` modification in `run.py` never reaches CLI sessions. Use `cli.py` `chat()` injection instead.
- **Git stash dry-run trap**: `safe-restart.sh --dry-run` STASHES your working tree. You MUST `git stash pop` after dry-run to restore patches.
- **SAFETY_NET blocks stash pop**: `rm -rf ~/hermes-agent/SAFETY_NET/` before `git stash pop`.
- **Running gateway caches modules**: Patched code on disk ≠ running code. Must `hermes gateway restart` after patching. Clear `__pycache__` too: `find ~/hermes-agent -type d -name __pycache__ -exec rm -rf {} +`
- **`hermes gateway restart --all` does not exist**: Use `bash ~/.hermes/scripts/safe-restart.sh` instead.
- **Watchdog health check may be wrong port**: The watchdog checks localhost:8321 and 8080 but the gateway uses port 8642. Watchdog failure ≠ gateway failure. Always `ps aux | grep gateway` to verify.
- **Marker file at ~/.hermes/.restart-marker**: Created by `_save_pre_restart_checkpoint()`. If it exists, the CLI will try to inject restore context. Clean it up manually if stale: `rm ~/.hermes/.restart-marker ~/.hermes/.restore-context.txt`.
- **safe-restart.sh uses `set -uo pipefail` (not `-euo pipefail`)**: Some git commands return non-zero on success (e.g., stash when tree becomes clean), which `-e` would catch as failure.
- **launchd uses the venv's working tree directly**: `hermes gateway restart` → `launchctl kickstart -k` → runs `/Users/dannygomez/hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace`. The venv imports directly from `~/hermes-agent/` (not an installed copy). So patches on disk ARE loaded after restart — but only if `__pycache__` is cleared.
