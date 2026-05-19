# X/Twitter Cookie API Integration Pattern

Discovered July 2026 during integration of x_api.py into Hermes tools.

## Architecture

X's internal GraphQL API requires:
1. **Cookie auth** — `auth_token`, `ct0`, `twid` cookies from an active browser session
2. **Dynamic query hashes** — GraphQL endpoint IDs rotate frequently; must extract from X's JS
3. **Bearer token** — Static: `AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA`

## Cookie Extraction

From browser DevTools → Application → Cookies → x.com:
- `auth_token` — long-lived session token
- `ct0` — CSRF token (also needed as `x-csrf-token` header)
- `twid` — user ID in format `u%3D<USER_ID>`

Store in `~/.hermes/config.yaml` under `x_cookies:` section.

## Dynamic Hash Extraction

X rotates GraphQL query hashes. The working approach:

```python
def _get_graphql_hashes(session: requests.Session) -> dict:
    """Extract current hashes from X's main page JS."""
    resp = session.get("https://x.com/home")
    if resp.status_code != 200:
        return {}
    
    patterns = [
        (r'"([a-zA-Z0-9_-]{15,25})":"TweetResultByRestId"', "tweet_by_id"),
        (r'"([a-zA-Z0-9_-]{15,25})":"UserTweets"', "user_tweets"),
        (r'"([a-zA-Z0-9_-]{15,25})":"SearchTimeline"', "search"),
        (r'"([a-zA-Z0-9_-]{15,25})":"UserByScreenName"', "user_by_screen_name"),
    ]
    
    hashes = {}
    for pattern, key in patterns:
        match = re.search(pattern, resp.text)
        if match:
            hashes[key] = match.group(1)
    return hashes
```

**Fallback hashes** (last known working — will stale over time):
```python
_FALLBACK_HASHES = {
    "tweet_by_id": "V3vfsYzNEyD9tsf4xoFRgw",
    "user_tweets": "E3opETHurmVJflFsUBVuUQ",
    "search": "g7SDsWwiaaKtRjngIIq-mA",
    "user_by_screen_name": "G3KGOAsY-d5iAE5-4S2-MA",
}
```

## Required Variables (CRITICAL — May 2026 Update)

X's GraphQL endpoints now require a **complete variable set**. Missing any variable causes 422 errors with "must be defined" messages.

### TweetResultByRestId (x_tweet_fetch)
```python
variables = json.dumps({
    "tweetId": tweet_id,
    "withCommunity": False,
    "includePromotedContent": False,
    "withVoice": False,
    "withBirdwatchNotes": False,
})
```

### UserTweets (x_user_tweets)
```python
variables = json.dumps({
    "userId": user_id,
    "count": min(count, 50),
    "includePromotedContent": False,
    "withCommunity": False,
    "withVoice": False,
    "withBirdwatchNotes": False,
})
```

### SearchTimeline (x_search)
```python
variables = json.dumps({
    "rawQuery": query,
    "count": min(count, 50),
    "querySource": "typed_query",
    "product": "Top",
})
```

**The `withVoice` and `withBirdwatchNotes` variables are NEW requirements as of May 2026.** Previously only `withCommunity` was needed. Always include ALL variables to avoid 422 errors.

## User ID Resolution (UserByScreenName Hash Stale)

The `UserByScreenName` endpoint hash rotates more frequently than other hashes. When it goes stale (404 "Query not found"), use a **two-tier resolution strategy**:

### Tier 1: Hardcoded cache for common users
```python
_USER_ID_CACHE = {
    "elonmusk": "44196397",
    "jack": "12",
    "twitter": "783214",
    "x": "17874544",
    "kanyewest": "169686021",
    "billgates": "50393960",
    "jeffbezos": "15506669",
    "sama": "1605",
    "karpathy": "408702380",
    "lexfridman": "323133381",
    "mrbeast": "2455740283",
    "nousresearch": "1487305860",
}
```

### Tier 2: API fallback (when hash is fresh)
```python
def _resolve_user_id(screen_name: str) -> Optional[str]:
    # Check cache first
    if screen_name.lower() in _USER_ID_CACHE:
        return _USER_ID_CACHE[screen_name.lower()]
    
    # Try API lookup with current hash
    # ... extract hash, make request, cache result ...
    return user_id
```

### Adding new users to cache
When you encounter a new user ID via successful API lookup or browser inspection, add it to `_USER_ID_CACHE` immediately so future calls skip the broken UserByScreenName endpoint.

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Stale cookies | Refresh auth_token, ct0, twid from live browser session |
| 404 Not Found | Wrong GraphQL hash | Extract fresh hashes from x.com/home JS |
| 422 "must be defined" | Missing required variable | Add ALL variables: `withVoice`, `withBirdwatchNotes`, `includePromotedContent` |
| 422 on UserTweets | Missing `withVoice`/`withBirdwatchNotes` | Add both variables to the JSON payload |
| 404 "Query not found" | UserByScreenName hash rotated | Use hardcoded `_USER_ID_CACHE` or extract from browser network tab |
| Empty timeline response | Correct hash but wrong structure | Check both `timeline_v2` and `timeline` keys in response |
| GraphQL validation failed | Hash mismatch | Verify hash matches query name exactly |

## Hermes Integration

Tool module at `~/hermes-agent/tools/x_tool.py`:
- Loads cookies from `~/.hermes/config.yaml`
- Extracts hashes dynamically with fallback
- Registers 3 tools: `x_tweet_fetch`, `x_search`, `x_user_tweets`
- READ-ONLY — never post, like, retweet

## Response Structure Variations

X's API response structure varies. The timeline data may be under either `timeline_v2` or `timeline`. Handle both:

```python
user_result = data.get("data", {}).get("user", {}).get("result", {})
# Try both structures
timeline = user_result.get("timeline_v2", {}).get("timeline", {}) \
           or user_result.get("timeline", {}).get("timeline", {})
instructions = timeline.get("instructions", [])
```

**Always check both keys.** The structure changed between API versions without notice.

## Testing

```python
from tools.x_tool import x_tweet_fetch, x_search, x_user_tweets

# Requires fresh cookies in ~/.hermes/config.yaml
result = x_tweet_fetch("2050886233921061281")
print(result.get("success"), result.get("tweet", {}).get("text", "")[:100])

# Test user tweets (uses cached ID for elonmusk)
result = x_user_tweets("elonmusk", count=3)
print(result.get("success"), result.get("count"))
```

## Maintenance

Cookies expire. When 401 errors appear:
1. Open x.com in browser
2. DevTools → Application → Cookies → x.com
3. Copy fresh `auth_token`, `ct0`, `twid`
4. Update `~/.hermes/config.yaml`
5. No code changes needed
