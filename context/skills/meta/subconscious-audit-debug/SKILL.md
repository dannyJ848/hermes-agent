---
name: subconscious-audit-debug
description: Diagnose and fix low subconscious audit scores by tracing failing metrics through SQLite data and controller.py queries.
version: 1.0
category: meta
triggers:
  - Subconscious audit alert with F grade
  - prediction backlog violation
  - tool success rate degrading
  - audit score below 4/10
---

# Subconscious Audit Debug

When the controller audit reports a low score (F grade, violations), use this diagnostic pipeline to trace root causes and fix them.

## Diagnostic Pipeline

### Step 1: Read the latest audit JSON
```
cat ~/subconscious/audits/$(ls -t ~/subconscious/audits/ | head -1)
```
Identify which section has the lowest score: facts, predictions, tool_performance, brain_cycles, or calibration.

### Step 2: Trace the failing metric to its SQL query
All audit metrics come from `~/subconscious/controller.py`. Grep for the function that computes the failing metric:
- `measure_prediction_health()` — predictions section
- `measure_tool_performance()` — tool_performance section
- `measure_fact_health()` — facts section
- `measure_calibration()` — calibration section

### Step 3: Query the actual data to confirm
Connect to `~/.hermes/cerebrum_memory.db` and run the same queries the audit uses. Key tables:
- `predictions` — columns: id, task_type, timestamp, resolved, predicted_outcome, actual_outcome, confidence
- `experiences` — columns: id, action_type, action_detail, result, error_pattern, lesson
- `semantic_facts` — columns: id, content, trust, source, category, salience

**ALWAYS** run `PRAGMA table_info(table_name)` before writing queries — schemas were auto-created by different modules and are NOT consistent. Common gotchas: `created_at` vs `timestamp`, `content` vs `task_summary`, `category` vs `task_type`.

### Step 4: Common root causes and fixes

#### Prediction backlog (unresolved > limit)
- **Cause**: Brain daemon creates predictions with NULL timestamps. `enforce_resolve_stale_predictions()` uses `WHERE timestamp < cutoff` which skips NULLs.
- **Fix**: Add `OR timestamp IS NULL` to the WHERE clause in controller.py.
- **Data fix**: Bulk-resolve: `UPDATE predictions SET resolved=1, actual_outcome='auto-resolved-stale' WHERE COALESCE(resolved,0)=0 AND (timestamp IS NULL OR timestamp < cutoff)`
- Most predictions are `type=intuition` — philosophical brain musings that are never verifiable.

#### Tool success rate artificially low
- **Cause**: Controller writes capability health alerts (e.g., read_file at 48% confidence) as result=failure. These are NOT real tool failures.
- **Fix**: In controller.py, change INSERT for capability alerts to use result=info.
- **Data fix**: `UPDATE experiences SET result='info' WHERE result='failure' AND action_detail LIKE 'capability alert%'`
- Always exclude result=info when computing success rates.

#### NULL timestamps everywhere
- Brain daemon creates records without timestamps (runs outside agent sessions).
- Always check for NULL timestamps before trusting time-based queries.

#### SQLite cross-type comparison phantom (TEXT vs REAL/INTEGER)
- **Cause**: When comparing a TEXT column (e.g. `created_at` storing `"2026-04-10 09:01:47"`) against a numeric parameter (e.g. `time.time() - 3600` → `1776884489.0`), SQLite does **NOT** convert the text to a number. Instead, it compares by storage class ordering: `NULL < INTEGER < REAL < TEXT < BLOB`. Since TEXT is always greater than REAL/INTEGER, **ALL rows match** the `>` condition.
- **Impact**: This creates a phantom metric like "492 facts/hr" when in reality zero facts were created in the last hour.
- **Fix**: Always match parameter type to column type. For TEXT datetime columns, use a TEXT cutoff: `cutoff_str = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")`.
- **Verify**: Run the query with both numeric and text cutoffs and confirm they return different (sane) counts.

### Step 5: Verify the fix
Run the same diagnostic queries after fixing. The next controller audit (hourly) should reflect the change.

## Key Files
- Audit runner: ~/subconscious/controller.py (run_audit function)
- Audit output: ~/subconscious/audits/*.json
- Cerebrum DB: ~/.hermes/cerebrum_memory.db
- Brain daemon: ~/subconscious/brain_daemon.py (source of NULL-timestamp records)

## Cross-Database Phantom Metrics (CRITICAL)

The subconscious has MULTIPLE databases with overlapping table names but DIFFERENT schemas:
- `~/.hermes/cerebrum_memory.db` — cerebrum tables (experiences, semantic_facts, distilled_tips, tool_stats)
- `~/subconscious/tool_capability.db` — real tool call stats (tool_stats with total_calls/successes/failures)
- `~/subconscious/agent_scorecard.py` — ICLR 5-level autonomy scoring

**PHANTOM METRIC PATTERN**: When a tool queries the WRONG database or uses wrong column names inside a try/except block, it silently returns 0 or None. This creates phantom metrics like "0.0% success rate (0 calls)" or "6.9% engineering score" that are completely wrong.

**Diagnosis steps**:
1. When you see an impossibly low metric (0% success, 0 calls, etc.), check which DB the query targets
2. Run `PRAGMA table_info(table_name)` on BOTH databases to compare schemas
3. Example: `tool_stats` in cerebrum has `call_count`/`success_count` (wrong), while tool_capability.db has `total_calls`/`successes` (correct)
4. Check `agent_scorecard.py` — its `score_error_recovery()` was querying cerebrum tool_stats with wrong column names, getting 0, showing "0.0% (0 calls)"

**Fix pattern**: Always point metric queries at the database that actually has the data:
- Tool success rates → `~/subconscious/tool_capability.db` (tool_stats table)
- Recovery tips count → `~/.hermes/cerebrum_memory.db` (distilled_tips table)
- Engineering score → compute from tool_capability.db, NOT from cerebrum experiences

**Verification**: After fixing, re-run `python3 ~/subconscious/agent_scorecard.py score` and confirm the metric shows real call counts.

## Pitfalls
- Do not trust the audit score at face value — trace the underlying data.
- Brain daemon records may lack fields the gateway populates.
- Multiple failures may be the same capability alert repeated every cycle (check frequency column).
- When in doubt, count action_detail LIKE capability alert% to separate real failures from health checks.
- NEVER assume table schemas are consistent across databases — always PRAGMA first.
- try/except returning 0 is the #1 cause of phantom metrics — silent failures hide schema mismatches.
- When integrating external scorecards (e.g. `agent_scorecard.py`), verify the dict keys match what the caller expects. A key mismatch like `scorecard.get("overall", 0)` vs `scorecard["overall_score"]` silently returns 0 and hides the real score.
