---
name: medical-exam-api-extraction
title: Medical Exam API Extraction
description: |
  Extract questions and review data from medical exam platforms (UWorld QBank, NBME
  self-assessments) using reverse-engineered REST APIs and Chrome CDP automation.
  Covers authentication, data extraction, image downloads, and Anki export.
triggers:
  - When extracting UWorld or NBME question data
  - When reverse-engineering medical exam platform APIs
  - When building Anki decks from QBank data
  - When the user says "uworld", "nbme", "qbank", "extract questions"
category: software-development
---

# Medical Exam API Extraction

## Overview

Medical exam platforms (UWorld, NBME) store valuable question data behind proprietary
interfaces. This skill covers extracting that data for study analysis, Anki card
creation, or QBank review export.

---

## Section 1: UWorld QBank Extraction

### Overview

UWorld's gateway REST API (`gateway-api.uworld.com`) exposes all QBank data as JSON.
Auth requires 3 mandatory headers captured from Chrome via CDP.

### Prerequisites

- Chrome with remote debugging:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  "--remote-allow-origins=*" \
  --user-data-dir=/tmp/chrome-uworld
```
- User logged into UWorld (apps.uworld.com) in that Chrome instance
- Python packages: `requests`, `websocket-client`

### Authentication (3 mandatory headers)

**Header 1: Authorization**
- Format: `Bearer {JWT}`
- Source: `sessionStorage.getItem('authInfo')` → parse JSON → `.at` field
- JWT has `exp` claim — expires ~1hr. Re-extract from Chrome if expired.
- Also available in cookie `uw_at_config` as `{"at":"eyJ..."}`

**Header 2: api-uwsub-key**
- Format: Long RSA-encrypted string (~1600 chars)
- NOT in cookies or sessionStorage — captured via Chrome CDP Network.requestWillBeSent interception
- Persistent across session (doesn't expire with JWT)
- Fallback: read from `~/Desktop/uworld_data/captured_headers.json`

**Header 3: x-uwsub-session-id**
- Format: UUID (e.g., `550e8400-e29b-41d4-a716-446655440000`)
- Source: sessionStorage `authInfo` → `.sessionId` field

### Chrome CDP Header Capture

```python
import json, websocket

def capture_uworld_headers():
    # Connect to Chrome DevTools Protocol
    ws = websocket.create_connection('ws://localhost:9222/devtools/browser/')
    
    # Enable Network domain
    ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
    
    # Intercept requestWillBeSent for headers
    while True:
        msg = json.loads(ws.recv())
        if msg.get('method') == 'Network.requestWillBeSent':
            headers = msg['params']['request']['headers']
            if 'api-uwsub-key' in headers:
                return headers
```

### Data Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/qbank/questions` | All questions with metadata |
| `GET /api/v1/qbank/questions/{id}` | Individual question detail |
| `GET /api/v1/qbank/tests` | User's test history |
| `GET /api/v1/qbank/performance` | Performance analytics |

### Question Data Structure

```json
{
  "id": 12345,
  "question": "A 45-year-old male presents with...",
  "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
  "correctAnswer": "B",
  "explanation": "Detailed explanation text...",
  "subject": "Cardiology",
  "system": "Cardiovascular",
  "difficulty": "Medium",
  "images": ["https://.../image1.png"]
}
```

### Image Download

Images are behind CDN with auth. Use captured Authorization header:
```python
import requests

headers = {
    'Authorization': 'Bearer ' + jwt_token,
    'api-uwsub-key': api_key,
    'x-uwsub-session-id': session_id
}

response = requests.get(image_url, headers=headers)
with open(f'images/{question_id}_{image_index}.png', 'wb') as f:
    f.write(response.content)
```

---

## Section 2: NBME Self-Assessment Extraction

### Overview

NBME self-assessments store exam review data across 3 systems:
1. **MyNBME** (Salesforce Lightning) — login portal
2. **INSIGHTS** (AWS QuickSight) — score dashboard with question-level report links
3. **starttest.com** (Prometric) — interactive exam review with individual questions

There is NO REST API for question data. All extraction goes through Chrome CDP automating the starttest.com exam review UI.

### Prerequisites

- Chrome with remote debugging:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  "--remote-allow-origins=*" \
  --user-data-dir=/tmp/chrome-nbme
```
- Python packages: `websocket-client`, `requests`

### Authentication — Salesforce Lightning Login

**MyNBME Login (mynbme.org)**
The login form is Salesforce Lightning with dynamic element IDs. Use CLASS selectors, NOT name/id:
- Username: `document.querySelector('.sfdc_usernameinput')`
- Password: `document.querySelector('.sfdc_passwordinput')`
- Submit: `document.querySelector('.sfdc_button')`

**MFA Required**
After password submit, Salesforce sends SMS/Email MFA code. The MFA input field has dynamic ID. Use:
```javascript
document.querySelector('input[type="text"][placeholder*="code"], input[type="number"]')
```

### Chrome CDP Automation Flow

1. **Navigate to MyNBME** → Login with credentials + MFA
2. **Navigate to INSIGHTS dashboard** → Find exam with "View Report" link
3. **Click "View Report"** → Opens starttest.com in new tab (Prometric)
4. **Switch to starttest.com tab** → This is where question data lives
5. **Iterate through questions** → CDP Runtime.evaluate to extract DOM content

### starttest.com Frame Architecture

starttest.com uses nested iframes:
```
Main page (starttest.com)
└── iframe #1 (exam container)
    └── iframe #2 (question content)
        └── Actual question HTML
```

Use CDP to traverse frames:
```python
# Get frame tree
ws.send(json.dumps({
    "id": 1,
    "method": "Page.getFrameTree"
}))

# Evaluate in specific frame
ws.send(json.dumps({
    "id": 2,
    "method": "Runtime.evaluate",
    "params": {
        "expression": "document.querySelector('.question-text').innerText",
        "contextId": frame_context_id  # From ExecutionContextCreated events
    }
}))
```

### Question Extraction Pattern

```python
def extract_nbme_question(ws, frame_id):
    # Get question text
    result = evaluate_in_frame(ws, frame_id, """
        {
            text: document.querySelector('.question-text')?.innerText,
            options: Array.from(document.querySelectorAll('.option-text')).map(o => o.innerText),
            correct: document.querySelector('.correct-answer')?.innerText,
            explanation: document.querySelector('.explanation')?.innerText
        }
    """)
    return json.loads(result['result']['value'])
```

### Incremental Save Strategy

NBME sessions timeout after ~30 minutes of inactivity. Save progress every 5 questions:
```python
import json

def save_progress(data, exam_name):
    with open(f'nbme_{exam_name}_progress.json', 'w') as f:
        json.dump(data, f, indent=2)

def load_progress(exam_name):
    try:
        with open(f'nbme_{exam_name}_progress.json') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'extracted': [], 'last_index': 0}
```

---

## Section 3: Common Patterns

### Chrome CDP Connection

```python
import websocket, json, requests

def connect_cdp():
    # Get WebSocket URL from Chrome
    resp = requests.get('http://localhost:9222/json/version')
    ws_url = resp.json()['webSocketDebuggerUrl']
    return websocket.create_connection(ws_url)
```

### Session Persistence

Both platforms require active browser sessions. Tips:
- Use `--user-data-dir` to persist login state between runs
- Capture headers to file for reuse within JWT expiry window
- Re-authenticate when JWT expires (UWorld: ~1hr, NBME: session-based)

### Rate Limiting

- UWorld API: ~100 requests/minute before throttling
- NBME starttest.com: No explicit rate limit but be respectful
- Add `time.sleep(0.5)` between requests

### Data Export Formats

**Anki CSV:**
```csv
question,options,correct,explanation,subject,tags
"Question text","A. Option 1|B. Option 2|C. Option 3|D. Option 4","B","Explanation...","Cardiology","uworld::cardiology"
```

**JSON for analysis:**
```json
{
  "source": "uworld",
  "exam_id": "step1-qbank",
  "extracted_at": "2026-04-01T12:00:00Z",
  "questions": [...]
}
```

## Pitfalls

- **JWT expiry:** UWorld JWT expires ~1 hour. Re-extract from Chrome when expired.
- **MFA timeout:** NBME MFA codes expire quickly. Have phone ready.
- **Frame traversal:** starttest.com uses nested iframes. Always verify you're evaluating in the correct frame context.
- **Salesforce dynamic IDs:** MyNBME element IDs change per session. Use class selectors only.
- **Image auth:** UWorld images require active auth headers. Download immediately after extraction.
- **Session timeout:** NBME review sessions expire after ~30 min inactivity. Save incrementally.

## References

- `references/uworld-api-endpoints.md` — Complete UWorld API endpoint catalog
- `references/nbme-starttest-dom-map.md` — starttest.com DOM selectors and frame structure
- `references/chrome-cdp-patterns.md` — Reusable CDP automation patterns
- `references/anki-export-format.md` — Anki CSV/JSON import formats
