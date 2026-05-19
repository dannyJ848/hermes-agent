# X/Twitter Cookie Extraction from Browser DevTools

## When to Use

X's GraphQL API requires `auth_token`, `ct0`, and `twid` cookies. These expire and must be refreshed periodically. The fastest way to get fresh cookies is directly from the user's browser dev tools.

## Prerequisites

- User is logged into x.com in their browser (Chrome/Safari/Firefox)
- Browser DevTools is open (F12 or Cmd+Option+I)

## Extraction Steps

### Method 1: Console (Fastest — 10 seconds)

1. Open x.com in browser
2. Open DevTools → Console tab
3. Paste and run:
```javascript
// Get individual cookies
document.cookie.split(';').map(c => c.trim()).filter(c => c.startsWith('auth_token=') || c.startsWith('ct0=') || c.startsWith('twid=')).join('\n')
```

4. Copy the output — three lines like:
```
auth_token=b73e8375d0979fb755fe808df41a935c2e9aa234
ct0=6b7dd71e0d2459a7b57f8c74309bf072be2821d96fe4dc333f00672548cc76e4ef9fc67b2e3bfc7503233e4a816e7b3f7cfd4edc283d2ff2540abeeb32b82b1eb3ac91da52a947e4b946ad29ce725a9c
twid=u%3D1225028680327614464
```

### Method 2: Application Tab (When Console Fails)

1. DevTools → Application (or Storage in Firefox) → Cookies → https://x.com
2. Find and copy:
   - `auth_token` — the session token
   - `ct0` — the CSRF token
   - `twid` — user ID in format `u%3D<USER_ID>`

### Method 3: Network Tab (For OAuth/SSO Users)

If `auth_token` is `undefined` in console, the user logged in via Google/Apple OAuth (not password). In this case:

1. DevTools → Network tab
2. Filter by "graphql" or "api"
3. Click any XHR request to x.com/i/api/graphql/...
4. In Request Headers, find:
   - `cookie:` header — contains all three cookies
   - `x-csrf-token:` header — same as `ct0` value

## Updating Hermes Config

After extracting cookies, update `~/.hermes/config.yaml`:

```yaml
x_cookies:
  auth_token: b73e8375d0979fb755fe808df41a935c2e9aa234
  ct0: 6b7dd71e0d2459a7b57f8c74309bf072be2821d96fe4dc333f00672548cc76e4ef9fc67b2e3bfc7503233e4a816e7b3f7cfd4edc283d2ff2540abeeb32b82b1eb3ac91da52a947e4b946ad29ce725a9c
  twid: u%3D1225028680327614464
```

## Testing Fresh Cookies

```python
import requests, json

AUTH_TOKEN = "b73e8375d0979fb755fe808df41a935c2e9aa234"
CT0 = "6b7dd71e0d2459a7b57f8c74309bf072be2821d96fe4dc333f00672548cc76e4ef9fc67b2e3bfc7503233e4a816e7b3f7cfd4edc283d2ff2540abeeb32b82b1eb3ac91da52a947e4b946ad29ce725a9c"
TWID = "u%3D1225028680327614464"
BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

s = requests.Session()
s.cookies.set("auth_token", AUTH_TOKEN, domain=".x.com")
s.cookies.set("ct0", CT0, domain=".x.com")
s.cookies.set("twid", TWID, domain=".x.com")
s.headers.update({
    "Authorization": f"Bearer {BEARER}",
    "x-csrf-token": CT0,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "x-twitter-active-user": "yes",
    "x-twitter-auth-type": "OAuth2Session",
})

# Test tweet fetch
variables = json.dumps({
    "tweetId": "2050886233921061281",
    "withCommunity": False,
    "includePromotedContent": False,
    "withVoice": False,
    "withBirdwatchNotes": False,
})
r = s.get("https://x.com/i/api/graphql/V3vfsYzNEyD9tsf4xoFRgw/TweetResultByRestId", params={"variables": variables})
print("Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    text = data.get("data", {}).get("tweetResult", {}).get("result", {}).get("legacy", {}).get("full_text", "")
    print("Tweet:", text[:100])
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `auth_token` undefined in console | OAuth login (Google/Apple) | Use Network tab to extract cookies from request headers |
| 401 on API calls | Stale cookies | Re-extract fresh cookies from browser |
| 404 "Query not found" | GraphQL hash rotated | Hash extraction from x.com/home JS needed |
| 422 "must be defined" | Missing variables | Add `withVoice`, `withBirdwatchNotes`, `includePromotedContent` |
| Console DOMException | Browser detached from dev tools | Reopen DevTools, refresh page |

## Cookie Expiry

- `auth_token`: ~7 days (but may invalidate sooner if X detects "suspicious" activity)
- `ct0`: Session-scoped, expires when browser closes
- `twid`: Long-lived, rarely changes

**Refresh schedule:** When 401 errors appear, re-extract cookies immediately. No code changes needed — just update config.yaml.
