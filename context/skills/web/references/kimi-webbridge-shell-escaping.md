# Kimi WebBridge Shell Escaping Guide

When sending JavaScript code through curl JSON payloads to the WebBridge daemon, shell escaping causes frequent failures.

## The Problem

The shell interprets escape sequences BEFORE the JSON parser sees them. Nested quotes, newlines, and backslashes get mangled.

## Failure Modes

### 1. Nested double quotes inside single-quoted JSON
```bash
# FAILS: shell strips \\ before JSON parser sees them
curl -d '{"code":"document.querySelectorAll(\"[data-testid=trend]\").length"}'
# Error: invalid character 't' after object key:value pair
```

### 2. Newlines in code string
```bash
# FAILS: JSON does not allow literal newlines in strings
curl -d '{"code":"(() => {\n  const x = 1;\n  return x;\n})()"}'
# Error: invalid character '\n' in string literal
```

### 3. Complex selectors with multiple quote types
```bash
# FAILS: attr selector with quotes inside JSON inside shell
curl -d '{"code":"document.querySelectorAll('[data-testid=\\"trend\\"]').length"}'
# Error: syntax error near unexpected token `)'
```

## Working Solutions

### Solution 1: Simple One-Liners (No Nested Quotes)

Use only single quotes in JS, no nested quotes, no newlines:

```bash
# WORKS: simple selector, no nested quotes
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"evaluate","args":{"code":"document.querySelectorAll(\"[data-testid=trend]\").length"},"session":"test"}'
```

**Limitation:** Only works for trivial code. Any nested quotes break it.

### Solution 2: Escape All Inner Quotes

Double-escape inner quotes so they survive shell + JSON:

```bash
# WORKS but fragile: \" becomes \" after shell, then " after JSON
curl -d '{"code":"document.querySelectorAll(\"[data-testid=trend]\").length"}'
```

This is hard to get right and breaks with complex code.

### Solution 3: Write JS to File (Recommended)

Write the JavaScript to a file, then send a minimal loader:

```bash
# Step 1: Write JS to file
cat > /tmp/webbridge_script.js << 'EOF'
(() => {
  const trends = [];
  document.querySelectorAll("[data-testid=trend]").forEach(el => {
    trends.push(el.innerText.trim());
  });
  return JSON.stringify(trends);
})()
EOF

# Step 2: Send loader that reads and evals the file
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"evaluate","args":{"code":"fetch(\"file:///tmp/webbridge_script.js\").then(r=>r.text()).then(t=>eval(t))"},"session":"test"}'
```

**Note:** `file://` URLs may be blocked by Chrome security policy. Alternative:

```bash
# Serve file via local HTTP
python3 -m http.server 8765 &
# Then fetch from http://localhost:8765/webbridge_script.js
```

### Solution 4: Base64 Encode (Most Reliable)

Encode the JS as base64, decode in the browser:

```bash
# Step 1: Encode JS
JS_CODE='(() => { const trends = []; document.querySelectorAll("[data-testid=trend]").forEach(el => { trends.push(el.innerText.trim()); }); return JSON.stringify(trends); })()'
ENCODED=$(echo "$JS_CODE" | base64)

# Step 2: Send decoder
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d "{\"action\":\"evaluate\",\"args\":{\"code\":\"eval(atob('$ENCODED'))\"},\"session\":\"test\"}"
```

### Solution 5: Use Python to Build the Request

Avoid shell escaping entirely by using Python:

```python
import requests, json

code = """
(() => {
  const trends = [];
  document.querySelectorAll("[data-testid=trend]").forEach(el => {
    trends.push(el.innerText.trim());
  });
  return JSON.stringify(trends);
})()
"""

resp = requests.post(
    "http://127.0.0.1:10086/command",
    json={
        "action": "evaluate",
        "args": {"code": code},
        "session": "test"
    }
)
print(resp.json())
```

## Quick Reference

| Complexity | Recommended Approach |
|-----------|---------------------|
| Trivial (no quotes, no newlines) | Direct curl with single-quoted JSON |
| Simple (few quotes) | Careful escaping or Python |
| Moderate (nested selectors) | Write to file + fetch |
| Complex (multi-line, many quotes) | Base64 encode or Python |

## Testing Your Payload

Before sending to WebBridge, validate the JSON:

```bash
# Test if your JSON is valid
echo '{"code":"your code here"}' | python3 -m json.tool
# If this fails, the payload is malformed
```

## Session-Specific Notes

- The WebBridge daemon runs on port 10086 by default
- Session names isolate tab groups — always use distinct names for parallel tasks
- The `evaluate` action shares the page's JS realm — re-declaring `const`/`let` across calls throws `SyntaxError`. Wrap in IIFE: `(() => { ... })()`
