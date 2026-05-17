---
name: nbme-api-extraction
version: 2.0
description: Extract wrong questions from NBME self-assessment exam review via Chrome CDP. Handles starttest.com frame architecture, image downloads, and incremental saves.
trigger: When extracting NBME exam question data for Anki card creation, study analysis, or exam review export.
---

# NBME Self-Assessment Extraction Pipeline

## Overview
NBME self-assessments store exam review data across 3 systems:
1. **MyNBME** (Salesforce Lightning) — login portal
2. **INSIGHTS** (AWS QuickSight) — score dashboard with question-level report links
3. **starttest.com** (Prometric) — interactive exam review with individual questions

There is NO REST API for question data. All extraction goes through Chrome CDP automating the starttest.com exam review UI.

## Prerequisites
- Chrome with remote debugging: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 "--remote-allow-origins=*" --user-data-dir=/tmp/chrome-nbme`
- Python packages: `websocket-client`, `requests`

## Authentication — Salesforce Lightning Login

### MyNBME Login (mynbme.org)
The login form is Salesforce Lightning with dynamic element IDs. Use CLASS selectors, NOT name/id:
- Username: `document.querySelector('.sfdc_usernameinput')`
- Password: `document.querySelector('.sfdc_passwordinput')`
- Submit: `document.querySelector('.sfdc_button')`

### MFA Required
After login, NBME sends SMS verification code to phone ending in last 4 digits shown. Enter code in `document.getElementById('smc')`, click `document.getElementById('save')`.

## Recommended Workflow (fastest path)

### Step 1: User opens exam review manually
Have the user navigate to INSIGHTS, click "Question-Level Report" for the desired form. When the score report loads, tell them to click **"Review Incorrect"** (the button INSIDE the score report page, not the outer nav). This filters to only wrong answers.

### Step 2: Run the scraper script
Use `~/Desktop/nbme_wrong_scraper.py` with the form name:
```bash
python ~/Desktop/nbme_wrong_scraper.py Form28
```

The scraper handles everything: reading questions, detecting answers, downloading images, incremental saves.

## starttest.com — Exam Review Interface

### Frame Architecture (5 frames)
- `ElementDisplayFrame` — question content (THE important one)
- `ExhibitFrame` — lab values, exhibits
- `infoPopUpFrame` — popup tools
- `UpToDateFrame` — references
- `VariableFrame` — variable content

### Accessing Frame Content via CDP
```python
cdp("Runtime.enable")
cdp("Page.enable")

frames = cdp("Page.getFrameTree")
elem_frame_id = [f['frame']['id'] for f in frames['frameTree']['childFrames'] 
                  if f['frame'].get('name') == 'ElementDisplayFrame'][0]

iso = cdp("Page.createIsolatedWorld", {
    "frameId": elem_frame_id, "worldName": "nbme", "grantUniveralAccess": True
})
ctx_id = iso['executionContextId']

# Execute JS in frame
result = cdp("Runtime.evaluate", {
    "expression": "document.body.innerText",
    "contextId": ctx_id, "returnByValue": True
})
```

**CRITICAL**: Frame context ID becomes invalid after navigation. Must recreate `createIsolatedWorld` after EVERY Next click.

### Clicking Buttons — MUST use CDP mouse events
JS `.click()` does NOT work for starttest or QuickSight buttons. Use CDP Input.dispatchMouseEvent:
```python
# Get button center coordinates
r = cdp("Runtime.evaluate", {
    "expression": "var r=document.getElementById('Next').getBoundingClientRect(); JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2})",
    "returnByValue": True
})
c = json.loads(r.get('result',{}).get('value','{}'))

cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": c['x'], "y": c['y'], "button": "left", "clickCount": 1})
time.sleep(0.05)
cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": c['x'], "y": c['y'], "button": "left", "clickCount": 1})
```

### Navigation Flow (WARNING)
1. Opens → Performance Profile page
2. Click Next → Score Report page (with "Review All" / "Review Incorrect" buttons)
3. Click Next again → **SURVEY** (SurveyMonkey) → session ENDS
4. Cannot go back. Must re-open the get-score-report URL.

**NEVER click Next past the score report page.** Tell the user to click "Review All" or "Review Incorrect" from INSIDE the score report frame to enter question review mode.

## Wrong Answer Detection

### CRITICAL: Do NOT use ITSIncorrectIcon
The `ITSIncorrectIcon` appears on ALL questions in review mode — it's not a reliable wrong-answer marker. Instead, compare user answer vs correct answer:

```javascript
var correctRow = document.querySelector('.correctOption');
var userRow = document.querySelector('.ITSMCOptionTableOn');
var correctLetter = correctRow ? correctRow.innerText.trim().match(/^([A-E])/)?.[1] : null;
var userLetter = userRow ? userRow.innerText.trim().match(/^([A-E])/)?.[1] : null;
// Wrong if: userLetter != correctLetter OR userLetter is null but correctLetter is not
```

### HTML Classes
- `.correctOption` — the correct answer row (on ALL questions)
- `.ITSMCOptionTableOn` — the answer the user SELECTED
- `.ITSIncorrectIcon` — WARNING: appears on ALL questions, NOT reliable for wrong detection

## Image Extraction

### How images work
Question images use `itdmedia.aspx?data=BASE64_ENCODED_TOKEN` URLs. These are session-bound — they require the starttest session cookies to download.

### Extracting content images
```javascript
// Filter: naturalWidth > 50, not nbmeLogo, not bkgdImg
var imgs = document.querySelectorAll('img');
var contentImgs = [];
for (var img of imgs) {
    if (img.naturalWidth > 50 && img.naturalHeight > 50 && 
        !img.classList.contains('nbmeLogo') && !img.classList.contains('bkgdImg')) {
        contentImgs.push(img.src);
    }
}
```

### Downloading images
```python
# Get cookies from Chrome session
cookies = cdp("Network.getCookies", {"urls": ["https://www.starttest.com"]})
sess = requests.Session()
for c in cookies.get('cookies', []):
    sess.cookies.set(c['name'], c['value'], domain=c.get('domain', ''))
sess.headers.update({'Referer': 'https://www.starttest.com/'})

# Download (verify=False needed)
r = sess.get(img_url, timeout=15, verify=False)
```

## Incremental Saves (CRITICAL)

Scripts WILL timeout at 300s when scraping large exams (~55 wrong questions × ~2s each = ~110s + image downloads). Save JSON after EVERY question:

```python
all_wrong.append(entry)
with open(json_path, 'w') as f:
    json.dump(all_wrong, f, indent=2, ensure_ascii=False)
```

Some questions have `correct_answer: null` and `user_answer: null` — these are **excluded from scoring** (pilot questions). Count them separately. Unanswered questions have `user_answer: null` but `correct_answer` is set.
```python
if os.path.exists(fpath) and os.path.getsize(fpath) > 100:
    entry['local_images'].append(fpath)
    continue  # skip download
```

## Output Data Format

Saved to `~/Desktop/nbme_data/{Form}_wrong_full.json`:
```json
[{
    "form": "Form28",
    "section": 1,
    "item": 1,
    "user_answer": "B",
    "correct_answer": "C",
    "text": "Question 1.\n...(full question + choices + rationale + educational objective)",
    "image_urls": ["https://www.starttest.com/..."],
    "local_images": ["/Users/danny/Desktop/nbme_data/Form28_images/S1_Q1_img0.png"]
}]
```

Images saved to: `~/Desktop/nbme_data/{Form}_images/S{section}_Q{item}_img{index}.png`

## NBME Text Parsing (Question → Structured Data)

The raw `text` field from the scraper has a specific line-by-line format that requires careful parsing:

### Line structure for each question:
```
[0] "Question 41."
[1] "This is a read only version of the item. You can only view..."  ← preamble
[2] "41.\xa0\xa0\t"                                                    ← preamble (item header)
[3] "A 70-year-old man dies in a motor vehicle collision..."            ← STEM starts
[6] "A"                                                                ← choice letter alone
[7] ")\xa0"                                                            ← closing paren + nbsp
[8] "Hyperplastic polyp"                                               ← choice text
[9] "B"
[10] ")\xa0"
[14] "Option is eliminated."                                           ← SKIP this line (review artifact)
[15] "Juvenile polyp"                                                  ← actual choice text is AFTER eliminated marker
...
[23] "Rationale:"
[24] ""
[25] "Correct Answer: E."
[27] "A tubular adenoma is shown..."                                    ← rationale text
[29] "Incorrect Answers: A, B, C, and D."                              ← skip
[31] "Each of these numbers..."                                         ← rationale continues
[33] "Educational Objective: ..."
```

### Parser algorithm (`parse_nbme`):
1. Skip preamble (everything before "select 1 answer from" line)
2. Stem = all lines from preamble end to first standalone `[A-E]` line
3. Choices: loop — find `[A-E]` line, skip `)\xa0` line, skip `Option is eliminated.` lines, read choice text
4. `Correct Answer:` regex → correct letter
5. Rationale = lines between `Rationale:` and `Educational Objective:`, skipping `Correct Answer:` and `Incorrect Answers:` lines
6. Educational Objective = regex on that line

### Key pitfall: "Option is eliminated."
In exam review mode, some choices show "Option is eliminated." between the ")" line and the actual choice text. The parser MUST skip this artifact line to reach the real choice text. Without this, choices parse as ")".

## Anki Card Generation (NBME → Cloze Deck)

### Target format (matches UWorld Weak Subtopics deck exactly)

**Text field:**
```html
<p>{stem text}</p>
<p><img src="nbme_form28_s1_q2_img0.png"></p>
<br><b>Choices:</b><br>
• A) Choice text A<br>
• B) Choice text B<br>
• C) Choice text C<br>
• D) Choice text D<br>
• E) Choice text E<br>
<br><b>Answer:</b> {{c1::Correct Choice Text}}
```

**Back Extra field:**
```html
<p>{rationale text}</p>
<p><strong>Educational Objective:</strong><br>{edu objective}</p>
```

**Model:** Cloze
**Tags:** `nbme::Form28::S1`

### Image storage
Store images in Anki media collection before adding cards:
```python
import base64, requests
def store_image_in_anki(image_path, filename):
    with open(image_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    anki("storeMediaFile", {"filename": filename, "data": b64})
```

Use deterministic names: `nbme_{form_lower}_s{section}_q{item}_img{idx}.png`

### Batch card insertion
Use `addNotes` with batches of 50 for performance:
```python
anki("addNotes", {"notes": [{
    "deckName": "NBME Wrong Questions",
    "modelName": "Cloze",
    "fields": {"Text": text_html, "Back Extra": back_html},
    "tags": [f"nbme::{form}::S{section}"],
    "options": {"allowDuplicate": False}
}]})
```

### Skip rules for Anki generation
- Skip questions where `correct_answer is None` (excluded/pilot questions)
- Skip questions where `user_answer is None` (unanswered)
- These have no cloze answer to test

### Completed stats
Form 28: 62 cards, Form 29: 69 cards, Form 30: 56 cards, Form 32: 58 cards = 245 total in "NBME Wrong Questions" deck.

## Known Issues & Pitfalls

1. **Survey trap**: NEVER click Next past the score report page. It redirects to SurveyMonkey and ends the session. Must re-open the get-score-report URL.

2. **Frame context invalidation**: Every Next click reloads the frame. MUST call `Page.createIsolatedWorld` again before reading content.

3. **ITSIncorrectIcon is a red herring**: In "Review All" mode, it appears on ALL 200 questions (not just wrong ones). In "Review Incorrect" mode it appears on all shown questions too. NEVER rely on it. Use `user_answer != correct_answer` comparison via `.ITSMCOptionTableOn` vs `.correctOption` HTML classes instead.

4. **Review Incorrect crashes starttest**: Clicking "Review Incorrect" from the OUTER control panel crashes the exam review. The button must be clicked from INSIDE the score report frame. Safest approach: have the user click it manually.

5. **QuickSight tabs**: JS `.click()` doesn't work. Must use CDP `Input.dispatchMouseEvent` at exact tab coordinates.

6. **Session expiry**: QuickSight ~2 hours, starttest unknown. Work fast once review is open.

7. **Script timeouts**: The 300s terminal timeout will kill long scrapes. Incremental JSON saves ensure no data loss. Script can be re-run and will skip already-scraped questions.

8. **"Review Incorrect" vs "Review All"**: Review Incorrect only shows wrong questions, making the scrape much faster (~55 Q vs 200 Q). Prefer it.

## File Locations
- Scraper script: `~/Desktop/nbme_wrong_scraper.py`
- Output data: `~/Desktop/nbme_data/{Form}_wrong_full.json`
- Images: `~/Desktop/nbme_data/{Form}_images/`
