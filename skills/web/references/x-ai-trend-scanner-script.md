# X AI Trend Scanner Script

Production scanner for extracting AI-related trending topics and posts from X/Twitter using Kimi WebBridge browser automation.

## Script Location
`~/.hermes/scripts/x_ai_trend_scan.py` (also mirrored at `/tmp/x_ai_trend_scan.py`)

## What It Does
1. Navigates to x.com via Kimi WebBridge
2. Extracts trending topics using accessibility tree + JS evaluation
3. Searches for AI-related posts using X's search
4. Generates timestamped JSON report

## Key Technical Pattern: Accessibility Tree + JS Evaluation

X's trending topics use `data-testid="trend"` attributes. The extraction uses TWO techniques:

### Technique 1: Accessibility Tree (snapshot)
```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"snapshot","session":"x-scan"}'
```
Returns structured accessibility tree with `@e` element references. Look for:
- Elements with `name` containing "Trending" or topic text
- Links with `url` pointing to `/search?q=...`

### Technique 2: JavaScript Evaluation (for complex extraction)
```bash
# Extract trending topics via JS
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"evaluate","args":{"code":"JSON.stringify(Array.from(document.querySelectorAll(\"[data-testid=trend]\")).map(el => el.innerText.trim()))"},"session":"x-scan"}'
```

**Shell escaping pitfall:** The nested quotes in `document.querySelectorAll("[data-testid=trend]")` break JSON parsing. Solutions:
1. Use single quotes in JS: `document.querySelectorAll('[data-testid=trend]')`
2. Base64 encode complex JS and decode in evaluate
3. Write JS to file, send minimal fetch+eval code

### Technique 3: Search URL Direct Navigation (most reliable)
Instead of interacting with X's UI, navigate directly to search URLs:
```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"navigate","args":{"url":"https://x.com/search?q=AI%20agent%20framework&src=typed_query&f=live"},"session":"x-scan"}'
```
Then snapshot and extract tweet text from the accessibility tree.

## Cron Integration

Job: `x-ai-trend-scanner` (id: 6380cf058764)
Schedule: Every 4 hours
Script: `x_ai_trend_scan.py`
Enabled toolsets: terminal, web

Created via: `cronjob(action='create', name='x-ai-trend-scanner', schedule='every 4h', script='x_ai_trend_scan.py')`

## Output Format

```json
{
  "timestamp": "2026-05-14T22:16:00",
  "trending_topics": ["Topic 1", "Topic 2", ...],
  "ai_posts": [
    {
      "text": "Post content...",
      "author": "@username",
      "likes": 42,
      "retweets": 5,
      "is_ai_related": true,
      "ai_keywords_found": ["LLM", "agent"]
    }
  ]
}
```

## Comparison: WebBridge vs Cookie API

| Method | Auth Required | Bot Detection | Speed | Best For |
|--------|--------------|---------------|-------|----------|
| Kimi WebBridge | No (uses real Chrome) | Zero | Medium | Trending topics, visual content |
| X Cookie API | Yes (cookies) | Low | Fast | Bulk tweet fetching, timelines |
| vxtwitter | No | Zero | Fast | Individual tweets (no auth) |

## When to Use Which

- **Trending topics**: WebBridge (X's trending page is JS-heavy, API doesn't expose it)
- **User timelines**: Cookie API (faster, more reliable)
- **Individual tweets**: vxtwitter (zero setup)
- **Search results**: Cookie API SearchTimeline (POST, structured data)

## Installation Requirements

```bash
# Kimi WebBridge
curl -fsSL https://kimi-web-img.moonshot.cn/webbridge/install.sh | bash
export PATH="$HOME/.kimi-webbridge/bin:$PATH"

# Chrome extension must be installed and connected
# Verify: kimi-webbridge status → extension_connected: true
```
