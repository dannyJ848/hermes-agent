---
name: hermes-session-operations
title: Hermes Session Operations — Debugging, Restarting, and Recovery
description: |
  Comprehensive guide for diagnosing stuck Hermes sessions, safely restarting the agent,
  patching the agent loop, and debugging TUI commands. Covers all operational
  scenarios where the agent needs intervention to recover or restart.
triggers:
  - When a Hermes session is stuck, frozen, or unresponsive
  - When restarting Hermes after crashes or updates
  - When patching run_agent.py to change core behavior
  - When debugging TUI slash commands
  - When the user says "did you get stuck?" or "restart hermes"
category: software-development
---

# Hermes Session Operations

## Overview

This skill covers the full operational lifecycle of a Hermes session: diagnosing failures,
safely recovering, patching core behavior, and debugging UI issues.

---

## Section 1: Stuck Session Diagnosis

### Symptom Checklist

- [ ] Session shows no output for 30+ seconds
- [ ] CPU usage high (>20%) but no responses
- [ ] Repeated rate limit (429) error messages
- [ ] Context bar at 90-100% with "compaction approaching"
- [ ] Multiple Hermes sessions running simultaneously
- [ ] Session shows "New message detected, interrupting..." then hangs
- [ ] Session at low context (20-30%) but frozen
- [ ] CLOSE_WAIT sockets visible in lsof output

### Diagnosis Steps

**Step 0: Socket deadlock check**
```bash
for pid in $(pgrep -f 'python.*hermes' | grep -v $(pgrep -f 'hermes_cli.main gateway')); do
    close_wait=$(lsof -p $pid 2>/dev/null | grep -c CLOSE_WAIT)
    echo "PID $pid: $close_wait CLOSE_WAIT sockets"
done
```
If CLOSE_WAIT found → Pattern 2c (Z.AI socket deadlock).

**Step 1: Count running sessions**
```bash
ps aux | grep 'python.*hermes' | grep -v grep | grep -v gateway | grep -v biomcp
```
3+ sessions → rate limit contention.

**Step 2: Check session state**
```bash
ps -eo pid,rss,pcpu,stat,comm | grep hermes | grep -v grep
```
- High CPU + low RSS → retry loop
- Low CPU + high RSS → memory pressure
- Stat=S+ → waiting on input
- Stat=R → actively computing

**Step 3: Check network**
```bash
lsof -p <PID> 2>/dev/null | grep TCP
```
- CLOSE_WAIT → dead connection
- ESTABLISHED → still trying

**Step 4: Check memory pressure (macOS)**
```bash
sysctl vm.swapusage
vm_stat | head -5
```

### Root Cause Patterns

**Pattern 1: Rate Limit Storm + Compaction Deadlock (MOST COMMON)**
Multiple sessions → all hit 429 → retry 3x → error messages fill context → 100% → compaction triggers → compaction ALSO needs API → gets 429'd → **deadlock**.

**Fix:** Kill stuck sessions. One session per API key.

**Pattern 2: Memory Pressure Freeze**
Docker VM (8GB) + Safari (~4GB) + multiple sessions → swap full → thrashing.

**Fix:** `docker system prune -a --volumes`. Reduce Docker VM to 4096MB. Close Safari tabs.

**Pattern 2b: Interrupt Handler Deadlock**
API drops → CLOSE_WAIT → interrupt fires → tries to cancel HTTP → blocked on same dead socket → **deadlock**.

**Fix:** Only `kill -9` works. SIGTERM often fails on kernel I/O block.

**Pattern 2c: Z.AI Socket Leak + Streaming Deadlock**
Z.AI load balancer drops TCP mid-stream → socket CLOSE_WAIT → streaming thread stuck in `socket.recv()` → stale detector in OUTER thread can't help → interrupt tries `close()` → also blocks → **deadlock**.

**macOS TCP keepalive defaults:**
```
net.inet.tcp.keepidle = 7,200,000 ms (2 HOURS!)
net.inet.tcp.keepintvl = 75,000 ms
net.inet.tcp.keepcnt = 8
Total detection: 7,200 + (75 × 8) = 7,800s = 130 MINUTES
```

**Fix hierarchy:**
1. Reduce Docker VM memory: `--memoryMiB 4096`
2. `docker system prune -a --volumes` (~51GB reclaimed)
3. Add SO_KEEPALIVE to httpx transport, or reduce `net.inet.tcp.keepidle`
4. Fix streaming deadlock: stale detector inside streaming thread
5. Hermes env: `HERMES_STREAM_STALE_TIMEOUT=180`, `HERMES_STREAM_READ_TIMEOUT=120`

**Pattern 3: Zombie Session**
Old session still running, consuming API quota.

**Fix:** `kill <PID>`.

### Prevention

Add to distillation plugin `pre_llm_call`:
```python
if hasattr(_on_post_api_request, '_recent_429_count'):
    if _on_post_api_request._recent_429_count >= 3:
        lines.append("[RATE LIMIT THROTTLE] 3+ consecutive 429s. Reduce frequency.")
```

---

## Section 2: Safe Restart Protocol

### Quick Usage

```bash
# Safe restart with full safety net
bash ~/.hermes/scripts/safe-restart.sh

# Dry run first
bash ~/.hermes/scripts/safe-restart.sh --dry-run

# Emergency restore (no gateway needed)
bash ~/.hermes/scripts/emergency-restore.sh [checkpoint_label]

# New agent handoff
bash ~/.hermes/scripts/new-agent-handoff.sh
```

### Critical Facts

1. `hermes gateway restart --all` **DOES NOT EXIST**. Use `safe-restart.sh`.
2. Restart flow is **MANUAL**: kill processes → `hermes gateway restart` → verify.
3. **Git stash trap:** `safe-restart.sh` stashes working tree. After ANY failure, `git stash pop` to restore patches. `--dry-run` ALSO stashes!
4. **SAFETY_NET blocks stash pop:** `rm -rf ~/hermes-agent/SAFETY_NET/` before popping.
5. **Gateway caches modules:** Patches on disk ≠ running code. Must restart gateway + clear `__pycache__`.

### What safe-restart.sh Does

1. STASH git state
2. VALIDATE patched files compile
3. BACKUP checkpoints to 3 locations
4. COPY checkpoint context to clipboard
5. LAUNCH 60s watchdog
6. KILL all Hermes processes via Python
7. START gateway fresh
8. VERIFY via watchdog

### 7 Failure Modes → 7 Contingencies

| # | Failure | Contingency |
|---|---------|-------------|
| 1 | Patch syntax error | Syntax check + git stash rollback |
| 2 | Checkpoint corrupted | Triple backup in 3 locations |
| 3 | Context lost | Clipboard pre-loaded |
| 4 | Marker injection fails | CLI yellow warning on startup |
| 5 | Cron eats marker | Cron guard — only interactive sessions consume |
| 6 | Gateway dies | 60s watchdog detects, manual restart |
| 7 | Total catastrophe | `new-agent-handoff.sh` — full diagnostics |

### Escape Hatches

```bash
# Revert all patches
rm -rf ~/hermes-agent/SAFETY_NET/
cd ~/hermes-agent && git stash pop

# Start gateway manually
cd ~/hermes-agent && source venv/bin/activate && hermes gateway run --replace &

# Clean stale markers
rm ~/.hermes/.restart-marker ~/.hermes/.restore-context.txt
```

---

## Section 3: Agent Loop Patching

### Why This Is Hard

- `run_agent.py` is ~9000 lines with deeply nested control flow
- Main loop: `while api_call_count < self.max_iterations` at ~line 6688
- Tool calls vs text branch at ~line 8054 (`if assistant_message.tool_calls:`)
- "No tool calls" / break path at ~line 8299

### Finding Target Lines

Use Python scripts, NOT bash grep with complex patterns:
```python
with open("run_agent.py") as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if "YOUR TARGET STRING" in line:
        print(f"Line {i}: {line.rstrip()}")
```

### Key Landmarks

| Line | Content |
|------|---------|
| 6688 | `while api_call_count < self.max_iterations` — main loop start |
| 8054 | `if assistant_message.tool_calls:` — tool vs text branch |
| 8299 | `else: # No tool calls` — break path |
| 9042 | `aggressive_continue` flag check (if patched) |
| 9079 | `_is_silent` guard (if patched) |

### Common Patches

**Anti-stop / aggressive_continue:**
When `aggressive_continue: true` in config.yaml AND text-only response AND platform is cron/gateway/telegram/discord:
- Log stop to cerebrum `stop_detection_log`
- Inject `[AGGRESSIVE CONTINUE]` message
- `continue` loop instead of `break`

**Silent guard fix:**
Change from exact match `in ('[SILENT]', ...)` to:
1. Strip zero-width chars (U+200B, U+200C, U+200D, U+FEFF)
2. Use substring check: `'[SILENT]' in cleaned`
3. Add debug logging with `repr()`

---

## Section 4: TUI Command Debugging

### Architecture (3 Layers)

1. **Python command registry** — `hermes_cli/commands/*.py`
2. **tui_gateway JSON-RPC bridge** — `tui_gateway.py`
3. **Ink/TypeScript frontend** — `frontend/src/components/terminal.tsx`

### When to Use

- Command exists in backend but not in autocomplete
- Works in CLI but not TUI
- Config persists but UI doesn't update
- Command needs to be added to both layers

### Diagnostic Steps

1. Check command exists in Python registry:
   ```bash
   grep -rn "def cmd_" hermes_cli/commands/ --include="*.py"
   ```
2. Check tui_gateway exposes it:
   ```bash
   grep -n "cmd_" hermes_cli/tui_gateway.py
   ```
3. Check frontend registers it:
   ```bash
   grep -n "commandName" frontend/src/components/terminal.tsx
   ```
4. Verify all 3 layers are in sync

---

## Key Numbers

- GLM-5.1 rate limit: ~10 RPM for shared keys
- 4 sessions × 3 retries = 12 API calls per failed attempt
- Safe concurrent sessions: 1-2 per API key
- Context compaction adds 1 API call (deadlock trigger)
- macOS TCP keepidle default: 2 HOURS
- Docker VM default: 8092MB → reduce to 4096MB

## References

- `references/stuck-session-patterns.md` — Full pattern catalog with fixes
- `references/safe-restart-scripts.md` — Script internals and contingency details
- `references/agent-loop-landmarks.md` — run_agent.py line numbers and patch templates
- `references/tui-layer-sync-checklist.md` — 3-layer debugging checklist
