---
name: ankiconnect-automation
version: 1.0
description: Automate Anki card/deck operations via AnkiConnect JSON-RPC API. Covers working actions, failed approaches for filtered deck creation, internal architecture, and the manual fallback pattern.
tags: [anki, ankiconnect, usmle, study, flashcards]
---

# AnkiConnect Automation for Anki Desktop

Automate Anki card/deck operations via AnkiConnect (localhost:8765) JSON-RPC API. For USMLE/medical study workflows and general Anki automation.

## When to Use
- Querying card counts by tag/deck
- Any programmatic Anki operation while Anki is running
- Building study guides from Anki deck structure

## Critical Rules

### NEVER open collection.anki2 with sqlite3 while Anki is running
This ZEROES OUT the file header and corrupts the entire database. ALWAYS use AnkiConnect exclusively.

### AnkiConnect API Pattern
```python
import json, urllib.request

def anki(action, **params):
    payload = json.dumps({"action": action, "version": 6, "params": params}).encode()
    req = urllib.request.Request("http://localhost:8765", data=payload,
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read())
    if data["error"]:
        raise Exception(data["error"])
    return data["result"]
```

### Working Actions (confirmed)
- `version` — returns 6
- `deckNames` — list all deck names
- `findCards(query=...)` — returns list of card IDs
- `findNotes(query=...)` — returns list of note IDs
- `cardsInfo(cards=[...])` — card details
- `notesInfo(notes=[...])` — note details
- `guiDeckBrowser()` — navigate to deck list
- `multi(actions=[...])` — batch multiple actions

### NOT Supported
- `createFilteredDeck` — does NOT exist as a native action
- `reloadAddons` — does NOT exist
- `evaluate` / `execute` / `runCode` — no code execution

## Query Syntax for findCards
- Deck scope: `deck:"AnKing Step Deck"`
- Tag match: `tag:#AK_Step1_v12::#B&B::16_Neuro::02_Nervous_System_Structures::02_Spinal_Cord`
- OR logic: wrap multiple tag terms in parens with OR
- Combined: `deck:"AnKing Step Deck" (tag:X OR tag:Y OR tag:Z)`
- Timeout: queries combining 5+ OR groups across 4000+ cards may timeout at 30s — query each area separately

## Creating Filtered Decks — WORKING APPROACH: Temp Addon with profile_did_open

The ONLY reliable method. Requires a temp addon that self-deletes after running.

### Step 1: Create the filtered deck via AppleScript (search only, default limit)
```bash
osascript -e 'tell application "System Events" to tell process "Anki" to click menu item "Create Filtered Deck..." of menu "Tools" of menu bar item "Tools" of menu bar 1'
```

The dialog is a **SHEET** (not a window): `sheet 1 of window 1`

Set deck name: `set value of text field 1 of group 1 of sheet 1 to "DECK NAME"`

Set search string: `set value of text field 1 of group 2 of sheet 1 to "search query"`

Click Build: `click button 1 of group 4 of sheet 1`

**CRITICAL: NEVER type into the incrementor (card limit)** — keystrokes go to the search field instead (it steals focus). Build with default limit first, then fix it via addon.

### Step 2: Fix card limit via temp addon

Create addon at `~/Library/Application Support/Anki2/addons21/hermes_patch_limit/`:

**meta.json** (REQUIRED, correct format):
```json
{"name": "Hermes Patch", "mod": 1745180100, "min_point_version": 240001, "max_point_version": 251201, "branch_index": 0, "disabled": false}
```

**__init__.py**:
```python
import os, shutil
from aqt import mw, gui_hooks

LOG = os.path.expanduser("~/Desktop/hermes_patch_log.txt")

def patch_deck():
    try:
        for did in mw.col.decks.all_ids():  # NOT all_items()!
            deck = mw.col.decks.get(did)
            if deck and deck['name'] == 'TARGET_DECK_NAME':
                deck['terms'][0][1] = 620  # Set card limit
                mw.col.decks.save(deck)
                mw.col.sched.rebuild_filtered_deck(int(did))
                break
        # Self-delete
        shutil.rmtree(os.path.dirname(os.path.abspath(__file__)), ignore_errors=True)
    except Exception as e:
        with open(LOG, 'a') as f:
            import traceback
            f.write(f"ERROR: {e}\n{traceback.format_exc()}")

gui_hooks.profile_did_open.append(patch_deck)
```

### Step 3: Restart Anki (MUST kill ALL processes first!)
```bash
killall -9 Anki; sleep 2
# Kill zombie children (mpv audio, python workers)
for pid in $(pgrep -fl -i anki | awk '{print $1}'); do kill -9 $pid; done
for pid in $(pgrep -fl mpv | awk '{print $1}'); do kill -9 $pid; done
sleep 1
pgrep -fl -i anki  # MUST be empty!
open -a Anki
```

Wait for AnkiConnect, then verify: `anki("findCards", query='"deck:DECK_NAME"')`

### Anki 24.x DeckManager API
- `all_ids()` returns list of deck ID strings — NOT `all_items()`
- `get(did)` returns deck dict — must call separately for each ID
- `save(deck)` persists changes
- `mw.col.sched.rebuild_filtered_deck(int(did))` rebuilds filtered deck
- Filtered deck `terms` is a list: `terms[0] = [search_string, limit, order]`

## APPROACHES THAT FAILED (for reference)

1. **AnkiConnect `createFilteredDeck`** — action doesn't exist
2. **Monkey-patching AnkiConnect** — setattr doesn't register for inspect.getmembers
3. **Patching AnkiConnect source** — cached modules, still "unsupported action"
4. **AppleScript stepper/incrementor** — can't set value, typing goes to search field
5. **AppleScript menu clicks with zombie processes** — dialogs don't open properly

### AnkiConnect Internal Architecture (for future reference)
- Class: `AnkiConnect` in `addons21/2055492159/__init__.py`
- Handler: `handler(self, request)` at line ~106
- Action discovery: `inspect.getmembers(self, predicate=inspect.ismethod)` looking for `api=True`
- Decorator: `@util.api()` in `addons21/2055492159/util.py` — sets `.api = True`

## Debugging When AnkiConnect Is Down

When AnkiConnect refuses connections (port 8765 not responding), you can still read Anki data by copying the SQLite DB:

```python
import shutil
shutil.copy2(
    "~/Library/Application Support/Anki2/User 1/collection.anki2",
    "/tmp/anki_collection_copy.db"
)
conn = sqlite3.connect("/tmp/anki_collection_copy.db")
```

**NEVER open the original while Anki runs** — copy first, read the copy.

### Anki 24+ Schema (Notetypes/Decks are separate tables)

Anki 24+ split the old `col` table JSON blobs into proper tables:
- `notetypes` — id, name, mtime_secs, usn, config (protobuf blob)
- `templates` — ntid, ord, name, mtime_secs, usn, config (protobuf blob)
- `decks` — id, name, ... (separate table)
- `deck_config` — id, name, ...
- `config` — KEY (text), usn, mtime_secs, val (blob)
- `notes`, `cards`, `revlog` — same as before

**Gotchas:**
- `config` table uses `KEY`/`val` columns (case-sensitive), not `key`/`value`
- JOINs may fail with `no such collation sequence: unicase` — avoid JOINs on text columns, query tables separately instead
- Notetype CSS is embedded inside the protobuf `config` blob, not a separate column
- Config values like `estTimes`, `fsrs`, `schedVer` are encoded as protobuf integers (0/1 for bools)

### Add-on Disabled State (meta.json)

Add-ons store their enabled/disabled state in `meta.json` **inside the add-on directory**, NOT in Anki's config DB:

```
~/Library/Application Support/Anki2/addons21/<addon_id>/meta.json
```

```json
{"name": "Add-on Name", "disabled": true, ...}
```

When a user toggles add-ons via Anki UI (Tools > Add-ons > Toggle) and something goes wrong (e.g. bulk toggle off/on), add-ons can get **stuck as disabled**. The Anki UI may show them as enabled, but `meta.json` still says `"disabled": true`.

**Fix**: Edit `meta.json` directly:
```python
import json
meta_path = f"~/Library/Application Support/Anki2/addons21/{addon_id}/meta.json"
meta = json.load(open(meta_path))
meta['disabled'] = False
json.dump(meta, open(meta_path, 'w'))
```

Then restart Anki. This is the ONLY reliable way to re-enable stuck add-ons.

**Quick audit** — find all disabled add-ons:
```python
import os, json
addon_dir = os.path.expanduser("~/Library/Application Support/Anki2/addons21")
for item in sorted(os.listdir(addon_dir)):
    meta_path = os.path.join(addon_dir, item, "meta.json")
    if os.path.exists(meta_path):
        meta = json.load(open(meta_path))
        if meta.get('disabled'):
            print(f"DISABLED: [{item}] {meta.get('name')}")
```

## Anki Backup Format
- `.colpkg` = ZIP containing `collection.anki21b` (Zstandard-compressed SQLite)
- Decompress with `zstandard` Python library, `stream_reader()` (no content size in frame header)

## AnKing Tag Structure
- Pattern: `#AK_Step1_v12::#Source::XX_System::XX_Subtopic::XX_Detail`
- Sources: `#B&B`, `#FirstAid`, `#Physeo`, `#Mehlman`
- Tag search is case-sensitive and exact-match

## Model Styling API (CSS updates)

### Getting CSS
```python
anki('modelStyling', modelName='Cloze')  # GET uses modelName
```

### Updating CSS
```python
anki('updateModelStyling', model={'name': 'Cloze', 'css': new_css})  # PUT uses model dict!
```

**API inconsistency**: `modelStyling` (GET) uses `modelName` kwarg, but `updateModelStyling` (PUT) uses `model={'name': ..., 'css': ...}` dict. Using `modelName` on the update call gives "unexpected keyword argument" error.

## Pitfalls
1. NEVER use sqlite3 on a running Anki collection — instant corruption
2. Large OR queries (>4000 cards) timeout at 30s — split into separate queries
3. AnkiConnect runs on `127.0.0.1:8765` by default
4. Wait 15-20s after Anki launch before AnkiConnect responds
5. **ZOMBIE PROCESSES**: `killall -9 Anki` kills the main binary but LEAVES child processes alive (mpv audio, python workers). These zombies keep the app "alive" on desktop, block addon loading, block menu responses, and corrupt GUI state. ALWAYS run `pgrep -fl -i anki` AND `pgrep -fl mpv` after killing, and `kill -9` every remaining PID. The app is NOT dead until ALL PIDs are gone.
6. Anki addon `max_point_version` uses YYMMDD format (e.g., `251201`), NOT plain integers
7. AppleScript: Anki's filtered deck dialog is a SHEET (`sheet 1 of window 1`), not a separate window
8. AppleScript: NEVER type into the card limit incrementor — keystrokes go to the search field in the same group. Use a temp addon to set the limit instead.
9. Anki 24.x DeckManager: use `all_ids()` + `get(did)`, NOT `all_items()` which doesn't exist
10. **PORT CONFLICTS**: If AnkiConnect fails with `RemoteDisconnected` despite Anki running, check `lsof -i :8765` for conflicting processes. A stale `python3 -m http.server 8765` can hijack the port on IPv6 while Anki binds IPv4 only. Kill with `kill -9 <PID>`.
11. `updateModelStyling` uses `model={'name':..., 'css':...}` (dict), NOT `modelName=...`. The GET `modelStyling` uses `modelName` — inconsistent API.
