---
name: distillation-quality-debug
description: Diagnose and fix noise in the distillation pipeline — when tips contain speed reports, arg patterns, or raw output instead of actionable behavioral rules.
version: 1.0
category: meta
triggers:
  - Distilled tips contain "FAST:", "args_pattern:", or "[tool_name]" prefixes
  - Noise ratio above 10% in distilled_tips table
  - epoch_synthesis producing speed statistics instead of behavioral rules
  - Controller cron re-inserting previously purged noise tips
---

# Distillation Quality Debug Skill

## CRITICAL: Plugin Hook Injection Paths (discovered Apr 2026)

Hermes has TWO hook types for context injection, but only ONE actually works:

- **`pre_tool_call`** — called in `model_tools.py:500` via `invoke_hook()`, but the **return value is DISCARDED** (line 500: bare call, no capture). Do NOT use for context injection.
- **`pre_llm_call`** — called in `run_agent.py:6962`, return values ARE captured and injected into the user message. Use this for TOP-DOWN context injection.

Both hooks return `List[Any]` from `invoke_hook()`, but only `pre_llm_call` results are actually appended to the agent's turn context (run_agent.py:6971-6978).

**Pattern for TOP-DOWN plugin injection:**
```python
def _on_pre_llm_call(session_id="", user_message="", conversation_history=None,
                      is_first_turn=False, model="", platform="", **kwargs) -> str:
    # Return a string — it gets injected into the user message
    return "[TOOL GUIDANCE]\n  tool_name: rule text here"

def register(ctx):
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)  # NOT pre_tool_call!
```

**plugin.yaml must declare the correct hook:**
```yaml
provides_hooks:
  - pre_llm_call  # NOT pre_tool_call
```

## Feedback Loop Pattern

The missing link between "brain growing, hands failing" is outcome-based tip confidence updates:

```python
def _update_tip_confidence(tool_name: str, status: str) -> None:
    """Called from post_tool_call. Success boosts +0.005, failure dampens -0.002."""
    # Update distilled_tips SET confidence = confidence +/- delta WHERE tool_name = ?
```

Wire this into `post_tool_call` so tips that correlate with success get stronger over time.

When the distillation pipeline produces low-quality tips (speed reports, arg key patterns, raw JSON) instead of actionable behavioral rules, use this diagnostic and fix pipeline.

## Quick Diagnosis

```sql
-- Check noise ratio
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN recommendation LIKE '%FAST:%' OR recommendation LIKE '%args_pattern%' 
      OR recommendation LIKE '[%' OR recommendation LIKE '%rich_output%' THEN 1 ELSE 0 END) as noise,
  ROUND(100.0 * SUM(CASE WHEN recommendation LIKE '%FAST:%' OR recommendation LIKE '%args_pattern%' 
      OR recommendation LIKE '[%' OR recommendation LIKE '%rich_output%' THEN 1 ELSE 0 END) / COUNT(*), 1) as noise_pct
FROM distilled_tips;

-- Show noise entries
SELECT id, tip_type, condition, substr(recommendation, 1, 100) FROM distilled_tips
WHERE recommendation LIKE '%FAST:%' OR recommendation LIKE '%args_pattern%' 
   OR recommendation LIKE '[%' OR recommendation LIKE '%rich_output%';
```

## Root Causes

### 1. Extraction captures arg KEY NAMES instead of task intent
The heuristic extractor looks at `args.keys()` instead of `args.values()`. Fix: use `_extract_task_intent()` that reads actual arg values to determine WHAT the tool was doing.

### 2. Iteration engine lesson field contains noise
The lesson field passes through raw output like "FAST: 489ms vs 10342ms" from the old iteration engine. Fix: `_is_noise_lesson()` filter returns True for any lesson containing FAST:, args_pattern, rich_output, or starting with [.

### 3. epoch_synthesis concatenates speed patterns as "principles"
The synthesis function just groups tips by tool and concatenates. Fix: categorize errors by root cause (403 forbidden, JSON parse, module import, path error, connection refused) and build behavioral rules.

## The Critical Fix Sequence

After patching extraction code, you MUST do all three of these or noise will recur:

### Step 1: Kill stale processes + clear bytecode cache
```bash
pkill -9 -f "controller.py"
pkill -9 -f "distillation"
find ~/subconscious/__pycache__ -name "distillation_bridge*" -exec rm {} \;
find ~/hermes-agent/plugins/distillation/__pycache__ -name "*.pyc" -exec rm {} \;
```
**WHY**: Running processes have the OLD module cached in memory. They will keep inserting noise using the old extraction logic regardless of your code patches. **pkill -9** is required (SIGTERM may not stop a busy loop). __pycache__ must be cleared because Python can load stale .pyc files that predate your patches. Each cron run is a fresh process, so killing alone isn't enough — the .pyc cache can persist.

### Step 2: Clear the JSONL buffer
```bash
> ~/subconscious/distillation_buffer.jsonl
```
**WHY**: The controller reprocesses buffer entries each cycle. Old entries contain noise lessons that will be re-inserted even with the new extraction code (the old process bypasses it).

### Step 3: Purge DB noise
```sql
DELETE FROM distilled_tips WHERE 
  recommendation LIKE '[%' 
  OR recommendation LIKE '%args_pattern%' 
  OR recommendation LIKE '%FAST%' 
  OR recommendation LIKE '%rich_output%'
  OR recommendation LIKE '%approach was%faster%'
  OR recommendation LIKE '{%';
DELETE FROM meta_insights WHERE 1=1;
```

### Step 4: Add DB-level noise guard
In `bottom_up_store()` in distillation_bridge.py, add a final guard BEFORE the INSERT:
```python
if recommendation and (
    recommendation.startswith("[")
    or "args_pattern" in recommendation
    or "FAST:" in recommendation
    or "rich_output" in recommendation
):
    return  # Noise tip — discard
```
This is the belt+suspenders approach — even if a stale process somehow gets through, the DB insertion rejects noise.

## Validation: 100-Cycle Quality Gates

Run `python3 ~/subconscious/distillation_100.py` and verify:

1. **Noise ratio < 10%** — should be 0% after cleanup
2. **Actionable ratio > 80%** — tips have IF/THEN structure with real advice
3. **Meta-insights zero noise** — no FAST/args_pattern in synthesized insights
4. **Recall relevance > 60%** — top_down_recall returns tips matching the task context

## Quality Heuristics for Good Tips

A good tip has:
- **Condition**: "When {doing specific thing} with {tool}" — derived from arg VALUES
- **Recommendation**: Concrete action to take — not "was fast" or "has args X,Y"
- **Tip type**: recovery (errors), strategy (approach), or optimization (performance)

Bad tip patterns (should be filtered):
- `[tool_name] FAST: 400ms vs 1200ms avg` — speed report
- `args_pattern: command,timeout` — arg key listing
- `[tool_name] {"content": "..."}` — raw JSON output
- `rich_output: 1722 chars` — output size report

## Verifying Plugin Hook Registration (Critical Check)

A plugin can have files in the right place and still be non-functional. The #1 diagnostic question is: "Are the hooks actually registered?"

### Step 1: Check gateway logs for plugin discovery
```bash
grep "plugin discovery\|Plugin.*load\|register" ~/.hermes/logs/gateway.log | tail -20
```
Look for: "Plugin discovery complete: N found, N enabled" — your plugin should be in the count.

### Step 2: Check for hook registration confirmation OR errors
```bash
grep -i "distillation\|Failed to load plugin" ~/.hermes/logs/gateway.log | tail -10
```
If no error AND no success message, the plugin loaded silently. This is OK if the register() function doesn't crash.

### Step 3: Check DB for evidence the hook is firing
```sql
-- Bottom-up evidence: recent call_log entries
SELECT COUNT(*) FROM call_log;
SELECT MAX(timestamp) FROM call_log;
-- If recent timestamp matches current time, post_tool_call hook is live
```

### Step 4: Test register() in isolation
```bash
cd ~/.hermes/plugins/distillation && python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('test', '__init__.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class FakeCtx:
    def register_hook(self, name, cb):
        print(f'Hook registered: {name} -> {cb.__name__}')
mod.register(FakeCtx())
"
```

### The "function exists but not wired" antipattern
The top_down_recall() function existed in distillation_bridge.py but was never called because the plugin only registered post_tool_call. When adding a new pipeline direction, you MUST also wire it into the plugin's register() function. A function without a hook registration is dead code.

## Comprehensive Cortex Audit Methodology (7-Audit Protocol, Apr 2026)

Run this when the cortex needs a full tune-up — not just tip noise, but DB health, injection efficiency, and structural issues.

### Audit 1: Tip Quality
```sql
SELECT tip_type, COUNT(*), ROUND(AVG(confidence),3), ROUND(AVG(upvotes),1), ROUND(AVG(downvotes),1)
FROM distilled_tips GROUP BY tip_type ORDER BY COUNT(*) DESC;
-- Check: noise markers, exact duplicates, dead tips (freq>50, upvotes<5), low confidence
```

### Audit 2: Orphan Detection
Count modules in ~/subconscious/ vs modules wired in plugin via `from X import get_instance`. Orphans = written but not wired. Also check for modules without `build_injection` — these are infrastructure, not injection modules.

### Audit 3: Injection Keyword Redundancy
Parse each module's keyword list from `build_injection`. Build a keyword-to-modules map. Keywords shared by 2+ modules will compete for injection slots. The 1500-char / 12-line governor prevents flood, but high overlap means some modules never inject.

### Audit 4: Injection Overhead
Count total modules with build_injection. Estimate: ~1-2ms per turn for 100+ module import checks (negligible). Token cost: ~114 tokens/turn for 3 matching modules (~$0.02/day on FriendliAI). The CPU cost is negligible; the TOKEN cost is what matters.

### Audit 5: DB Bloat
Check table row counts, identify bloat candidates (perspective_diversity, token_usage, empty tables). Run VACUUM after cleanup. Add indexes on frequently queried columns in tables with >100 rows and 0 custom indexes.

### Audit 6: 3-Database Sync
**CRITICAL**: Compare tool_stats total_calls vs call_log COUNT(*) per tool. If tool_stats shows >2x call_log counts, there's phantom inflation (old classifier bug). Resync from call_log (ground truth), then update mastery_scores from corrected tool_stats.

```python
# Resync script pattern
cap.execute("""
    UPDATE tool_stats SET 
      total_calls = (SELECT COUNT(*) FROM call_log cl WHERE cl.tool_name = tool_stats.tool_name),
      successes = (SELECT COUNT(*) FROM call_log cl WHERE cl.tool_name = tool_stats.tool_name AND cl.result_status = 'success'),
      failures = (SELECT COUNT(*) FROM call_log cl WHERE cl.tool_name = tool_stats.tool_name AND cl.result_status IN ('failure', 'partial'))
""")
# Then sync mastery from tool_stats
for tool, total, wins in stats:
    rate = wins / total
    level = 'mastered' if rate >= 0.95 else 'proficient' if rate >= 0.8 else 'intermediate' if rate >= 0.6 else 'novice' if rate >= 0.4 else 'critical'
```

### Audit 7: Critical Tools
Find tools with <50% success rate and 5+ calls. Check if they have distilled tips. If tips exist but tool is still failing, the tips aren't actionable enough — not a distillation problem but a tool-specific issue.

### Fix Sequence (always run in this order)
1. 3-DB sync (tool_stats from call_log, mastery from tool_stats)
2. tip_elo seeding from confidence (if avg elo is approximately 1200)
3. Bloat purge (perspective_diversity, dead tips, duplicate tips)
4. Drop dead empty tables (no rows + no write paths)
5. Add missing indexes
6. VACUUM
7. Restart gateway

### Key DB Paths
- `~/.hermes/cerebrum_memory.db` — tips, mastery, knowledge graph, predictions
- `~/subconscious/tool_capability.db` — tool_stats (aggregate), call_log (ground truth), tool_recipes
- `~/subconscious/api_analytics.db` — API call tracking, model_daily
- `~/subconscious/skill_rewards.db` — skill rewards, injection stats
- Always run `PRAGMA table_info(table)` before querying unfamiliar tables

## Key Files
- Extraction + synthesis: ~/subconscious/distillation_bridge.py
- Controller cron: ~/subconscious/controller.py
- 100-cycle validator: ~/subconscious/distillation_100.py
- Live hook plugin: ~/.hermes/plugins/distillation/__init__.py (ALSO keep in sync with ~/hermes-agent/plugins/distillation/__init__.py)
- DB: ~/.hermes/cerebrum_memory.db (tables: distilled_tips, meta_insights)
- Tool stats DB: ~/subconscious/tool_capability.db (tables: tool_stats, call_log)

## Engineering Audit: "Brain Growing, Hands Failing"

When tips are clean but success rates don't improve, the problem is NOT in the distillation pipeline itself — it's in the **feedback gap** between learning and execution.

### The 4 Root Causes (discovered Apr 6, 2026)

**ROOT CAUSE 1: Noise pollution in the experiences table**
- The `experiences` table in cerebrum_memory.db stores "lessons" that get recalled as "ITERATION LESSONS" every turn
- ~21% of these lessons were noise (raw tool output, arg patterns, speed reports)
- Agent recalls noise disguised as learning → pollutes decision context
- **Fix**: `DELETE FROM experiences WHERE lesson LIKE '%args_pattern%' OR lesson LIKE '%FAST:%' OR lesson LIKE '%rich_output%'`
- Noise detection function: check for markers ['args_pattern:', 'rich_output:', 'FAST:', 'approach was', '{"status":']

**ROOT CAUSE 2: Tips exist but aren't applied**
- terminal has 7 tips but 27.7% success across 6,061 calls — tips don't change behavior
- The distillation plugin fires post_tool_call (stores tips) and pre_tool_call (retrieves tips)
- BUT the pre_tool_call hook caches tips in a module variable that NEVER gets injected into agent context
- Tips are "retrieved" but sit in a Python variable — the agent never sees them at decision time
- **Fix needed**: Wire `_tip_cache` into the actual context injection path (e.g., write to a file that the session prompt reads)

**ROOT CAUSE 3: Mastery scores detached from reality**
- cerebrum mastery_scores and tool_capability.db tool_stats are completely separate systems
- Example: browser_navigate claimed 100% mastery but real rate was 38%
- Example: delegate_with_model claimed 100% but real rate was 0%
- Agent "thinks" it's better than it is → doesn't apply caution where needed
- **Fix**: Sync mastery scores from tool_capability.db (the source of truth):
  ```python
  real_rate = successes / total_calls  # from tool_capability.db
  new_level = 'mastered' if real_rate > 0.8 else 'proficient' if real_rate > 0.6 else 'novice'
  UPDATE mastery_scores SET level=?, confidence=?, call_count=?, success_count=? WHERE tool_name=?
  ```

**ROOT CAUSE 4: No outcome feedback loop** — FIXED (Apr 6, 2026)
- The `_update_tip_confidence()` function in `~/.hermes/plugins/distillation/__init__.py` now runs on every post_tool_call
- Asymmetric update: success boosts +0.005, failure dampens -0.002 (slow growth, slow decay)
- Tips that work gradually rise in confidence; tips that don't sink below 0.3 and get filtered
- The `_on_pre_tool_call()` hook returns a `[TOOL GUIDANCE: tool_name]` string with top 3 tips (confidence >= 0.3) via direct SQL — no LLM cost
- The feedback loop is non-critical: wrapped in try/except so it never breaks the main hook
- **Implementation in ~/.hermes/plugins/distillation/__init__.py**:
  ```python
  def _update_tip_confidence(tool_name, status):
      tips = db.execute("SELECT id, confidence FROM distilled_tips WHERE tool_name=?", (tool_name,)).fetchall()
      for tip_id, conf in tips:
          if status == "success":
              new_conf = min(conf + 0.005, 1.0)
              db.execute("UPDATE distilled_tips SET confidence=?, upvotes=upvotes+1 WHERE id=?", (new_conf, tip_id))
          elif status == "error":
              new_conf = max(conf - 0.002, 0.1)
              db.execute("UPDATE distilled_tips SET confidence=?, downvotes=downvotes+1 WHERE id=?", (new_conf, tip_id))
  ```

### Engineering Audit Script
`~/subconscious/engineering_audit_v3.py` — 4-phase audit (25 cycles each):
1. **Diagnose**: Measure noise in experiences, tips, mastery mismatches, tips-vs-reality gap
2. **Fix**: Purge noise, sync mastery, clear noisy last_lessons from tool_capability.db
3. **Generate**: Create missing actionable tips for low-success tools (terminal, execute_code, read_file, etc.)
4. **Validate**: Re-measure everything, run 5 quality gates

### Feedback Loop Script
`~/subconscious/engineering_feedback_loop.py` — Functions for closing the learning→execution gap:
- `get_tips_for_tool(tool_name)` — Get highest-confidence tips before a call
- `update_tip_outcome(tool_name, success)` — Update confidence after a call
- `generate_pre_call_context(tool_name)` — Build actionable guidance string
- `generate_critical_tools_context()` — Session-start context for worst-performing tools

### Condition-Aware Voting (discovered Apr 7, 2026)

**The dead-tip root cause**: The original `_update_tip_confidence()` voted on ALL tips for a tool on every call, regardless of whether the tip's condition matched the call context. Result: 78% of tips accumulated votes from unrelated calls → noisy confidence scores → tips never distinguished signal from noise.

**Fix**: 3-tier condition matching before voting:

```python
def _update_tip_confidence(tool_name: str, status: str, args: dict = None):
    """Only vote on tips whose condition matches the current call context."""
    if args is None:
        args = {}
    
    tips = db.execute(
        "SELECT id, confidence, condition FROM distilled_tips WHERE tool_name=?",
        (tool_name,)
    ).fetchall()
    
    for tip_id, conf, condition in tips:
        # 3-tier condition matching
        if not _condition_matches(condition, status, args):
            continue  # Skip — this tip isn't relevant to this call
        
        if status == "success":
            new_conf = min(conf + 0.005, 1.0)
            db.execute("UPDATE distilled_tips SET confidence=?, upvotes=upvotes+1 WHERE id=?",
                       (new_conf, tip_id))
        elif status == "error":
            new_conf = max(conf - 0.002, 0.1)
            db.execute("UPDATE distilled_tips SET confidence=?, downvotes=downvotes+1 WHERE id=?",
                       (new_conf, tip_id))

def _condition_matches(condition: str, status: str, args: dict) -> bool:
    """3-tier condition matching: generic, error-only, keyword."""
    cond_lower = condition.lower().strip()
    
    # Tier 1: Generic conditions — always match
    generic_markers = ["when using", "when calling", "general", "default", "always"]
    if any(m in cond_lower for m in generic_markers):
        return True
    
    # Tier 2: Error-only conditions — only match on errors
    error_markers = ["error", "fail", "exception", "timeout", "crash", "when .* fails"]
    if any(m in cond_lower for m in error_markers):
        return status == "error"
    
    # Tier 3: Keyword matching — check if condition keywords appear in args
    # Extract key nouns from condition and check against stringified args
    args_str = str(args).lower()
    cond_words = [w for w in cond_lower.split() if len(w) > 4 and w not in 
                  ("when", "with", "from", "that", "this", "which", "where")]
    if any(w in args_str for w in cond_words):
        return True
    
    return False  # No match — don't vote on this tip
```

**Call site**: The `post_tool_call` hook must pass `args` dict to `_update_tip_confidence()`. Without args, keyword matching (Tier 3) can't work.

### Tip Consolidation Diagnostic

When tip engagement is low (many tips with near-initial votes):

1. **Check engagement rate**: `SELECT COUNT(*) FROM distilled_tips WHERE upvotes > 5 OR downvotes > 2` — healthy is >45%
2. **Find dead tips**: Tips with frequency > 100 but upvotes < 10 = never match conditions
3. **Identify non-tool tips**: Tips with `tip_type` like "reasoning" or "meta" that aren't for a real tool
4. **Merge exact-duplicate conditions**: `SELECT tool_name, condition, COUNT(*) FROM distilled_tips GROUP BY tool_name, condition HAVING COUNT(*) > 1`
5. **Take snapshot before changes**: Save current state to JSON for pre/post comparison

**Consolidation tools** (in `~/subconscious/`):
- `tip_health_monitor.py` — Measures engagement rate, dead tip ratio, per-tool health
- `tip_condition_rewriter.py` — Rewrites generic conditions to specific ones for better matching
- `tip_feedback_validator.py` — Takes snapshots, compares pre/post, validates predictions

**Target**: 30-50 high-quality tips with >50% engagement rate. More tips ≠ better — noise drowns signal.

### Key Cross-Database Queries
The audit requires reading from BOTH databases:
- `~/.hermes/cerebrum_memory.db`: experiences, distilled_tips, mastery_scores
- `~/subconscious/tool_capability.db`: tool_stats (total_calls, successes, failures), call_log

The agent_scorecard.py `score_error_recovery()` was reading from cerebrum tool_stats (wrong schema, returned 0 calls, 0% success) instead of tool_capability.db (real data: 12,876 calls, 50.5% success). Always use tool_capability.db for real success rates.

### Real Failure Data (corrected Apr 6, 2026 after 3-DB sync)
- terminal: 77.8% success (464 calls in call_log) — was falsely reported as 28.8% due to tool_stats drift
- read_file: 52.2% success (92 calls) — weakest tool after sync
- web_extract: 67.3% success (159 calls)
- web_research: 74.8% success (103 calls)
- execute_code: 77.2% success (158 calls)
- patch: 100% success (31 calls)
- Overall: clean and accurate after sync

## The 3-Database Discrepancy Problem (discovered Apr 6, 2026)

Hermes tracks tool performance in THREE separate databases that can drift wildly:

1. **`~/subconscious/tool_capability.db` → `tool_stats`** (aggregate table, 1 row per tool)
2. **`~/subconscious/tool_capability.db` → `call_log`** (row-level, 1 row per call — GROUND TRUTH)
3. **`~/.hermes/cerebrum_memory.db` → `mastery_scores`** (cerebrum's own tracking)

Before sync, these showed terminal at 28.8%, 77.2%, and 22.1% respectively — a 55pp range. The `pre_llm_call` hook reads from `tool_stats`, so it was injecting WRONG weakness signals.

### Why tool_stats drifts from call_log

`tool_stats` has been accumulating since day 1. The `bottom_up_store` in distillation_bridge.py writes to `call_log` but does NOT reliably update `tool_stats`. Additionally, "partial" status calls (successful execution with truncated output or stderr) were counted as failures in tool_stats but may be successes.

### The fix: sync tool_stats from call_log (ground truth)

```python
import sqlite3
from pathlib import Path

TOOL_CAP = str(Path.home() / "subconscious" / "tool_capability.db")
CEREBRUM = str(Path.home() / ".hermes" / "cerebrum_memory.db")

cap = sqlite3.connect(TOOL_CAP, timeout=5)
cap.execute("""
    UPDATE tool_stats SET 
      total_calls = (SELECT COUNT(*) FROM call_log cl WHERE cl.tool_name = tool_stats.tool_name),
      successes = (SELECT COUNT(*) FROM call_log cl WHERE cl.tool_name = tool_stats.tool_name AND cl.result_status = 'success'),
      failures = (SELECT COUNT(*) FROM call_log cl WHERE cl.tool_name = tool_stats.tool_name AND cl.result_status IN ('failure', 'partial'))
    WHERE tool_name IN (SELECT DISTINCT tool_name FROM call_log)
""")
cap.commit()

# Also sync cerebrum mastery_scores
cer = sqlite3.connect(CEREBRUM, timeout=5)
stats = cap.execute("SELECT tool_name, total_calls, successes FROM tool_stats WHERE total_calls >= 5").fetchall()
for tool, total, wins in stats:
    rate = wins / total
    level = 'mastered' if rate >= 0.95 else 'proficient' if rate >= 0.8 else 'intermediate' if rate >= 0.6 else 'novice' if rate >= 0.4 else 'critical'
    cer.execute("UPDATE mastery_scores SET call_count=?, success_count=?, confidence=?, level=? WHERE tool_name=?",
                (total, wins, rate, level, tool))
cer.commit()
```

### 100-Cycle Performance Audit Script

`~/subconscious/performance_audit_100.py` — 6-phase audit (96.8% score after fixes):
1. **BOTTOM-UP**: Hook registration, tip storage, call_log entries
2. **TOP-DOWN**: Plugin registration, gateway injection, hook output test
3. **FEEDBACK LOOP**: Confidence boost/dampen simulation
4. **DATA INTEGRITY**: Corruption, duplicates, echo patterns, noise ratio
5. **TERMINAL DEEP DIVE**: 3-database comparison, failure categorization
6. **INJECTION VERIFICATION**: Direct plugin function test, post_tool_call test
# Quick Fix
Run the audit: `cd ~/subconscious && python3 performance_audit_100.py`

# CRITICAL: 3-Database Sync
There are 3 sources of tool performance data that MUST stay aligned:
1. cerebrum_memory.db mastery_scores (confidence, call_count, success_count)
2. subconscious/tool_capability.db tool_stats (total_calls, successes, failures)
3. subconscious/tool_capability.db call_log (per-call records)

The plugin's `_sync_tool_capability()` writes to both call_log AND tool_stats on every post_tool_call.
If they drift, run: `cd ~/subconscious && python3 performance_audit_100.py` to diagnose.
Manual sync: UPDATE tool_stats from call_log aggregate, then UPDATE mastery_scores from tool_stats.

### Classification Feedback Loop (discovered Apr 6, 2026)

A subtle but devastating bug: `_classify_result()` in evey-tool-intelligence plugin was doing text-based pattern matching BEFORE JSON parsing. When the agent's injected context mentioned errors (from RECENT FAILURES section), those error words appeared in execute_code output, which got classified as "failure", which added MORE errors to RECENT FAILURES, which got injected next turn, creating an amplifying feedback loop.

**Symptoms:**
- execute_code showing as "RECENT FAILURE" when its output clearly says `"status": "success"`
- Tool success rates drifting downward over time without actual failures
- RECENT FAILURES section listing results that weren't failures

**Root cause:** Old classifier checked for `"error":` and `"error"` as failure signals — but JSON output legitimately contains `"error": null` (success) and the RECENT FAILURES injection contains error descriptions that match these patterns.

**Fix:** JSON-first classification — parse the JSON, check `status`, `success`, `exit_code` fields first, only fall back to text pattern matching for non-JSON results:
```python
def _classify_result(result_str, tool_name="", args=None):
    # JSON-FIRST: Check structured fields before text patterns
    try:
        parsed = json.loads(result_str)
        if isinstance(parsed, dict):
            if parsed.get("error") and parsed.get("error") is not None:
                return "failure"  # explicit error, not null
            if parsed.get("status") == "success":
                return "success"
            if parsed.get("status") == "error":
                return "failure"
            ec = parsed.get("exit_code")
            if ec == 0: return "success"
            if ec is not None and ec != 0: return "failure"
            if parsed.get("output") or parsed.get("content"):
                return "success"  # has output without error = success
    except (json.JSONDecodeError, TypeError):
        pass
    # FALLBACK: text patterns only for non-JSON results
    ...
```

**After fixing classifier, recalculate tool_stats from call_log:**
```sql
UPDATE tool_stats SET
    successes = (SELECT COUNT(*) FROM call_log WHERE tool_name = tool_stats.tool_name AND result_status IN ('success','partial')),
    total_calls = (SELECT COUNT(*) FROM call_log WHERE tool_name = tool_stats.tool_name),
    confidence = ROUND(successes * 1.0 / total_calls, 2);
```

### Injection Bloat Reduction (Apr 6, 2026)

Multiple injection sections provided zero additional signal but consumed tokens every turn:
- **META-INSIGHTS**: Just tips reorganized by "Principles/Procedures" — same distilled_tips data, different grouping. Killed.
- **CEREBRUM FACTS**: Semantic facts injected proactively — caused memory echo bug. Facts available via knowledge_search when needed. Killed.
- **Stale iteration lessons**: Lessons with frequency >100 are noise, not learning. Purge: `DELETE FROM experiences WHERE frequency > 100 AND lesson IS NOT NULL`
- **Inflated tips**: Tips with upvotes/frequency ratio >10 were never validated. Purge: `DELETE FROM distilled_tips WHERE (upvotes * 1.0 / frequency) > 10 AND frequency < 5`
- **Raw output "lessons"**: Experiences table stores tool output as lessons. Purge: `DELETE FROM experiences WHERE lesson LIKE '%RECURRING FAILURE:%{"output":%' AND lesson NOT LIKE '%Avoid%'`

Result: injection trimmed from ~625 tokens/turn to ~250 tokens/turn (60% reduction).

### Remaining known issue

The bridge does NOT update `tool_stats` aggregate table on each call — only writes to `call_log`. This means tool_stats will drift again over time. Fix options:
- (A) Have the bridge update tool_stats on each call (slower but always accurate)
- (B) Run periodic sync from cron (fast but delayed)
- (C) Make pre_llm_call read from call_log directly instead of tool_stats (accurate but slower query)

### Duplicate Optimization Tips from Dedup Bypass (discovered Apr 12, 2026)

### Symptom
`optimization` tip type shows 894 tips at avg confidence 0.503 (barely above threshold), with meta-loop reporting 1% survival rate. Most tips are exact duplicates.

### Root Cause
`find_similar_tip()` in `distillation_bridge.py` had `LIMIT 200` on the dedup query. With 1500+ tips in the DB, the function only compared against 200 rows — missing most existing tips. This caused the same optimization tip (e.g., "Pre-split the work: paginate results, reduce output size, or cache for reuse.") to be inserted **395 times** at confidence 0.50.

### Diagnosis SQL
```sql
-- Find exact duplicate recommendations
SELECT recommendation, COUNT(*) as cnt 
FROM distilled_tips 
WHERE tip_type = 'optimization' 
GROUP BY recommendation 
HAVING cnt > 1 
ORDER BY cnt DESC;

-- Count per type with avg confidence
SELECT tip_type, COUNT(*), ROUND(AVG(confidence),3)
FROM distilled_tips GROUP BY tip_type ORDER BY COUNT(*) DESC;
```

### Fix
1. **Patch dedup LIMIT**: In `distillation_bridge.py` `find_similar_tip()`, increase `LIMIT 200` to `LIMIT 1000` (or higher). The function does in-memory keyword matching, so 1000 rows is still fast.
2. **Purge existing duplicates**: Keep one copy per unique recommendation, delete the rest:
```python
dupes = db.execute(
    "SELECT recommendation, COUNT(*) as cnt FROM distilled_tips "
    "WHERE tip_type = 'optimization' GROUP BY recommendation HAVING cnt > 1"
).fetchall()
for rec, cnt in dupes:
    keep = db.execute("SELECT id FROM distilled_tips WHERE recommendation = ? LIMIT 1", (rec,)).fetchone()[0]
    db.execute("DELETE FROM distilled_tips WHERE recommendation = ? AND id != ?", (rec, keep))
db.commit()
```
3. **Result**: 894 optimization tips at 0.503 → 9 tips at 0.767 after cleanup. Total tips dropped from ~2500 to 1586 (96.8% high-confidence).

### Prevention
Consider adding a UNIQUE index or pre-INSERT check on `recommendation` text to prevent exact duplicates at the DB level:
```sql
-- Soft prevention: check before insert
SELECT COUNT(*) FROM distilled_tips WHERE recommendation = ?;
```

### Generic Template Recovery Tips (discovered Apr 8, 2026)

### Symptom
`recovery` tip type shows unusually low survival rate (32%) compared to all other types (94-100%).

### Root Cause
The generic error fallback in `distillation_bridge.py` (the "When {tool} encounters errors during: {intent}" → "Check error message for root cause. Common fix: verify inputs, check permissions, retry with backoff." path) produces identical low-value tips for every tool error. These accumulate as noise — 45 identical tips across terminal, execute_code, web_research, etc.

### Diagnosis SQL
```sql
SELECT tip_type, COUNT(*), ROUND(AVG(confidence),2),
  SUM(CASE WHEN recommendation LIKE '%verify inputs, check permissions%' THEN 1 ELSE 0 END) as generic_count
FROM distilled_tips GROUP BY tip_type ORDER BY generic_count DESC;
```

### Fix
1. **Purge existing junk**: `DELETE FROM distilled_tips WHERE tip_type='recovery' AND confidence=0.5 AND recommendation LIKE '%verify inputs, check permissions%'`
2. **Patch the fallback**: In `distillation_bridge.py`, the generic error handler should `return None` instead of producing a template tip. Better to produce nothing than generic advice.

### Prevention
Add to the DB-level noise guard in `bottom_up_store()`:
```python
if "verify inputs, check permissions, retry with backoff" in recommendation:
    return  # Template tip — discard
```

### Adversarial Tip Validation (May 9, 2026)

**The problem:** Tips are generated but never stress-tested. Bad tips can persist indefinitely.

**The fix:** Red-team each tip using the LLM judge before promotion.

```python
def _adversarial_validate_tip(tip_text: str, tip_condition: str, tip_recommendation: str) -> dict:
    """Find cases where this tip fails or causes harm."""
    messages = [
        {"role": "system", "content": "You are a precise adversarial tester. Return only valid JSON."},
        {"role": "user", "content": f"""Find 3 scenarios where this tip would FAIL:
Tip: "{tip_text}"
Rate robustness 0-10. Return JSON: {{"robustness": 0-10, "failure_modes": [...], "verdict": "keep|revise|reject"}}"""}
    ]
    response = judge._call_llm(messages)
    return json.loads(response)
```

**Wiring:** Call `_adversarial_validate_tip()` in the graduator before promoting tips from `pending` to `active`.

### Tip Survival Rate Tracking (May 9, 2026)

**The problem:** No systematic quality filter for tips. Tips with <30% survival across types indicate extraction criteria are too speculative.

**The fix:** Track opportunities vs applications per tip.

```sql
-- Create tracking table
CREATE TABLE tip_survival (
    tip_id INTEGER PRIMARY KEY,
    opportunities INTEGER DEFAULT 0,
    applications INTEGER DEFAULT 0,
    survival_rate REAL DEFAULT 0.0,
    last_opportunity REAL DEFAULT 0
);

-- On every tool call, count opportunity for relevant tips
UPDATE tip_survival SET opportunities = opportunities + 1 
WHERE tip_id IN (SELECT id FROM distilled_tips WHERE tool_name = ? OR tool_name = '');

-- Auto-prune tips with <30% survival after 100 opportunities
DELETE FROM distilled_tips WHERE id IN (
    SELECT tip_id FROM tip_survival 
    WHERE opportunities > 100 AND survival_rate < 0.3
);
```

**Key insight:** Tips with <30% survival across types (debugging, memory, recovery, strategy) indicate the extraction criteria are too speculative — tighten to only extract tips grounded in 3+ successful applications.

### Training Data Export for Model Fine-Tuning (May 9, 2026)

**The pattern:** Convert the entire cognitive apparatus into structured training data for model fine-tuning.

```python
# Export high-quality tips with Elo ratings
SELECT t.id, t.tip_type, t.condition, t.recommendation, t.rationale, 
       t.tool_name, t.domain, t.confidence, e.elo, e.matches
FROM distilled_tips t
LEFT JOIN tip_elo e ON t.id = e.tip_id
WHERE t.confidence >= 0.7

# Export tool call patterns with outcomes
SELECT tool_name, success, duration_ms, tokens_in, tokens_out, 
       error_type, context, timestamp
FROM tool_calls
ORDER BY timestamp DESC

# Generate curriculum by Elo difficulty
sorted_tips = sorted(tips, key=lambda x: x["elo"], reverse=True)
curriculum = {
    "easy": [t for t in sorted_tips if t["elo"] < 1600][:100],
    "medium": [t for t in sorted_tips if 1600 <= t["elo"] < 1800][:100],
    "hard": [t for t in sorted_tips if 1800 <= t["elo"] < 2000][:100],
    "expert": [t for t in sorted_tips if t["elo"] >= 2000][:100]
}
```

**Output format:** JSONL files for tips corpus, tool patterns, reasoning traces, and curriculum JSON with 4 difficulty levels.

**Use case:** Feed into Qwen 27B fine-tuning on DGX Spark to train the model on the agent's own distilled behavioral patterns.

## Pitfalls
- Controller cron has module cached in memory — code patches don't take effect until process restart
- JSONL buffer entries get reprocessed — must clear after purges
- The 100-cycle test creates tips from simulated outcomes — these can add noise if the test's lesson strings contain noise patterns
- After any code change to distillation_bridge.py, kill the controller AND clear the buffer
- **The controller-hourly cron job** (not just the controller process) is the primary noise reinsertion vector — it runs `cd ~/subconscious && python3 controller.py` hourly, importing the module fresh each time. If you patched the file but didn't clear __pycache__, the cron may still load stale bytecode.
- **Belt+suspenders is mandatory**: The noise guard must exist at BOTH the extraction level (extract_tip_heuristic returning None) AND the DB INSERT level (final check before INSERT). Reason: you cannot guarantee all calling processes have the updated extraction code.
- **Don't trust a single purge round**: Noise tips reappear across multiple rounds because (1) the AGI continuous loop cron makes tool calls that write to the buffer, (2) the controller processes them, (3) the noise gets inserted again. You must kill ALL processes, clear ALL caches, clear the buffer, purge the DB, AND verify with a fresh `python3 distillation_100.py` run.
- **Verify the loaded module actually has your patch**: Use `inspect.getsource(mod.bottom_up_store)` to confirm the running code matches the file on disk. __pycache__ can silently serve stale code.
- **"Function exists" ≠ "function is wired"**: top_down_recall() was in distillation_bridge.py but the plugin only registered post_tool_call. After writing any new pipeline function, you MUST also add it to the plugin's register() function AND copy the updated __init__.py to both ~/.hermes/plugins/distillation/ and ~/hermes-agent/plugins/distillation/. A gateway restart is needed for the new hook to take effect.
- **Plugin file locations**: The running gateway loads from ~/.hermes/plugins/ (NOT ~/hermes-agent/plugins/). Keep both in sync — the repo copy is for version control, the ~/.hermes copy is what actually runs.
- **SQLite dict() unpacking gotcha**: `dict(cursor.fetchall())` only works for 2-column queries (key, value). For 3+ columns, iterate rows directly: `for col1, col2, col3 in rows:` instead of `for key, (v1, v2) in dict(rows).items():`. The dict() call silently fails or crashes on 3-column results.
- **Gateway launchd service lost**: If `hermes gateway restart` fails with "Could not find service in domain", the plist exists but isn't loaded. Fix: `launchctl bootout gui/501/ai.hermes.gateway 2>/dev/null; launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.hermes.gateway.plist && launchctl kickstart gui/501/ai.hermes.gateway`. The bootout clears stale state; bootstrap re-registers; kickstart starts.
- **Noise tips with raw JSON in recommendation**: Some tips store raw tool output as the recommendation (e.g. `[read_file] {\"content\": \"   350|...`). These pass through the noise guard because the guard checks for specific markers but not generic JSON patterns. Add periodic purge: `DELETE FROM distilled_tips WHERE recommendation LIKE '{%' OR length(recommendation) < 20`.
- **3-database drift**: tool_stats, call_log, and mastery_scores can show completely different success rates for the same tool. ALWAYS verify with call_log (ground truth) before trusting aggregate numbers. The pre_llm_call hook reads from tool_stats — if that table is stale, the agent gets wrong "weakest tools" injected into its context.
- **Empty experiences bloat**: The experiences table can accumulate 50%+ empty/trivial lessons (NULL or <5 chars). These don't cause direct errors but waste space and slow queries. Periodic purge: `DELETE FROM experiences WHERE lesson IS NULL OR lesson = '' OR length(lesson) < 5`.
- **tool_stats partial classification**: "partial" result_status in call_log (successful execution with truncated/stderr output) gets counted as "failure" when synced to tool_stats. Consider whether partials should count as successes for rate calculation.
- **tool_stats PHANTOM INFLATION (discovered Apr 15, 2026)**: The old classifier bug that counted every agent turn as a terminal call inflated tool_stats by 100x (terminal: 31,500 in tool_stats vs 302 in call_log). This is far worse than simple "drift" — it's systematic inflation. The fix MUST resync tool_stats from call_log (ground truth) and also reset mastery_scores from the corrected tool_stats. Without this, the pre_llm_call hook injects wildly wrong "weakest tools" signals. **Run 3-DB sync monthly as maintenance.**
- **PRAGMA table_info before querying**: SQLite schemas vary and column names are NOT predictable across DBs. `token_usage` uses `created_at` not `timestamp`. `perspective_diversity` uses `diversity_score` not `score`. `api_calls` has no `cost` column. Always run `PRAGMA table_info(table_name)` first to discover actual column names before writing queries. Shell-quoted inline SQL in terminal() compounds this — write Python audit scripts to /tmp/ instead.
- **tip_elo baseline trap**: The elo_rating system defaults all tips to elo=1200. If the competitive tournament never ran properly, ALL tips sit at 1200 regardless of quality → Elo becomes meaningless. Fix: seed elo from confidence using formula `elo = 1200 + (confidence - 0.5) * 1200`, with bonuses for high upvotes. After seeding: tips with confidence 0.95 → elo ~1800, tips at 0.5 → elo ~1200.
- **Elo-aware injection priority**: When the injection governor must triage (over 1500 chars / 12 lines), it uses priority tags (P0-P4). Adding an Elo-lookup step boosts priority of lines matching high-Elo tip types. Implementation: before the tag-matching loop, query tip_elo for average elo per tip_type, then lines mentioning high-Elo domains get -1 priority boost. This ensures the governor keeps the BEST tips when forced to cut.
- **perspective_diversity bloat**: This table accumulates rows from every perspective-taking cron run. 82% of rows have diversity_score < 0.1 (single perspective, near-zero value). Periodic purge: `DELETE FROM perspective_diversity WHERE diversity_score < 0.1` — typical savings: 19K rows purged from 23K total.
- **Dead empty table cleanup**: Cerebrum accumulates tables from abandoned features. 22 empty tables with 0 rows and NO write paths were identified. Dropping them reduces query overhead during `SELECT COUNT(*)` audits and keeps schema clean. Safe to drop tables with 0 rows and no INSERT statements found in `grep -rn` across ~/subconscious/ and plugins/.
