# chrome-applescript-bridge

*Researched: 2026-04-05 15:15 CDT*

# Chrome-to-Hermes Bridge (Apr 2026)

## Architecture
Direct DOM access to user's real Chrome browser via AppleScript + JavaScript execution.
Requires: Chrome → View → Developer → Allow JavaScript from Apple Events (checked).

## API
```python
def chrome_js(js):
    escaped = js.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
    script = f'''
    tell application "Google Chrome"
        tell active tab of front window
            execute javascript "{escaped}"
        end tell
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
    return result.stdout.strip()
```

## Capabilities
- Read page title, URL, body text
- Navigate to URLs via AppleScript `set URL to`
- Scroll via `window.scrollBy(0, N)`
- Extract React DOM elements via `querySelector` / `querySelectorAll`
- X/Twitter: `document.querySelectorAll('[data-testid="tweetText"]')` returns tweet content
- X/Twitter: `document.querySelectorAll('[data-testid="tweet"]')` returns full tweet cards
- No bot detection - uses user's real logged-in session

## Limitations
- No `querySelector('a[href]')` for X links (React shadow DOM hides them)
- No CDP (Chrome ignores --remote-debugging-port on macOS when using real profile)
- Must be single-line JS (escape newlines)
- 15s AppleScript timeout
- X innerText returns full visible viewport, not individual scroll positions

## X/Twitter Scraping Pattern
1. Navigate: `chrome_url("https://x.com/teknium")`
2. Wait for load: check `document.title` contains "X"
3. Extract tweets: `querySelectorAll('[data-testid="tweetText"]')`
4. Scroll + repeat: `window.scrollBy(0, 2000)` + extract again
5. Deduplicate by first 80 chars of text


## Sources

- chrome://inspect/#remote-debugging
- osascript JavaScript execution
