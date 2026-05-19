# Kimi WebBridge Reference

Complete reference for the Kimi WebBridge browser automation system.

## Installation

```bash
curl -fsSL https://kimi-web-img.moonshot.cn/webbridge/install.sh | bash
```

Installs:
- Binary: `~/.kimi-webbridge/bin/kimi-webbridge`
- Daemon auto-starts on port 10086
- Skills for Claude Code, Codex, Kimi CLI, OpenClaw
- Chrome extension (must be installed separately from Chrome Web Store)

## Daemon Management

```bash
export PATH="$HOME/.kimi-webbridge/bin:$PATH"

kimi-webbridge status      # Check daemon + extension connection
kimi-webbridge start       # Start daemon
kimi-webbridge stop        # Stop daemon
kimi-webbridge restart     # Restart daemon
kimi-webbridge logs        # View daemon logs
kimi-webbridge upgrade     # Check for updates
kimi-webbridge uninstall   # Remove completely
```

## Health Check Response

```json
{
  "extension_connected": true,
  "extension_id": "fldmhceldgbpfpkbgopacenieobmligc",
  "extension_version": "1.9.7",
  "port": 10086,
  "running": true,
  "uptime_seconds": 100,
  "version": "v1.9.7"
}
```

**Healthy:** `running: true` AND `extension_connected: true`
**Unhealthy:** Read `~/.claude/skills/kimi-webbridge/references/operations.md` for diagnosis

## API Endpoint

All commands: `POST http://127.0.0.1:10086/command`
Content-Type: `application/json`

## Tool Reference

### navigate
Open a URL. Use `newTab: true` on first call to a session.

```json
{
  "action": "navigate",
  "args": {
    "url": "https://example.com",
    "newTab": true,
    "group_title": "My Task"
  },
  "session": "task-name"
}
```

Returns: `{success, url, tabId}`

### find_tab
Reuse an already-open tab. Matches by domain.

```json
{
  "action": "find_tab",
  "args": {
    "url": "https://www.kimi.com",
    "active": true
  },
  "session": "task-name"
}
```

- `active: true` — picks the tab the user is currently viewing
- `active: false` (default) — picks the leftmost matching tab

If "no open tab found", fall back to `navigate` with `newTab: true`.

### snapshot
Get accessibility tree with `@e` references for interactive elements.

```json
{
  "action": "snapshot",
  "session": "task-name"
}
```

Returns: `{url, title, tree}` where tree contains elements with `ref: "@e1"`, `ref: "@e2"`, etc.

### click
Click an element by `@e` ref or CSS selector.

```json
{
  "action": "click",
  "args": {
    "selector": "@e5"
  },
  "session": "task-name"
}
```

Returns: `{success, tag, text}`

### fill
Type into input, textarea, or contenteditable element. Clears existing content first.

```json
{
  "action": "fill",
  "args": {
    "selector": "@e9",
    "value": "text to type"
  },
  "session": "task-name"
}
```

Returns: `{success, tag, mode}` where mode is `"value"` or `"contenteditable"`

For appending to existing text: read current value via `evaluate`, concatenate, then `fill`.

### evaluate
Execute JavaScript on the page. Supports async/await.

```json
{
  "action": "evaluate",
  "args": {
    "code": "document.title"
  },
  "session": "task-name"
}
```

Returns: `{type, value}`

Tips:
- Use compact `JSON.stringify(data)` — never `JSON.stringify(data, null, 2)` (inflates response)
- Wrap in IIFE for fresh scope: `(() => { const x = ...; return x; })()`

### screenshot
Capture page or element. Returns base64 (large — use helper script instead).

```json
{
  "action": "screenshot",
  "args": {
    "format": "png",
    "quality": 90,
    "selector": "@e5"
  },
  "session": "task-name"
}
```

**Always use helper script instead of direct API call:**
```bash
# Default path: /tmp/kimi-webbridge-screenshots/{timestamp}.png
bash ~/.claude/skills/kimi-webbridge/scripts/screenshot.sh

# With session
bash ~/.claude/skills/kimi-webbridge/scripts/screenshot.sh -s my-task

# Custom output
bash ~/.claude/skills/kimi-webbridge/scripts/screenshot.sh -o /tmp/page.png

# JPEG, quality 60
bash ~/.claude/skills/kimi-webbridge/scripts/screenshot.sh -f jpeg -q 60
```

### network
Monitor network requests.

```json
{
  "action": "network",
  "args": {
    "cmd": "start"
  },
  "session": "task-name"
}
```

Commands: `start`, `stop`, `list`, `detail`

### upload
Upload files to a file input.

```json
{
  "action": "upload",
  "args": {
    "selector": "@e8",
    "files": ["/path/to/file.pdf"]
  },
  "session": "task-name"
}
```

### save_as_pdf
Render current page to PDF.

```json
{
  "action": "save_as_pdf",
  "args": {
    "paper_format": "letter",
    "landscape": false,
    "scale": 1.0,
    "print_background": true,
    "file_name": "my-page"
  },
  "session": "task-name"
}
```

Saved to: `/tmp/kimi-webbridge-pdfs/`

### list_tabs
List all tabs in the session.

```json
{
  "action": "list_tabs",
  "session": "task-name"
}
```

Returns: `{success, tabs: [{tabId, url, title, active, groupTitle}]}`

### close_tab
Close current tab.

```json
{
  "action": "close_tab",
  "session": "task-name"
}
```

### close_session
Close all tabs in the session.

```json
{
  "action": "close_session",
  "session": "task-name"
}
```

Returns: `{success, closed: int}` (count of closed tabs)

## Sessions

Each session name maps to a separate browser tab group. Use distinct names for parallel tasks.

```bash
# Task 1: Google search
curl -s -X POST http://127.0.0.1:10086/command \
  -d '{"action":"navigate","args":{"url":"https://google.com","newTab":true},"session":"search"}'

# Task 2: GitHub issues (concurrent)
curl -s -X POST http://127.0.0.1:10086/command \
  -d '{"action":"navigate","args":{"url":"https://github.com/issues","newTab":true},"session":"github"}'
```

## Special Keys / Form Submit

No separate "press Enter" tool. Options:

1. Click the submit button directly:
```json
{"action":"click","args":{"selector":"@e13"}}
```

2. Dispatch keyboard event via evaluate:
```json
{
  "action": "evaluate",
  "args": {
    "code": "document.activeElement.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))"
  }
}
```

## Limitations

- **isTrusted check**: Sites verifying `event.isTrusted` (some banking, captchas) reject synthetic events. This is a product boundary — no workaround.
- **Cross-origin iframes**: Tools operate on top frame only. Navigate to iframe URL directly if needed.
- **Extension version**: If error says "Please update the Kimi WebBridge extension", direct user to https://kimi.com/features/webbridge

## File Locations

| File | Purpose |
|------|---------|
| `~/.kimi-webbridge/bin/kimi-webbridge` | CLI binary |
| `~/.kimi-webbridge/daemon.pid` | Daemon PID |
| `~/.kimi-webbridge/identity.json` | Device ID |
| `~/.kimi-webbridge/logs/` | Daemon logs |
| `~/.claude/skills/kimi-webbridge/` | Claude Code skill |
| `~/.codex/skills/kimi-webbridge/` | Codex skill |
| `~/.config/agents/skills/kimi-webbridge/` | Kimi CLI skill |
