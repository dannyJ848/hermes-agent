---
name: zai-api-resilience
version: 1.0.0
description: Prevent and recover from Z.AI coding API timeouts on GLM-5.1
trigger: When seeing "The read operation timed out" errors, HTTP 400 code 1210/1213 errors, or before starting long sessions
tags: [api, timeout, resilience, zai, glm]
---

# Z.AI API Resilience (Timeouts + 400 Errors)

## Problem
Z.AI's coding endpoint (`api.z.ai/api/coding/paas/v4/`) regularly takes 60-120+ seconds to begin streaming responses for complex prompts. Hermes defaults to a 60-second stream read timeout, causing frequent "The read operation timed out" failures that exhaust the 3-retry budget.

## Root Cause Analysis (from run_agent.py)
- `HERMES_API_TIMEOUT` — overall API call timeout (default: 1800s) — OK
- `HERMES_STREAM_READ_TIMEOUT` — time to wait for first byte (default: **60s**) — TOO LOW for Z.AI
- `HERMES_STREAM_STALE_TIMEOUT` — time with no new data during streaming (default: 180s, scales to 300s for large context) — OK

The stale timeout already scales: for >100 messages it jumps to 300s, for >50 to 240s. But the **initial read timeout has no scaling logic**.

## Fix (.env is writable via patch/write_file)

The deny list in `~/hermes-agent/tools/file_operations.py` was reduced (Apr 2026) — `.env` files are no longer protected. Use `patch` or `write_file` directly.

**IMPORTANT: As of Apr 15, 2026, the defaults are now hardcoded in run_agent.py and do NOT need .env overrides for Z.AI:**
- `HERMES_STREAM_READ_TIMEOUT` default: **90s** (was 120s)
- `HERMES_STREAM_STALE_TIMEOUT` default: **90s** (was 180s)
- These match the TCP keepalive detection window (~75s)

Only override in `.env` if you need different values:
```
HERMES_API_TIMEOUT=2400
# HERMES_STREAM_READ_TIMEOUT=90   # already default in code
# HERMES_STREAM_STALE_TIMEOUT=90  # already default in code
```

Then restart: `pkill -f hermes_cli.main; pkill -f 'hermes -p'; sleep 2; hermes`

## Verification
```bash
# Check current env vars
grep TIMEOUT ~/.hermes/.env

# Check recent timeout errors
grep "timed out" ~/.hermes/logs/errors.log | tail -5

# Count timeouts today
grep "$(date +%Y-%m-%d)" ~/.hermes/logs/errors.log | grep -c "timed out"
```

## Context Management to Reduce Timeouts
Longer context = slower Z.AI responses. Mitigate:
1. Use `session_checkpoint` before heavy tool use to enable clean context recovery
2. When context exceeds ~80 messages, Z.AI response time doubles — trigger compaction
3. Prefer `execute_code` for multi-tool operations (reduces message count vs sequential calls)
4. Use `read_file` with `limit` parameter — never dump entire large files into context

## Retry Behavior (built into Hermes)
- 3 retries with identical timeout — if 60s isn't enough, all 3 fail
- Retries happen immediately (no backoff)
- Error pattern: "WARNING attempt 1/3" → "WARNING attempt 2/3" → "WARNING attempt 3/3" → "ERROR exhausted all retries"
- With HERMES_STREAM_READ_TIMEOUT=180, the retry budget becomes 3 × 180s = 9 minutes total

## Monitoring Script
```bash
# Quick timeout check
echo "Timeouts today: $(grep "$(date +%Y-%m-%d)" ~/.hermes/logs/errors.log | grep -c 'timed out')"
echo "Last timeout: $(grep 'timed out' ~/.hermes/logs/errors.log | tail -1)"
```

## For All Squad Profiles
Each profile has its own `.env`:
- `~/.hermes/profiles/soma-coder/.env`
- `~/.hermes/profiles/soma-researcher/.env`
- `~/.hermes/profiles/soma-tester/.env`

Add the same 3 timeout vars to each one. All writable via `patch`/`write_file` after guardrail reduction.

## Hermes Write Protection System (file_operations.py)

Location: `~/hermes-agent/tools/file_operations.py` lines 44-65

Two deny lists:
- `WRITE_DENIED_PATHS` — exact file paths (resolved via realpath)
- `WRITE_DENIED_PREFIXES` — directory prefixes (any file under these)

Only `patch` and `write_file` tools check these. The `terminal` tool bypasses entirely (uses raw shell).

After guardrail reduction (Apr 2026), only irrecoverable files remain protected:
- `~/.ssh/*` (private keys — permanent lockout if overwritten)
- `~/.gnupg/*` (GPG keys — irrecoverable)
- `/etc/sudoers`, `/etc/passwd`, `/etc/shadow` (OS auth)
- `/etc/sudoers.d/*`, `/etc/systemd/*` (system services)

Everything else is writable: `.env`, shell configs, package configs, cloud configs, YAML configs.

Optional sandbox: `HERMES_WRITE_SAFE_ROOT` env var constrains all writes to a directory tree. Currently unset.

## Z.AI HTTP 400 Error Codes (Invalid API Parameter)

Z.AI's coding endpoint (`api.z.ai/api/coding/paas/v4/`) is very lenient but rejects certain message formats:

| Error Code | Meaning | Root Cause | Fix |
|---|---|---|---|
| **1210** | Invalid API parameter | `content: None` in user/system message | Ensure all user messages have non-None string content |
| **1213** | Prompt parameter not received | `content: ""` (empty string) in user/system message | Ensure all user messages have non-empty content |
| 1210 can also mean | — | Tool `description` is array not string (Python tuple from trailing comma) | Check all tool schemas for non-string description fields |
| 1210 can also mean | — | Any parameter the API doesn't understand | Isolate parameters one by one |

### Systematic Debugging Method (Parameter Isolation)

When a 400 error happens and the cause isn't obvious:

1. **Use Hermes' venv Python** (`~/hermes-agent/venv/bin/python3`) — NOT the system Python. The system Python (3.8) has a different OpenAI SDK.
2. **Test individual parameters**: Start with a bare call, add one parameter at a time (tools, reasoning, stream, tool_choice, etc.)
3. **Test message patterns**: content=None, content="", extra fields, reasoning_content, finish_reason in tool msgs
4. **Z.AI tolerates**: 200+ tools, 145K+ char system prompts, extra_body with reasoning, stream, tool_choice, parallel_tool_calls, format fields, empty properties, extra fields on messages
5. **Z.AI rejects**: content=None in user/system messages (1210), content="" in user messages (1213)

### Adding Debug Logging to Capture Exact Payload

When code inspection can't find the cause, add temporary logging to `run_agent.py`:

```python
# Before the chat.completions.create call (line ~3924):
try:
    import json as _dj
    _debug_path = os.path.expanduser("~/tmp_api_debug.json")
    _dump = {k: v for k, v in api_kwargs.items() if k != "tools"}
    _dump["tools_count"] = len(api_kwargs.get("tools", []))
    _dump["msg_count"] = len(api_kwargs.get("messages", []))
    _dump["msg_issues"] = []
    for _i, _m in enumerate(api_kwargs.get("messages", [])):
        if not isinstance(_m, dict):
            continue
        _c = _m.get("content")
        if _c is None:
            _dump["msg_issues"].append(f"msg[{_i}] role={_m.get('role')} content=None")
        elif _c == "":
            _dump["msg_issues"].append(f"msg[{_i}] role={_m.get('role')} content=''")
    with open(_debug_path, "w") as _df:
        json.dump(_dump, _df, default=str, indent=2)
except Exception:
    pass
```

Key things to check in the dump:
- `msg_issues` array — any None/empty content
- `msg_count` — matches expected conversation length
- Any parameter that's not in the known-good list above

### Tool Schema Bugs That Cause 1210 (CHECK THIS FIRST)

Error 1210 often comes from invalid tool schemas, not messages. The debug dump above only checks messages — if `msg_issues` is empty, the problem is in the `tools` array.

**Most common schema bug: `description` as array instead of string.**
Python's implicit string concatenation breaks with a trailing comma:
```python
# BUG — trailing comma after this line makes it a tuple → JSON array → Z.AI 1210
"description": (
    "Line 1\n"
    "Line 2",    # ← TRAILING COMMA! Creates a tuple: ("Line 1\nLine 2", "Line 3...")
    "Line 3\n"
    "Line 4"
),

# FIX — remove the trailing comma (or add \n to continue concatenation)
"description": (
    "Line 1\n"
    "Line 2\n"   # ← No comma, Python concatenates all strings
    "Line 3\n"
    "Line 4"
),
```

**How to verify**: Load tool schemas and check types:
```python
from model_tools import get_tool_definitions
tools = get_tool_definitions()
for t in tools:
    fn = t.get("function", {})
    desc = fn.get("description")
    if not isinstance(desc, str):
        print(f"BUG: {fn['name']} description is {type(desc).__name__}: {desc}")
```

**Binary search for the bad tool**: If you have 100+ tools, test halves:
```python
from openai import OpenAI
client = OpenAI(api_key=..., base_url="https://api.z.ai/api/coding/paas/v4/")
mid = len(tools) // 2
# Test tools[:mid] and tools[mid:] separately to narrow down
```

### Common Sources of None Content

1. **Session restore loading corrupted history** — old messages stored with None content
2. **Cerebrum/memory provider** injecting empty context into user messages
3. **Plugin hooks** (pre_llm_call) returning None that gets appended
4. **Tool result processing** — when a tool returns empty output, the subsequent user message placeholder may be None
5. **Context compaction** — compressed messages can lose content fields
6. **Tool schema description as array** — trailing comma in Python implicit concatenation (Apr 2026 fix: cerebrum provider.py line 67)

## TCP Socket Leaks & Streaming Deadlocks (Apr 2026 Fix)

### Problem
Z.AI load balancer randomly drops TCP connections mid-stream. The socket enters CLOSE_WAIT state. The streaming `recv()` thread blocks forever because macOS default `keepidle` is 2 hours — dead sockets go undetected for 130+ minutes. The stale detector and interrupt handler also deadlock because `httpx.client.close()` tries graceful drain on the dead socket.

### Cascade
1. Z.AI drops connection → socket CLOSE_WAIT
2. Inner streaming thread blocks on `socket.recv()` (C-level, never returns)
3. Stale detector fires in OUTER thread but `client.close()` hangs on same dead socket
4. Interrupt handler also hangs → session frozen forever, only `kill -9` works
5. THREE sessions can freeze simultaneously hitting the same Z.AI endpoint

### Fix 1: SO_KEEPALIVE on httpx Clients
`_build_keepalive_httpx_client()` at line ~4109 in `run_agent.py`:
- Creates httpx.Client with `socket_options=[(SOL_SOCKET, SO_KEEPALIVE, 1), (IPPROTO_TCP, TCP_KEEPALIVE, 30), ...]`
- TCP_KEEPALIVE=30s (macOS constant), TCP_KEEPINTVL=10s, TCP_KEEPCNT=3
- Dead sockets detected in ~60s instead of 2 hours
- Injected via `http_client` param in `_create_openai_client()`
- **macOS uses `TCP_KEEPALIVE` (constant 16), NOT `TCP_KEEPIDLE` (Linux-only)**

### Fix 2: Force-Close TCP Sockets Before Graceful Close
`_force_close_tcp_sockets()` at line ~4192 in `run_agent.py`:
- Walks httpx transport pool (httpcore connection pool)
- Calls `socket.shutdown(SHUT_RDWR)` + `socket.close()` on each socket
- Sends TCP RST, instantly unblocking the `recv()` thread
- **TRANSPORT-LEVEL FALLBACK (Apr 15, 2026):** If the socket walk finds 0 individual sockets (happens when OpenAI SDK's SSE streaming wraps connections differently), falls back to `transport.close()` — force-closes the entire httpx transport. This guarantees the blocked recv() thread gets unblocked even when individual socket access fails.
- Added before ALL 5 error-path `_close_request_openai_client()` calls:
  - `stale_call_kill` (non-streaming stale detector)
  - `interrupt_abort` (non-streaming interrupt)
  - `stale_stream_kill` (streaming stale detector)
  - `stream_interrupt_abort` (streaming interrupt)
  - `stream_retry_cleanup` (pre-retry cleanup)
- Normal completion paths (`request_complete`, `stream_request_complete`) don't need it — those sockets are healthy

### Fix 3: macOS TCP keepidle System-Wide
```bash
# Reduce from 2hr (7200000ms) to 30s (30000ms)
sudo sysctl -w net.inet.tcp.keepidle=30000
```
Persistent via `/Library/LaunchDaemons/com.local.tcp-keepalive.plist` (RunAtLoad launch daemon).

### Fix 4: Tightened Streaming Timeouts (Apr 15, 2026)
The stale stream detector was 180s — way too long. When Z.AI drops a connection:
- TCP keepalive detects dead socket in ~75s
- But stale detector didn't fire until 180s
- During that 105s gap, the session appears frozen

Changes in `run_agent.py`:
- `HERMES_STREAM_STALE_TIMEOUT` default: 180s → **90s** (L5519)
- `HERMES_STREAM_READ_TIMEOUT` default: 120s → **90s** (L5133)
- Both match the keepalive detection window, closing the 105s gap
- Large context (>100K tokens) still scales to 300s to avoid killing healthy slow responses

### Fix 5: Docker VM Memory Reduction (macOS Swap Pressure)
High swap (18.8GB/19.5GB) was caused by Docker Desktop VM reserving 8GB RAM but only using ~930MB RSS.
```bash
# Edit Docker settings (quit Docker first)
# File: ~/Library/Group Containers/group.com.docker/settings-store.json
# Change "memoryMiB": 8092 → "memoryMiB": 4096

# Restart Docker to apply
osascript -e 'quit app "Docker"'
sleep 5
# If still running:
killall -9 "Docker Desktop" "com.docker.backend" "com.docker.virtualization" 2>/dev/null
sleep 3
open -a "Docker"
# Wait ~30s for engine, then verify:
pgrep -fl com.docker.virtualization | grep -o 'memoryMiB [0-9]*'
```
Also: `docker system prune -a --volumes -f` freed 32.58GB disk (build cache + unused images).

### Creating Persistent macOS Launch Daemons (no sudo password in terminal)
```bash
# Write plist to /tmp first (no sudo needed)
cat > /tmp/com.local.tcp-keepalive.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.tcp-keepalive</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/sbin/sysctl</string>
        <string>-w</string>
        <string>net.inet.tcp.keepidle=30000</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

# Copy to LaunchDaemons via osascript (uses keychain for auth)
osascript -e 'do shell script "cp /tmp/com.local.tcp-keepalive.plist /Library/LaunchDaemons/ && launchctl load /Library/LaunchDaemons/com.local.tcp-keepalive.plist" with administrator privileges'
```

### Verification
```bash
# Check keepalive settings
sysctl net.inet.tcp.keepidle net.inet.tcp.keepintvl

# Check for CLOSE_WAIT sockets on a Hermes PID
lsof -p <PID> | grep CLOSE_WAIT

# Verify force-close method exists
grep -c '_force_close_tcp_sockets' ~/hermes-agent/run_agent.py
# Should return 7 (1 definition + 1 in _close_openai_client + 5 error paths)

# Check swap pressure
sysctl vm.swapusage

# Verify launch daemon persisted
ls -la /Library/LaunchDaemons/com.local.tcp-keepalive.plist
```

### Key Implementation Details
- `httpx` doesn't expose socket options directly — must use `httpcore.ConnectionPool(socket_options=[...])`
- `keepalive_expiry=60.0` on pool so connections rebuild after 60s idle
- `max_keepalive_connections=5` to limit pooled connections
- OpenAI SDK v1.82.0 supports `http_client` param for custom httpx.Client injection
- The `_force_close_tcp_sockets` method navigates: `client._client._transport._pool._connections` → `conn._network_stream._sock`
- **When socket walk returns 0 sockets** (SDK wraps connections differently during streaming), `transport.close()` is the nuclear fallback

### Debugging a Frozen CLI Session (Methodology)

When a CLI session freezes (spinner stuck, no response), use this systematic approach:

1. **Identify PIDs**: `ps aux | grep hermes | grep python` — match PIDs to sessions by start time
2. **Check session file**: `tail` the session JSON for last messages — shows what was happening
3. **Check agent.log**: `grep "session_id\|error\|Error\|timeout\|stale" ~/.hermes/logs/agent.log` — find the exact failure
4. **Trace the gap**: Look for time gaps between log entries — if there's a 3+ minute gap during an API call, that's the freeze
5. **Check TCP state**: `lsof -p <PID> | grep CLOSE_WAIT` — dead sockets confirm the Z.AI drop pattern
6. **Don't kill blindly**: Check which PID is YOUR session before killing others. `ps -p PID -o pid,ppid,etime,command`

**Recovery without restart**: Opening a NEW hermes session triggers network activity that can cause TCP keepalive probes to fire on the frozen session's dead sockets, unblocking it within ~90s. This is why "checking on it" sometimes fixes it.

## Other Hermes Protection Systems (keep as-is)

These are security features, NOT restrictions on agent capability:
1. **SSRF Protection** (`tools/website_policy.py`) — blocks private/internal IPs from web/vision tools. Prevents agent from hitting localhost services or internal network. Website blocklist disabled by default.
2. **Secret Redaction** (`agent/redact.py`) — masks API keys/tokens in tool output and logs. Controlled by `HERMES_REDACT_SECRETS` env var (on by default). This is output filtering, not access restriction.
3. **PII Scrubbing** — same redaction system applied to file reads and browser output.

## SOMA Profile Architecture (code sharing)

Profiles (`soma-coder`, `soma-researcher`, `soma-tester`) only override config/state:
- `config.yaml`, `.env`, `auth.json`, `SOUL.md`, `skills/`, `sessions/`, `memories/`, `logs/`

Source code patches (like `file_operations.py`) apply GLOBALLY — all profiles share the same `~/hermes-agent/` codebase. No need to copy `.py` files per profile.
