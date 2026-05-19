# Direct HTML Extraction for X/Twitter (No Auth, No JS)

Session: 2026-05-16 — Extracted tweet from x.com/nftcps/status/2055528097349554480 after all API methods failed.

## When to Use

- Cookie auth expired and user not available to re-extract
- GraphQL endpoints returning 404 (hash rotation)
- vxtwitter API down or rate-limited
- Need to read a single tweet quickly without setup
- Browser automation (Kimi Webbridge) unavailable — extension not connected to current window
- web_extract tool fails (X requires JS)
- web_research tool fails (Firecrawl/SearXNG not configured)
- Nitter instances return empty or 403

## Technique

X serves tweet content in the initial HTML payload as escaped JSON strings. The HTML is ~275KB and contains the tweet data embedded in `<script>` tags.

### Python Pattern

```python
import requests, re

def extract_tweet_text(user: str, tweet_id: str) -> list[str]:
    """Extract tweet text from x.com HTML without auth or JS."""
    url = f"https://x.com/{user}/status/{tweet_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
    
    results = []
    
    # Method 1: Extract from "text":"..." fields (may contain Unicode escapes)
    texts = re.findall(r'"text":"([^"]{50,2000})"', r.text)
    for text in texts:
        try:
            decoded = text.encode('utf-8').decode('unicode_escape')
            results.append(decoded)
        except UnicodeDecodeError:
            results.append(text)
    
    # Method 2: Extract from "full_text":"..." fields (more reliable for longer tweets)
    full_texts = re.findall(r'"full_text":"([^"]{50,2000})"', r.text)
    for text in full_texts:
        try:
            decoded = text.encode('utf-8').decode('unicode_escape')
            results.append(decoded)
        except UnicodeDecodeError:
            results.append(text)
    
    return results
```

### Bash Pattern

```bash
# Fetch tweet page
curl -sL "https://x.com/USER/status/TWEET_ID" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" | \
  grep -o '"text":"[^"]*"' | head -5
```

## Key Technical Details

1. **Unicode Escaping**: Text is stored as `\uXXXX` sequences. Must decode with `.encode('utf-8').decode('unicode_escape')`.
2. **Multiple Matches**: The HTML contains the main tweet + replies + related tweets. First match is usually the main tweet.
3. **HTML Entities**: `&quot;` appears for quotes. Python's `html.unescape()` may be needed after Unicode decoding.
4. **Size**: Response is ~275KB of HTML with embedded JSON.
5. **Rate Limiting**: X may block aggressive scraping. Add delays between requests.

## Limitations

- Only extracts text content (no images, no engagement metrics, no replies threading)
- May break if X changes their HTML structure
- Not suitable for bulk scanning (use cookie API for that)
- Chinese/Japanese text requires proper Unicode decoding

## Verified Working Example (2026-05-16)

Target: https://x.com/nftcps/status/2055528097349554480

Extracted text (Chinese, translated):
> "Hermes ecosystem exploded this week — community developers turned it into an Agent marketplace!"
> 
> 1. HermesHub — Skills install/unload like apps, can even buy them
> 2. Enterprise adapters — Hermes becomes a company's "digital employee"
> 3. Local memory plugins — Agent truly "understands you"

All other methods failed:
- web_extract: JS not available
- web_research: Firecrawl/SearXNG not configured
- Nitter instances: Empty response or 403
- vxtwitter: Did not attempt (direct HTML worked first)
- Kimi Webbridge: Extension not connected to current window
- Bluesky API: Post not found (different platform)
