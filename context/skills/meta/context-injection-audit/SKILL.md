---
name: context-injection-audit
description: Audit and trim plugin context injection bloat — when pre_llm_call hooks waste tokens on low-signal data every turn.
version: 1.0
tags: [plugin, optimization, tokens, context, bloat]
---

# Context Injection Audit

## Trigger
- Agent context is bloated with plugin-injected noise every turn
- Token usage is high despite few user-facing tool calls
- Plugin pre_llm_call hooks inject more than ~300 tokens/turn combined
- Danny says "fix the injection" or "too much noise" or "brain growing"

## Diagnosis Steps

### 1. Measure the injection
Load the plugin module directly and call its `on_pre_llm_call()` to see what it injects:
```python
import sys, importlib
spec = importlib.util.spec_from_file_location('ti', '<plugin_path>/__init__.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
result = mod.on_pre_llm_call(user_message='test', conversation_history=[])
if result and 'context' in result:
    ctx = result['context']
    print(f'SIZE: {len(ctx)} chars = ~{len(ctx)//4} tokens')
    print(ctx)
```

### 2. Find all injection sources
Search for all `pre_llm_call` hooks across plugins:
```bash
grep -rl 'pre_llm_call' ~/.hermes/plugins/ --include='*.py' | grep -v __pycache__
```

### 3. Classify each injection by signal value
For each section in the injection output, rate it:
- **ZERO**: Always same value, never actionable (e.g., perspective_diversity always 0.0)
- **LOW**: Rarely changes behavior, could check manually (e.g., token_tracker, active_inference)
- **MEDIUM**: Sometimes useful but needs filtering (e.g., tool_intelligence report)
- **HIGH**: Directly improves tool use every turn (e.g., distilled tips, relevant rules)

### 4. Disable low/zero signal sources
Comment out the code blocks (don't delete — preserve for potential re-enable):
```python
# DISABLED: Perspective Diversity — always 0.0, pure noise
# try:
#     from perspective_diversity import get_diversity_advice
#     ...
```

### 5. Trim remaining HIGH/MEDIUM sources
- **Tool intelligence report**: Require `total_calls >= 10` (3 calls doesn't mean weak, just rare)
- **Iteration lessons**: Cap frequency at `< 100` (counts like 2758x are stale noise, not signal)
- **Sort by recency not frequency** for iteration lessons (new > old with high counts)
- **Compress proven tools** to single line: `PROVEN: tool1(89%), tool2(91%)`
- **Limit weak tools** to top 3, skip verbose last_lesson fields

### 6. Clean database noise
- Delete duplicate tips (same condition/recommendation for same tool)
- Delete generic useless tips ("Check error message for root cause")
- These inflate injection size and dilute signal

## Files
- `~/.hermes/plugins/evey-tool-intelligence/__init__.py` — main injection source (pre_llm_call at line ~804)
- `~/subconscious/distillation_bridge.py` — top_down_recall() builds iteration lessons + meta-insights
- `~/.hermes/plugins/distillation/__init__.py` — secondary injection via distilled tool rules

## Key Rules
1. **Never delete code, comment it out** with a reason (DISABLED: ...)
2. **Always clear __pycache__** after editing: `rm -rf ~/.hermes/plugins/<name>/__pycache__/`
3. **Test before declaring done** — load the module and measure the new injection size
4. **Target < 500 tokens/turn** for all injection combined
5. **Rarely-used tools with 0% success and <5 calls are NOT weak** — they're just uncommon. Filter to >=10 calls.

## Pitfalls
- The iteration lessons `ORDER BY frequency DESC` surfaces stale lessons with 2000+ counts. Use `ORDER BY last_seen DESC` with a `frequency < 100` cap instead.
- Duplicate tips inflate injection — two tips saying "switch to web_research for 403" both get injected. Deduplicate by condition+tool_name.
- The `_get_capability_report()` reads from `tool_stats` which may drift from `call_log`. Ensure the distillation plugin's `_sync_tool_capability()` keeps them aligned.
- `call_log.result_status = 'failure'` for recent failures may include successful calls misclassified. Check the actual error_pattern before trusting it.

## RESOLVED: Dual-Path Injection (Apr 7, 2026)

Ghost sections had TWO distinct root causes:

### Cause 1: Gateway core injection (gateway/run.py)
**File**: `gateway/run.py` lines ~2340-2380
The gateway core had its OWN injection block that read directly from `cerebrum_memory.db` and injected ITERATION LESSONS + META-INSIGHTS into context_prompt. This was COMPLETELY OUTSIDE the plugin system — no pre_llm_call hook involved. It duplicated the distillation plugin's work and injected garbage META-INSIGHTS (regurgitated text, not real insights).

**Fix**: Commented out the entire block at run.py L2340-2380. The distillation plugin's `top_down_recall()` handles this properly.

### Cause 2: Compressed context from previous sessions
ACTIVE INFERENCE, PERSPECTIVE DIVERSITY, TOKEN TRACKER, SELF-DEBUG were NOT injecting from any current code path. They survived from a previous session via context compression — the agent's own compressed context carried these stale injection artifacts forward. They only appear in long-running sessions that started before the modules were disabled.

**Fix**: No code fix needed. These disappear on the next fresh session start.

### Key Diagnostic Method
When debugging ghost injection, search ALL code paths — not just plugins:
```bash
# Search plugin hooks
grep -rn 'SECTION_NAME' ~/.hermes/plugins/ --include='*.py' | grep -v __pycache__

# Search gateway core (THIS is what we missed initially)
grep -rn 'SECTION_NAME' ~/hermes-agent/gateway/ --include='*.py' | grep -v __pycache__

# Search run_agent.py and other top-level files
grep -rn 'SECTION_NAME' ~/hermes-agent/ --include='*.py' | grep -v __pycache__ | grep -v subconscious/ | grep -v plugins/
```

The gateway core (run.py) has its own injection path at the session setup stage that appends to `context_prompt` BEFORE any plugin hooks fire. This is easy to miss because it's not part of the plugin system.

## Greeting Guard Pattern (Apr 7)

Added `_is_throwaway_greeting()` check to BOTH pre_llm_call hooks:
- Returns None/"" for messages <=20 chars with no task keywords
- Prevents context injection from priming autonomous work on throwaway messages like "hi", "hey", "sup"
- Applied in: evey-tool-intelligence/__init__.py and distillation/__init__.py
- Unit tested: "hi" → None, "hey" → None, "fix the bug" → full injection

## Verifying Bottom-Up + Top-Down Are Both Active (Apr 7)

After killing ghost injections, ALWAYS verify the distillation pipeline is still complete:

### Bottom-up verification
```python
import sqlite3, os
cb = sqlite3.connect(os.path.expanduser("~/.hermes/cerebrum_memory.db"))
# Check tips from tool outcomes (empty source = bottom-up heuristic extraction)
rows = cb.execute("SELECT source_ids, COUNT(*) FROM distilled_tips GROUP BY source_ids ORDER BY COUNT(*) DESC LIMIT 10").fetchall()
for r in rows:
    print(f"  source={r[0][:40]:40s} count={r[1]}")
# Also check JSONL buffer is growing
jsonl = os.path.expanduser("~/subconscious/distillation_buffer.jsonl")
print(f"Buffer entries: {sum(1 for _ in open(jsonl))}")
cb.close()
```

The 3 tip sources and their expected proportions:
- `wiki:*` = research-to-distillation (~70%, bulk of tips)
- (empty) = bottom-up from tool outcomes (~20%, heuristic extraction)
- `cycle*` / `timestamp` = AGI cycle synthesis (~10%)

### Top-down verification
```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/subconscious"))
from distillation_bridge import top_down_recall
result = top_down_recall("debug the greeting echo fix")
# Should contain ONLY: [ACTIONABLE TIPS]
# Should NOT contain: [ITERATION LESSONS], [AGI CONTEXT], [MEMORY HEALTH],
#   [ACTIVE INFERENCE], [META-INSIGHTS], [PERSPECTIVE DIVERSITY], etc.
# Those 3 were disabled Apr 7 — they injected garbage (failed tasks, DNS errors,
# meaningless cycle counters, admin data). Memory prune still runs silently.
assert 'ACTIONABLE TIPS' in result or result.strip() == '', f"Unexpected: {result[:200]}"
assert 'ITERATION LESSONS' not in result, "ITERATION LESSONS should be disabled"
assert 'AGI CONTEXT' not in result, "AGI CONTEXT should be disabled"
assert 'MEMORY HEALTH' not in result, "MEMORY HEALTH should be disabled"
```

### Key insight: Active injection vs compression artifacts
When you see ghost sections in a running session:
1. Check if session started BEFORE or AFTER the code fix
2. Search ALL code paths (plugins AND gateway core) for the section name
3. If no code path produces it AND the session is old → it's a compression artifact
4. Only a full restart (new CLI session) clears compression artifacts

### Definitive test: Call plugins directly in isolation (Apr 7)
When ghost sections persist but grep finds nothing in source files, test each plugin's injection function OUTSIDE the running session:

```python
# Test evey-tool-intelligence plugin directly
cd ~/hermes-agent && source venv/bin/activate && python3 << 'PYEOF'
import sys, os
sys.path.insert(0, os.path.expanduser("~/.hermes/plugins/evey-tool-intelligence"))
sys.path.insert(0, os.path.expanduser("~/subconscious"))
from __init__ import on_pre_llm_call
result = on_pre_llm_call(user_message="research deep learning", conversation_history=[])
if result and "context" in result:
    print(result["context"])
else:
    print("(no injection)")
PYEOF
```

```python
# Test distillation bridge directly
cd ~/hermes-agent && source venv/bin/activate && python3 << 'PYEOF'
import sys, os
sys.path.insert(0, os.path.expanduser("~/subconscious"))
from distillation_bridge import top_down_recall
result = top_down_recall("test task")
print(repr(result[:2000]) if result else "(empty)")
PYEOF
```

If the direct test output is CLEAN (no ghost sections), then the ghosts are NOT from code — they're from old session compressed history bleeding through on checkpoint restore. Fix: start a fresh session without restoring old compressed context.

This distinction saves hours of chasing code paths that don't exist.

## Tip Quality Audit (Apr 7, 2026)

The distilled_tips table (in cerebrum_memory.db) accumulates junk tips that pollute injection.
Run this audit when tips look broken (empty tool names, truncated text, research speculation):

### Junk tip patterns to purge
```python
import sqlite3, os
db = sqlite3.connect(os.path.expanduser("~/.hermes/cerebrum_memory.db"))
c = db.cursor()

# 1. Research speculation — "From research: ..." is NOT an operational tip
c.execute("SELECT COUNT(*) FROM distilled_tips WHERE condition LIKE 'From research:%'")
# DELETE if found — these are research notes, not tool rules

# 2. Generic error handling — "Check error message for root cause" = useless
c.execute("SELECT COUNT(*) FROM distilled_tips WHERE recommendation LIKE 'Check error message%'")
# DELETE — tells the agent nothing it doesn't already know

# 3. Non-tool tool_name — general, distillation, memory, VISION, REASONING, etc.
c.execute("SELECT tool_name, COUNT(*) FROM distilled_tips GROUP BY tool_name ORDER BY COUNT(*) DESC")
# Any tool_name that isn't a real Hermes tool = junk from research distillation
# Real tools: terminal, execute_code, read_file, write_file, patch, web_extract, 
# web_research, search_files, browser_navigate, browser_vision, delegate_task, etc.

# 4. Empty tool_name
c.execute("DELETE FROM distilled_tips WHERE tool_name IS NULL OR TRIM(tool_name) = ''")
```

### After purge, verify remaining tips are clean
```python
c.execute("SELECT tool_name, condition, recommendation, upvotes FROM distilled_tips ORDER BY upvotes DESC")
for row in c.fetchall():
    print(f"[{row[0]}] ({row[3]}v) IF {row[1][:50]} THEN {row[2][:50]}")
# Every tip should have: real tool_name, specific condition, actionable recommendation
db.commit()
db.close()
```

### Prevention: Three-layer defense against tip re-pollution

**Layer 1: Guard in `bottom_up_store()` (distillation_bridge.py)**
After the existing noise guard block, add two more rejection rules:
```python
# REJECT "From research:" tips — speculative, not operational
if condition and condition.startswith("From research:"):
    return

# REJECT tips with fake tool names (research domains, not actual tools)
_REAL_TOOLS = {"execute_code", "terminal", "read_file", "write_file", "patch", ...}
if tool_name not in _REAL_TOOLS:
    return  # Fake tool name — reject
```

**Layer 2: Disable `research_to_distillation.py` at function entry**
This script reads wiki pages and seeds "From research:" tips into distilled_tips.
It runs from the controller and can regenerate hundreds of tips after a purge.
Disable it with an early return:
```python
def convert_research_to_tips():
    # DISABLED: Research tip seeding disabled — tips must be operational
    return {"error": "Research tip seeding disabled", "tips_created": 0}
```

**Layer 3: Purge + guard must happen BEFORE restart**
The running gateway caches code in memory. When you purge tips from the DB,
the old code can regenerate them before the restart takes effect.
Fix order: (1) patch bottom_up_store guards, (2) disable research_to_distillation,
(3) purge DB, (4) clear __pycache__, (5) THEN restart gateway.

### Critical lesson: Tips regenerate from hidden sources
After purging 277 tips to 27, they regenerated to 215 within minutes because
`research_to_distillation.py` was still running in the controller pipeline.
The DB purge alone is useless — you MUST also disable the source.
Symptom: you purge, verify count is 29, check again 2 min later and it's 200+.
This means something is auto-seeding. Trace it:
```bash
grep -rn 'INSERT INTO distilled_tips' ~/subconscious/ --include='*.py'
grep -rn 'bottom_up_store' ~/.hermes/plugins/ ~/subconscious/controller.py --include='*.py'
```

## Disabling try/except Injection Blocks Safely (Apr 10, 2026)

When disabling injection blocks that are wrapped in try/except, you CANNOT just replace `try:` with `if False:` — the `except` clause becomes orphaned and causes SyntaxError. 

**Correct method:** Replace the entire try/except block (comment + try + body + except + pass) with just the comment + `pass`:
```python
# Use a Python script that finds try/except pairs and collapses them
# See /tmp/disable_noise.py for the reusable pattern
```

**Key steps:**
1. Find block start line (the `# ── R###:` comment)
2. Find the `try:` within 3 lines after
3. Find the matching `except` at the same indent level
4. Replace entire range with: `# ── R###: ... [DISABLED: noise reduction]` + `pass` + blank line
5. Track line number offset as each edit shifts subsequent line numbers

**Why `if False: try:` doesn't work:** Python's parser sees `if False:` as starting a new block, then `try:` as a nested block, but the `except Exception:` at the end matches the `try:` not the `if`, creating an indentation mismatch when the block ends.

## Tip Limit Trimming (Apr 10, 2026)

When the distilled tips injection is too large, trim at the SQL level:
- ERL task-relevant tips: reduce LIMIT and raise confidence floor (e.g., LIMIT 4 → 2, confidence >= 0.5 → 0.6)
- Weakest tools: reduce tool count and tips-per-tool (e.g., 3 tools x 2 tips → 2 tools x 1 tip)
- Recent failure patches: reduce LIMIT (e.g., 3 → 2)
- This cuts ~40% of injection size without losing high-signal tips

## R-Module Noise Audit Pattern (Apr 10, 2026)

After building 13+ subconscious modules (R100-R140), many injection blocks become noise:
- **Stats-only blocks** (counts, averages, percentages) → DISABLE (tool_stats is queryable on demand)
- **Duplicate blocks** (R124 and R113 both call safety_validator) → keep one, disable the other
- **Low-confidence predictions** ("46% confidence next tool: X") → DISABLE (below decision threshold)
- **Generic warnings** ("Quality avg=0.67") → DISABLE (not actionable)

**Test each module's actual output:**
```python
cd ~/subconscious && python3 -c '
import sys; sys.path.insert(0, ".")
mod = __import__("module_name")
inst = mod.factory_fn("test")
result = inst.build_injection("test query")
print(f"{len(str(result))} chars: {str(result)[:100]}")
'
```
If output is 0 chars or just stats → DISABLE. If it's actionable advice → KEEP.

## Batch Noise Kill Pattern (Apr 10, R142 audit)

When 15+ modules have `build_injection()` and you need to kill many at once:

### Step 1: Find noise markers in module outputs
```bash
# Search subconscious modules for known noisy output strings
for mod in meta_reasoning tool_chain_validator prompt_optimizer self_eval_loop spec_predictor skill_versioner plan_verifier safety_validator think_budget knowledge_retrieval; do
    grep -n 'LOOP DETECTED\|CHAIN_VALIDATOR\|PROMPT_OPT\|QUALITY:\|NEXT_TOOL\|SKILL_HEALTH\|VERIFIER\|SAFETY:\|THINK_BUDGET\|RETRIEVAL_STATS' ~/subconscious/${mod}.py 2>/dev/null | head -3
done
```

### Step 2: Read the plugin injection section to find active blocks
```bash
sed -n '1540,1760p' ~/.hermes/plugins/distillation/__init__.py
```

### Step 3: Classify each block (NOISE vs USEFUL)
- **NOISE** (pure stats, not actionable): THINK_BUDGET tier, RETRIEVAL_STATS, CHAIN_VALIDATOR counts, PROMPT_OPT fitness scores, QUALITY averages, NEXT_TOOL_HINT predictions, SKILL_HEALTH, VERIFIER stats, SAFETY counters, META: LOOP DETECTED, process reward weak-tools list, value retriever, skill taxonomy, advantage estimator, LLM+P planner
- **USEFUL** (actionable rules/predictions): distilled tool rules, experience replay, reward shaping, error predictor risk warnings, reflective heuristics, proposition indexer, local inference status

### Step 4: Batch-disable with patch tool
Replace each try/except block with `# ── R###: ... [DISABLED: noise reduction]` + `pass`.
Do multiple modules per patch call when they're adjacent in the file.

### Step 5: Verify
```bash
python3 -c 'import ast; ast.parse(open("~/.hermes/plugins/distillation/__init__.py").read()); print("OK")'
grep -c 'lines.append' ~/.hermes/plugins/distillation/__init__.py
grep -c 'DISABLED.*noise' ~/.hermes/plugins/distillation/__init__.py
hermes gateway restart
```

### R142 audit results
- Killed 11 more noise blocks (R106, R107, R117, R118, R113, R114, R122, R132, R134, R136, R140)
- Plugin: 1939 → 1861 lines, lines.append calls: 34 → 23
- Total disabled blocks: 22, active injections: ~11 (down from 34)
- **Pattern**: subconscious modules that output ONLY stats (counts, averages, percentages) are always noise. Modules that output CONDITIONAL rules (IF...THEN...) or risk warnings are useful.

## Comprehensive Full-Function Audit (Apr 11, 2026)

### CRITICAL LESSON: R-Module Trimming Is NOT Enough
The R102-R145 trim (292→77 lines) was a false finish. After restart, injection was STILL bloated because many noise blocks exist OUTSIDE the R-module section. The pre_llm_call function has injection sources scattered across 3+ distinct code regions.

### Three Injection Regions in Distillation Plugin
The pre_llm_call function (~L1840-2400) has THREE distinct injection zones:

**Region 1: Uncertainty + Core Rules (~L1920-2060)**
- Uncertainty signal (KEEP — conditional)
- Distilled tool rules with ERL + weakest tools (KEEP — high signal)
- Recent failure patches (CONDITIONAL — keep but already trimmed)
- Hindsight KG recall (KEEP — keyword-triggered, cached)
- Arg feedback (CONDITIONAL — tool-mention triggered)

**Region 2: R-Module Blocks (~L2060-2190)**
- R100-R145 + TIER 2 + MYTHOS (TRIMMED — 292→77 lines)
- See "R-Module Noise Audit Pattern" above

**Region 3: Additional Sources (UNKNOWN — scattered before/after R-modules)**
These were NOT caught in the R102-R145 trim:
- `[CROSS-SESSION: AVOID]` — from distillation_bridge.py or another source
- `[TOP TOOLS: ...]` — tool rankings, probably from tool_capability.db
- `[HEURISTICS: ...]` — iteration lessons from distillation_bridge
- `[PROPOSITIONS: ...]` — from proposition_indexer (should have been killed)
- `[LOCAL_INFERENCE: ...]` — from local_inference_enhancer (should have been killed)
- `[NLAC CRITIC ...]` — from NLAC module (should have been killed)
- `[CRITICAL TOOL GUIDANCE ...]` — weakest tool verbose report
- `[TOOL INTELLIGENCE ...]` — from evey-tool-intelligence plugin
- `[ACTIONABLE TIPS ...]` — from distillation_bridge top_down_recall
- `[DEBUG_HINT: ...]` — from self_debug module (should have been killed)
- `[DELEGATE REASONING ...]` — kept but old format

### Proper Full Audit Methodology
1. **Capture the ACTUAL injection** — trigger an LLM call and read what was injected
2. **Map EVERY [BRACKET] section** to its source (plugin function + line number)
3. **grep for EACH bracket tag** across ALL injection sources:
   ```bash
   grep -rn 'CROSS-SESSION\|TOP TOOLS\|HEURISTICS\|PROPOSITIONS\|LOCAL_INFERENCE\|NLAC CRITIC\|CRITICAL TOOL\|TOOL INTELLIGENCE\|ACTIONABLE TIPS\|DEBUG_HINT\|DELEGATE REASONING' ~/.hermes/plugins/ --include='*.py' | grep -v __pycache__
   grep -rn 'CROSS-SESSION\|TOP TOOLS\|HEURISTICS' ~/subconscious/ --include='*.py'
   grep -rn 'CROSS-SESSION\|TOP TOOLS\|HEURISTICS' ~/hermes-agent/ --include='*.py' | grep -v __pycache__
   ```
4. **Kill at the SOURCE** — don't assume all blocks are in one section
5. **Verify by measuring injection AFTER restart** — compare before/after char counts

### Why R-Module Audit Was Insufficient
The R102-R145 blocks were in one contiguous section of the plugin. But:
- Some blocks (NLAC, PROPOSITIONS, LOCAL_INFERENCE, DEBUG_HINT) that I "killed" are STILL appearing — suggesting either duplicate code paths or stale bytecode
- Other blocks (CROSS-SESSION, TOP TOOLS, HEURISTICS, ACTIONABLE TIPS) come from DIFFERENT code paths entirely (distillation_bridge.py, evey-tool-intelligence plugin)
- The `[CRITICAL TOOL GUIDANCE]` and `[TOOL INTELLIGENCE]` sections come from the OTHER plugin, not the distillation plugin

### Cross-Plugin Audit Pattern (Apr 11, 2026)

When the distillation plugin is trimmed but injection is STILL bloated, the noise comes from OTHER plugins. The two main injection sources are:

1. **`~/.hermes/plugins/distillation/__init__.py`** — `on_pre_llm_call()` returns a string
2. **`~/.hermes/plugins/evey-tool-intelligence/__init__.py`** — `on_pre_llm_call()` returns `{"context": "..."}`

Both fire independently. The tool-intelligence plugin's `on_pre_llm_call()` (at line ~803) calls multiple subsystems:
- `_get_capability_report()` → `[TOOL INTELLIGENCE]` (KEEP — useful stats)
- `ops.on_pre_llm_injection()` → `[CROSS-SESSION]`, `[TOP TOOLS]`, `[HEURISTICS]`, `[CRITICAL TOOL GUIDANCE]` (KILL — redundant with DISTILLED TOOL RULES)
- `top_down_recall()` → `[ACTIONABLE TIPS]` (KILL — duplicate of DISTILLED TOOL RULES)
- Code intelligence / flow graph / regression → KEEP (conditional, code-tasks-only)
- Self-awareness stop detection → KEEP (only fires when >2 stops/hour)

**Pattern: When two plugins inject similar data, kill the weaker one.** The distillation plugin's `[DISTILLED TOOL RULES]` with ERL keyword matching + weakest tools is higher quality than the tool-intelligence plugin's operational mastery chain.

**How to find cross-plugin noise:**
```bash
# Find ALL bracket tags across ALL injection sources
grep -rn 'lines\.append\|parts\.append' ~/.hermes/plugins/ --include='*.py' | grep -v __pycache__
# Then grep for each bracket tag in subconscious modules
grep -rn 'CROSS-SESSION\|TOP TOOLS\|HEURISTICS\|CRITICAL TOOL' ~/subconscious/ --include='*.py'
```

**Key insight**: The `[TOOL INTELLIGENCE]` plugin calls operational mastery which calls experience_replay.build_injection(), reward_shaping.build_injection(), reflective_heuristic.build_injection(), engineering_feedback_loop.generate_critical_tools_context(). Each of these generates a `[BRACKET]` section. ALL of these duplicate what the distillation plugin already injects via `[DISTILLED TOOL RULES]`. Kill the entire operational mastery call.

### Post-Restart Verification Is Mandatory
After ANY injection trim:
1. Restart gateway
2. Send a test message
3. Read the ACTUAL injection that fires
4. Compare with pre-trim injection
5. If noise persists, grep for the bracket tag to find the ACTUAL source

## Hard Cap Pattern (Apr 11, 2026)

When injection keeps growing because new modules keep getting wired in, the per-source filtering approach fails — you trim 5 sources but 3 new ones appear. The nuclear option: **hard cap total injection to N items with a counter**.

### Pattern
```python
# Replace sprawling multi-source injection with:
lines.append("[CORE MEMORY — top rules from 900+ distilled tips]")
_injected_count = 0
_MAX_INJECT = 5

# Priority 1: ERL task-relevant (max 3)
for tool, cond, rec, conf in _erl_tips[:3]:
    if conf >= 0.7 and _injected_count < _MAX_INJECT:
        lines.append(f"  {tool}: IF {cond[:50]} THEN {rec[:80]}")
        _injected_count += 1

# Priority 2: Highest-voted experience (max 2)
if _injected_count < _MAX_INJECT:
    patches = cer.execute(
        "SELECT condition, recommendation FROM distilled_tips "
        "WHERE domain='agi-experience' AND confidence >= 0.7 "
        "ORDER BY upvotes DESC LIMIT 2"
    ).fetchall()
    for cond, rec in patches:
        if _injected_count < _MAX_INJECT:
            lines.append(f"  EXPERIENCE: {cond[:50]} → {rec[:70]}")
            _injected_count += 1
```

### Why this works
- Counter prevents injection from growing regardless of how many sources exist
- Priority ordering ensures highest-value tips always get through
- conf>=0.7 filter eliminates mediocre tips that dilute signal
- Remove Nomic/embed dedup entirely — unnecessary when capping at 5

### What to kill when hard-capping
- Nomic semantic dedup block (~40 lines) — overkill for 5 tips
- Mixture-of-Difficulty balancer — complexity that doesn't help
- Weakest tool iteration loops — replaced by priority selection
- Arg Feedback injection — covered by core tips
- Multi-fact Hindsight recall — reduce to max 1 fact, single line

### Conditional blocks to KEEP
These are gated and only fire in specific situations (not every turn):
- R101 Recovery (only on error keywords)
- R145 Error Storm (only on 3+ fails in 5min)
- Context Health (only in critical zone)
- Watch Alerts (only on urgent hits)
- Delegate Reasoning (only on delegate keywords)

### Result
Injection trimmed from ~25 lines/2357 chars → realistic 5 lines/~400 chars. Plugin dropped from 2730→2643 lines.

## Results (Apr 2026)
- Cut from 828 tokens/turn to ~468 tokens/turn (43% reduction), then further cuts
- Disabled 9 sources, kept 6 → further trimmed to keep only HIGH-signal
- 277 tips purged to 29 clean tips (all real tools, all actionable)
- research_to_distillation.py DISABLED — was auto-seeding 188+ speculative tips per cycle
- bottom_up_store() now guards against "From research:" conditions AND fake tool names
- Active injection sections (1): ACTIONABLE TIPS (only high-signal section left)
- Disabled sections (3): ITERATION LESSONS (garbage), AGI CONTEXT (noise), MEMORY HEALTH (admin data, prune runs silently)
- THREE-LAYER DEFENSE: (1) bottom_up_store rejection guards, (2) research_to_distillation disabled, (3) DB purged
- AUDIT ROUND 2 (Apr 10): Disabled 11 more noise blocks (R108, R109, R110, R121, R123, R124, R113, R112, R115, R116, R119) — stats/duplicates/low-value. Trimmed tip limits (ERL 4→2 conf≥0.6, weakest 3→2, failures 3→2). Plugin 1999→1916 lines.
- AUDIT ROUND 3 (Apr 10, R142): Killed 11 more (R106, R107, R117, R118, R113, R114, R122, R132, R134, R136, R140). Plugin 1939→1861 lines. 22 total disabled blocks, 23 active append calls.
- Audit: `cd ~/subconscious && python3 performance_audit_100.py`
- DUAL-PATH INJECTION RESOLVED: run.py L2340-2380 (gateway core) + stale compressed context. Both fixed Apr 7.
- AUDIT ROUND 4 (Apr 11): Trimmed R102-R145 + TIER2 + MYTHOS (292→77 lines). Plugin 2611→2375. BUT audit was INCOMPLETE — 10+ noise blocks from other sources still present.
- AUDIT ROUND 5 (Apr 11): Cross-plugin audit. Killed noise in TWO plugins simultaneously:
  - distillation plugin: duplicate R101 block removed, R102+ trimmed
  - evey-tool-intelligence plugin: disabled operational mastery (L878-897, generated [CROSS-SESSION], [TOP TOOLS], [HEURISTICS], [CRITICAL TOOL GUIDANCE] via experience_replay/reward_shaping/reflective_heuristic/engineering_feedback_loop modules) and distillation bridge top_down_recall (L1026-1034, generated [ACTIONABLE TIPS] which duplicated [DISTILLED TOOL RULES])
  - Final injection: ~8-12 lines / ~500-800 chars for typical task (down from 25 lines / 2357 chars)
- TIP QUALITY AUDIT: distillation_bridge.py top_down_recall() now only emits ACTIONABLE TIPS.
- AUTO-SEED FIX: Tips regenerated from hidden research_to_distillation.py even after manual purge. Must disable source AND add bottom_up_store guards before restart.

## Stale Bloat Alert vs Empty File Migration (Apr 28, 2026)

### Symptom
Agent reports "⚠ [BLOAT ALERT] MEMORY.md approaching limit: 2431/2500" but `cat ~/.hermes/memory/MEMORY.md` shows 0 bytes. The alert references files that are literally empty — the memory system migrated to SQLite (cerebrum_memory.db) long ago.

### Root Cause
The bloat alert is a **compression artifact** from a pre-migration session. When context compresses, the old warning survives in LCM (Long Context Memory) and gets injected into new sessions even though:
- MEMORY.md and USER.md are 0 bytes (empty files, no longer used)
- Actual memory lives in cerebrum_memory.db (13.4MB, 1890 tips, healthy)
- The alert references a file-based limit (2500 chars) that doesn't apply to SQLite

### Diagnostic Pattern
When you see a bloat/limit alert in a new session:
1. **Verify the files actually exist and have content**: `ls -la ~/.hermes/memory/MEMORY.md ~/.hermes/memory/USER.md`
2. **Check the real storage backend**: `sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM distilled_tips"`
3. **If files are empty but alert persists** → compression artifact, not real issue. Let it expire naturally or force a fresh session start.
4. **If files have content AND SQLite has content** → dual storage bug, migrate and purge files.
5. **Never act on a bloat alert without verifying the underlying files first.**

### Key Lesson
**Migration without context purge creates phantom alerts.** When moving from file-based memory (MEMORY.md/USER.md) to database-backed memory (cerebrum/cortex), old sessions carry the file-size warnings forward via LCM compression. The alert is "real" in the sense that it was once true, but "ghost" in that it references state that no longer exists.

## CONTEXT_CRITICAL Ghost Injection Bug (Apr 15, 2026)

### Symptom
After context compression, the agent calls `session_restore()` on every turn without the user asking. The agent says "restore to last saved checkpoint" or similar unprompted.

### Root Cause
`~/subconscious/context_health_guard.py` estimates context usage from the **session FILE SIZE on disk** (line ~70):
```python
estimated_tokens = file_size * 0.25
estimated_pct = estimated_tokens / 32000
```
After compression, the in-memory context shrinks but the session FILE keeps growing (it's the raw log). So `estimated_pct` permanently returns 1.0 ("critical") with action "force_restart".

The distillation plugin's `pre_llm_call` hook (~line 2998) checks this and injects:
```
[CONTEXT_CRITICAL: force_restart]
```
The model reads "force_restart" as a literal command → calls session_restore → ghost behavior.

### Fix
Disabled the Context Health injection block in `~/.hermes/plugins/distillation/__init__.py` (line ~2998). Context management is already handled by `context_compressor.py` which tracks actual token counts, not file sizes.

### Diagnostic Pattern for Ghost Injections
When the agent does something unprompted after compression:
1. Look for `[BRACKET:TAG]` injections from `pre_llm_call` hooks that contain imperative verbs ("force_restart", "compress_now", "exit")
2. Check if the underlying heuristic uses stale proxies (file size, DB row count) instead of live context metrics
3. The `context_compressor.py` already manages context — any secondary "health guard" that duplicates this is suspect
4. File: `grep -n 'CONTEXT_CRITICAL\|force_restart' ~/.hermes/plugins/distillation/__init__.py`
5. Source: `~/subconscious/context_health_guard.py` — the broken estimator

### Key Lesson
**Never use file-size as a proxy for in-memory context.** Session files are append-only logs. After compression the file stays large but the active context is small. This creates a permanent false-positive "critical" signal that never clears.

## Injection Pipeline Dead — End-to-End Diagnosis (Apr 15, 2026)

### Symptom
ALL tips have `access_count = 0`. Injection text appears in context but no code path ever records which tips were accessed. The pipeline writes tips but never tracks reads, so you can't measure what's actually useful.

### Root Causes Found

**Cause 1: Missing touch_node() call**
The distillation plugin's cortex injection path (line ~3116) calls `_cdb.search_text()` to retrieve tips but NEVER calls `_cdb.touch_node(tip_id)` afterwards. Tip access_count stays at 0 forever. Without this, you can't tell which tips are actually useful — mediocre tips look identical to gold tips.

**Fix**: After every `_cdb.search_text()` result that gets injected, call `_cdb.touch_node(tip_id)`. Same for any direct SQL query that pulls tips for injection.

**Cause 2: Dead domain filter**
Priority 2 injection queried `domain='agi-experience'` which had 0 active tips after domain normalization. The query returned nothing every turn — an entire injection priority was silently dead.

**Fix**: Replace dead domains with actual canonical domains. After normalization, the 13 canonical domains are: reasoning, tool_usage, coding, agent_architecture, agent_evaluation, self-improvement, meta, research, memory, training, planning, security, cost.

**Cause 3: JSON tip parsing broken**
Cortex tips are stored as JSON (`{"tip_type":"strategy","condition":"...","action":"..."}`) but the injection code was splitting them by space as if they were old `tool_name condition recommendation` tuples. This produced garbage injection text.

**Fix**: Try `json.loads(text)` first, extract condition/action fields, fall back to raw text if not JSON.

**Cause 4: 18,858 experience nodes all at default values**
Every experience node has elo=1200, confidence=0.50 — the Elo system never rated them. They're raw action logs (`action_hash`, `action_type`, `action_detail`) that get stored but never distilled into useful tips. And there's no code path to inject experiences into context.

### Diagnosis Pattern

When injected content looks wrong or tips have zero access:
1. **Check access_count**: `SELECT COUNT(*) FROM cortex_nodes WHERE node_type='tip' AND access_count > 0` — if 0, the pipeline is writing but never tracking reads
2. **Trace the full read path**: grep for `search_text\|cortex_nodes.*tip.*SELECT` in the plugin to find WHERE tips are retrieved
3. **Check touch_node is called AFTER retrieval**: if the retrieval path doesn't call touch_node, access tracking is dead
4. **Check domain filters match actual data**: `SELECT domain, COUNT(*) FROM cortex_nodes WHERE node_type='tip' GROUP BY domain` — if the plugin queries a domain with 0 tips, that path is dead
5. **Check tip text format**: `SELECT LEFT(text, 100) FROM cortex_nodes WHERE node_type='tip' LIMIT 10` — if JSON, the injection parser needs json.loads(), not space-split
6. **Check experience nodes**: `SELECT AVG(elo), AVG(confidence) FROM cortex_nodes WHERE node_type='experience'` — if elo=1200 and conf=0.50 for ALL, the rating system isn't processing them

### Key Lesson
**Writing data != Using data.** A pipeline that stores tips but never tracks which ones get injected is a pipeline you can't optimize. You need the full loop: store → retrieve → inject → track access → rate by usage. Without the tracking step, you're flying blind on quality.

## Token Bloat Audit: System Prompt + Tool Schemas (Apr 15, 2026)

### Scope: Beyond Injection
Per-turn injection is only HALF the cost story. System prompt tokens (tool schemas, memory, persona, skills list) are SENT EVERY TURN and can be prefix-cached. With providers like FriendliAI ($0.26/M cached vs $1.40/M full), reducing system prompt size has massive cost impact.

### Audit Steps

1. **Measure components** -- Tool schemas are usually the biggest (~20K tokens for 100+ tools). Memory, persona, skills list add thousands more. Use char_count/4 for rough token estimate.

2. **Disable unused plugins** -- grep for `register_tool` in each plugin to find tool-registering ones. Disable via config.yaml `plugins.disabled`. Plugins with hooks only (no register_tool) cost ZERO schema tokens.

3. **Trim context engine tools** -- Context engines register via `get_tool_schemas()`. Remove diagnostic tools (describe, status, doctor) from the return list. Saves ~600 tokens.

4. **Gate dev doc injection** -- Disable by default (saves ~5K tokens). Re-enable for coding sessions via env var.

5. **Fix repeated phrases** -- R169 had "Apply systematic critical evaluation" repeated 6x per injection. Move task-type hint to single header, strip per-module "For this X task:" prefixes, truncate lines over 80 chars.

6. **Cost-aware injection governor** -- Hard cap (1500 chars / 12 lines) with priority triage:
   P0(always): RECOVERY, ERROR_STORM, WATCH
   P1(high): TOOL ROUTING, CORE MEMORY, EPISODIC MEMORY
   P2(medium): REASONING STRUCTURE, REASONING EFFORT, KG
   P3(low): NOVELTY, METACOG, WORLD MODEL, FRONTIER TASK
   P4(cut-first): DELEGATE, CURRICULUM, EVAL-FLYWHEEL
   If injection exceeds budget, sort lines by priority tag match, keep highest until budget exhausted.

### Apr 15 Results
~14,000 tokens/session + ~116 tokens/turn saved. 7 plugins disabled (15 tools), 3 LCM tools removed, memory trimmed 23K->3K, dev docs gated, R169 deduped, governor installed.

### Pitfalls
- patch tool `path` param: use FULL expanded path, NOT tilde shorthand (fails silently)
- Tools have TWO sources: plugins (disable via config.yaml) and context engine (trim in engine source)
- Always clear __pycache__ after plugin changes, always syntax-check with ast.parse()
