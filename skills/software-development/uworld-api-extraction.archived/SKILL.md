---
name: uworld-api-extraction
version: 1.0
description: Extract all questions from UWorld QBank via reverse-engineered REST API. Chrome CDP for auth, gateway API for data.
trigger: When extracting UWorld question data for Anki card creation, study analysis, or QBank review export.
---

# UWorld API Extraction Pipeline

## Overview
UWorld's gateway REST API (`gateway-api.uworld.com`) exposes all QBank data as JSON. Auth requires 3 mandatory headers captured from Chrome via CDP.

## Prerequisites
- Chrome launched with remote debugging: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 "--remote-allow-origins=*" --user-data-dir=/tmp/chrome-uworld`
- User logged into UWorld (apps.uworld.com) in that Chrome instance
- Python packages: `requests`, `websocket-client`

## Authentication (3 mandatory headers)

### Header 1: Authorization
- Format: `Bearer {JWT}`
- Source: `sessionStorage.getItem('authInfo')` → parse JSON → `.at` field
- JWT has `exp` claim — expires ~1hr. Re-extract from Chrome if expired.
- Also available in cookie `uw_at_config` as `{"at":"eyJ..."}`

### Header 2: api-uwsub-key
- Format: Long RSA-encrypted string (~1600 chars)
- NOT in cookies or sessionStorage — captured via Chrome CDP Network.requestWillBeSent interception
- Persistent across session (doesn't expire with JWT)
- Fallback: read from `~/Desktop/uworld_data/captured_headers.json`

### Header 3: config-parameters
- Static value: `{"configId":7,"deviceTypeId":1,"topLevelProductId":1}`
- Always the same for Step 1 QBank

### Additional required headers
```
Content-Type: text/json  (NOT application/json!)
Origin: https://apps.uworld.com
Referer: https://apps.uworld.com/
```

## API Endpoints

### 1. Get Test Record Details
```
GET https://gateway-api.uworld.com/api/qbank/GetTestRecordDetails/{testRecordId}
```
Returns: test metadata + `testQuestionInfoList` (array of question summaries)
Each question has: `questionId`, `subject`, `system`, `topic`, `topicAttribute`, `isCorrect`, `questionText`, `level1Name`, `level2Name`, `level3Name`

### 2. Get All Test Records
```
GET https://gateway-api.uworld.com/api/qbank/GetTestRecords/1/0
```
Returns: array of 186 test record objects. Each has `id` (testRecordId). Use this to get all test IDs.

### 3. Get Full Question Content (CRITICAL: exact body format required!)
```
POST https://gateway-api.uworld.com/api/qbank/getTestByQuestionIndexes/
Body (EXACT format — PascalCase, STRING TestRecordId):
{
  "TestRecordId": "421548864",   // MUST be STRING, not int!
  "QbankId": 1,                  // PascalCase Q
  "QuestionIndexes": [1507, 1493, ...]  // PascalCase Q, global questionId values from GetTestRecordDetails
}
```
**COMMON MISTAKES THAT CAUSE PARSE ERRORS:**
- WRONG: `{"testRecordId": 421548864, "questionIds": [1507]}` → "Unexpected character" error
- WRONG: `{"TestRecordId": 421548864, ...}` (int instead of string) → parse error
- WRONG: camelCase field names → parse error
- The body MUST use: PascalCase keys, STRING TestRecordId, "QuestionIndexes" not "questionIds"

**Field mapping between endpoints:**
- `GetTestRecordDetails` → `questionId` field = global ID (e.g., 1507)
- `getTestByQuestionIndexes` → uses same global ID as `QuestionIndexes` value
- Response field: `questionIndex` = same global ID

Returns: `questionList` array with full content:
- `questionText` — HTML with embedded images (`<img src="https://www.uworld.com/media/...">`)
- `explanationText` — HTML explanation with images
- `answerChoiceList` — choices with `choiceNumber` (INT) and `choice` (text or just letter label for image-based Qs)
- `correctAnswer` — STRING (e.g., "2"), NOT int — MUST `int()` before comparing to `choiceNumber`!
- `subject`, `system`, `topic`, `topicAttribute` — classification tags
- `subjectId`, `systemId`, `topicId` — numeric IDs

### 3. Test List
```
GET https://gateway-api.uworld.com/api/qbank/GetTestRecords/1/0
```
Returns array of all 186 test records with `id` = testRecordId. No scraping needed.

## Key Data Points
- User ID: 5326037
- Config ID: 14592700
- QBank ID: 1
- Example test record ID: 421548864 (Test 186)
- Total: 186 tests, 3658 questions, 46% correct

## Question Filtering (38 Weak Subtopics)

Match against UWorld's `system` + `topic`/`topicAttribute` fields:

### Neurology
- system="Nervous System" + topic contains: spinal, reflex, autonomic, cerebrovascular, stroke, brain stem, brainstem, cranial nerve, basal ganglia, cerebellum, parkinson, huntington, tremor, hemiballismus, peripheral nerve, plexus, guillain, neuropathy, charcot
- Also: subject contains "pharmacology" + topic: autonomic

### Cardiovascular
- system="Cardiovascular System" + topic: dyslipidemia, hyperlipidemia, cholesterol, statin, heart failure, cardiomyopathy, ejection, ischemic, atherosclerosis, coronary, angina, myocardial infarct, murmur, heart sound, cardiac cycle, pressure-volume, valvular, antiarrhythmic, antihypertensive

### Respiratory
- system="Pulmonary & Critical Care" (NOT "Respiratory"!) + topic: obstructive, COPD, asthma, emphysema, bronchitis, bronchiectasis, pneumonia, lung infection, tuberculosis

### Hematology/Immunology
- system="Hematology & Oncology" + topic: leukemia, lymphoma, multiple myeloma, hodgkin
- system="Allergy & Immunology" + topic: immunodeficiency, SCID, DiGeorge, hypogammaglobulinemia, wiskott

### Endocrine
- system="Endocrine, Diabetes & Metabolism" (full name!) + topic: diabetes mellitus, insulin, glucose tolerance, HbA1c, ketoacidosis, DKA, hypoglycemia, diabetic, pituitary, acromegaly, prolactin, SIADH, ADH

### Behavioral
- system="Psychiatric/Behavioral & Substance Use Disorder" (full name!) + topic: developmental, milestone, Piaget, Erikson, substance, withdrawal, intoxication, alcohol use, opioid

## Image Handling

### Inline `<img>` Tags (SAFE — these work as-is)
Question images are hosted at `https://www.uworld.com/media/{filename}.jpg` — embedded as `<img>` tags in `questionText` and `explanationText`. These URLs work directly with the auth session. Download via Chrome CDP `fetch()`, store via `anki.storeMediaFile`, rewrite `<img src>` to local filename (e.g., `uw_L26367.jpg`).

### Exhibit Links — CRITICAL BUG (DO NOT USE NAIVE APPROACH!)
**The exhibit ID in `<a href="XXXX">exhibit</a>` is NOT the media file ID.** Downloading `U{XXXX}.png` or `L{XXXX}.jpg` gives the WRONG IMAGE.

**What happens in UWorld's frontend:** The Angular app tries a CASCADE of URL patterns when you click an exhibit:
```
apps.uworld.com/media/U{ID}.png → .jpg → L{ID}.png → .jpg
www.uworld.com/media/U{ID}.png → .jpg → etc.
www.uworld.com/media/highresdefault/U{ID}.jpg → L{ID}.jpg → etc.
```
Whichever returns 200 wins. BUT some exhibit IDs in the HTML map to DIFFERENT media IDs than the href value. The mapping is embedded in the Angular app's internal state, NOT in any API response.

**CORRECT approach to get exhibit images:**
1. Navigate to the question in Chrome CDP
2. Click the exhibit link — opens a `mat-dialog-container` with class `exhibits-dialog-contain`
3. Grab the ACTUAL image URL from the dialog: `document.querySelector('.exhibits-dialog-contain img').src`
4. The URL will be something like `https://apps.uworld.com/media/U67968.png` — where `67968` ≠ the `href` value
5. Download that exact URL, store in Anki media, replace the `<a>` tag with `<img>`

**FAILED approach (DO NOT USE):**
- ❌ Guessing URL patterns from exhibit href ID alone
- ❌ Assuming exhibit href ID = media file ID
- ❌ The `exhibits`, `questionMedia`, `hotspotImageUrl` API fields are always `null`
- ❌ API endpoints like `/GetMedia/{id}`, `/GetExhibit/{id}` all return 500

**Mapping exhibit href IDs to UWorld question IDs:**
Anki note tags use format `uworld::q{questionId}`. Use `notesInfo` (not `cardsInfo`) to get tags:
```python
ni = anki('notesInfo', notes=[nid]).get('result', [])
qid = None
for tag in ni[0]['tags']:
    m = re.match(r'uworld::q(\d+)', tag)
    if m: qid = int(m.group(1))
```
Then navigate Chrome to that question to resolve exhibit images.

**If exhibit images were incorrectly saved (wrong images), revert:**
```python
# Replace <img src="uw_exhibit_{ID}.{ext}"> back to <a href="{ID}">exhibit</a>
new_text = re.sub(r'<img src="uw_exhibit_(\d+)\.\w+"[^>]*>', r'<a href="\1">exhibit</a>', text)
```

**Practical decision (Apr 16):** Only 49/1823 cards (2.7%) have exhibit links. The per-question Chrome click-and-capture process is too slow for 49 questions. **Recommendation: leave exhibit links as `<a>` tags** — they render as plain text in Anki (not broken images) and are negligible coverage. Do NOT invest time fixing exhibit images unless Danny specifically requests it.

**Cleanup if wrong exhibit images were previously stored:**
```bash
# Delete wrong uw_exhibit_* files from Anki media
rm ~/Library/Application\ Support/Anki2/User\ 1/collection.media/uw_exhibit_*
```
30 files deleted in Apr 16 cleanup session.

## Anki Card Format & Structure
- **Model:** Cloze (standard Anki model)
- **Text field (front):** Question HTML + `<b>Choices:</b>` list + `{{c1::answer}}` cloze
- **Back Extra field (back):** Explanation HTML + explanation images — only visible after flipping
- Deck: "UWorld Weak Subtopics"

### Card Building Logic
```python
q_html = qt.strip()  # questionText from API (already HTML)
if '<' not in q_html: q_html = q_html.replace('\n', '<br>')

ch = "<br><b>Choices:</b><br>"
for a in sorted(answers, key=lambda x: x['choiceNumber']):
    ch += f"• {a['choice']}<br>"

cloze = f'<br><b>Answer:</b> {{{{c1::{correct_text}}}}}'
text = q_html + ch + cloze  # NO explanation here!
extra = explanation_html     # Goes in Back Extra
```

### AnKing-Matching CSS (applied to Cloze model — updated Apr 16)
```css
/* Desktop — front 16px matches back 1.0rem (~16px) */
.card {
  font-family: Arial Greek, Arial, sans-serif;
  font-size: 16px; text-align: left;
  color: black; background-color: #D1CFCE;
  margin: 20px; line-height: 1.4;
}
/* Mobile — Danny likes phone font ~15px */
.mobile .card { font-size: 15px; }
.cloze { color: blue; font-weight: bold; }
#extra, #back_extra, .extra { color: navy; font-size: 1.0rem; }
.mobile #extra, .mobile #back_extra, .mobile .extra { font-size: 1.0rem; }
.explanation { color: navy; font-size: 1.0rem; }
img { max-width: 85%; max-height: 85%; }
```

### Template Update (Cloze model)
- Front: `{{cloze:Text}}` (+ bionic reading script)
- Back: `{{cloze:Text}}<br><br><hr id="answer"><br><div id="back_extra">{{Back Extra}}</div>`

### AnkiConnect Field Update Pattern
Use `updateNoteFields` with `note` (SINGULAR, not `notes`):
```python
anki("updateNoteFields", note={"id": nid, "fields": {"Text": new_text, "Back Extra": new_extra}})
```
NOT `notes=[...]` — AnkiConnect uses singular `note` for this action, unlike `addNotes` which uses plural.

### Reformatting Existing Cards (split explanation to Back Extra)
```python
import re
expl_match = re.split(r'<br><br><b>Explanation:</b><br>', text_field, maxsplit=1)
if len(expl_match) > 1:
    new_text = expl_match[0]     # Question + choices + cloze
    new_extra = expl_match[1]    # Explanation only
```
Apply per-card via `updateNoteFields` — processed 1,822 cards in ~3 min.

## Pipeline Architecture (PROVEN — 1,822 cards created)
1. Chrome CDP on port 9222 with UWorld logged in
2. Phase 1 (`uworld_phase1_broad.py`): GET all 186 test IDs → GET details for each → filter by SYSTEM ONLY → save matches to `phase1_broad_matches.json`
3. Phase 2 (`uworld_phase2_broad_v2.py`): Load matches → POST getTestByQuestionIndexes for each test → build cloze cards → addNotes via AnkiConnect
4. Token refresh between phases via `location.reload()` in CDP

## CRITICAL: AnkiConnect Batch Error Handling

When `addNotes` is called with a batch of notes where ANY note is a duplicate, AnkiConnect returns an error ARRAY (not a result array). The ENTIRE batch is reported as failed, and **any NEW cards mixed in with the duplicates are silently lost**.

**Symptoms:** Pipeline reports `addNotes error: ['cannot create note because it is a duplicate', ...]` and counts the whole batch as failed, even though it contains new unique cards.

**Fix:** When batch `addNotes` returns an error, retry EACH note individually:
```python
r = anki("addNotes", notes=notes)
if r.get('error'):
    # Batch failed — retry each note individually to rescue new cards
    for note in notes:
        sr = anki("addNotes", notes=[note])
        if sr.get('result') and sr['result'][0] is not None:
            cards_ok += 1
        else:
            cards_dup += 1
```

This rescued 1,239 cards that the batch approach was silently dropping (583 → 1,822).

## CRITICAL: Filter Strategy — Start Broad

**NEVER use narrow topic+system dual-filtering without first verifying coverage.** A topic keyword AND system keyword requirement captured only 396/1,803 questions (22%) in weak systems. The narrow filter silently excluded 78% of relevant questions.

**Correct approach:**
1. First run a verification scan counting ALL questions by system across 186 tests
2. Compare system-level totals against narrow filter matches
3. If coverage < 80%, drop topic keywords and use system-only filter
4. System-only filter captured 1,803 questions (100% of weak-system pool)

**Broad filter keywords (system name substring match, case-insensitive):**
```python
WEAK_SYSTEMS = [
    "nervous", "cardiovascular", "pulmonary", "hematology", "oncology",
    "allergy", "immunology", "endocrine", "diabetes", "psychiatric",
    "behavioral", "substance",
]
# Match: any(ws in system.lower() for ws in WEAK_SYSTEMS)
```

## Full Pull Pattern (Second Deck / Reference Deck)

When creating a SECOND UWorld deck that should contain ALL questions (duplicates OK across decks):

### Strategy: Copy Existing + Fetch Only Missing
1. Run Phase 1 scan (all 186 tests) to get full questionId list
2. Check existing Anki notes by `uworld::q*` tags to find QIDs already in ANY deck
3. Calculate `missing_qids = all_qids - existing_qids`
4. Copy existing cards to new deck (deck-scoped duplicate check)
5. Fetch only missing questions via CDP API
6. Download + localize only new images

### Copying Existing Cards to New Deck
Use `addNotes` with `duplicateScope: "deck"` and `duplicateScopeOptions.deckName` set to the target deck. This allows identical content across different decks:
```python
note = {
    "deckName": "UWorld Complete Reference",  # target deck
    "modelName": "Cloze",
    "fields": existing_fields,    # copied from notesInfo
    "tags": existing_tags,        # copied from notesInfo
    "options": {
        "allowDuplicate": False,
        "duplicateScope": "deck",
        "duplicateScopeOptions": {
            "deckName": "UWorld Complete Reference",  # only check THIS deck
            "checkChildren": False,
            "checkAllModels": False
        }
    }
}
```
Add one note at a time (NOT batch) to handle duplicates — batch `addNotes` silently drops new cards mixed with duplicates.

### CDP API Response Bug (CRITICAL)
`GetTestRecordDetails` returns a DICT (not a list). The check `isinstance(details, dict)` is ALWAYS True. Don't use isinstance to check for errors — instead check for the presence of `testQuestionInfoList`:
```python
# WRONG — details is always a dict, this filters valid responses!
if isinstance(details, dict):
    # ERROR PATH — skips everything!

# CORRECT — check for the data we need
q_list = details.get("testQuestionInfoList", [])
if not q_list:
    continue  # truly empty or error
```

### Checking Existing QIDs via Tags (Efficient)
To find which questions already exist across ALL decks:
```python
result = anki("findNotes", query="tag:uworld")
note_ids = result.get("result", [])
existing_qids = set()
for i in range(0, len(note_ids), 100):
    batch = note_ids[i:i+100]
    info = anki("notesInfo", notes=batch)
    for n in info["result"]:
        for tag in n.get("tags", []):
            if tag.startswith("uworld::q"):
                existing_qids.add(int(tag.split("q")[1]))
```

### Localizing Images Inline (during card creation)
When creating cards, replace remote URLs with local `uw_*` filenames IN the HTML before saving to Anki — avoids a separate update pass:
```python
for url in re.findall(r'src="(https://(?:www|apps)\.uworld\.com/media/[^"]+)"', q_html):
    fname = url.split("/")[-1]
    q_html = q_html.replace(url, f"uw_{fname}")
```

## File Locations
- Phase 1 broad scanner: `~/Desktop/uworld_phase1_broad.py`
- Phase 2 broad card creator: `~/Desktop/uworld_phase2_broad_v2.py`
- Phase 1 broad output: `~/Desktop/uworld_data/phase1_broad_matches.json` (1,803 questions)
- Verification scanner: `~/Desktop/uworld_verification.py` (system distribution analysis)
- Dedup checker: `~/Desktop/uworld_dedup_check.py` (uniqueness analysis)
- All test IDs: `~/Desktop/uworld_data/test_record_ids.json`
- Weak subtopics reference: `~/Desktop/USMLE_Targeted_Filters.md`

## Reflection Lessons (Apr 15 retrospective — 10 tips distilled into Cortex)

### Critical Pattern: Silent Failures Are Most Dangerous
The UWorld project had 3 silent failures that all reported "success":
1. correctAnswer STRING vs INT — wrong cloze answers, no error
2. AnkiConnect batch+dup — 1,239 cards silently dropped
3. Narrow filter — excluded 78% of relevant questions

**RULE**: When output quantity seems low, ALWAYS verify against independent count before proceeding.

### Pre-Project System Hardening (30 min saves hours)
Before ANY marathon data pipeline: check swap usage, reduce Docker memory, verify TCP keepalive is active, install LCM context engine if not already running. The UWorld project lost 3 sessions (30-60 min each) to Z.AI freezes that could have been prevented.

### API Reverse Engineering Checklist
1. Capture EXACT request body from browser Network tab — use verbatim
2. Type-check every response field with `type()` before first comparison
3. Copy ALL custom headers (not just Authorization)
4. Test with single record first, verify types match, then scale up
5. Expect JWT expiry (~1hr) and plan phase boundaries accordingly

### Data Pipeline Design Pattern
Pass 1: Quick scan for scope (count only, no processing)
Pass 2: Build with rough format (don't optimize yet)
Pass 3: Refine format (split fields, optimize CSS, add mobile overrides)
Verify coverage between each pass.

### Checkpoint Quality Rule
Save decision RATIONALE (WHY), not just outcomes (WHAT). When context compresses mid-project, rationale prevents re-litigating decisions across sessions.

## Exhibit Investigation Debugging Anti-Pattern (Apr 16 Lesson)

**We wasted 30+ minutes trying URL pattern cascades** (U{id}.png, L{id}.jpg, etc.) before discovering the fundamental problem: exhibit href IDs ≠ media file IDs. The UWorld Angular app has an INTERNAL lookup table that maps exhibit IDs to completely different media IDs. Example: `href="42465"` → `U67968.png`.

**Debugging timeline that wasted time:**
1. ❌ Tried guessing API endpoints: `/GetMedia/{id}`, `/GetExhibit/{id}`, `/GetQuestionMedia/{id}` — all 500
2. ❌ Tried extended URL patterns with .gif, .webp, different path prefixes — all 404
3. ❌ Downloaded Angular JS bundles — only 5KB bootstrappers (lazy-loaded)
4. ❌ Tried searching source code via Debugger domain — nothing found
5. ✅ **The ONLY method that worked:** Danny clicked exhibit in Chrome → we grabbed `<img src>` from `mat-dialog-container`

**Lesson:** When an Angular SPA resolves data dynamically through internal state, STOP trying to guess/reverse-engineer the mapping. Just let the app do the resolution and grab the result from the DOM.

## Chrome CDP Script Gotchas
- **f-string backslash limit**: Python f-strings cannot contain backslashes in expression parts. When building JS fetch bodies with `json.dumps()`, pre-escape the body string BEFORE inserting into the f-string: `escaped_body = body.replace("\\","\\\\\\\\").replace("'","\\\\'")`
- **websocket-client**: Must be installed in hermes venv: `~/hermes-agent/venv/bin/python3 -m pip install websocket-client`
- **AnkiConnect modelStyling API inconsistency**: GET uses `modelName='Cloze'` but UPDATE uses `model={'name': 'Cloze', 'css': ...}`. Different param names for same model!

## Port Conflict Check
Before debugging AnkiConnect issues, always check for stale processes: `lsof -i :8765`. Only Anki (python3.1 on IPv4 localhost) should be there. A stale `python3 -m http.server 8765` will hijack IPv6 connections silently.

## Known Errors & Fixes
- **`"Unexpected character encountered while parsing value: Q"` on POST** → Wrong body format! Must use EXACT PascalCase: `{\"TestRecordId\": \"STRING\", \"QbankId\": 1, \"QuestionIndexes\": [...]}`. CamelCase or int TestRecordId causes this.
- **All cards skip (0 created) with no errors** → `correctAnswer` is STRING "2", `choiceNumber` is INT 2. `"2" == 2` is False in Python. MUST `int(correctAnswer)` before comparison.
- **JWT expiry (~1hr)** → Split pipeline into Phase 1 (scan) and Phase 2 (cards). Refresh token between phases via CDP `location.reload()` + re-extract from `sessionStorage`.
- **CORS errors calling from Python** → ALL API calls MUST go through Chrome CDP `Runtime.evaluate` executing `fetch()` in the page context. Cannot call directly from Python `requests`.
- Content-Type must be `text/json` NOT `application/json` — UWorld's server rejects the latter.
- `api-uwsub-key` is in `sessionStorage.authInfo.apiSubKey` — no Network interception needed.

## Auth Extraction Simplified
Auth is stored in `sessionStorage.authInfo` as JSON:
```python
auth = json.loads(js("sessionStorage.getItem('authInfo')"))
token = auth['at']        # JWT Bearer token
apiSubKey = auth['apiSubKey']  # api-uwsub-key header
```
No Network interception needed. Just CDP `Runtime.evaluate` to read sessionStorage.

## Full QBank Pull (Apr 16 — 3,665 questions)

### GetTestRecordDetails Response Format CRITICAL
`GetTestRecordDetails/{id}` returns a **DICT** (not a list). The dict has key `testQuestionInfoList` containing the question array. Do NOT check `isinstance(details, dict)` as an error condition — the response is ALWAYS a dict. The correct check:
```python
# WRONG — treats valid dict response as error:
if isinstance(details, dict):  # Always true! Loses all data.
    print("ERROR")

# CORRECT — check for error key or missing data:
if details.get("error"):
    print("ERROR")
q_list = details.get("testQuestionInfoList", [])
```

### Full Pull Pipeline (no filtering)
For a complete reference deck with ALL questions:
1. **Phase 1 Scan**: GET GetTestRecords → for each test GET GetTestRecordDetails → collect all questionId values into a set (dedup across tests — questions appear in multiple tests but have the same ID)
2. **Phase 2 Cards**: For each test, POST getTestByQuestionIndexes with that test's question IDs → build cloze cards → addNotes individually (avoid batch+dup issue)
3. **Phase 3 Images**: Collect all `src="https://..."` URLs from questionText+explanationText → download via CDP fetch() → store via AnkiConnect storeMediaFile

**Key: Total unique questions = 3,665 (not 3,658 — count varies slightly).** Scan first, then use actual unique count.

### Inline Image Localization (BEST PRACTICE)
Replace remote URLs with local filenames DURING card creation, not post-hoc:
```python
# During card building — before adding to Anki:
for url in set(re.findall(r'src="(https://www\.uworld\.com/media/[^"]+)"', q_html)):
    fname = url.split("/")[-1]
    q_html = q_html.replace(url, f"uw_{fname}")
for url in set(re.findall(r'src="(https://apps\.uworld\.com/media/[^"]+)"', expl_html)):
    fname = url.split("/")[-1]
    expl_html = expl_html.replace(url, f"uw_{fname}")
```
This avoids a separate pass of findNotes → notesInfo → updateNoteFields for 3000+ notes (which is very slow via AnkiConnect).

### Image File Extensions
UWorld images are NOT just .jpg/.png. Also found: `.gif` (e.g., `AgonistAndAntagonist.gif`, `EssentialFructosuria.gif`). The download regex must capture all extensions:
```python
re.findall(r'src="(https://[^"]*uworld\.com/media/[^"]+)"', html)
```
Then `url.split("/")[-1]` preserves whatever extension the file has.

### CDP Performance Warning
Each CDP `api_fetch` call goes through: Python → websocket → Chrome JS → fetch → parse JSON → serialize → websocket → Python. At ~0.3-0.5s per call, fetching 186 tests takes ~60-90s for Phase 1, and 3,665 cards across ~150 API batches takes 5-10 min for Phase 2+3. **Set terminal timeout to 600s+ or use `notify_on_complete=true` for long runs.** The 180s default will time out on full pulls.

### Deck-to-Deck Copying: Just Re-Create
AnkiConnect has no move/clone operation. To put existing cards (from another deck) into a new deck, the options are:
1. `changeDeck` — moves cards (removes from original deck)
2. `addNotes` with deck-scoped duplicate checking — creates new notes in target deck

For a reference deck that keeps the original intact, use option 2 with `duplicateScope: "deck"` and `duplicateScopeOptions.deckName` set to the NEW deck. This allows same content in multiple decks.

### JWT Refresh During Long Runs
JWT expires ~1hr. Full pull of 3,665 questions takes ~10 min through CDP, so refresh every 15 tests:
```python
if test_count % 15 == 0:
    js_eval(ws, "location.reload()")
    time.sleep(3)
```
Also refresh between Phase 1 and Phase 2. If API returns 401 mid-run, refresh immediately and retry.

### Full Pull Verified Results (Apr 16)
- Total unique QIDs: 3,665
- Cards with local images: 1,834
- Text-only cards: 1,831
- Remote URLs remaining: 0
- uw_* media files: 1,160
- Deck: "UWorld Complete Reference"
