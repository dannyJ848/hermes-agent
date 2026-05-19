# zai-freeze-regression-forensics

*Researched: 2026-04-14 22:01 CDT*

# Z.AI Freeze Regression Forensics: "What Changed Between X and Y"

## Diagnostic Workflow

When Z.AI worked fine yesterday but freezes today, systematically eliminate change vectors:

### Step 1: Network Layer (fastest to rule out)
```bash
# Tailscale / VPN check
/Applications/Tailscale.app/Contents/MacOS/Tailscale status
netstat -rn | grep -E "^default|utun"  # default should be en0, NOT utun
curl -s --connect-timeout 5 -o /dev/null -w "connect=%{time_connect}s remote_ip=%{remote_ip}\n" https://api.z.ai/api/paas/v4/models
```
If default route goes through utun (exit node), ALL traffic is VPN-tunneled. If default is en0 and only 100.x.x.x goes through utun, VPN is NOT the cause.

### Step 2: Code Changes (hermes update pulls upstream commits)
```bash
cd ~/hermes-agent
git reflog --since="YYYY-MM-DD"
git log --oneline --since="YYYY-MM-DD" -- run_agent.py
git diff run_agent.py | wc -l  # are local patches still present?
```
Key patches to verify: `_build_keepalive_httpx_client`, `_force_close_tcp_sockets`, `_check_socket_liveness`, `_stale_timeout = min(..., 120.0)`.

### Step 3: hermes doctor --fix Side Effects
Doctor can: create missing .env, copy example config → config.yaml, run config migration. If config.yaml was overwritten, verify endpoint and model settings.

### Step 4: httpx/OpenAI SDK Version Changes
```bash
cd ~/hermes-agent && source venv/bin/activate
python3 -c "import httpx; print(httpx.__version__)"
python3 -c "import inspect, httpx; print(list(inspect.signature(httpx.HTTPTransport.__init__).parameters))"
```
If HTTPTransport.__init__ signature changed, the keepalive builder may silently fail.

### Step 5: Provider-Side Changes
- Z.AI server load varies by time of day (evening = more loaded)
- Context size: tool-heavy sessions have short responses; research/gym sessions inject 35K+ tokens before first call
- The 120s stale timeout firing IS the recovery mechanism working, not a bug

## Key Finding (Apr 14, 2026)
Danny ran `hermes update` + `hermes doctor --fix` to try fixing an error. The update pulled 9 upstream commits including a Z.AI endpoint probe change (commit 6448e1da). This did NOT overwrite our patches (322 lines of uncommitted diff survived). The Tailscale VPN was NOT the cause (only routing mesh traffic, not exit node). The freezes were Z.AI server-side load during evening hours.

## Error Pattern: HTTPTransport.__init__() got an unexpected keyword argument 'pool'
This error appears when the keepalive client builder incompatibility occurs. It's actually `httpx.Timeout(pool=30.0)` which is valid in httpx 0.28.1. If this error appears, check if httpx was upgraded to a version where Timeout(pool=...) was renamed.


## Sources

- session:20260414_214323_5a9d43
- internal:zai-api-resilience-skill
