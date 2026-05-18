# Multi-Persona Propaganda Demystification Engine — Session Notes

## What We Built (May 16, 2026)

A complete pipeline that scans X/Twitter from multiple ideological perspectives, generates a daily digest with narrative analysis, produces a dark-themed static site, and distributes via bots.

### Architecture

```
scanner.py (4 personas) → digest_generator.py → site_generator.py → bot/run_bots.py
```

### Key Files

| File | Purpose |
|------|---------|
| `~/propaganda-demystifier/scanner.py` | Multi-persona feed scanner (left/center/right/personal) |
| `~/propaganda-demystifier/digest_generator.py` | Cross-reference, detect patterns, write digest JSON |
| `~/propaganda-demystifier/site_generator.py` | Render digest JSON → dark-themed static HTML |
| `~/propaganda-demystifier/bot/run_bots.py` | Orchestrate Mastodon/Bluesky/Newsletter posting |
| `~/propaganda-demystifier/run_pipeline.py` | Main orchestrator, called by cron |
| `~/propaganda-demystifier/config/personas.yaml` | Persona definitions (follows, queries, cookies) |

### What Worked

1. **Modular pipeline** — Each stage reads JSON, writes JSON. Easy to debug, easy to replace.
2. **Cookie-based API** — GraphQL with browser cookies bypasses all bot detection. No browser automation needed.
3. **Single-account multi-persona** — One X account's cookies work for all personas if you query different follows/search terms.
4. **Static site with embedded CSS** — Single-file HTML, no build step, hosts anywhere.
5. **Type-checking JSON fields** — `methodology` was dict not string; `isinstance` check prevented crash.

### What Didn't Work

1. **Terminal heredocs with `&`** — Backgrounding detector rejects scripts with ampersands. Use `write_file` instead.
2. **Browser tools for X** — `browser_navigate` 55% success rate. X blocks cloud browsers, headless detection, automated logins.
3. **cronjob tool** — 17% success rate. Use `crontab -e` directly.
4. **Dict assumptions** — Expected `methodology` as string, got dict. Always `isinstance` check.
5. **Patch on large files** — Patching >500 line files without full read causes mismatches. Read full file first.

### Cookie Extraction

The `auth_token` is httpOnly — invisible to JavaScript. Use Chrome extension with `chrome.cookies` API:

```javascript
// manifest.json
{
  "manifest_version": 3,
  "name": "X Cookie Extractor",
  "permissions": ["cookies"],
  "host_permissions": ["https://x.com/*", "https://twitter.com/*"]
}
```

Extension code in `~/propaganda-demystifier/extract_x_cookies_extension/`

### Personal Feed Integration

Add `use_home_timeline: true` to a persona to fetch your actual X "For You" feed:

```yaml
personas:
  - name: "personal_lens"
    display_name: "Your Feed"
    use_home_timeline: true
```

Uses `HomeLatestTimeline` endpoint (NOT `HomeTimeline` which returns 404).

### Pipeline Cron

```bash
# crontab -e
0 6 * * * cd ~/propaganda-demystifier && python3 run_pipeline.py >> logs/cron.log 2>&1
```

### Site Output

- `~/propaganda-demystifier/site/index.html` — Latest digest (auto-updated)
- `~/propaganda-demystifier/site/2026-05-16.html` — Archive copy

### Bot Distribution

| Bot | Env Var | Status |
|-----|---------|--------|
| Mastodon | `FEDIVERSE_TOKEN` | Ready (needs token) |
| Bluesky | `BLUESKY_PASSWORD` | Ready (needs password) |
| Newsletter | `SMTP_USER`, `SMTP_PASS` | Ready (needs SMTP) |

All bots skip posting if tokens missing — safe to run in dry-run mode.

### Lessons for Reddit Project

Same modular pipeline applies:
1. **Scanner** — Reddit API (PRAW) or cookie-based JSON endpoints
2. **Digest** — Cross-subreddit narrative analysis
3. **Site** — Same static site generator pattern
4. **Bots** — Same distribution layer

Key differences:
- Reddit has official API (PRAW) — no cookie extraction needed
- Subreddits = personas (r/politics, r/conservative, r/neutralpolitics)
- Reddit posts have built-in engagement scores (upvotes)
- No httpOnly cookie issues — use OAuth or app credentials
