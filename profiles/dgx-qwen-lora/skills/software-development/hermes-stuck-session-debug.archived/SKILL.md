---
name: hermes-stuck-session-debug
version: "1.0.0"
description: Diagnose and fix Hermes CLI sessions that freeze or get stuck. Covers rate limit storms, context compaction deadlocks, memory pressure, and zombie processes.
trigger: Hermes CLI session appears frozen, stuck, or unresponsive. User reports "did you get stuck?" or similar.
---

# Hermes Stuck Session Debug

## Symptom Checklist

- [ ] Session shows no output for 30+ seconds
- [ ] CPU usage high (>20%) but no responses
- [ ] Repeated rate limit (429) error messages in terminal
- [ ] Context bar at 90-100% with "compaction approaching"
- [ ] Multiple Hermes sessions running simultaneously
- [ ] Session shows "New message detected, interrupting..." then hangs
- [ ] Session at low context (20-30%) but frozen — NOT a compaction issue
- [ ] CLOSE_WAIT sockets visible in lsof output

## Diagnosis Steps (run in order)

### Step 0: Quick check — is it a socket deadlock?
```bash
# If session shows "interrupting..." or is frozen at LOW context, check for dead sockets
for pid in $(pgrep -f 'python.*hermes' | grep -v $(pgrep -f 'hermes_cli.main gateway')); do
    close_wait=$(lsof -p $pid 2>/dev/null | grep -c CLOSE_WAIT)
    echo "PID $pid: $close_wait CLOSE_WAIT sockets"
done
```
If any session has CLOSE_WAIT → **Pattern 2c (Z.AI socket deadlock)**. Skip to that section.

### Step 1: Count running Hermes sessions
```bash
ps aux | grep 'python.*hermes' | grep -v grep | grep -v gateway | grep -v biomcp
```
If 3+ sessions found → likely **rate limit contention**.

### Step 2: Check stuck session state
```bash
ps -eo pid,rss,pcpu,stat,comm | grep hermes | grep -v grep
```
- **High CPU + low RSS** → retry loop (rate limit storm)
- **Low CPU + high RSS** → memory pressure
- **Stat=S+** → waiting on terminal input (might be fine)
- **Stat=R** → actively computing (might be fine)

### Step 3: Check network connections
```bash
lsof -p <PID> 2>/dev/null | grep TCP
```
- **CLOSE_WAIT** → dead connection, session won't recover
- **ESTABLISHED to api endpoint** → still trying

### Step 4: Check memory pressure (macOS)
```bash
sysctl vm.swapusage
vm_stat | head -5
```
- **Swap >80% used** → system thrashing, everything slow
- Llama.cpp models use 1-3 GB each, check total:
```bash
ps -eo rss,comm | grep llama | awk '{s+=$1} END {printf "%.0f MB\n", s/1024}'
```

### Step 5: Check rate limit evidence
Look for these in the stuck session's terminal:
- `⚠️ API call failed (attempt 1/3): RateLimitError [HTTP 429]`
- `⚠ Max retries (3) exhausted — trying fallback...`
- `❌ Rate limited after 3 retries`

## Root Cause Patterns

### Pattern 1: Rate Limit Storm + Compaction Deadlock (MOST COMMON)
**Chain:** Multiple sessions → all hit 429 → retry 3x each → error messages fill context → context hits 100% → compaction triggers → compaction ALSO needs API call → that ALSO gets 429'd → **deadlock**

**Fix:** Kill stuck sessions. One session per API key at a time.

### Pattern 2: Memory Pressure Freeze
**Chain:** Docker VM (8GB reserved) + Safari WebKit (~4GB) + multiple Hermes sessions → swap full → system thrashing → everything crawls → appears stuck

**Docker is the #1 swap hog on Danny's MacBook:**
- Docker VM: `--memoryMiB 8092` reserves 8GB (actual RSS only ~813MB but macOS reserves swap for full allocation)
- Docker images: 43GB on disk, 30GB reclaimable → filesystem pressure → more swap
- Docker build cache: 31GB, 21GB reclaimable
- Fix: `docker system prune -a --volumes` reclaims ~51GB. Reduce VM to `--memoryMiB 4096`.

**Other swap consumers (Danny's MacBook, 24GB RAM, ~12GB RSS total):**
- Safari + WebKit: ~4GB (multiple renderer processes)
- Anki + 6 QtWebEngine processes: ~300MB
- Hermes python processes: ~360MB (multiple sessions)
- WPS Office: ~140MB
- Postgres, mds_stores, spotlight: ~600MB

**Fix:** Kill unnecessary processes. Reduce Docker VM memory. Close Safari tabs.

### Pattern 2b: Interrupt Handler Deadlock (NEW)
**Chain:** API connection drops → socket enters CLOSE_WAIT → session appears stuck → user sends new message → interrupt handler fires ("New message detected, interrupting...") → interrupt tries to cancel current HTTP request → that HTTP request is blocked on the same dead CLOSE_WAIT socket → **interrupt itself deadlocks**

**Symptoms:** Session shows "New message detected, interrupting..." or "⚡ New message detected" at low context (20-25%), then freezes forever. No 429 errors, no rate limits — just silent hang.

**Diagnosis:** `lsof -p <PID> | grep TCP` shows CLOSE_WAIT connections to the API endpoint. Session is at low context (not a compaction issue).

**Fix:** Only `kill -9` works. Regular `kill` (SIGTERM) often fails because the process is blocked in kernel I/O on the dead socket. Always verify with `ps aux` after killing — if still alive, `kill -9`.

**Prevention:** Z.AI API connections are unreliable over long sessions. For sessions running >2 hours, consider periodic restarts. The Hermes gateway auto-reconnects, but individual CLI sessions do not.

### Pattern 2c: Z.AI Socket Leak + Streaming Deadlock (CONFIRMED Apr 2026)

**Root Cause Chain:**
1. Z.AI's load balancer (zensafedns.net → `2607:a400:4:58::2c` IPv6) randomly drops TCP connections mid-stream
2. Socket enters CLOSE_WAIT on macOS — server sent FIN but client hasn't acknowledged
3. The streaming thread is stuck inside `for chunk in stream:` which calls `socket.recv()` — blocks indefinitely
4. The stale-stream detector runs in the OUTER polling thread, not inside the streaming thread — it CANNOT help because the inner thread never returns control
5. The interrupt handler tries `close()` on the httpx client, but httpcore's close() also tries to drain the socket — blocks on the same dead recv() → **DEADLOCK**
6. macOS TCP keepalive default is `net.inet.tcp.keepidle = 7,200,000 ms` (2 HOURS!) — dead sockets sit undetected for 130 minutes
7. Result: session frozen forever. Only `kill -9` works.

**Why "recovered" sessions still have CLOSE_WAIT:**
Hermes has `_cleanup_dead_connections()` that runs pre-turn — it detects dead sockets via MSG_PEEK and rebuilds the client. But the OLD socket is never properly closed — it leaks. So sessions accumulate CLOSE_WAIT sockets over time. Check with `lsof -p <PID> | grep TCP` — you'll see the leaked sockets.

**macOS TCP keepalive defaults (CRITICAL):**
```
net.inet.tcp.keepidle = 7,200,000 ms (2 HOURS before first probe!)
net.inet.tcp.keepintvl = 75,000 ms
net.inet.tcp.keepcnt = 8
Total dead socket detection: 7,200s + (75s × 8) = 7,800s = 130 MINUTES
net.inet.tcp.always_keepalive = 0 (disabled by default!)
```
Hermes/httpx does NOT set SO_KEEPALIVE on its sockets, so the OS never probes dead connections.

**Fix hierarchy (by impact):**
1. Reduce Docker VM memory: `--memoryMiB 4096` instead of `8092` (frees ~4GB swap immediately)
2. `docker system prune -a --volumes` reclaims ~51GB disk + reduces swap pressure
3. Fix socket leak: add SO_KEEPALIVE with aggressive timeouts to httpx transport, OR reduce `net.inet.tcp.keepidle` system-wide via `sysctl -w net.inet.tcp.keepidle=30000`
4. Fix streaming deadlock: the stale detector needs to run INSIDE the streaming thread (wrap socket.recv with a timeout), or use `select()` before recv() to detect dead sockets
5. Hermes env vars for timeouts: `HERMES_STREAM_STALE_TIMEOUT=180` (stale detector), `HERMES_STREAM_READ_TIMEOUT=120` (httpx read timeout)

### Pattern 3: Zombie Session
**Chain:** Old session from previous day still running, consuming API quota, causing rate limits for active sessions.

**Fix:** `kill <PID>` — zombie sessions serve no purpose.

## Fix Actions

### Immediate (unstick now)
1. Kill zombie sessions: `kill <zombie_PID>`
2. Kill stuck sessions in compaction deadlock: `kill <stuck_PID>`
3. If multiple active sessions, keep only the one doing important work

### Prevention (build into plugin)
Add to distillation plugin `pre_llm_call`:
```python
# Rate limit throttle: if last 3 API calls were 429, inject backoff
if hasattr(_on_post_api_request, '_recent_429_count'):
    if _on_post_api_request._recent_429_count >= 3:
        lines.append("[RATE LIMIT THROTTLE] 3+ consecutive 429s detected. "
                     "Reduce tool call frequency. Wait before retrying API calls.")
```

### Prevention (config)
In `config.yaml`:
```yaml
agent:
  context:
    engine: hindsight  # Uses local DB + Hindsight, doesn't need API for compaction
```

## Verification
After fixes:
```bash
# Confirm sessions count is reasonable (1-2)
ps aux | grep 'python.*hermes' | grep -v grep | grep -v gateway | wc -l

# Confirm swap is manageable
sysctl vm.swapusage | awk '{print $4, $5, $6}'

# Confirm API is reachable
curl -s --connect-timeout 5 https://api.z.ai/api/coding/paas/v4/models \
  -H "Authorization: Bearer $GLM_API_KEY" | head -1
```

## Key Numbers
- GLM-5.1 rate limit: ~10 RPM for shared keys
- 4 sessions × 3 retries = 12 API calls per failed attempt
- Context compaction adds 1 more API call (the deadlock trigger)
- Safe concurrent sessions: 1-2 per API key
