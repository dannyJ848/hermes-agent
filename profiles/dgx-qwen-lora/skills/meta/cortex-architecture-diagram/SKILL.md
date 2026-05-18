---
name: cortex-architecture-diagram
description: Generate a dark-themed HTML/SVG architecture diagram of the full Cortex system. Run after every training gym round, then analyze with GLM-5V-Turbo to decide what to build next.
version: "2.0"
---

# Cortex Architecture Diagram + Vision-Guided Training Gym

Adapted from Cocoon-AI/architecture-diagram-generator. Produces a self-contained HTML file with inline SVG, then feeds it to GLM-5V-Turbo for visual gap analysis that drives the next training gym round.

## When to Use

- After every training gym round (generate -> analyze -> decide next)
- When Danny asks "show me where we are"
- After major refactors or module additions
- For checkpoint documentation before session end

## Vision-Guided Training Gym Loop (the main workflow)

```
1. Generate diagram with live Cortex stats
2. Open in Chrome + screenshot
3. Base64 encode + send to GLM-5V-Turbo for gap analysis
4. GLM-5V identifies structural gaps and recommends next module
5. Research frontier paper for the biggest gap
6. Build module + wire into plugin
7. Distill tips to Cortex
8. Go to step 1 (regenerate diagram with new module visible)
```

This is the primary driver for autonomous training gym rounds. GLM-5V acts as the "architect's eye" — it spots things that raw stats alone miss (like "Memory domain 0%" when the numbers show 17K nodes with 0 modules reading them).

## Step 1: Gather Current Data

Run these queries to get live state:

```bash
# 1. Module count + plugin size
ls ~/subconscious/*.py | wc -l
wc -l ~/.hermes/plugins/distillation/__init__.py

# 2. Cortex DB stats via temp script (shell quoting breaks inline Python)
# Write Python psycopg2 script to /tmp/, then execute

# 3. Plugin wiring
grep -n 'get_instance' ~/.hermes/plugins/distillation/__init__.py | head -60

# 4. Node type + embedding coverage
# Query cortex_nodes for type counts and embedding counts

# 5. Domain coverage analysis
# Map modules to domains: reasoning, planning, adaptation, execution, safety, evaluation, memory, trajectory
```

## Step 2: Generate the Diagram

Save to `~/Desktop/cortex_architecture.html`. Self-contained HTML with embedded CSS and inline SVG.

### Color Palette
| Type | Fill | Stroke | Use For |
|------|------|--------|---------|
| Frontend/Input | rgba(8, 51, 68, 0.4) | #22d3ee | Hermes Agent, LCM |
| Cognitive Module | rgba(6, 78, 59, 0.4) | #34d399 | All R### modules |
| Database | rgba(76, 29, 149, 0.4) | #a78bfa | Cortex DB, tables |
| Pipeline/Bridge | rgba(120, 53, 15, 0.3) | #fbbf24 | Distillation bridge |
| Message Bus | rgba(251, 146, 60, 0.3) | #fb923c | Eval flywheel |
| Security/Eval | rgba(136, 19, 55, 0.3) | #fb7185 | LLM judges |
| Memory | rgba(190, 24, 93, 0.3) | #f472b6 | Episodic memory |
| External/Generic | rgba(30, 41, 59, 0.5) | #94a3b8 | Daemon, backup |

### Critical SVG Rules
1. **Arrows BEFORE boxes** — SVG paints in document order
2. **Opaque background rects** — fill="#0f172a" behind semi-transparent fills
3. **Color-specific arrow markers** — arrow-cyan, arrow-emerald, arrow-pink
4. **Region boundaries** — dashed stroke (stroke-dasharray="4,4"), rx=8
5. **Gap highlight box** — pink/rose stroke-dasharray for structural gap section

### Layout Structure
```
Y=30:   INPUT LAYER (Hermes Agent + LCM + Context Governor)
Y=85:   Distillation Plugin (central hub)
Y=125:  POST_TOOL_CALL (left, 2 columns, ~18 modules)
Y=125:  PRE_LLM_CALL (right, 1 column, ~8 modules)
Y=500:  Highlight boxes (Episodic Memory, etc.)
Y=540:  Cortex DB + Eval Flywheel + LLM Judges
Y=640:  Tip Injection + Daemon/Backup
Y=700:  Gap Analysis box (pink)
Y=770:  Research Papers (multi-column)
```

## Step 3: Vision Analysis with GLM-5V-Turbo

### WORKING Pipeline (tested Apr 14-15, 2026):

**CRITICAL: Must use base64-encoded images, NOT URLs. GLM-5V returns HTTP 400 on URL-based images.**

```bash
# 1. Open in Chrome + screenshot
open -a "Google Chrome" ~/Desktop/cortex_architecture.html && sleep 3 && screencapture -x /tmp/cortex_screenshot.png
```

Then write a Python script to /tmp/ and execute it:

```python
import base64, urllib.request, json, yaml, os

# Read API key from Hermes vision config
# Use the key from auxiliary.vision section in config.yaml
key = "<read from hermes vision config>"

# Base64 encode screenshot (NOT a URL — must be data URI)
with open("/tmp/cortex_screenshot.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

# Call GLM-5V directly via Model API
url = "https://api.z.ai/api/paas/v4/chat/completions"
payload = {
    "model": "glm-5v-turbo",
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": "Analyze this architecture diagram..."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
    ]}]
}
req = urllib.request.Request(url,
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
resp = urllib.request.urlopen(req, timeout=60)
data = json.loads(resp.read())
analysis = data["choices"][0]["message"]["content"]
```

### API Config:
- **endpoint**: https://api.z.ai/api/paas/v4/ (Model API, NOT coding API)
- **model**: glm-5v-turbo
- **key**: from Hermes config auxiliary.vision section
- **timeout**: 60s

### Performance Stats:
- 2MB screenshot: ~35s analysis, 3250 tokens output (1202 reasoning tokens)
- Accurately identified memory domain 0% gap, rated balance 2/10->7/10 after fix
- Cost: ~$0.012/call

### Why NOT vision_analyze() or browser_vision():
- vision_analyze() cannot read local file paths (only URLs)
- browser_navigate blocks localhost/private URLs
- Direct API call with base64 bypasses ALL of these

### What to Ask GLM-5V for Gap Analysis:
1. STRUCTURAL GAPS: Which cognitive domains are missing?
2. CONNECTIVITY: Are there isolated modules?
3. BALANCE: Is the architecture balanced?
4. CRITICAL MISSING PIECE: What module to add next?
5. SPARSE REGIONS: Which areas look empty?

For verification rounds (after building the module):
1. Can you see the new module? Where?
2. Does the domain now have coverage?
3. What is the NEXT biggest gap?
4. Rate balance 1-10 vs previous.

## Step 4: Programmatic Gap Analysis (supplementary)

When vision isn't available, query Cortex directly:

```sql
-- Domain coverage by node type
SELECT node_type, COUNT(*), COUNT(embedding) FROM cortex_nodes GROUP BY node_type;

-- Elo distribution for tips
SELECT elo, domain FROM cortex_nodes WHERE node_type='tip' ORDER BY elo DESC LIMIT 10;
```

```bash
# Orphan detection: modules in ~/subconscious/ not wired in plugin
ls ~/subconscious/*.py | xargs -I{} basename {} .py | sort > /tmp/all_modules.txt
grep 'from.*import.*get_instance' plugin | sed 's/.*from //' | sed 's/ import//' | sort -u > /tmp/wired.txt
comm -23 /tmp/all_modules.txt /tmp/wired.txt  # orphans
```

## Pitfalls

- **Shell quoting**: Never inline Python with psycopg2 in terminal(). Always write to /tmp/ first.
- **SVG overlaps**: Stacking modules with < 35px vertical gap causes overlap.
- **Arrow masking**: Without opaque background rects, arrows bleed through semi-transparent fills.
- **Z.AI endpoints**: Model API is /api/paas/v4/, Coding API is /api/coding/paas/v4/. GLM-5V uses Model API.
- **Vision base64**: GLM-5V REQUIRES base64-encoded images. URLs return 400. Write script to /tmp/.
- **__pycache__**: Must clear after patching: `find ~/hermes-agent -type d -name __pycache__ -exec rm -rf {} +`
- **Postgres arrays**: Cortex tags column is Postgres array — cannot INSERT JSON strings. Use None or proper array literals.
- **Screencapture timing**: Need sleep 3 after opening Chrome before screencapture.
- **execute_code terminal()**: No background kwarg — use top-level terminal tool for background processes.
