---
name: web
version: 2.0
description: Web scraping, extraction, and browser automation skills — umbrella covering anti-detection browsers, anonymous extraction, social media scraping, and API reverse engineering.
trigger: When scraping websites, bypassing bot detection, extracting data from web pages, automating browsers, or reverse engineering web APIs.
---

# Web Skills

## Anti-Detection Browser Automation

### Camofox (Firefox fork with C++ fingerprint spoofing)

Anti-detection browser server for AI agents:
- Server runs on port 9377 (default): `cd ~/camofox-browser && bash run.sh &`
- Health check: `curl http://localhost:9377/health`
- REST API: `/navigate`, `/screenshot`, `/extract`, `/cookies`, `/close`
- Environment: `CAMOFOX_PORT`, `CAMOFOX_API_KEY`, proxy config, cookies directory
- Bypasses Cloudflare, Google, and most bot detection
- Python client: `camofox_client.py` (context manager, auto-cleanup)

### Phantom Browser (Tor-routed Playwright Chromium)

16-layer anti-fingerprint injection:
- Location: `~/subconscious/phantom_browser.py`
- Architecture: Request → Playwright → Anti-fingerprint → Tor SOCKS5 → Exit Node → Target
- Defeats: CDP detection, navigator fingerprint, canvas fingerprint, WebGL, audio, font enumeration, hardware probes, screen, timezone, WebRTC, performance timing, iframe patches
- Tor proxy: `socks5://127.0.0.1:9050`
- Launch: `python3 ~/subconscious/phantom_browser.py --test`
- Stealth test: `python3 ~/subconscious/phantom_browser.py --stealth-test`

## Social Media Scraping

### Chrome X/Twitter Scraper

Scrapes X/Twitter via user's real logged-in Chrome session:
- Bypasses all bot detection by using real browser
- Prerequisites: Chrome → View → Developer → Allow JavaScript from Apple Events (ENABLED)
- Tool: `~/subconscious/chrome_x_bridge.py`
- Commands: `scan`, `search`, `user`, `home`, `notifications`
- Example: `python3 ~/subconscious/chrome_x_bridge.py scan 5`

## API Reverse Engineering

### Autonomous Pipeline (4-phase)

**DISCOVER → ANALYZE → REPLICATE → VERIFY**

Tools at `~/subconscious/`:
1. `reverse_engineer.py` — Unified CLI orchestrator
   - `discover <url>` — Phantom + mitmproxy capture
   - `analyze <domain>` — JS analysis + flow analysis
   - `replicate <domain>` — Build authenticated session
   - `verify <domain>` — Test session against live API
   - `full <url>` — Complete pipeline

2. `extraction_toolkit.py` — Cookie/session/curl/JWT tools
   - `cookies <domain>` — Chrome cookie decryption
   - `session <domain>` — Full session data
   - `curl <url>` — Authenticated curl command
   - `fetch <url>` — Make authenticated request
   - `js-analyze <url>` — JS bundle analysis

3. `phantom_browser.py` — Tor-routed anti-fingerprint browser (see above)

## Web Extraction Tools

| Tool | Use Case | Detection Level |
|------|----------|----------------|
| Camofox | General scraping, Cloudflare bypass | Low |
| Phantom | Anonymous extraction, Tor-routed | Very Low |
| Chrome X | Social media (logged-in session) | Zero (real user) |
| Kimi WebBridge | Real browser automation via Chrome extension | Zero (real user) |
| curl + cookies | API endpoints, authenticated requests | N/A |

## Kimi WebBridge (Real Browser Control)

Control the user's actual Chrome browser with their real login sessions via a local daemon.

**Installation:**
```bash
curl -fsSL https://kimi-web-img.moonshot.cn/webbridge/install.sh | bash
```

**Status check:**
```bash
export PATH="$HOME/.kimi-webbridge/bin:$PATH"
kimi-webbridge status
```

**Expected healthy response:**
```json
{"extension_connected":true,"extension_version":"1.9.7","port":10086,"running":true,"version":"v1.9.7"}
```

**Core tools (HTTP POST to http://127.0.0.1:10086/command):**
| Action | Args | Purpose |
|--------|------|---------|
| `navigate` | `url`, `newTab`(bool), `session` | Open URL in new tab or existing |
| `snapshot` | `session` | Accessibility tree with `@e` refs for elements |
| `click` | `selector` (@e ref or CSS), `session` | Click element |
| `fill` | `selector`, `value`, `session` | Type into input/textarea/contenteditable |
| `evaluate` | `code` (supports async/await), `session` | Run JS on page |
| `screenshot` | `format`(png\|jpeg), `quality`, `selector`, `session` | Capture page or element |
| `find_tab` | `url`, `active`(bool), `session` | Reuse already-open tab |
| `list_tabs` | `session` | List all tabs in session |
| `close_tab` | `session` | Close current tab |
| `close_session` | `session` | Close all tabs in session |

**Sessions:** Each session name maps to a separate browser tab group. Use distinct names for parallel tasks.

**Screenshot helper script (avoids base64 flooding context):**
```bash
bash ~/.claude/skills/kimi-webbridge/scripts/screenshot.sh -s my-session -o /tmp/page.png
```

**Example workflow:**
```bash
# 1. Navigate
curl -s -X POST http://127.0.0.1:10086/command -H 'Content-Type: application/json' \
  -d '{"action":"navigate","args":{"url":"https://example.com","newTab":true},"session":"task1"}'

# 2. Snapshot to read page
curl -s -X POST http://127.0.0.1:10086/command -H 'Content-Type: application/json' \
  -d '{"action":"snapshot","session":"task1"}'

# 3. Click element by @e ref
curl -s -X POST http://127.0.0.1:10086/command -H 'Content-Type: application/json' \
  -d '{"action":"click","args":{"selector":"@e5"},"session":"task1"}'

# 4. Fill form
curl -s -X POST http://127.0.0.1:10086/command -H 'Content-Type: application/json' \
  -d '{"action":"fill","args":{"selector":"@e9","value":"search query"},"session":"task1"}'

# 5. Screenshot via helper
bash ~/.claude/skills/kimi-webbridge/scripts/screenshot.sh -s task1 -o /tmp/result.png

# 6. Cleanup
curl -s -X POST http://127.0.0.1:10086/command -H 'Content-Type: application/json' \
  -d '{"action":"close_session","session":"task1"}'
```

**Key advantages over headless browsers:**
- Uses user's real Chrome with real login sessions (cookies, 2FA already passed)
- Zero bot detection (it's the user's actual browser)
- Works with sites that block automation (banking, some social media)

**Limitations:**
- Sites checking `event.isTrusted` strictly (some banking, captchas) reject synthetic clicks/typing — this is a browser security boundary
- Cross-origin iframes: operate on top frame only; navigate to iframe URL directly if needed
- Requires Chrome extension installed and connected

**Troubleshooting:**
- **`extension_connected: false` or `No current window`**: The Chrome extension is running but not connected to any active Chrome window. Open a Chrome window (any tab) and the extension will auto-connect.
- **Extension disconnecting/reconnecting rapidly**: Check `kimi-webbridge logs` for WebSocket errors. If the extension keeps disconnecting, try restarting Chrome or the daemon: `kimi-webbridge restart`.
- **`No last-focused window`**: The extension lost track of which Chrome window was last active. Click on any Chrome window to restore focus tracking.
- **Skills installed at**: `~/.claude/skills/kimi-webbridge/`, `~/.codex/skills/kimi-webbridge/`, `~/.config/agents/skills/kimi-webbridge/`, `~/.agents/skills/kimi-webbridge/`

**Shell Escaping Pitfall (critical):**
When sending JavaScript code through curl JSON payloads, nested quotes and newlines cause `invalid JSON` errors. The shell interprets escape sequences before JSON sees them.

❌ **Broken:** Nested double quotes inside single-quoted JSON
```bash
# FAILS: shell strips \ before JSON parser sees them
curl -d '{"code":"document.querySelectorAll(\"[data-testid=trend]\").length"}'
```

✅ **Working patterns:**
1. **Simple one-liner:** Use only single quotes inside the JS, no nested quotes:
   ```bash
   curl -d '{"code":"document.querySelectorAll(\"[data-testid=trend]\").length"}'
   # Actually this still fails — see pattern 2
   ```

2. **No nested quotes:** Use attribute selectors without quotes, or escape carefully:
   ```bash
   curl -d '{"code":"document.querySelectorAll(\"[data-testid=trend]\").length"}'
   # Still fragile. Best approach:
   ```

3. **Base64 encode complex JS** (most reliable):
   ```bash
   echo '(() => { const trends = []; document.querySelectorAll("[data-testid=trend]").forEach(el => { trends.push(el.innerText.trim()); }); return JSON.stringify(trends); })()' | base64
   # Then decode in evaluate: atob("...")
   ```

4. **Write JS to file, reference minimally:**
   ```bash
   # Write JS to temp file
   cat > /tmp/script.js << 'EOF'
   JSON.stringify(Array.from(document.querySelectorAll('[data-testid=trend]')).map(el => el.innerText.trim()))
   EOF
   # Then send simple code that reads and evals the file content
   ```

**Recommended:** For anything beyond trivial one-liners, write JS to a file first, then send a minimal `fetch('/tmp/script.js').then(r=>r.text()).then(t=>eval(t))` or similar. See `references/kimi-webbridge-shell-escaping.md` for full recipes.

**Skills installed for:** Claude Code, Codex, Kimi CLI, OpenClaw at `~/.claude/skills/kimi-webbridge/`, etc.

**PATH setup:** Add `export PATH="$HOME/.kimi-webbridge/bin:$PATH"` to `~/.zshrc` for persistent access.

**Pitfalls**

- **Camofox**: Requires server running. Check health before use. Cookie import needs API key.
- **Phantom**: Tor must be running (`brew services start tor`). Exit nodes may be slow.
- **Chrome X**: Requires user logged into X on Chrome. Apple Events permission must be enabled.
- **Rate limiting**: Even stealth browsers hit rate limits. Add delays between requests.
- **Legal**: Respect robots.txt and ToS. Some sites prohibit scraping in terms.
- **Session expiry**: Cookies and tokens expire. Monitor and refresh sessions.
- **Fingerprint drift**: Anti-detection patches need updates as detection evolves.
- **Headless Chromium WebGL**: `MeshPhysicalMaterial` crashes headless chromium. Use `MeshPhongMaterial` or `MeshLambertMaterial` for 3D content. See `references/headless-browser-compatibility.md`.
- **Playwright Version Mismatch**: Hermes expects `chromium_headless_shell-1217`. Use `npx playwright install chromium` (not bare `playwright install`). See `references/headless-browser-compatibility.md`.
- **file:// URLs Blocked**: Serve files via `python3 -m http.server` instead of `file://` for browser tools.
- **WebBridge Shell Escaping**: Complex JS in curl payloads fails due to shell+JSON escaping. See `references/kimi-webbridge-shell-escaping.md` for solutions.
- **WebBridge X Trending**: X uses `data-testid="trend"` for trending topics. See `references/x-twitter-trending-extraction.md` for extraction patterns.
- **WebBridge X AI Scanner**: Production cron-based X AI trend scanner using WebBridge. See `references/x-ai-trend-scanner-script.md` for the full script, cron integration, and comparison with Cookie API approach.
