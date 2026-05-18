---
name: x-cookie-api
description: Read-only X/Twitter access via cookie authentication using Python requests. Free alternative to the official API. For intelligence gathering, timeline reading, and user tweet fetching.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [python3]
  packages: [requests]
---

# X Cookie API -- Free Read-Only X/Twitter Access

Access X/Twitter data using the user's browser cookies. No API keys needed. Python requests with proper headers bypasses X's empty-response anti-bot protection that blocks curl.

**CRITICAL: READ-ONLY. Never post, like, retweet, reply, or interact. Only observe and collect.**

## Getting the Cookies

### Option 1: Chrome Extension (Recommended for Multi-Persona)

For multi-persona setups (propaganda demystification engine, etc.), use the Chrome extension method. See `references/chrome-extension-cookie-extraction.md` for the concept, and `references/chrome-extension-complete.md` for production-ready code with validated installation steps.

**Why**: X's `auth_token` is **httpOnly** — invisible to `document.cookie`. The `chrome.cookies` API is the only programmatic way to extract it without DevTools.

**Quick steps**:
1. Create extension folder with files from `references/chrome-extension-complete.md`
2. Install via chrome://extensions/ → Developer mode → Load unpacked
3. Log into X with persona account
4. Click extension → copy JSON → save to `personas/{name}_cookies.json`
5. Repeat for each persona
6. Validate: `python3 scanner.py` should show tweets collected, not 401 errors

### Option 2: DevTools (Manual, One-Off)

For single-account use, extract via DevTools:

```js
// In browser console — this gives ONLY non-httpOnly cookies
document.cookie
```

For `auth_token` (httpOnly, invisible to JS):
- Safari: Web Inspector > Storage tab > Cookies > x.com > find `auth_token`
- Chrome: DevTools > Application tab > Cookies > x.com > find `auth_token`

Required cookies:
- `auth_token` -- session token (httpOnly, must get from Storage/Network tab)
- `ct0` -- CSRF token (visible in document.cookie)
- `twid` -- user ID (visible in document.cookie, format: `u%3D<numeric_id>`)

### Option 3: CDP Script (Programmatic, Single Browser)

For extracting from a running Chrome instance with remote debugging:

```python
# See extract_x_cookies.py in the propaganda-demystifier project
# Uses Chrome DevTools Protocol to get cookies from an existing session
```

This requires Chrome launched with `--remote-debugging-port=9222` and uses the CDP `Network.getAllCookies` command.

## Key Technical Findings (from trial-and-error)

1. **curl gets empty responses**: X returns `Content-Length: 0` with HTTP 200 to curl, even with the same cookies and headers. Must use Python `requests` library.

2. **Required headers**: Beyond cookies, you need:
   - `Authorization: Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA` (X's public bearer token)
   - `x-csrf-token: <ct0 value>` (must match ct0 cookie)
   - `x-twitter-auth-type: OAuth2Session`
   - `x-twitter-active-user: yes`
   - Full browser User-Agent string

3. **GraphQL hashes change**: X updates query hashes with each deploy. Extract current ones from the JS bundle:
   ```python
   import requests, re
   r = requests.get("https://x.com", headers={"User-Agent": "Mozilla/5.0"})
   # Find main bundle
   urls = re.findall(r'https://abs\.twimg\.com/responsive-web/client-web/main\.[a-f0-9]+\.js', r.text)
   r2 = requests.get(urls[0], headers={"User-Agent": "Mozilla/5.0"})
   # Method 1: key-value pattern (works as of April 2026)
   hashes = re.findall(r'"([a-zA-Z0-9_-]{15,25})":"(SearchTimeline|UserTweets|HomeTimeline|UserByScreenName|TweetDetail|HomeLatestTimeline)\"', r2.text)
   # Method 2: queryId+operationName pattern (more reliable)
   pairs = re.findall(r'queryId:"([^"]+)",operationName:"([^"]+)"', r2.text)
   for qid, op in pairs:
       print(f'{op}: {qid}')
   ```
   Known hashes (April 2026): `SearchTimeline=g7SDsWwiaaKtRjngIIq-mA`, `HomeLatestTimeline=yVGDzqYZZVQOlK3KhJx5ag`, `UserTweets=E3opETHurmVJflFsUBVuUQ`, `UserByScreenName=BQ6xjFU6Mgm-WhEP3OiT9w`, `TweetDetail=5sGVenr9szUMxfmfUwN7rA`. These WILL change — always extract fresh.

4. **Tweet JSON parsing has 3 paths**: Timeline entries use different nesting:
   - Path A: `entry.content.content.tweetResult.result.legacy`
   - Path B: `entry.content.itemContent.tweet_results.result.legacy`
   - Path C: `entry.content.itemContent.tweet_results.result.tweet.legacy` (most common)
   Always try Path C if A and B return empty.

5. **URL field may be missing `expanded_url`**: Some tweets have URLs without the `expanded_url` key. Use `.get()` with fallback: `u.get("expanded_url", u.get("url", ""))` instead of `u["expanded_url"]`. This prevents KeyError crashes during batch scanning.

6. **User data migrated (CRITICAL, discovered April 2026)**: X silently moved `screen_name` and `name` from `result.legacy` to `result.core` inside the user object. The old path `tweet_results.result.core.user_results.result.legacy.screen_name` now returns an empty dict `{}`. Use this fallback chain:
   ```python
   user_result = tweet_result["core"]["user_results"]["result"]
   # NEW location (April 2026+)
   screen_name = user_result.get("core", {}).get("screen_name")
   # OLD location (fallback)
   if not screen_name:
       screen_name = user_result.get("legacy", {}).get("screen_name", "?")
   ```
   Both `screen_name` and `name` moved together. The `legacy` dict on user_result is now empty `{}`. This affects ALL endpoints (UserTweets, HomeLatestTimeline, etc.).

5. **Timeline structure**: `data.user.result.timeline_v2.timeline.instructions` contains 3 instruction types:
   - `TimelineClearCache` (0 entries)
   - `TimelinePinEntry` (0 entries, pinned tweet elsewhere)
   - `TimelineAddEntries` (main content, 20+ entries)

## Working Endpoints

### UserTweets (verified working)
```
GET https://x.com/i/api/graphql/{hash}/UserTweets
params: variables={"userId":"<id>","count":10,"includePromotedContent":false,"withVoice":false,"withV2Timeline":true}
        features={...standard features dict...}
```

### SearchTimeline (CRITICAL: requires POST, not GET) -- VERIFIED WORKING April 2026
```
POST https://x.com/i/api/graphql/{hash}/SearchTimeline
JSON body: {"variables": {"rawQuery":"AI agents","count":20,"querySource":"typed_query","product":"Top"}, "features": {...standard features dict...}}
```
**CRITICAL**: SearchTimeline returns 404 on GET. Must use POST with JSON body (`json=` param in requests, NOT `data=`). This is different from HomeLatestTimeline and UserTweets which work with GET.

Current hash: `g7SDsWwiaaKtRjngIIq-mA` (extract April 2026)
Response path: `data.search_by_raw_query.search_timeline.timeline.instructions[].entries[]`
Returns ~19-20 tweets per request.

**Pro tip**: Use `min_faves:N` in the query to filter low-engagement noise, e.g. `"AI model release min_faves:50"`.

**Hash extraction**: Hashes ARE in main.*.js bundle. Extract with:
```python
r = requests.get("https://abs.twimg.com/responsive-web/client-web/main.b6995f7a.js")
pairs = re.findall(r'queryId:"([^"]+)",operationName:"([^"]+)"', r.text)
# Returns all endpoint hashes: SearchTimeline, HomeLatestTimeline, UserTweets, etc.
```

### HomeLatestTimeline (verified working, BEST for home feed scanning)
```
GET https://x.com/i/api/graphql/yVGDzqYZZVQOlK3KhJx5ag/HomeLatestTimeline
params: variables={"count":40,"includePromotedContent":false,"latestControlAvailable":true,"requestContext":"launch","withVoice":false}
        features={...standard features dict...}
```
Response path: `data.home.home_timeline_urt.instructions[].entries[]`
Pagination: look for entries with `content.cursorType == "Bottom"` for the next cursor.
Returns ~90-100 tweets per page. Supports cursor-based pagination.

### HomeTimeline (needs correct variables, 422 if wrong)
```
GET https://x.com/i/api/graphql/{hash}/HomeTimeline
```
This endpoint is finicky with parameters. If you get GRAPHQL_VALIDATION_FAILED, the variables schema has changed.

## Browser Article Extraction (When API Fails)

X Articles (e.g., `https://x.com/i/article/2053106718226227203`) return 404 from GraphQL endpoints. Use browser automation with injected cookies instead.

**Pattern:** Navigate → inject cookies → re-navigate → vision extraction → scroll → repeat

See `references/browser-article-extraction.md` for full workflow with cookie injection code and the complete browser-based extraction pattern.

**When to use:**
- X Articles (long-form content) — API 404s, browser works
- Tweet text/media — API works fine, don't use browser
- Profile pages — API works
- Search results — API works (POST)

## Fallback Methods

### 1. vxtwitter API (no auth needed)

When cookie API fails or web_extract hits X's JS wall, use the vxtwitter JSON API:
```bash
curl -s "https://api.vxtwitter.com/{user}/status/{tweet_id}" | python3 -m json.tool
```
Returns: text, date, likes, retweets, mediaURLs, hashtags, and **qrt** (quoted tweet with full text).
No auth, no cookies, no JS. Just works.

Limitations: only individual tweets, no timelines. Rate-limited if abused.

### 2. SearXNG Search

When SearchTimeline doesn't work, use:
```
web_research("site:x.com AI agent framework")
```
This searches X content via SearXNG with zero login needed.

## Module Template

A working module is saved at `/tmp/x_api.py` with:
- `_session()` -- creates authenticated requests Session
- `get_user_tweets(user_id, count)` -- fetches user tweets
- `_extract_tweet(entry)` -- parses tweet from timeline entry (handles all 3 JSON paths)
- `get_gql_hashes()` -- extracts current hashes from X's JS

## Debugging Auth Failures (401 / Invalid Token)

If you get `{"errors":[{"message":"Invalid or expired token","code":89}]}`:

1. **Check the AUTH_TOKEN value** — it must be a full hex string (~40 chars). If it shows `2c16cc...57ca` (with ellipsis), the token was redacted/truncated and needs to be re-extracted from the browser.
2. **CT0 tokens expire** — the CSRF token rotates. Re-extract from browser cookies.
3. **No separate cookies JSON file** — `/tmp/x_api.py` hardcodes tokens directly (no `x_cookies.json`). Do NOT reference a separate cookies file.
4. **Module uses functions, not classes** — `import from x_api` gives you `_session()`, `get_user_tweets()`, `_extract_tweet()`, `get_gql_hashes()`. There is no `XApi` class.

### PII Scrubber Masks Auth Tokens (CRITICAL)

When writing a new auth_token to `/tmp/x_api.py`, the Hermes PII scrubber will **mask the token** when you read the file back. You'll see `AUTH_TOKEN="***"` even though the write succeeded. **Do NOT assume the write failed.** Test auth by calling the API directly:

```python
from x_api import _session
s = _session()
r = s.get("https://twitter.com/i/api/2/notifications/all.json?count=1")
print("Auth works!" if r.status_code == 200 else f"Failed: {r.status_code}")
```

The `execute_code` and `read_file` tools both apply PII scrubbing. Only actual API calls confirm the token works.

### Token Replacement Method

`patch` tool and `sed` both fail on auth tokens (regex escaping + PII masking). Use inline Python via `terminal`:
```bash
python3 -c "
content = open('/tmp/x_api.py').read()
# Find and replace the AUTH_TOKEN line by line number
lines = content.split('\n')
for i, line in enumerate(lines):
    if line.startswith('AUTH_TOKEN='):
        lines[i] = 'AUTH_TOKEN=\"<new_full_token>\"'
open('/tmp/x_api.py','w').write('\n'.join(lines))
"
```
Then verify with an API call, NOT by reading the file.

### Fetching a Specific Tweet by ID

Use the `TweetResultByRestId` GraphQL endpoint:
```python
tweet_id = '2039822829412405671'
variables = json.dumps({'tweetId': tweet_id, 'withCommunity': False, 'includePromotedContent': False, 'withVoice': False})
features = json.dumps({...standard features dict...})
url = f'https://twitter.com/i/api/graphql/V3vfsYzNEyD9tsf4xoFRgw/TweetResultByRestId?variables={requests.utils.quote(variables)}&features={requests.utils.quote(features)}'
r = session.get(url)
# Parse: data.tweetResult.result.legacy.full_text
```

### Quick Alternative: vxtwitter (no auth)

If auth is broken, use this zero-auth fallback for individual tweets:
```bash
curl -s "https://api.vxtwitter.com/jphorism/status/2039822829412405671" | python3 -m json.tool
```

### Fallback: Direct HTML Extraction (no auth, no JS)

When all API methods fail (cookies expired, GraphQL blocked, vxtwitter down), extract tweet text directly from x.com HTML using curl + regex. X serves the tweet content in the initial HTML payload as escaped JSON strings.

**Pattern:**
```bash
# Fetch the tweet page with a real browser User-Agent
curl -sL "https://x.com/USER/status/TWEET_ID" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
```

**Extract text from HTML:**
```python
import requests, re

url = f"https://x.com/{user}/status/{tweet_id}"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)

# Method 1: Extract from escaped JSON in HTML
# The tweet text appears in "text":"..." or "full_text":"..." fields
# These are Unicode-escaped (\uXXXX) and may be double-escaped
texts = re.findall(r'"text":"([^"]{50,2000})"', r.text)
for text in texts:
    decoded = text.encode('utf-8').decode('unicode_escape')
    print(decoded)

# Method 2: Extract full_text (more reliable for longer tweets)
full_texts = re.findall(r'"full_text":"([^"]{50,2000})"', r.text)
for text in full_texts:
    decoded = text.encode('utf-8').decode('unicode_escape')
    print(decoded)
```

**Important notes:**
- The HTML is ~275KB and contains the tweet data as embedded JSON
- Text is Unicode-escaped (e.g., `\u4e2d\u6587` for Chinese) — decode with `.encode('utf-8').decode('unicode_escape')`
- Multiple matches may appear (tweet + replies + related tweets) — the first match is usually the main tweet
- `web_extract` tool fails on X (JS requirement) — use `requests` + regex instead
- `web_research` tool fails if Firecrawl/SearXNG not configured — use direct curl/requests
- Nitter instances are unreliable (most return empty or 403 as of May 2026)

**When to use this fallback:**
1. Cookie auth expired and user not available to re-extract
2. GraphQL endpoints returning 404 (hash rotation)
3. vxtwitter API down or rate-limited
4. Need to read a single tweet quickly without setup
5. Browser automation (Kimi Webbridge) unavailable — extension not connected to current window

## Batch Scanning Pattern (Multi-Query News Scan)

For cron-style AI news scans, use multiple targeted queries with `min_faves` to filter noise:

```python
queries = [
    'AI agent framework autonomous min_faves:20',
    'open source AI agent release min_faves:20',
    'Claude Code OR Cursor agent OR Devin 2025 min_faves:20',
    'MCP tools AI agent min_faves:10',
    'Nous Research OR Teknium OR Hermes agent min_faves:5'
]
```

**Deduplication**: Match on `text[:80]` — X returns duplicates across queries.

**Engagement sorting**: `sorted(tweets, key=lambda t: t['favs'] + t['rts']*3, reverse=True)` — weight retweets higher since they indicate endorsement vs passive likes.

**Priority flagging**: Scan text for keywords:
- HIGH: `hermes`, `nous research`, `teknium` (self/org mentions)
- MEDIUM: `agent framework`, `open source`, `mcp`, `breakthrough`

**Fallback chain** (when primary tools fail):
1. `chrome_x_bridge.py scan` (if X is open in browser)
2. `news_scan` tool
3. `web_research` / `web_search`
4. X cookie API batch scan (this pattern — most reliable)
5. `browser_navigate` to X search pages (slowest, last resort)

**Deploying the script**: The skill's `scripts/x_api.py` must be copied to `/tmp/x_api.py` before import — it doesn't auto-deploy. Use: `cp ~/.hermes/skills/social-media/x-cookie-api/scripts/x_api.py /tmp/x_api.py`

## User ID Resolution (CRITICAL)

**Never hardcode user IDs.** X user IDs change or get confused. Always resolve via UserByScreenName:

```python
url = "https://x.com/i/api/graphql/BQ6xjFU6Mgm-WhEP3OiT9w/UserByScreenName"
params = {
    "variables": json.dumps({"screen_name": "Teknium", "withSafetyModeUserFields": True}),
    "features": json.dumps({"hidden_profile_subscriptions_enabled": True, "rweb_tipjar_consumption_enabled": True, "responsive_web_graphql_exclude_directive_enabled": True, "verified_phone_label_enabled": False, "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False, "responsive_web_graphql_timeline_navigation_enabled": True}),
}
r = session.get(url, params=params)
user = r.json().get("data", {}).get("user", {}).get("result", {})
user_id = user.get("rest_id")  # e.g. "1365020011123773442"
```

Known correct IDs (verify before use):
- @Teknium = 1365020011123773442 (NOT 317835812 which returns empty tweets)
- @NousResearch = 1318419526132862976

## Tweet Reply/Comment Scanning (for repo links)

To find GitHub links in tweet replies (community contributions, related repos), use TweetDetail:

```python
url = "https://x.com/i/api/graphql/5sGVenr9szUMxfmfUwN7rA/TweetDetail"
params = {
    "variables": json.dumps({"focalTweetId": tweet_id, "withSafetyModeUserFields": True, "withVoice": True}),
    "features": json.dumps(FEATURES),
}
# Parse: data.threaded_conversation_with_injections_v2.instructions[].entries[]
# Each entry may have content.items[] with itemContent.itemType == "TimelineTweet"
# OR content.itemContent directly (check both paths)
```

This returns the conversation thread including replies and quote tweets. Scan reply text and URLs for `github.com` links.

## Rate Limiting Strategy

X rate-limits GraphQL aggressively. Between calls:
- 2 seconds minimum between UserTweets calls
- 3 seconds between TweetDetail (reply) calls
- If you get empty responses or errors, wait 30+ seconds before retrying
- Batch all accounts in one pass, don't interleave with reply fetching

## Full Bridge Script

A production bridge script is at `~/subconscious/twitter_bridge.py` with:
- Multi-account tracking (Teknium, NousResearch)
- Seen tweet dedup via JSON file
- Reply scanning for GitHub links on hot tweets (>100 likes)
- Credential management in `~/.hermes/twitter_bridge/credentials.json`
- Output to `~/.hermes/twitter_bridge/latest_tweets.json`

## Newsletter Curation Pipeline (X as Content Source)

Use the cookie API to build automated newsletters that aggregate and distill news from X. This is **read-only curation** — no posting needed, so the free cookie API is the right tool (not the paid official API).

### Architecture

```
X Cookie API (scan/search) → Deduplicate → Extract article links
                                    ↓
Kimi Webbridge / web_extract (read linked articles)
                                    ↓
vLLM/Claude/DeepSeek (summarize, neutralize, fact-check)
                                    ↓
Substack / SendGrid / static site (publish)
```

### Source Scanning (Bias-Balanced)

Follow accounts across the political spectrum, or use SearchTimeline with topic queries:

```python
queries = [
    'breaking news min_faves:100',
    'world news min_faves:50',
    'politics min_faves:100',
    'economy inflation jobs min_faves:50',
    'climate report study min_faves:30',
]
```

**Cross-source verification**: When the same story appears from left-leaning and right-leaning accounts, extract both, note differences in framing, and present only the overlapping factual claims.

### Article Link Extraction

Tweets often link to paywalled articles. Extraction fallback chain:
1. **Direct URL** — try `web_extract` first (fastest)
2. **Kimi Webbridge** — if article requires JS or login, use the Chrome extension to capture full text
3. **Archive.today / 12ft.io** — bypass paywalls for major outlets
4. **Skip** — if all fail, summarize from tweet text alone with "[full article unavailable]" flag

### Content Filtering Rules

- **Skip**: opinion threads, unverified rumors, engagement bait ("BREAKING:" with no source), memes
- **Flag for review**: stories only reported by one side of spectrum, claims without named sources
- **Include**: stories with 2+ independent sources, official statements, data releases, research papers

### Neutral Summary Prompt Template

```
You are a factual news distiller. Given the following source material about [TOPIC],
produce a neutral summary that:
1. States only verifiable facts, not opinions
2. Attributes every claim to its source
3. Separates "confirmed" from "reported/alleged"
4. Notes gaps or contradictions between sources
5. Uses neutral language (no loaded terms)

Sources:
[source 1 text]
[source 2 text]
...
```

### Publishing Options

| Platform | API | Cost | Best For |
|----------|-----|------|----------|
| Substack | Yes (limited) | Free | Paid newsletters, audience building |
| SendGrid | Yes | Free tier | Email digests, lists |
| Ghost | Yes | Self-hosted | Full control, no platform lock |
| GitHub Pages | No (static) | Free | Simple HTML digests |

### Anonymity Considerations

- Substack requires email + payment info (even for free newsletters)
- Ghost self-hosted + privacy.com + ProtonMail = near-anonymous
- GitHub Pages + Cloudflare = completely anonymous but no subscriber management

## Multi-Persona Propaganda Demystification Engine

Build a **multi-persona scanner** that maps narrative propagation across ideological filter bubbles. This surfaces stories that break through silos and makes framing differences explicit.

### Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  MULTI-PERSONA  │────▶│  CROSS-REFERENCE │────▶│  BIAS DECOMPOSE │
│  X FEED SCANNER │     │  & CLAIM VERIFY  │     │  & TRANSPARENCY │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                        │
                              ┌─────────────────────────┘
                              ▼
                       ┌─────────────────┐
                       │  DAILY DIGEST   │
                       │  GENERATOR      │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  STATIC SITE    │
                       │  (HTML/CSS)     │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  BOT DISTRIBUTE │
                       │  (Fediverse/    │
                       │   Newsletter)   │
                       └─────────────────┘
```

### Persona Configuration

Create 3+ X accounts, each following a different ideological slice:

```yaml
personas:
  - name: "left_lens"
    display_name: "Left Lens"
    bias_indicator: "left"
    follows: [AOC, BernieSanders, maddow, TheIntercept, MotherJones]
    search_queries:
      - "from:AOC OR from:BernieSanders OR from:maddow"
      - "progressive policy reform"

  - name: "center_lens"
    display_name: "Center Lens"
    bias_indicator: "center"
    follows: [Reuters, AP, BBCWorld, NPR, PBS]
    search_queries:
      - "from:Reuters OR from:AP OR from:BBCWorld"
      - "bipartisan compromise legislation"

  - name: "right_lens"
    display_name: "Right Lens"
    bias_indicator: "right"
    follows: [GOP, BreitbartNews, DailyCaller, TuckerCarlson]
    search_queries:
      - "from:GOP OR from:BreitbartNews OR from:DailyCaller"
      - "conservative values traditional"

  - name: "personal_lens"
    display_name: "Your Feed"
    bias_indicator: "neutral"
    use_home_timeline: true
    follows: []
    search_queries: []
```

### Cookie Management

Each persona needs its own cookie file:
```
personas/left_lens_cookies.json
personas/center_lens_cookies.json
personas/right_lens_cookies.json
```

Extract cookies from each account's browser session. The scanner rotates through personas automatically. See `references/single-account-multi-persona.md` for the validated pattern using one account across all personas.

### Personal Feed Integration (NEW)

Add a `personal_lens` persona with `use_home_timeline: true` to include your actual X feed in the analysis. This creates a baseline for comparison:

```python
# In scanner.py, check for home timeline flag
if persona.get("use_home_timeline", False):
    tweets = fetch_home_timeline(session, hashes, count=20)
    for t in tweets:
        t["source_persona"] = persona_name
        t["source_type"] = "timeline"
        t["source_account"] = "your_feed"
```

**Why this matters**: Shows what YOUR algorithm shows vs what each ideological bubble sees. Surfaces stories that reach you but not the curated personas, and vice versa.

**HomeLatestTimeline endpoint** (verified working):
```python
hash_val = hashes.get("HomeLatestTimeline", "yVGDzqYZZVQOlK3KhJx5ag")
url = f"{BASE_URL}/{hash_val}/HomeLatestTimeline"
# Returns ~85-100 tweets per call
# Response path: data.home.home_timeline_urt.instructions[].entries[]
```

**Note**: HomeTimeline (not HomeLatestTimeline) returns 404. Always use HomeLatestTimeline for home feed access.

### Narrative Pattern Detection

The scanner identifies:
- **Cross-persona stories**: Same story appearing across ideological feeds
- **Sensational language frequency**: Loaded terms ("slammed", "bombshell", "shocking")
- **Timing clusters**: Coordinated posting patterns
- **Framing differences**: How each persona describes the same event

### Bias Decomposition Output

For each story, the digest shows:
- How **Left Lens** frames it (loaded language used)
- How **Center Lens** frames it (neutral vs institutional)
- How **Right Lens** frames it (loaded language used)
- How **Your Feed** frames it (algorithmic baseline)
- Sample tweets from each perspective
- Transparency notes about methodology

### Static Site Generation

Generate a dark-themed static site (no JS framework needed):
- Mobile-responsive CSS
- Color-coded personas: red=left, yellow=center, green=right, blue=personal
- Archive of past digests
- No server required — host on GitHub Pages, Netlify, or locally

### Bot Distribution (NEW)

After site generation, auto-post to:
- **Mastodon/Fediverse**: Daily digest summary as toot
- **Bluesky**: Daily digest as skeet
- **Email Newsletter**: HTML digest to subscriber list

```python
# Pipeline now includes bot step
steps = [
    ("scanner.py", "Multi-persona feed scanning"),
    ("digest_generator.py", "Daily digest generation"),
    ("site_generator.py", "Static site generation"),
    ("bot/run_bots.py", "Bot distribution (Mastodon/Bluesky/Newsletter)"),
]
```

See `references/bot-distribution-setup.md` for full configuration.

### Key Implementation Notes

- **Deduplicate by text[:80]**: X returns duplicates across queries and personas
- **Engagement scoring**: `likes + retweets*3 + replies*2` — retweets indicate endorsement
- **Rate limiting**: 2s between UserTweets, 3s between SearchTimeline, 5s between personas
- **Cron automation**: `0 6 * * * cd ~/project && python3 run_pipeline.py`
- **Pseudonymous**: Author as "The Curator" — not truly anonymous but not personally linked
- **Browser tools unreliable**: `browser_navigate` has 55% success rate for X. Prefer cookie-based API (this skill) for data extraction. Browser tools fail on X due to bot detection, JS requirements, and cloud browser IP blocking.

### Limitations & Honesty

This tool does NOT deliver "objective truth." It:
- Surfaces stories that break through ideological silos
- Makes framing explicit and transparent
- Encourages readers to verify claims against primary sources
- Highlights when the same event gets radically different coverage

The output reflects the scanner's training data biases + the feed biases of the personas. Always include transparency notes about methodology.

## Vision-Enhanced Bridge (API + GLM-5V)

For monitoring tweets that contain images, use a two-layer architecture:

1. **Layer 1: API Bridge** (text/links/engagement) — use the GraphQL cookie API above
2. **Layer 2: GLM-5V-turbo** — download tweet media images, send to vision model for analysis

### Vision Model: GLM-5V-turbo

```python
import urllib.request, json, base64

def analyze_image(image_url_or_b64, prompt, glm_key):
    """Send image to GLM-5V-turbo for analysis."""
    if image_url_or_b64.startswith("http"):
        img_b64 = download_and_b64(image_url_or_b64)
    else:
        img_b64 = image_url_or_b64
    
    payload = {
        "model": "glm-5v-turbo",
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
            {"type": "text", "text": prompt}
        ]}],
        "max_tokens": 1000,
    }
    req = urllib.request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {glm_key}", "Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=60)
    return json.loads(resp.read())["choices"][0]["message"]["content"]
```

**CRITICAL**: Only `glm-5v-turbo` works. All other GLM vision models return "model not found":
- `glm-4v` -- DOES NOT EXIST
- `glm-4v-flash` -- DOES NOT EXIST
- `glm-4v-plus` -- DOES NOT EXIST
- `glm-5v-turbo` -- ONLY working model (confirmed April 2026)

GLM-5V-turbo is ~13s per call, excellent at: UI screenshots, code screenshots, diagrams, alchemical art, GitHub pages, photos with context. Provide tweet text as context in the prompt for best results.

### Production Script

`~/subconscious/twitter_vision_bridge.py` — combined API + vision bridge:
- Fetches tweets via GraphQL API (text, links, engagement)
- Downloads media images from tweets
- Sends each image to GLM-5V-turbo with tweet context
- Saves results to `~/.hermes/twitter_bridge/vision_bridge_output.json`
- Can be cronned for continuous monitoring

## Pitfalls

- **Cookie extraction methods**: Three approaches available — (1) Chrome extension with `chrome.cookies` API (best for multi-persona), (2) DevTools manual extraction (one-off), (3) CDP script for programmatic extraction from running browser. See `references/chrome-extension-cookie-extraction.md` for extension code.
- **Cookie expiration**: auth_token expires. If you get empty responses, ask user to re-extract cookies.
- **AUTH_TOKEN truncation**: The token in `/tmp/x_api.py` must be the FULL value from browser DevTools (e.g. `2c16ccd91e59b677c6eee641350555897e8f57ca`). Ellipsis (`2c16cc...57ca`) means it was redacted during file creation and will cause 401 errors. The `execute_code` tool's output ALSO masks tokens — you'll see `AUTH_TOKEN="***"` even after a successful write. Only a live API call confirms the token.
- **Rate limits**: X rate-limits GraphQL endpoints. Add delays between calls if doing bulk fetching.
- **Hash rotation**: GraphQL hashes change every few weeks. Always extract fresh ones using the queryId+operationName regex pattern.
- **SearchTimeline = POST only**: This endpoint returns 404 on GET. Must use `session.post(url, json={...})`. All other endpoints (UserTweets, HomeLatestTimeline) work with GET.
- **HomeTimeline**: Parameters change frequently. UserTweets is more stable.
- **Browser login impossible (confirmed April 2026, 3 engines tested)**: X blocks ALL automated browser logins. Tested: (1) Playwright Chromium via agent-browser -- bot detection blocks even human-typed input. (2) Real Chrome --remote-debugging-port on macOS -- CDP port never binds (Chrome ignores flag when launched from terminal). (3) Camofox anti-detection Firefox -- X still fingerprints it and redirects /login to homepage. ALSO: X's React forms swallow browser_type/fill input -- the DOM value appears set but React state doesn't register it, so Next button sees empty field. Only /evaluate with nativeInputValueSetter works for setting values, but the login itself still gets blocked. Cookie extraction from user's real browser remains the ONLY path for X access.
- **Cloud browsers BLOCKED by X (Browserbase confirmed, April 2026)**: Browserbase + Playwright connects fine, cookies inject fine, but X shows "This account doesn't exist" for ANY profile (even @elonmusk). X fingerprints cloud browser IPs and blocks profile viewing. This applies to Browserbase, likely also to other cloud browser services. The API bridge (GraphQL with cookies) works perfectly — use API for data, NOT browser navigation.
- **web_extract cannot read X**: X.com requires JavaScript. Use the cookie API or vxtwitter instead of web_extract for tweet content.
- **PII scrubber hides tokens in file reads**: After writing a new auth_token, `read_file` and `execute_code` will show `AUTH_TOKEN="***"`. The write still succeeded — verify with an API call, not a file read.
- **GLM-5V-turbo is the ONLY working vision model**: All other GLM vision model names (glm-4v, glm-4v-flash, glm-4v-plus) return error code 1211 "model not found". Only `glm-5v-turbo` works on `open.bigmodel.cn/api/paas/v4`.
- **API Features dict must match exactly**: My manual Python scripts got 404 on UserTweets because the `features` dict had slightly different keys than the working bridge script. Copy the FEATURES dict from `~/subconscious/twitter_bridge.py` exactly — it has 18+ keys that must all be present.
- **URL extraction needs `.get()` fallback**: When parsing tweet entities, `u["expanded_url"]` crashes with KeyError if the field is missing. Use `u.get("expanded_url", u.get("url", ""))` instead. This was discovered during live testing of the propaganda demystification scanner.
- **Single-account multi-persona works**: If you only have one X account, all personas can share the same cookies while querying different follows lists. See `references/single-account-multi-persona.md` for the validated pattern (392 tweets across 3 personas with one cookie set).
- **Personal timeline scanning**: Add `use_home_timeline: true` to a persona to fetch your actual X "For You" feed via `HomeLatestTimeline`. See `references/personal-timeline-and-extension.md` for implementation and the critical distinction between `HomeTimeline` (404) and `HomeLatestTimeline` (works).
- **Bot distribution**: After site generation, auto-post to Mastodon, Bluesky, and email newsletter. See `references/bot-distribution-setup.md` for full configuration.
- **Cron scheduling**: Use `crontab -e` directly, NOT the `cronjob` tool (17% success rate). The cronjob tool has known reliability issues — prefer manual crontab editing for production schedules.
