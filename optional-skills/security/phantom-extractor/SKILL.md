---
name: phantom-extractor
version: 3.0
description: 6-layer fully-Tor-routed paywall extraction pipeline. Every network call goes through a single gateway function — zero IP/DNS leak paths.
tags: [anonymity, tor, extraction, paywall, opsec, stealth, research]
---

# Phantom Extractor v3

## Location
`/Users/dannygomez/subconscious/phantom_extractor_v3.py`

## Architecture: Single-Gateway Tor Funnel
```
ALL requests → _tor_fetch() → curl --socks5-hostname 127.0.0.1:9050 → Tor → Exit Node → Target
```
There is ONE network function. Every layer calls `_tor_fetch()` or `_tor_fetch_json()`. No exceptions.

## 6-Layer Pipeline
1. **Archive services** (archive.ph, Wayback, Google/Bing cache) — zero contact with target
2. **Academic open-access** (Unpaywall, oaDOI, Semantic Scholar → arXiv/PMC) — legal OA resolution
3. **Bypass services** (12ft.io, smry.pro) — intermediary contact only
4. **Site-specific tricks** (Medium→scribe.rip, news AMP, Googlebot spoof, cookie bust)
5. **Stealth HTTP** (fresh Tor circuit + rotated UA/headers)
6. **Phantom browser** (Tor + anti-fingerprint Playwright + JS render) — last resort

## OPSEC Guarantees
- Zero `urlopen` calls, zero `requests` calls, zero raw `subprocess curl` without `--socks5-hostname`
- DNS resolved by Tor exit node (`--socks5-hostname` = remote DNS), never local resolver
- Different Tor circuit per extraction via `_tor_new_circuit()`
- Pre-flight Tor verification in `extract()` — refuses to run if Tor is down or not routing
- Random delays between all requests
- No cookies, no JavaScript unless Layer 6

## Critical Lesson (Why v3 Exists)
v2 had **silent IP leaks**: Layers 1-3 (archive services, academic APIs, bypass services) made DIRECT connections via `urllib.request.urlopen`. Your real Comcast IP (73.73.x.x) was visible to archive.org, unpaywall.org, semanticscholar.org, etc. If subpoenaed, those services would have your IP.

**Root cause**: No single-gateway architecture. Each layer independently chose between `urllib`, `curl`, and Tor — and most chose `urllib` (no Tor).

**Fix**: v3 has ONE function `_tor_fetch()` and ONE function `_tor_fetch_json()`. All 14+ network call sites funnel through these. Adding a new extraction method REQUIRES using `_tor_fetch()`.

## Leak Audit Checklist (run before trusting any extraction tool)
```
1. grep -c 'urlopen' <file>          → must be 0
2. grep -c 'requests\.' <file>       → must be 0  
3. grep 'subprocess.run.*curl' <file> | grep -v socks5  → must be 0
4. grep -c 'Real IP' <file>          → must be 0 (don't fetch your own IP in the tool)
5. Verify _tor_fetch is the ONLY network function
6. Run: python3 phantom_extractor_v3.py check  → must say "Tor: ACTIVE, IsTor: True"
```

## CLI Usage
```bash
# OPSEC pre-flight check
python3 ~/subconscious/phantom_extractor_v3.py check

# Extract article
python3 ~/subconscious/phantom_extractor_v3.py extract "https://example.com/article"
```

## Python Usage
```python
import sys
sys.path.insert(0, '/Users/dannygomez/subconscious')
from phantom_extractor_v3 import extract

result = extract("https://paywalled-site.com/article", max_layers=6)
if result["success"]:
    print(f"Got {len(result['content'])} chars via {result['method']}")
    for method, status in result["attempts"]:
        print(f"  {method}: {status}")
else:
    print(f"All layers failed: {result.get('error', 'unknown')}")
```

## Integration with red_team_hippocampus.py
`red_team_hippocampus.py` imports `phantom_extractor_v3.extract` directly:
```python
from phantom_extractor_v3 import extract as phantom_extract
result = phantom_extract(url, max_layers=6)
```
Layer map for scoring: archives=1, academic=2, bypass=3, tricks=4, stealth=5, phantom=6.

## Dark Web Access (Confirmed Working)
```bash
# Access .onion sites directly through Tor SOCKS proxy
curl -s --socks5-hostname 127.0.0.1:9050 --max-time 20 "http://<onion-address>/" 
```
- Tor running at `/opt/homebrew/opt/tor/bin/tor` (PID varies), listening on `localhost:9050`
- No torrc file needed — default config supports .onion resolution
- Confirmed working: Tor Project onion, Hidden Wiki (527 links), DuckDuckGo onion, Ahmia search
- Hidden Wiki URL: `http://zqktlwiuavvvqqt4ybvgvi7tyo4hjl5xgfuvpdf6otjiycgwqbym2qad.onion/wiki/index.php/Main_Page`

## PAYWALL REALITY (Apr 2026 Session Findings)
**ALL mainstream bypass tools block Tor exits with CAPTCHAs:**
- archive.ph → Cloudflare CAPTCHA
- 12ft.io → Cloudflare CAPTCHA  
- smry.pro → Cloudflare CAPTCHA
- Google Cache → "unusual traffic" block
- The `_is_captcha_or_block()` gate correctly rejects these (3+ marker threshold)

**Dark web does NOT have paywall bypass tools.** Hidden Wiki is 90% markets/forums. Nobody runs archive services as hidden services.

**Real solutions (not on dark web):**
1. **BPC (Bypass Paywalls Clean)** — browser extension with site-specific JS/CSS/cookie/header tricks for 300+ sites. Source on Greasy Fork: `https://greasyfork.org/en/scripts/542350-bypass-paywalls-clean-de-at-ch/code` (88KB of bypass logic). DMCA'd off GitHub but survives on Greasy Fork and GitFlic.
2. **ladder** (github.com/everywall/ladder) — self-hosted 12ft.io alternative, Go proxy + CORS removal. Docker-ready.
3. **13ft** (github.com/wasi-master/13ft) — self-hosted, Googlebot impersonation. Python.
4. **BPC tricks to extract:** CSS selectors to hide paywall overlays, cookie manipulation, header injection (Referer, X-Forwarded-For), Googlebot UA spoofing, AMP page redirect, JavaScript paywall element removal.

**Next steps for phantom_extractor:**
- Extract per-site bypass logic from BPC source (site-specific selectors + headers)
- Self-host ladder or 13ft as a local proxy layer
- Wire BPC tricks into Layer 4 of the pipeline

## Pitfalls
- **Tor must be running** — `extract()` returns error dict with `tor_offline` method if not
- **`_tor_fetch_json` needs raw fetch + manual parse** — some APIs return HTML not JSON through Tor, so catch JSONDecodeError
- **execute_code quoting** — Python one-liners with f-strings and nested quotes will SyntaxError. Use write_file to create a temp script instead
- **phantom_browser.py subprocess** — Layer 6 calls `phantom_browser.py` as subprocess with `--tor` flag. If phantom_browser.py isn't Tor-aware, it could leak. Verify independently.
- **Do NOT fetch your real IP inside the tool** — the v2 `check` command did `curl ifconfig.me` without Tor to "compare" IPs. That's a leak. The real IP check should only be done externally, never from within the anonymized tool.

## Related Skills
- `phantom-browser` — The Layer 6 browser engine (Tor + anti-fingerprint Playwright)
- `camofox` — Anti-detection browser automation via Camofox server
