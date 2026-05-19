# X/Twitter Trending Topics Extraction via Kimi WebBridge

Extract trending topics from X/Twitter using the real browser automation bridge.

## Prerequisites

- Kimi WebBridge daemon running (`kimi-webbridge status` shows `extension_connected: true`)
- User logged into X/Twitter in Chrome (WebBridge uses real sessions)

## Extraction Pattern

### Step 1: Navigate to trending page

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"navigate","args":{"url":"https://x.com/explore/tabs/trending","newTab":true},"session":"x-trending"}'
```

Wait 2-3 seconds for the page to fully render before extracting.

### Step 2: Extract trending topics via JavaScript

X uses `data-testid="trend"` on trending topic containers. The most reliable extraction:

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"evaluate","args":{"code":"JSON.stringify(Array.from(document.querySelectorAll(\"[data-testid=trend]\")).map(el => el.innerText.trim()))"},"session":"x-trending"}'
```

**Expected output format:**
```json
[
  "IN THE GREY\nNow Playing Only In Theaters\nPromoted by BLACK BEAR",
  "1\n·\nTrending in United States\n#iceman\nTrending with Drake, Khaled",
  "2\n·\nTrending in United States\n3 ALBUMS",
  "3\n·\nSports · Trending\nMitch Marner",
  ...
]
```

Each entry is newline-separated with:
- Rank number (for numbered trends)
- Category: `Trending in [Location]`, `Sports · Trending`, `Politics · Trending`, etc.
- Topic name (hashtag or plain text)
- Related topics (optional, prefixed with "Trending with")

### Step 3: Parse the extracted data

```python
import json

def parse_x_trends(raw_text):
    """Parse X trending topics from WebBridge evaluate output."""
    trends = json.loads(raw_text)
    parsed = []
    for trend in trends:
        lines = [l.strip() for l in trend.split('\n') if l.strip()]
        if not lines:
            continue
        
        # Detect promoted content
        is_promoted = 'Promoted by' in trend
        
        # Extract rank (numeric first line)
        rank = None
        if lines[0].isdigit():
            rank = int(lines[0])
            lines = lines[1:]
        
        # Extract category (contains '·')
        category = None
        for i, line in enumerate(lines):
            if '·' in line and ('Trending' in line or 'Sports' in line or 'Politics' in line):
                category = line
                lines.pop(i)
                break
        
        # Topic name is typically the first remaining line
        topic = lines[0] if lines else ''
        
        # Related topics (lines after "Trending with")
        related = []
        for line in lines[1:]:
            if line.startswith('Trending with'):
                related = [r.strip() for r in line.replace('Trending with', '').split(',')]
            else:
                related.append(line)
        
        parsed.append({
            'rank': rank,
            'category': category,
            'topic': topic,
            'related': related,
            'is_promoted': is_promoted,
            'raw': trend
        })
    return parsed
```

### Alternative: Accessibility Tree Snapshot

If JavaScript evaluation fails, use `snapshot` to read the accessibility tree:

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"snapshot","session":"x-trending"}'
```

Look for elements with:
- `role: "link"` containing post counts (e.g., "25.1K posts")
- `role: "heading"` with "Trending now" or "What's happening"
- `role: "region"` labeled "Trending now"

### Step 4: Cleanup

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"close_session","session":"x-trending"}'
```

## Pitfalls

1. **Page load timing:** X is a React app. The trending list may not be in the DOM immediately. Always wait 2-3 seconds after navigation before extracting.

2. **Selector fragility:** `data-testid="trend"` is more stable than CSS class names (which are hashed). If this changes, fall back to snapshot-based extraction.

3. **Rate limiting:** X may throttle if you navigate/extract too frequently. Add delays between requests.

4. **Login gate:** If the user is not logged into X, the trending page will show a login prompt. Check for `data-testid="loginButton"` to detect this.

5. **Regional variation:** Trending topics are personalized by location. The extracted topics reflect the user's account location settings.

6. **Shell escaping:** See `references/kimi-webbridge-shell-escaping.md` for handling complex JavaScript in curl payloads.

## Verification

After extraction, verify the data looks correct:
- Should have 20-30 trending topics
- First entry may be promoted (marked with "Promoted by")
- Each should have a topic name and category
- Sports/politics/entertainment categories should be present
