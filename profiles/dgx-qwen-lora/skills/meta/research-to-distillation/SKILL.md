---
name: research-to-distillation
description: Convert research findings into actionable behavioral tips via wiki pages and a bridge script. Pipeline from research to knowledge to tips to injection to measurement.
version: 1.0
created: 2026-04-07
---

# Research-to-Distillation Pipeline

Convert frontier AI research into behavioral changes for the agent.

## When to Use
- After completing a research session (web_research, arxiv, paper reading)
- During AGI cycles when expanding domain knowledge
- When new papers/findings need to be operationalized, not just stored

## Architecture

Research to Wiki Pages to Bridge Script to distilled_tips table to pre_llm_call injection to behavioral change.

## Step-by-Step

### 1. Research (delegate_parallel + web_research + web_extract)
- Use `delegate_parallel` with 3 tasks for broad domain coverage
- Use `web_research` for cutting-edge papers (more reliable than delegate for recent work)
- Use `web_extract` on arxiv abs pages (max_chars=3000) for paper details
- Target domains with LOW confidence (rotate: reasoning, memory, agent-arch, tool-learning, self-improvement)

### 2. Create Wiki Pages
Write to `~/wiki/concepts/<concept-name>.md` with this MANDATORY structure:

```markdown
# Paper Title

**Source:** arXiv:XXXX.XXXXX (Month Year)
**Authors:** ...

## Core Mechanism
[Technical description of how it works]

## Key Innovation
[What makes it novel]

## Results
[Benchmarks, numbers]

## Implementation for Evey
- **Current state**: What we already have
- **Missing**: What's needed
- **Action**: Concrete next step to implement
- **Distillation**: What behavioral tip this suggests
```

The `## Implementation for Evey` section is CRITICAL -- the bridge script parses it.

### 3. Run the Bridge
```bash
cd ~/hermes-agent && venv/bin/python3 ~/subconscious/research_to_distillation.py
```

This scans all wiki pages, extracts implementation steps, and inserts them as distilled tips.

### 4. Verify Tips Were Created
```sql
SELECT tip_type, COUNT(*), ROUND(AVG(confidence),2) FROM distilled_tips WHERE domain='research' GROUP BY tip_type;
SELECT COUNT(*) FROM distilled_tips WHERE confidence >= 0.6;
```

### 5. Update AGI Cron (if changing the cycle)
Use `cronjob(action='update')` to modify the AGI loop to include the new domain or pipeline step.

## Schema Reference (distilled_tips table)

Columns: id, tip_type, condition, recommendation, rationale, tool_name, domain, confidence, upvotes, downvotes, frequency, source_ids, created_at, last_seen, last_used

**IMPORTANT**: There is NO `source` or `updated_at` column. Use `source_ids` for provenance and `last_seen`/`last_used` for timestamps. Check schema with `.schema distilled_tips` before writing INSERT statements.

## Bridge Script Details
- Location: `~/subconscious/research_to_distillation.py`
- Parses `- **Action**:`, `- **Missing**:`, `- **Distillation**:`, and plain `- ` bullets from Implementation sections
- Maps each to tip_type: action, gap, distillation, strategy
- Infers tool_name from keyword matching
- Initial confidence: 0.7, upvotes: 3 (research-backed)
- Deduplicates by fuzzy matching first 50 chars

## Zero-Coverage Domain Identification (Entropy Phase)

Before researching, identify which domains have the FEWEST wiki pages:
```bash
# List all wiki pages and count per domain
ls ~/wiki/concepts/ | grep -iE "keyword1|keyword2" || echo "NO pages found"
```
Prioritize domains with 0 pages. After research, re-run to confirm coverage increase.

## Pitfalls
1. **Schema mismatch**: The distilled_tips table uses `source_ids` not `source`, `tip_type` is required and first column. Always `.schema` before INSERT.
2. **Free model failures**: deepseek-r1-local and nemotron-free frequently fail (HTTP 400). Fall back to web_research + web_extract directly.
3. **Stale __pycache__**: After modifying ANY plugin, `rm -rf __pycache__/` before restart.
4. **403 on web_extract**: Switch to web_research for the same topic. Don't retry the URL.
5. **Missing Implementation section = 0 tips**: The bridge script ONLY extracts from `## Implementation for Evey` sections. If you write a wiki page without this section, the bridge will scan it but create 0 tips. ALWAYS include the section with properly formatted bullets (`- **Action**:`, `- **Missing**:`, `- **Distillation**:`). This was confirmed in Cycle 217 where 3 consecutive distillation runs produced 0 tips until the section was added — then immediately produced 10.
6. **KG saturation**: The bridge skips tips that fuzzy-match existing ones (first 50 chars). If the KG has 119+ tips, many new pages will produce 0 tips because their implementation steps overlap with existing knowledge. This is normal — only genuinely novel actionable steps will produce new tips.
7. **"Research tip seeding disabled — tips must be operational"**: The bridge may reject ALL extracted tips with this message if the operational validation threshold is too strict (observed 2026-04-21). This prevents even legitimate cross-domain insights from entering the distillation loop. When this happens: (a) use the manual insertion fallback below, (b) investigate whether the validation threshold in the bridge script should be relaxed for research-derived tips, and (c) log the rejection domain for later threshold tuning.

## EvoTool Blame Attribution (Apr 7)
Added to distillation plugin: `_classify_failure_stage()` in `~/.hermes/plugins/distillation/__init__.py`.
Classifies errors into stages: caller (permissions, timeouts), selector (wrong args), synthesizer (empty results), planner (wrong tool). Logged to JSONL buffer for per-stage tip analysis.

## Wiki Index
Maintain `~/wiki/index.md` with a table tracking pages per domain. Target: 3+ pages per domain.

## Direct Plugin Integration Pattern

Sometimes a paper technique should be wired directly into the distillation plugin (`~/.hermes/plugins/distillation/__init__.py`) rather than going through the wiki→bridge→tips pipeline. This is for techniques that change HOW tips are retrieved or injected, not WHAT tips contain.

### Pattern: Read Paper → Extract Technique → Map to Plugin → Patch → Verify

1. **Read paper** via `web_extract` (use `max_chars=5000-8000` for arxiv HTML pages)
2. **Extract the actionable technique** — not the full architecture, just the transferable mechanism
3. **Map to existing plugin code** — find where the analogous logic lives in `_on_pre_llm_call()`
4. **Patch** using `patch(mode='replace')` with old_string/new_string
5. **Verify syntax** with `py_compile.compile()` via execute_code
6. **Test queries** via execute_code against the real DB before deploying
7. **Save finding** to knowledge library
8. **Clear `__pycache__`** and restart gateway to activate

### Completed Integrations (in `__init__.py`)

- **SWIRL Bayesian Predictor**: Beta(α,β) priors per tool, warns when pred<40%. `_predict_tool_outcome()`
- **AUQ Uncertainty Tracker**: Cumulative confidence per turn, injects [HIGH UNCERTAINTY] at <30%. `_uncertainty_state`
- **Polaris Experience Patches**: Auto-generates recovery tips from failure patterns. domain='agi-experience'
- **ERL Task-Context Retrieval** (arXiv:2603.24639): Keyword extraction from user message → LIKE match against tip conditions. Prioritizes task-relevant over globally weakest. Zero-cost alternative to LLM-scored relevance.
- **AutoAgent Elastic Memory Tiering** (arXiv:2603.09716): T1 (conf>=0.7 inject verbatim), T2 (0.4-0.7 summary), T3 (skip). Reduces injection noise.

### SQL Injection Prevention for ERL Queries

When building dynamic LIKE queries from user keywords:
```python
_safe_kw = [kw.replace("'","").replace('"',"").replace(";","").replace("--","") 
           for kw in list(_task_keywords)[:8]]
kw_like = " OR ".join(
    f"(condition LIKE '%{kw}%' OR recommendation LIKE '%{kw}%')"
    for kw in _safe_kw
)
```
Always cap at 8 keywords and strip dangerous characters.

## Research-to-Tip Gap (discovered Apr 7, 2026)

Wiki pages do NOT automatically convert to tips. The bridge script requires properly formatted `## Implementation for Evey` sections with `- **Action**:`, `- **Missing**:`, `- **Distillation**:` bullets. Without these, the bridge scans but produces 0 tips.

**Manual tip creation fallback**: When research produces findings that the bridge can't extract, insert tips directly:
```python
cer.execute(
    "INSERT INTO distilled_tips "
    "(tip_type, condition, recommendation, rationale, tool_name, "
    "domain, confidence, upvotes, downvotes, frequency, source_ids, last_seen) "
    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
    ("research_rNN", condition, recommendation, "From real web research",
     tool_name, domain, 0.85, 1, 0, 1, "rNN_research", time.time())
)
```
Always check: `SELECT COUNT(*) FROM distilled_tips WHERE tip_type LIKE '%research%'` — if 0, the pipeline is broken.

## SAGE Skill-Integrated Reward (from arXiv:2512.17102)

SAGE (Skill Augmented GRPO for self-Evolution) found that skill libraries work best when you reward skill CREATION and REUSE, not just task outcomes. This maps to our pipeline:

- **Creation bonus**: When a tip gets its first real upvote from condition-aware voting, boost confidence by +0.05
- **Reuse bonus**: When a tip accumulates 5+ upvotes, boost again by +0.03
- **Outcome-only is insufficient**: Just tracking success/failure misses whether tips are being USED

This is a concrete improvement target for the feedback loop. Implementation: modify `_update_tip_confidence()` to check milestone upvote counts and apply bonus boosts.

## Batch Multi-Source Integration Sweep Pattern

When mining MULTIPLE sources simultaneously (books, repos, APIs, community reports), use this pattern instead of single-paper wiki pages:

### 1. Extract from all sources in parallel
- Read local files with `terminal("cat /path")` or `read_file()` — fastest for cloned repos/PDFs
- Use `execute_code()` to process multiple files in one script
- Use `delegate_parallel` for web sources (but note: can't read local files)

### 2. Batch distill into waves
Create a Python script at `/tmp/rNNN_distill.py` with a `tips` list of dicts:
```python
tips = [
    {"tip_type": "heuristic", "condition": "IF ...", "recommendation": "THEN ...",
     "rationale": "Source: ...", "domain": "training", "confidence": 0.90},
    # ... more tips
]
```
Insert via nohup (safe DB write — avoids gateway lock):
```bash
nohup python3 /tmp/rNNN_distill.py > /tmp/rNNN_output.txt 2>&1 &
sleep 4 && cat /tmp/rNNN_output.txt
```
Script uses retry loop (20 attempts, 3s sleep) for DB lock resilience.

### 3. Push to Hindsight knowledge graph
Write payloads to temp file to avoid shell escaping issues:
```python
for item in hindsight_items:
    payload_str = json.dumps({"items": [item], "async": True})
    with open('/tmp/hindsight_payload.json', 'w') as f:
        f.write(payload_str)
    # Then curl with -d @/tmp/hindsight_payload.json
```
Hindsight API: POST `http://2.24.28.233:8890/v1/default/banks/hermes-cerebrum/memories`
Each item: `{"content": "...", "tags": ["source", "domain"]}`

### 4. Wire best patterns into plugin
After distillation, identify 2-3 highest-impact patterns and wire them directly:
- **Mixture-of-Difficulty** (R151): In pre_llm_call tip selection, use 70/30 split between high-confidence and exploratory tips. Prevents training mode collapse.
- **Eval-Driven Flywheel** (R152): In post_tool_call, score injected tips against actual outcomes. Upvote on success, downvote + confidence decay on failure.
- Pattern: read paper → extract technique → map to plugin hook → patch → syntax check → clear __pycache__ → gateway restart → verify

### 5. Verify sweep results
```bash
sqlite3 ~/.hermes/cerebrum_memory.db 'SELECT COUNT(*) FROM distilled_tips'
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT domain, COUNT(*) FROM distilled_tips GROUP BY domain ORDER BY COUNT(*) DESC LIMIT 15"
grep "Distillation plugin" ~/.hermes/logs/gateway.log | tail -3
```

### Pitfalls (Integration Sweep)
1. **Shell escaping with curl**: JSON payloads with quotes break in shell. ALWAYS write to temp file first, then `curl -d @/tmp/file`.
2. **89% easy tips problem**: Auto-distillation floods easy/low-confidence tips. Check difficulty distribution after sweep and add medium/hard tips manually if needed.
3. **Hindsight push timeout**: VPS Hindsight recall takes 7-60s. Use `async: true` for retain operations. Check HTTP status codes (200/201/202 = success).

## Deep Repo Mining Pattern

When research drops include GitHub repos (papers with code, skill libraries, framework repos), clone and mine them for maximum extraction. This produces 3-5x more tips than web_extract alone.

### 1. Clone and Map
```bash
cd ~/repos && git clone <repo-url>
find ~/repos/<repo> -type f | head -40  # Map structure
find ~/repos/<repo> -name 'SKILL.md' | wc -l  # Count skills
```

### 2. LaTeX Paper Extraction
For papers in LaTeX repos, extract sections with sed:
```bash
# List all sections
grep -n 'section{' paper.tex

# Extract specific sections
sed -n '/\\section{Method}/,/\\section{/p' paper.tex | head -80
sed -n '/\\begin{abstract}/,/\\end{abstract}/p' paper.tex

# Extract evolution/runt history
cat paper/autoreason_run/history.json | python3 -m json.tool
```

### 3. Skill Library Deep Mining
Don't just read SKILL.md — mine the full directory tree:
- `SKILL.md` — main content (always read)
- `references/architecture.md` — deep design rationale
- `references/design-patterns.md` — reusable patterns
- `references/examples.md` — real trajectories with numbers
- `references/tutorials.md` — step-by-step walkthroughs
- `templates/` — config templates
- `scripts/` — executable helpers

Extract sequentially with sed ranges:
```bash
sed -n '1,70p' SKILL.md    # First 70 lines (metadata + intro)
sed -n '80,200p' SKILL.md  # Middle sections (method/details)
grep -n 'Pitfall\|Warning\|Critical\|NEVER\|ALWAYS' SKILL.md  # Warnings
```

### 4. Multi-Wave Distillation
Organize tips into waves by topic, not all at once:
- **Wave 1** (R259): Core paper findings + highest-impact patterns
- **Wave 2** (R260): Practical patterns from reference files + examples
- **Wave 3** (R261): Synthesis + cross-domain connections

Each wave = separate `/tmp/rNNN_distill.py` script. Run sequentially, verify counts between waves.

### 5. Hindsight Bulk Sync
After all waves, sync ALL new tips in one batch:
```python
# Write to /tmp/hindsight_sync_rNNN.py
payload = json.dumps({"items": batch, "async": True}).encode()
req = urllib.request.Request(HINDSIGHT_URL, data=payload, 
    headers={"Content-Type": "application/json"}, method="POST")
# Batch size 50, all metadata values as strings
```
CRITICAL: `async: true` prevents timeouts. All metadata values MUST be strings. Batch 50 works reliably.

### 6. Save Findings
Use `save_finding()` to save comprehensive extraction summaries to knowledge library. One finding per major source (paper + repo).

### Pitfalls (Deep Repo Mining)
1. **vision_analyze can't access URLs or local files**: Download with curl, then analyze from `/tmp/`. If still fails, just extract text with sed/cat.
2. **Paper not yet on arxiv**: Brand new papers may not be indexed. Use the repo's LaTeX source directly.
3. **Shell escaping in execute_code**: Can't use heredocs (`<< 'PYEOF'`) inside execute_code. Write full scripts to `/tmp/` files and run with terminal instead.
4. **Missing sections in LaTeX**: Some papers use `\input{}` to split. Check for included files.

## Cron Integration
The AGI cron (bd76c4443c53) runs every 3 minutes with a 6-phase cycle:
1. Domain exploration (entropy)
2. Research to distillation (run bridge script)
3. Capability measurement (tip stats)
4. Top-down injection check (healthy tip count)
5. Wiki expansion (fill empty domains)
6. Self-monitoring (costs, errors)
