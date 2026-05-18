# Personal Timeline + Chrome Extension Cookie Extraction

## Personal Timeline (Your Feed)

Add a `personal_lens` persona with `use_home_timeline: true` to include your actual X algorithmic feed as a baseline:

```yaml
personas:
  - name: "personal_lens"
    display_name: "Your Feed"
    bias_indicator: "personal"
    follows: []
    search_queries: []
    use_home_timeline: true
```

The scanner will call `HomeLatestTimeline` (not `HomeTimeline` — the latter returns 404) to fetch ~85 tweets from your actual "For You" feed. This lets you compare what X's algorithm serves you vs what the curated personas see.

**Implementation in scanner.py:**
```python
if persona.get("use_home_timeline", False):
    tweets = fetch_home_timeline(session, hashes, count=20)
    for t in tweets:
        t["source_persona"] = persona_name
        t["source_type"] = "timeline"
        t["source_account"] = "your_feed"
```

**HomeLatestTimeline endpoint (verified working May 2026):**
```
GET https://x.com/i/api/graphql/{hash}/HomeLatestTimeline
params: variables={"count":40,"includePromotedContent":false,"latestControlAvailable":true,"requestContext":"launch","withVoice":false}
        features={...standard features dict...}
```
Response path: `data.home.home_timeline_urt.instructions[].entries[]`
Returns ~85 tweets per call.

**CRITICAL**: `HomeTimeline` (without "Latest") returns 404. Always use `HomeLatestTimeline`.

## Chrome Extension for Cookie Extraction

For multi-persona setups, a Chrome extension is the cleanest way to extract httpOnly cookies (`auth_token` is invisible to `document.cookie`).

**Extension files** (save to `extract_x_cookies_extension/`):

`manifest.json`:
```json
{
  "manifest_version": 3,
  "name": "X Cookie Extractor",
  "version": "1.0",
  "permissions": ["cookies", "activeTab"],
  "host_permissions": ["https://x.com/*", "https://twitter.com/*"],
  "action": {"default_popup": "popup.html"}
}
```

`popup.js` (core logic):
```javascript
async function extractCookies() {
  const cookies = await chrome.cookies.getAll({domain: ".x.com"});
  const result = {};
  for (const c of cookies) {
    if (c.name === "auth_token") result.auth_token = c.value;
    if (c.name === "ct0") result.ct0 = c.value;
    if (c.name === "twid") result.twid = c.value;
  }
  navigator.clipboard.writeText(JSON.stringify(result, null, 2));
  return result;
}
```

**Installation:**
1. Open Chrome → `chrome://extensions/`
2. Enable Developer mode (top right)
3. Click "Load unpacked"
4. Select the `extract_x_cookies_extension/` folder
5. Pin to toolbar
6. Log into X, click extension, hit "Extract Cookies"
7. Paste JSON into `personas/{name}_cookies.json`

## Scanner Patching Pitfalls

When patching `scanner.py` via the `patch` tool:
- **Always read the full file first** — partial reads with offset/limit cause patch mismatches
- **The file is large** (~600 lines) — use `read_file` without offset to get the complete content
- **Syntax errors cascade** — one bad patch can corrupt function signatures, causing IndentationError on subsequent patches
- **Recovery**: If patching breaks, `git checkout scanner.py` and start over
- **Alternative**: Use `sed` or Python inline replacement for surgical edits when patch tool struggles

## Validated Results (May 2026)

With one account and 4 personas (including personal timeline):
- Left Lens: 141 tweets
- Your Feed: 85 tweets (from HomeLatestTimeline)
- Center Lens: 138 tweets
- Right Lens: 113 tweets
- Total: 472 tweets, 460 unique after dedup

All endpoints working: UserTweets (GET), SearchTimeline (POST), HomeLatestTimeline (GET).
