---
name: cerebrum-tip-injection
version: 1.0
description: Insert distilled tips into cerebrum_memory.db distilled_tips table. Use named parameters to avoid binding count mismatches.
trigger: When manually adding distilled tips from research findings into the cerebrum knowledge graph.
---

# Cerebrum Tip Injection

## Schema

```
distilled_tips columns:
  id (INTEGER PK auto)
  tip_type (TEXT, required) — strategy | action | gap | recovery | optimization | distillation
  condition (TEXT, required) — IF ... THEN ... trigger
  recommendation (TEXT, required) — what to do
  rationale (TEXT, default '')
  tool_name (TEXT, default '')
  domain (TEXT, default '') — VISION | ENGINEERING | REASONING | research
  confidence (REAL, default 0.5) — 0.0 to 1.0
  upvotes (INTEGER, default 1)
  downvotes (INTEGER, default 0)
  frequency (INTEGER, default 1)
  source_ids (TEXT, default '')
  created_at (REAL)
  last_seen (REAL)
  last_used (REAL)
```

## Correct Pattern — Use Named Parameters

```python
import sqlite3, time
from pathlib import Path

db = sqlite3.connect(str(Path.home() / '.hermes' / 'cerebrum_memory.db'), timeout=5)
now = time.time()  # Unix epoch float, NOT datetime('now')

tips = [
    {
        'tip_type': 'strategy',
        'condition': 'IF ... THEN ...',
        'recommendation': 'Do X because Y',
        'rationale': '',
        'tool_name': '',
        'domain': 'VISION',
        'confidence': 0.8,
        'source_ids': 'wiki:source-name',
        'now': now,  # pass timestamp as named param
    },
]

for t in tips:
    db.execute(
        """INSERT INTO distilled_tips
           (tip_type, condition, recommendation, rationale, tool_name, domain, confidence, source_ids, upvotes, frequency, created_at, last_seen, last_used)
           VALUES (:tip_type, :condition, :recommendation, :rationale, :tool_name, :domain, :confidence, :source_ids, 1, 1, :now, :now, :now)""",
        t
    )

db.commit()
count = db.execute("SELECT COUNT(*) FROM distilled_tips WHERE domain='VISION'").fetchone()[0]
print(f'Total tips: {count}')
db.close()
```

## Pitfalls

1. **NEVER use positional `?` with tuples for this table.** The 11-column INSERT with 7 user params + 4 hardcoded params causes `ProgrammingError: Incorrect number of bindings supplied` every time. The mental math of counting `?` vs tuple items is error-prone.

2. **Use dicts with `:named` placeholders.** This is self-documenting and immune to ordering mistakes.

3. **Always set `timeout=5`** on the connection — cerebrum_memory.db can be locked by concurrent cron processes.

4. **Verify with a SELECT COUNT after insert** to confirm the tips landed.

5. **Timestamps must be Unix epoch floats (`time.time()`), NOT `datetime('now')`.** The `created_at`, `last_seen`, `last_used` columns are REAL type expecting seconds-since-epoch (e.g., `1744120560.123`). Using SQLite's `datetime('now')` produces an ISO string like `'2025-04-08 10:56:00'` which silently stores as text in a REAL column. Always precompute `now = time.time()` in Python and pass it as a bound parameter.

6. **Column name is `recommendation`, NOT `action`.** The actual schema column is `recommendation` (TEXT, required). If you get `OperationalError: no such column: action`, you're using the wrong name. Run `PRAGMA table_info(distilled_tips)` to verify if unsure.

## Fallback: When External Search Is Down

When `knowledge_search` (Qdrant), `web_search` (Firecrawl), or `web_research` (SearXNG) are unavailable:
1. Use `web_extract` directly on known URLs (arXiv, blogs, docs)
2. **Direct arXiv API via curl** — reliable, no API key needed:
   ```bash
   curl -sL "https://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+ti:reasoning+agent&max_results=5&sortBy=submittedDate&sortOrder=descending" | python3 -c "
   import sys, xml.etree.ElementTree as ET
   data = sys.stdin.read()
   root = ET.fromstring(data)
   ns = {'a': 'http://www.w3.org/2005/Atom'}
   for entry in root.findall('a:entry', ns):
       title = entry.find('a:title', ns).text.strip().replace('\n', ' ')
       summary = entry.find('a:summary', ns).text.strip()[:250]
       print(f'Title: {title}')
       print(f'Summary: {summary}...')
       print('---')
   "
   ```
   **Key:** Must use `curl -sL` (follow redirects) — arXiv returns HTTP 301 from HTTP to HTTPS. Plain `curl -s` on `http://` returns empty body.
   **Date filter syntax:** `submittedDate:[202501010000 TO 202604100000]`
   **Sort:** `sortBy=submittedDate&sortOrder=descending` for newest first
3. Fall back to internal synthesis — write from existing knowledge + the cerebrum DB itself
4. Use `PRAGMA table_info()` and `SELECT` to explore what's already in the knowledge graph
5. Create wiki pages and inject tips from the synthesized content
6. This "internal research → wiki → tip injection" pipeline works with zero external dependencies

## Knowledge Graph Tables (kg_nodes / kg_edges)

When inserting research concepts into the knowledge graph, the schemas are:

```
kg_nodes columns:
  id (INTEGER PK auto)
  concept (TEXT, required) — the concept name/label
  node_type (TEXT, default 'concept') — NOT "type"
  salience (REAL, default 0.5) — importance 0-1
  created_at (REAL) — unix timestamp
  last_accessed (REAL) — unix timestamp
  access_count (INTEGER, default 0)

kg_edges columns:
  id (INTEGER PK auto)
  source_concept (TEXT, required) — NOT "source", matches kg_nodes.concept
  target_concept (TEXT, required) — NOT "target", matches kg_nodes.concept
  relation (TEXT, required) — e.g. "enables", "improves", "related_to"
  weight (REAL, default 1.0)
  source_fact_id (INTEGER, nullable)
  created_at (REAL) — unix timestamp
```

### Insert Pattern

```python
import sqlite3, time
from pathlib import Path

db = sqlite3.connect(str(Path.home() / '.hermes' / 'cerebrum_memory.db'), timeout=5)
now = time.time()

# Insert node
db.execute(
    'INSERT INTO kg_nodes (concept, node_type, salience, created_at, last_accessed, access_count) VALUES (?,?,?,?,?,?)',
    ('My Concept', 'concept', 0.7, now, now, 1)
)

# Insert edge (uses concept names, not IDs)
db.execute(
    'INSERT INTO kg_edges (source_concept, target_concept, relation, weight, created_at) VALUES (?,?,?,?,?)',
    ('My Concept', 'Existing Concept', 'enables', 0.8, now)
)

db.commit()
```

### Pitfalls

1. **Column names are `source_concept`/`target_concept`, NOT `source`/`target`.** Using wrong names gives `no such column` error.
2. **Column name is `node_type`, NOT `type`.** The `type` column does not exist.
3. **Edges reference concept names (TEXT), not node IDs.** Use the actual string from `kg_nodes.concept`.
4. **Always check `PRAGMA table_info(table_name)`** before inserting if you haven't worked with a table recently. The schema has changed between versions.
5. **Use `time.time()` for timestamps** (unix epoch float), not `datetime.isoformat()`.

## Tip Quality Audit Methodology

When inheriting or reviewing a tips database, run this 5-step audit:

### Step 1: Duplicate Detection
```python
# Find exact duplicate recommendations
for row in db.execute("""
    SELECT recommendation, COUNT(*) as cnt
    FROM distilled_tips GROUP BY recommendation HAVING cnt > 1
"""):
    print(f"  DUP ({row[1]}x): {row[0][:100]}")
```
Action: Delete duplicates, keeping the one with highest confidence or most relevant tool_name.

### Step 2: Confidence Distribution
```python
for row in db.execute("""
    SELECT CASE
        WHEN confidence >= 0.9 THEN 'excellent'
        WHEN confidence >= 0.85 THEN 'high'
        WHEN confidence >= 0.80 THEN 'good'
        WHEN confidence >= 0.75 THEN 'acceptable'
        ELSE 'needs_review'
    END as tier, COUNT(*) FROM distilled_tips GROUP BY tier ORDER BY MIN(confidence) DESC
"""):
    print(f"  {row[0]:15s}: {row[1]:3d} tips")
```
Action: Tips below 0.70 confidence are noise unless they have high frequency (proven by usage). Delete generic recovery tips at 0.5.

### Step 3: Tool Coverage Gap Analysis
```python
# Target: every core tool should have 3+ tips
core_tools = ['terminal', 'execute_code', 'read_file', 'write_file', 'patch',
    'search_files', 'web_extract', 'web_research', 'web_search',
    'browser_navigate', 'delegate_task', 'delegate_with_model',
    'delegate_parallel', 'memory', 'skill_manage', 'skill_view',
    'knowledge_search', 'validate_output', 'vision_analyze',
    'session_search', 'save_finding']

for tool in core_tools:
    cnt = db.execute("SELECT COUNT(*) FROM distilled_tips WHERE tool_name=?", (tool,)).fetchone()[0]
    status = "✓" if cnt >= 3 else ("~" if cnt >= 2 else "!")
    print(f"  {status} {tool:25s} | {cnt:2d} tips")
```
Action: Tools with <3 tips need research-backed tips created.

### Step 4: Research-Backed Tip Creation
When creating tips from research papers:
- Initial confidence: 0.85-0.90 for research-backed, 0.75-0.80 for heuristic
- Include arXiv ID or source URL in the rationale field
- Structure: condition → recommendation → rationale (actionable, not descriptive)
- Include the domain field for semantic clustering

### Step 5: High-Frequency Tip Boosting
```python
# Tips with high frequency (proven useful) deserve confidence boost
for row in db.execute("SELECT id, confidence, frequency FROM distilled_tips WHERE frequency > 10"):
    boost = min(0.05, 0.01 * min(row[2], 100) / 10)
    new_conf = min(0.95, row[1] + boost)
    db.execute("UPDATE distilled_tips SET confidence=? WHERE id=?", (new_conf, row[0]))
```

## Pitfall: execute_code web_extract API Difference

The `web_extract` function has DIFFERENT signatures depending on context:

**Direct tool call** (outside execute_code):
```python
# Takes url as kwarg
web_extract(url="https://example.com", max_chars=3000)
```

**Inside execute_code (hermes_tools wrapper)**:
```python
from hermes_tools import web_extract
# Takes a LIST of URLs
result = web_extract(["https://example.com"])
# Returns dict with 'results' key containing list of {url, title, content, error}
```

**DO NOT** use `url=` or `max_chars=` in the hermes_tools version — it will fail with TypeError. Use the direct tool call for single-URL extraction with max_chars control.

## CRITICAL: DB Lock Avoidance (Gateway Holds cerebrum_memory.db)

The Hermes gateway process holds an open connection to cerebrum_memory.db. When the distillation plugin's post_tool_call hook writes to it, the DB is locked. This causes every direct write attempt to time out or hang.

**NEVER do this (kills the Hermes session):**
```python
# Inside execute_code or terminal — this WILL kill Hermes
from hermes_tools import terminal
terminal("kill -9 $(pgrep -f 'hermes.*gateway')")  # KILLS HERMES ITSELF
```

The gateway IS the Hermes process. Killing it kills the CLI session. Danny has had to manually restart 4+ times.

**SAFE Method 1: nohup bash retry loop**
Write tips to a Python script at `/tmp/rNNN_distill.py`, then launch a background retry loop:
```bash
nohup bash -c 'for i in $(seq 1 60); do python3 /tmp/rNNN_distill.py && break; sleep 5; done' > /dev/null 2>&1 &
```
The script uses `timeout=60` and `PRAGMA journal_mode=WAL` for best concurrency. The loop retries every 5s for up to 5 minutes.

**SAFE Method 2: tip_inserter queue daemon**
```python
# ~/subconscious/tip_inserter.py — enqueue tips as JSON files
import json, time
from pathlib import Path

queue_dir = Path.home() / "subconscious" / "tip_queue"
queue_dir.mkdir(exist_ok=True)

tip = {
    "tip_type": "heuristic",
    "condition": "WHEN ...",
    "recommendation": "Do X",
    "rationale": "Source 2025",
    "tool_name": "execute_code",
    "domain": "research",
    "confidence": 0.85,
    "source_ids": json.dumps({"round": "r117"})
}

# Write to queue file — the daemon picks it up
queue_file = queue_dir / f"tip_{int(time.time()*1000)}.json"
queue_file.write_text(json.dumps(tip))
```

**SAFE Method 3: Direct write when gateway is stopped**
If you need to guarantee insertion immediately, stop the gateway FIRST using the safe CLI command, then write, then restart:
```bash
hermes gateway stop    # Safe — uses hermes CLI, not kill
python3 /tmp/rNNN_distill.py
hermes gateway start
```

**Script template for tip insertion (use with nohup method):**
```python
#!/usr/bin/env python3
import sqlite3, json, time
from pathlib import Path

DB = str(Path.home() / ".hermes" / "cerebrum_memory.db")

tips = [
    ("heuristic", "WHEN condition", "recommendation text", "rationale", "tool_name", "domain", 0.85),
]

db = sqlite3.connect(DB, timeout=120)
db.execute("PRAGMA journal_mode=WAL")
db.execute("PRAGMA busy_timeout=120000")
now = time.time()
n = 0
for t in tips:
    try:
        db.execute(
            "INSERT OR IGNORE INTO distilled_tips "
            "(tip_type,condition,recommendation,rationale,tool_name,domain,confidence,"
            "upvotes,downvotes,frequency,created_at,last_seen,source_ids) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (t[0],t[1],t[2],t[3],t[4],t[5],t[6],0,0,1,now,now,json.dumps({"round":"rNNN"}))
        )
        n += 1
    except Exception as e:
        print(f"Err: {e}")
db.commit()
total = db.execute("SELECT COUNT(*) FROM distilled_tips").fetchone()[0]
db.close()
print(f"OK: {n} inserted, total={total}")
```

## Verification

After insertion, confirm domain coverage improved:
```bash
cd ~/hermes-agent && venv/bin/python3 ~/subconscious/domain_certainty.py
```
