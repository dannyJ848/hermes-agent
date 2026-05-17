# Browser Article Extraction for X/Twitter

When the GraphQL API returns 404 for X articles (e.g., `https://x.com/i/article/2053106718226227203`), use browser automation with injected cookies.

## Pattern

1. Navigate to article URL (will redirect to login)
2. Inject cookies via browser console
3. Re-navigate to article URL
4. Use browser vision to extract text
5. Scroll to get remaining content

## Cookie Injection

```javascript
// In browser console (via browser_console tool)
document.cookie = "auth_token=<full_token>; domain=.x.com; path=/; secure";
document.cookie = "ct0=<csrf_token>; domain=.x.com; path=/; secure";
document.cookie = "twid=<user_id>; domain=.x.com; path=/; secure";
```

## Full Workflow

```python
# Step 1: Navigate (will hit login wall)
browser_navigate(url="https://x.com/i/article/2053106718226227203")

# Step 2: Inject cookies
browser_console(code="""
document.cookie = "auth_token=2aecf52afb3e83777058b0c9744030caf0b9f076; domain=.x.com; path=/; secure";
document.cookie = "ct0=5707023c848787b9bc3851b85a8ad2c93546e14c74874bed994e43c48f43c880b8509da0218787316cdf540c42c213955e64419adad71e2c39996cadbb0fbaa41a5cdb704cc5d15611c02860b5bbb6c9; domain=.x.com; path=/; secure";
document.cookie = "twid=u%3D1225028680327614464; domain=.x.com; path=/; secure";
""")

# Step 3: Re-navigate (now logged in)
browser_navigate(url="https://x.com/i/article/2053106718226227203")

# Step 4: Extract with vision
browser_vision(question="Extract all text from this article. Show me everything visible.")

# Step 5: Scroll and repeat
browser_scroll(direction="down")
browser_vision(question="Extract the remaining text. Continue from where previous extraction left off.")
```

## When to Use This vs API

| Content Type | Method | Works? |
|-------------|--------|--------|
| Tweet text | GraphQL API | ✅ Yes |
| Tweet media | GraphQL API | ✅ Yes (URLs in JSON) |
| X Articles | GraphQL API | ❌ 404 — use browser |
| X Articles | Browser + cookies | ✅ Yes |
| Profile pages | GraphQL API | ✅ Yes |
| Search results | GraphQL API | ✅ Yes (POST) |

## Pitfalls

- **Browser connection drops**: CDP connections to Browserbase can fail. Restart browser if needed.
- **Vision extraction limits**: Long articles need multiple scroll+vision cycles. The article may have 10+ screens of content.
- **Cookie expiration**: Same as API — if cookies expire, re-extract from browser.
- **Cloud browsers blocked**: X fingerprints cloud browser IPs. Use local browser or API for data.
