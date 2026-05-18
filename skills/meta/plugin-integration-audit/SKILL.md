---
name: plugin-integration-audit
version: 1.0
created: 2026-04-04
description: Systematic audit methodology for verifying Hermes plugin/hook integration. Catches silent failures, data flow gaps, redundancy, and performance issues.
triggers:
  - After adding new learning engines or cognitive modules
  - After modifying hook callbacks (pre_llm_call, pre_tool_call, post_tool_call)
  - After creating new DB tables for learning systems
  - When Danny asks for "integration audit" or "maximize integration"
---

# Plugin Integration Audit

Systematic 10-cycle audit for verifying that learning/cognitive plugins are fully integrated with the Hermes core. Each cycle follows: **audit → fix → ask "how could this be even better?"**

## The 10 Cycles

### Cycle 1: Hook Wiring
**Goal**: Verify every hook callback actually fires with correct parameters.

1. Find hook dispatch points in the core:
   ```
   grep -rn "invoke_hook" hermes_cli/ run_agent.py model_tools.py --include="*.py"
   ```
2. For each hook (`pre_tool_call`, `post_tool_call`, `pre_llm_call`, `on_session_start`), note what kwargs the core passes.
3. Cross-reference with what the plugin's callback function reads via `kwargs.get()`.
4. **COMMON BUG**: Core passes `user_message` and `conversation_history` but plugin reads `messages` and `prompt`. These silent mismatches mean the plugin gets empty data forever.
5. Fix: Align kwarg names. Verify with a test print.

**Improvement prompt**: Does the plugin register ALL available hooks? Is there a hook the core fires that the plugin ignores (e.g., `on_session_start`)?

### Cycle 2: Data Flow Integrity
**Goal**: Trace end-to-end: tool call → classify → DB write → read back → inject.

1. Simulate a chain of tool calls feeding into all engines.
2. After writes, verify DB rows exist with correct data.
3. Call each engine's `on_pre_llm_injection()` and verify it returns data.
4. Check thresholds — some engines only inject after N observations. Are thresholds too high?

**Improvement prompt**: What data is collected but never used? What injection would be valuable but isn't generated?

### Cycle 3: Cross-Engine Redundancy
**Goal**: Map every DB table to its owning engine and find overlaps.

1. List all tables: `SELECT name FROM sqlite_master WHERE type='table'`
2. Map each table to the engine that creates/writes it.
3. Find tables with similar purposes (e.g., 3 engines tracking tool sequences).
4. Determine if overlap is complementary (different angles) or wasteful (same data twice).
5. If complementary: wire them to feed each other rather than merging.

**Improvement prompt**: Can engines share data instead of duplicating collection?

### Cycle 4: Performance Bottlenecks
**Goal**: Measure latency each hook adds to the critical path.

1. Time 20 DB writes to each learning table.
2. Average should be < 5ms (SQLite WAL mode).
3. If slow, check: missing indexes? too many conn.open/close? locking contention?

### Cycle 5: Coverage Gaps
**Goal**: Find tools/actions that slip through all engines.

1. List all Hermes tools (from tool registry or available_tools list).
2. Check which are explicitly handled in each engine's `on_post_tool_call_hook`.
3. Tools not explicitly handled still get generic capability tracking, but miss specialized learning.
4. Priority gaps: high-frequency tools (browser_*, delegate_*, memory tools).

**Improvement prompt**: Which untracked tools fail most often? Those should get tracking first.

### Cycle 6: Squad Sync Verification
**Goal**: Ensure all squad profiles have identical plugin code.

1. Use `filecmp.cmp()` to compare base plugin with each profile's copy.
2. Also compare learning engine .py files if they need to be in profile dirs.
3. Fix: `cp` the canonical version to each profile.

### Cycle 7: DB Schema Efficiency
**Goal**: Index coverage, WAL health, query patterns.

1. List all indexes: `SELECT name, tbl_name FROM sqlite_master WHERE type='index'`
2. Find tables with > 5 rows but no custom indexes.
3. Add indexes on frequently queried columns (tool_name, timestamps, hashes).
4. Verify WAL mode: `PRAGMA journal_mode` should return 'wal'.

### Cycle 8: Injection Quality
**Goal**: What actually gets injected vs noise ratio.

1. Call all engine injections and measure total character count.
2. Target: < 1000 chars for LOW noise, 1000-2000 MODERATE, > 2000 HIGH.
3. Check relevance: does a coding task get research tips? (Needs task-type filtering.)
4. Improvement: Add task-type relevance filter to injection methods.

### Cycle 9: Brain + Mastery Integration
**Goal**: Verify the subconscious brain consumes mastery data.

1. Check brain.py and parallel_brain.py for references to mastery/operational modules.
2. If absent: add mastery status to the brain's perceive() phase so it can see learning progress.
3. The brain should know: how many patterns learned, confidence trends, weak tools.

### Cycle 10: Final Fixes + Scorecard
**Goal**: Document everything and prioritize remaining work.

Generate a scorecard with:
- Engine count, dimension count, table count, row count
- Code lines, avg DB write time, squad sync status
- Each cycle's verdict (FIXED / OK / NEEDS WORK)
- Prioritized remaining improvements

## Key Lessons from Audits (Apr 2026)

0. **Dead code detection via import search** — For any function you suspect is dead code, run `search_files(pattern="import.*function_name|from.*module.*import.*function_name")`. Zero results = dead code. This caught `top_down_recall()` being defined in 731 lines but never imported anywhere — 903 distilled tips existed in DB but were never injected into agent context. The entire top-down pipeline was invisible.

0a. **Pipeline connectivity audit method** — For any data pipeline (write → transform → read):
   1. Find the WRITE function (e.g., `bottom_up_store`). Search for ALL callers: `search_files(pattern="bottom_up_store")`.
   2. Find the READ function (e.g., `top_down_recall`). Search for ALL callers.
   3. Check the intermediate DB: does data actually exist? `sqlite3 db "SELECT COUNT(*) FROM table"`
   4. If data exists but is never read → the pipeline is DISCONNECTED. This is the most common integration failure.
   5. Find the injection point in the consumer (e.g., `gateway/run.py` line ~2254 where `context_prompt` is built) and add a direct read.

0b. **Crash-safe file writes** — Never clear a file with `path.write_text("")` after DB writes. If the process crashes between db.commit() and write_text(), data is duplicated on next run. Use rename-then-delete: `path.rename(backup); backup.unlink()`.

0c. **String modulo bug pattern** — If `cycle_id` is set to a datetime string like `"2026-04-06_13:24"` and later used in `% 10`, it crashes with TypeError. Always use a separate integer counter for modulo operations.

1. **Silent kwarg mismatches are the #1 killer** — plugins never crash, they just get empty data. Always verify kwargs by reading the core's invoke_hook call site.
1a. **Gateway kwargs TypeError pattern (CONFIRMED Apr 8 2026)** — `invoke_hook("post_tool_call", ..., session_id=..., task_id=...)` passes ALL kwargs directly to every registered callback. If a callback has explicit params like `def _on_post_tool_call(tool_name, args, result, task_id="")` WITHOUT `**kwargs`, it raises `TypeError: got an unexpected keyword argument 'session_id'`. The `except Exception: pass` in run_agent.py swallows this silently — zero logs, zero errors, just dead hooks. **FIX**: Every hook callback MUST end with `**kwargs` to absorb extra gateway kwargs. **Known gateway kwargs**: `session_id`, `task_id`, `turn_id`, `request_id`, `user_task`, `context`. **Same bug hit**: evey-mesh plugin (fixed with `_GATEWAY_KWARGS` filter) AND distillation plugin `_on_post_tool_call` (fixed by adding `**kwargs`). **Detection method**: Write a standalone test (`/tmp/test_hook.py`) that calls `discover_plugins()` then `invoke_hook("post_tool_call", tool_name="test", args={}, result="test", task_id="t", session_id="s")` — if it prints `Hook 'post_tool_call' callback ... raised: TypeError`, the callback is missing `**kwargs`. Do NOT trust silent `except: pass` — replace with `logging.warning` during debugging.
2. **Thresholds matter** — if advice only appears after 3+ uses, the first 2 failures get no guidance. Add low-threshold error warnings (even 1 occurrence).
3. **Cross-engine data is more valuable merged** — don't merge tables, but wire engines to feed each other.
4. **DB writes are fast (0.08ms)** — don't worry about performance until you see > 10ms.
5. **The brain should see mastery** — without it, the brain is blind to its own learning rate.
6. **Python scoping: variables assigned inside `if` blocks must not be referenced outside** — Python 3.11+ raises `UnboundLocalError` if a variable is assigned inside a conditional but referenced after it when the condition was false. Extract variable assignment to the top level BEFORE any conditional that uses it.
7. **Gateway restart kills active user sessions** — `hermes gateway restart` terminates the running process, disconnecting all connected terminals. ALWAYS warn the user and ask before restarting. Save checkpoint first.
8. **Test with gateway error logs, not just isolated imports** — `python3 -c "from module import ..."` only proves the module loads. Real bugs show up in `~/.hermes/logs/gateway.error.log` or `errors.log` when hooks fire with actual kwargs.
9. **Diagnostic call detection must handle shell chains** — `terminal` commands like `cd ~/dir && python3 -c "..."` start with `cd`, not `python3`. The `_is_diagnostic()` check must split on `&&` and test the last segment too. Also match full venv paths (`/Users/.../venv/bin/python3`). Without this, legitimate diagnostic calls poison tool confidence scores (terminal dropped to 21% "success").
10. **Gateway error logs are the FIRST place to look** — `~/.hermes/logs/errors.log` shows every hook failure with timestamp. Grep for the plugin name to find silent crashes. The `pre_llm_call` scoping bug was crashing every turn for hours but only visible in this log.
11. **Lazy-init engines report FAILED outside gateway** — Mastery/Operational/Session/FluidReasoning engines use lazy init that only loads inside the gateway's hook dispatch. Testing with `python3 -c "plugin._get_mastery_engine()"` returns None. This is expected; don't chase it as a bug.
12. **Build-Activate-Test-Grow cycle (Danny's rule)** — After building ANY plugin code change, the full cycle is: (1) BUILD the code, (2) ACTIVATE by clearing __pycache__ + restarting gateway + starting new CLI session, (3) TEST with real tool calls and verify DB gets live entries, (4) DEBUG if data is missing, (5) THEN continue growing. Never skip Activate+Test or you accumulate dead code that looks alive. Building without integrating is a LIABILITY.
13. **Registered ≠ Invoked** — A plugin registering a hook via `ctx.register_hook("post_tool_call", fn)` means the callback is STORED in the hook registry. But if the runtime never calls `invoke_hook("post_tool_call", ...)`, the callback never fires. This is the most insidious integration bug — zero errors, zero logs, just silence. Always grep for invoke_hook calls to match registered hooks.
14. **CLI sessions cache run_agent.py** — After patching run_agent.py, existing CLI sessions still run the OLD code. Only NEW CLI sessions (started after gateway restart) pick up changes. This means verification must happen in a fresh session, not the one that applied the patch.
15. **Postgres array column gotcha (psycopg2)** — `json.dumps(tags or [])` passes `"[]"` as a string to Postgres array columns, causing `InvalidTextRepresentation: malformed array literal: "[]"`. Fix: pass `tags or None` (None becomes SQL NULL which Postgres accepts) or use psycopg2's native list adaptation which converts Python lists to Postgres arrays automatically. This is especially tricky because the same `json.dumps()` pattern works fine for `jsonb`/`text` columns — the bug only manifests on `array` type columns.
16. **Injection threshold bootstrap problem** — When adding a new injection path with entry criteria (e.g., `elo > 1400 AND confidence >= 0.6`), verify that existing data can actually satisfy those criteria. If all records start at default values (elo=1200, confidence=0.5), the path is dead on arrival — 0 records eligible, 0 ever will be. Fix: set initial thresholds to match existing data distribution, then tighten as the system matures. General test: `SELECT COUNT(*) WHERE <your_criteria>` must return > 0 BEFORE you ship the injection path.
17. **E2E pipeline test pattern for Postgres/Cortex** — After any change to the cortex pipeline (insert, search, injection, Elo), write a `/tmp/e2e_test.py` that tests ALL stages: (1) insert a test node, (2) verify it exists in DB, (3) search finds it, (4) dedup blocks second insert, (5) injection queries return results, (6) Elo system has rated entries, (7) daemon is healthy, (8) data quality checks (domain diversity, embedding coverage, no dead domains). Cleanup test data at the end. Run with `source venv/bin/activate && python3 /tmp/e2e_test.py`.

## Context Injection Points in gateway/run.py

When adding new data sources to agent context, inject at these points:

| Point | Line (~) | What | How |
|-------|----------|------|-----|
| Context prompt build | 2254 | Session context assembly | `context_prompt = build_session_context_prompt(...)` — append AFTER this |
| Distillation recall | 2256 | Distilled tips + meta-insights | Already wired: reads from `cerebrum_memory.db` distilled_tips + meta_insights tables |
| Auto-reset notice | 2259 | Session expiry warning | Prepends to context_prompt |
| Restart marker | 2314 | Checkpoint restore | Prepends to context_prompt |
| Voice channel | 2655 | Discord voice state | Appends to context_prompt |
| Memory prefetch | run_agent.py:7003 | External memory recall | `_ext_prefetch_cache = self._memory_manager.prefetch_all(query)` |
| Prefetch injection | run_agent.py:7073 | Merge into user message | `_injections.append(_ext_prefetch_cache)` |

## Files to Check
- Plugin: `~/.hermes/plugins/evey-tool-intelligence/__init__.py`
- Core dispatch: `model_tools.py` (lines ~405-430), `run_agent.py` (lines ~6560-6660)
- Learning engines: `plugins/memory/cerebrum/{mastery_engine,operational_mastery,session_meta_mastery,fluid_reasoning}.py`
- Brain: `~/subconscious/brain.py`, `~/subconscious/parallel_brain.py`
- DB: `~/.hermes/cerebrum_memory.db`

## Support Files
- `references/live-cognitive-systems-verification.md` — live PluginManager verification for the cognitive-systems plugin: discover_and_load(), check _plugins and _hooks, test module loading from the actual plugin path, verify DB health and experience counts. Includes complete verification script.

## Quantitative Benchmarks (Apr 2026)

These are proven performance baselines for a healthy plugin + iteration engine:

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| DB write latency | <5ms | 5-20ms | >20ms |
| Brain perceive overhead | <50ms | 50-200ms | >200ms |
| Perceptual call throughput | >10 calls/sec | 5-10 | <5 |
| Cache speedup on repeated input | >5x | 2-5x | <2x |
| Medical modality accuracy | >90% | 70-90% | <70% |
| Plugin registration checks | ALL PASS | 1 FAIL | 2+ FAILS |
| Iteration engine tracking | >0 calls | 0 calls | errors |
| Cross-plugin feedback loops | ALL WIRED | partial | broken |

## Critical Pipeline Finding: post_tool_call Never Invoked from Runtime (Apr 8 2026)

The distillation plugin registered `post_tool_call` via `ctx.register_hook()`. The module imported cleanly. __pycache__ was rebuilt on gateway start. Everything looked correct — but the hook NEVER FIRED with real tool data.

**Root cause:** `run_agent.py` had `invoke_hook()` calls for `on_session_start` (L6996), `pre_llm_call` (L7116), `pre_api_request` (L7351), `post_api_request` (L8518), `on_session_end` (L9303) — but **zero calls** to `invoke_hook("post_tool_call", ...)`. The hook was registered in the plugin but the runtime never dispatched it.

**UPDATE (May 2026):** The same gap affects `pre_tool_call`. Both `pre_tool_call` and `post_tool_call` are registered by the plugin system but NOT invoked by run_agent.py. Only these hooks are actually dispatched:
- `on_session_start` — line ~11459
- `pre_llm_call` — line ~11593 (context injection works)
- `pre_api_request` — line ~12097 (telemetry only)
- `post_api_request` — line ~13915 (telemetry only)
- `transform_llm_output` — line ~14849 (output transformation)
- `post_llm_call` — line ~14870 (fire-and-forget)
- `on_session_end` — line ~14985 (fire-and-forget)

**Both tool execution paths needed the fix:**
- Concurrent path: `_execute_tool_calls_concurrent` (~L6245, after `tool_complete_callback`)
- Sequential path: `_execute_tool_calls_sequential` (~L6559, after `tool_complete_callback`)

**Patch pattern (add after tool_complete_callback in both paths):**
```python
# Plugin hook: post_tool_call
try:
    from hermes_cli.plugins import invoke_hook as _invoke_hook
    _invoke_hook(
        "post_tool_call",
        tool_name=name,  # or function_name in sequential path
        args=args if isinstance(args, dict) else {},
        result=function_result,
        task_id=effective_task_id,
        session_id=self.session_id or "",
    )
except Exception:
    pass
```

**How to detect this class of bug:** Search for ALL hooks the plugin registers, then search for ALL `invoke_hook` calls in the runtime for each one. If a hook has zero invoke_hook calls, the pipeline is dead.

```bash
# 1. What hooks does the plugin register?
grep -n "register_hook\|provides_hooks" ~/.hermes/plugins/<name>/plugin.yaml

# 2. For each hook, is it invoked from the runtime?
grep -rn "invoke_hook.*<hook_name>" run_agent.py model_tools.py gateway/run.py
```

**CLI session staleness:** Gateway restart does NOT update running CLI sessions. The CLI process loaded run_agent.py at startup and caches it. After patching run_agent.py, you need BOTH: (1) gateway restart AND (2) new CLI session. Existing CLI sessions use stale code until they die and respawn.

**Verification protocol:** After any hook wiring fix:
1. `python -m py_compile run_agent.py` — verify syntax
2. `grep -n "invoke_hook.*post_tool_call" run_agent.py` — verify patch present
3. Restart gateway + start new CLI session
4. Make 3-5 tool calls
5. Check DB: `SELECT COUNT(*) FROM <table> WHERE timestamp > <now-5min>` — must be > 0

## Critical Pipeline Finding: pre_tool_call vs pre_llm_call (Apr 2026)

The distillation plugin registers hooks with different injection capabilities:

1. **`pre_tool_call`** — IS dispatched at model_tools.py L502 via `invoke_hook("pre_tool_call", tool_name=..., args=..., ...)`. The return value is discarded (not used), BUT the callback DOES execute for side effects. Safe to use for: circuit breaker checks, cache lookups, validation, prediction recording. NOT safe for: context injection (return value ignored). Must register via `ctx.register_hook("pre_tool_call", fn)` — the hook was previously dead code (defined but never registered), now confirmed working as of Apr 2026.

2. **`pre_llm_call`** — This is the ONLY working injection path. The gateway fires it once per turn (run_agent.py ~line 6963), collects results, and injects them into the user message (run_agent.py ~line 7089-7092).

**The injection flow (verified end-to-end):**
```
run_agent.py:6963  invoke_hook("pre_llm_call", ...)
run_agent.py:6970  collect results (dict with "context" key or plain string)
run_agent.py:7089  inject into user message: api_msg["content"] += injections
```

**Data source gotcha:** The distillation plugin's `_on_pre_llm_call` queries `~/subconscious/tool_capability.db` (NOT `~/.hermes/tool_capability.db`). If data exists only in the latter, the hook returns empty string silently — no error, no log, just no injection. Always verify the plugin is reading from the DB that actually has data.

**What gets injected:** Top 3 weakest tools (by success rate, minimum 30 calls) get their top 2 tips (confidence >= 0.4) injected as `[DISTILLED TOOL RULES — apply these proactively]` block in the user message. This is a broad brush — not per-tool-call guidance, but blanket guidance once per turn.

**How to verify injection is working:** The injected text appears as `[DISTILLED TOOL RULES — apply these proactively]` in the agent's context. If you see this block in your conversation, the pipeline is live.

## Cross-Hook State Bridging Pattern (Apr 2026)

When one hook (e.g., `post_tool_call`) produces data that another hook (e.g., `pre_llm_call`) needs to inject, the two hooks run in separate call frames. You CANNOT just return data from one and expect the other to see it.

**Working bridge pattern — module-level attribute:**
```python
# In your module (e.g., mythos_enhancements.py):
_last_cycle_info = None  # module-level state

def on_post_tool_call_enhanced(tool_name, args, result, status, error):
    global _last_cycle_info
    cycle_info = detect_cycle(tool_name, args, status, error)
    if cycle_info and cycle_info.get("cycle_detected"):
        _last_cycle_info = cycle_info  # store on module
        on_post_tool_call_enhanced._last_cycle_info = cycle_info  # AND on function attr
    return cycle_info

def on_pre_llm_call_enhanced(user_message):
    # Read from BOTH locations (belt + suspenders)
    cycle_info = getattr(on_post_tool_call_enhanced, '_last_cycle_info', None)
    if cycle_info is None:
        import mythos_enhancements as _self
        cycle_info = getattr(_self, '_last_cycle_info', None)
    return build_adaptive_context(user_message, cycle_info=cycle_info)
```

**Why both locations?** The gateway may import the module differently (module object vs function object), so store on both the module and the function attribute for reliability.

**Common failure pattern:** `except Exception: pass` in the hook wrapper silently swallows ALL errors, including the import of the sub-module. The plugin appears to load (hooks registered), but the enhancement code never runs. Always add logging inside the try block during development:
```python
try:
    from mythos_enhancements import on_post_tool_call_enhanced
    logger.debug("Mythos import succeeded")
    on_post_tool_call_enhanced(...)
    logger.debug("Mythos post_tool_call completed")
except Exception as e:
    logger.warning("Mythos enhancement failed: %s", e)  # NOT pass
```

**Diagnostic workflow for "plugin registered but not working":**
1. Check DB tables for row counts — 0 rows in tables = data never written
2. Write a standalone test script (`/tmp/test_foo.py`) that imports the module and calls functions directly
3. Use `write_file` + `terminal` for complex Python tests — `execute_code` with inline multi-line Python is fragile (string escaping issues)
4. Check `__pycache__/` for stale `.pyc` files from wrong Python versions
5. After fixes, ALWAYS `rm -rf ~/.hermes/plugins/<name>/__pycache__/` before restart

### Cycle 11: Empty Table Root Cause Analysis
**Goal**: Find tables that exist but never receive data.

1. List all tables with 0 rows:
   ```bash
   for db in ~/.hermes/cerebrum_memory.db ~/subconscious/*.db; do
     echo "=== $db ==="
     sqlite3 "$db" "SELECT name, (SELECT COUNT(*) FROM \"\" || name || \"\") as cnt FROM sqlite_master WHERE type='table'" 2>/dev/null
   done
   ```
2. For each 0-row table, trace the write path:
   - Search for INSERT statements: `grep -n "INSERT INTO <table>" plugin/*.py subconscious/*.py`
   - Search for the write function: `grep -n "_record_<table>\|_save_<table>" plugin/*.py subconscious/*.py`
   - Search for callers of the write function: `grep -n "_record_<table>" plugin/*.py`
3. **Three possible root causes**:
   - **NO WRITE PATH**: Table created by schema migration but no code ever inserts. Dead infrastructure — either build the writer or drop the table.
   - **WRITE PATH EXISTS BUT NEVER TRIGGERED**: Function defined and called, but the condition that triggers it (e.g., tool errors → arg_feedback) never occurs. This is usually GOOD news.
   - **WRITE PATH BROKEN**: Function called but silently fails. Check gateway error logs for exceptions.

### Cycle 12: DB Journal Mode + Index Health
**Goal**: Ensure all active DBs use WAL mode and have proper indexes.

1. Check journal modes:
   ```bash
   for db in ~/.hermes/cerebrum_memory.db ~/subconscious/*.db; do
     mode=$(sqlite3 "$db" 'PRAGMA journal_mode' 2>/dev/null)
     size=$(du -h "$db" 2>/dev/null | cut -f1)
     echo "$db | $mode | $size"
   done
   ```
2. Tables with >100 rows on DELETE mode should be upgraded to WAL:
   ```bash
   sqlite3 <db> 'PRAGMA journal_mode=WAL'
   ```
3. Find tables missing indexes:
   ```bash
   sqlite3 <db> "SELECT m.name as tbl FROM sqlite_master m WHERE m.type='table' AND (SELECT COUNT(*) FROM sqlite_master i WHERE i.type='index' AND i.tbl_name=m.name AND i.name NOT LIKE 'sqlite_autoindex%') = 0 AND m.name NOT IN ('sqlite_sequence')"
   ```
   Add indexes on frequently queried columns (tool_name, timestamp, hash columns).

### Cycle 13: Tip/Memory Quality Distribution
**Goal**: Catch toxic low-quality data that degrades injection relevance.

1. Tip confidence distribution:
   ```sql
   SELECT 
     CASE WHEN confidence >= 0.8 THEN 'HIGH' WHEN confidence >= 0.5 THEN 'MED' ELSE 'LOW' END as tier,
     COUNT(*), AVG(upvotes), AVG(downvotes)
   FROM distilled_tips GROUP BY tier ORDER BY MIN(confidence) DESC;
   ```
2. **Toxic tip detection**: Any tier with AVG(downvotes) > 10x AVG(upvotes) is toxic. These tips actively harm agent performance when injected.
3. Remediation options:
   - Quarantine: `UPDATE distilled_tips SET confidence = 0.1 WHERE confidence < 0.3 AND downvotes > upvotes * 5`
   - Delete: `DELETE FROM distilled_tips WHERE confidence < 0.2 AND downvotes > 50`

### Cycle 14: API Analytics & Cost Wiring
**Goal**: Verify API tracking pipeline is capturing data.

1. Check the correct DB path — plugins may write to `~/subconscious/api_analytics.db` NOT `~/.hermes/api_analytics.db`. Always grep the plugin code for the actual path:
   ```bash
   grep -n '_api_db_path\|api_analytics' ~/.hermes/plugins/*/**.init**.py
   ```
2. Verify row counts: `sqlite3 <correct_path>/api_analytics.db 'SELECT COUNT(*) FROM api_calls'`
3. If 0 rows: the `_ensure_api_db()` function may not have run, or the `post_api_request` hook isn't firing.

### Cycle 15: Cron Job Health Check
**Goal**: All scheduled jobs are running on schedule without errors.

1. List all jobs: `hermes cron list`
2. For each job, verify: schedule is sensible, last run shows "ok", next run is in the future.
3. Jobs that haven't run in >2x their interval are likely stuck.

## DB Path Mismatch Pattern (Apr 2026)

Different subsystems write to different base directories:
- `~/.hermes/` — cerebrum_memory.db (main tips/facts DB)
- `~/subconscious/` — tool_capability.db, api_analytics.db, skill_rewards.db, tool_predictor.db, arg_feedback.db, etc.
- Always grep the plugin code for `_db_path` or `_db` to find the actual path before querying.

## DB Bloat Cleanup Pattern (Apr 2026)

Learning DBs accumulate junk rows from cron runs and failed experiments. Periodic cleanup prevents bloat:

1. **Score-0 row purge**: Tables like `perspective_diversity` accumulate rows with score=0.0 from every cron run — 24K rows in 5 days. Delete: `DELETE FROM perspective_diversity WHERE score = 0.0`
2. **Time-bounded retention**: Tables like `token_usage` grow linearly. Trim to N days: `DELETE FROM token_usage WHERE timestamp < datetime('now', '-3 days')`
3. **Always VACUUM after bulk deletes**: `sqlite3 <db> 'VACUUM'` reclaims disk space. Example: 12M → 9.5M (21% reduction) after purging 38K rows.
4. **Check empty tables**: 26 cerebrum tables existed with schema but zero write paths. Low priority but worth documenting to avoid confusion during audits.

### Cycle 16: Undefined Module Reference Audit (Apr 2026)
**Goal**: Find module-level variables used in hooks that aren't actually imported.

After zombie culling (removing unused module imports), hooks may still reference the old variable names. The `try/except` blocks silently set them to `None`, so hooks never crash — they just skip real logic.

**Detection method:**
1. Extract all module-level variable definitions (before first `def`): `re.findall(r'^(_\w+)\s*[:=]', top_section)`
2. For each hook function, find all `_xxx` references: `re.findall(r'\b(_\w{3,})\b', body)`
3. Subtract locals, params, function names, constants, for-loop vars
4. Remaining that appear in `if _var and` or `_var.method()` context are REAL undefined references
5. Write a script that adds back the missing imports with correct constructors

**Gotchas:**
- Auto-generators often set `module = SomeClass(session_id="default")` but some classes don't accept `session_id` (e.g., `EpisodicMemory()` takes no args). Always check the actual `__init__` signature.
- When inserting import blocks, ensure every `except Exception:` block has a body (e.g., `_var = None`). Empty except bodies are syntax errors.
- Use Python script approach for bulk import additions — the `patch` tool has a 42% failure rate on multi-line replacements.

### Cycle 17: API Signature Verification (Apr 2026)
**Goal**: Verify that the plugin's usage of module methods matches the actual API.

The plugin may call `module.retrieve(query=..., limit=...)` but the actual signature is `module.retrieve(current_task, tool_name=None, domain=None)`. These mismatches are swallowed by `except Exception: pass` blocks.

**Verification method:**
1. For each module used in injection, write a test script:
   ```python
   from module import ModuleClass
   m = ModuleClass()  # Test constructor
   result = m.retrieve(current_task="test task")  # Test actual API
   print(f"type: {type(result)}, keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
   ```
2. If `retrieve()` returns a dict (not a list), the plugin's iteration `for item in result[:2]` iterates DICT KEYS (strings), not items. This silently produces garbage.
3. Check that returned data includes `id` fields for `touch_node()` calls — many Retriever classes SELECT `text, domain, elo` but omit `id`, so access tracking never fires.
4. For `build_injection()` methods that return empty strings (utility modules), the hook should use the module's `retrieve()` or other methods instead.

**Common API mismatch patterns:**
| Plugin calls | Actual API | Effect |
|---|---|---|
| `retrieve(query=..., limit=...)` | `retrieve(current_task, tool_name, domain)` | TypeError → empty result |
| `for item in result[:2]` where result is dict | Iterates keys ("tips", "experiences") | Garbage injection |
| `item.get("text")` on dict key "tips" | String has no `.get()` | AttributeError → skip |
| `item.get("id")` but id not in SELECT | Always returns "" | touch_node never fires |
| `ModuleClass(session_id="default")` | `ModuleClass()` (no session_id) | TypeError → module=None |

### Cycle 18: Multi-Layer Duplicate Prevention (Apr 2026)
**Goal**: Prevent duplicate nodes at both the code level AND the database constraint level.

The daemon and other R-modules (episodic_memory, novelty_detector, trajectory_intel, failure_exemplar_bank) may do raw `INSERT INTO cortex_nodes` that bypass Python-level dedup gates.

**Three-layer dedup strategy:**
1. **Code-level gate**: In `insert_node()`, check `md5(text)` before inserting. If match found, bump `frequency` and return existing ID. Covers all node types (not just tips).
2. **DB-level constraint**: Add partial unique indexes:
   ```sql
   CREATE UNIQUE INDEX cortex_active_tip_md5_uniq
   ON cortex_nodes (md5(text))
   WHERE node_type = 'tip' AND is_active = TRUE;
   
   CREATE UNIQUE INDEX cortex_active_exp_md5_uniq
   ON cortex_nodes (md5(text))
   WHERE node_type = 'experience' AND is_active = TRUE;
   ```
   These prevent raw SQL inserts from creating duplicates. Deactivating a node frees the MD5 slot.
3. **Periodic cleanup**: When unique index creation fails due to existing dupes, clean them with:
   ```sql
   WITH ranked AS (
     SELECT id, ROW_NUMBER() OVER (PARTITION BY md5(text) ORDER BY elo DESC) as rn
     FROM cortex_nodes WHERE node_type='tip' AND is_active=TRUE
   )
   UPDATE cortex_nodes SET is_active=FALSE
   WHERE id IN (SELECT id FROM ranked WHERE rn > 1);
   ```

**Fuzzy dedup (first-N-chars) for audit compliance:** Some audit checks group by `LEFT(text, 80)`. These near-dupes (slightly different whitespace or IF prefix) need the same ROW_NUMBER cleanup approach.

**Gotcha:** `array_agg(id)` on UUID columns may return numeric strings like "0", "4" that crash when used as UUID params. Use the `ROW_NUMBER` approach instead of `array_agg` for cleanup.

### Cycle 19: Dead Code and Self-Import Audit (May 2026)
**Goal**: Find dead code that silently fails and self-imports that work by accident.

**Dead code pattern:**
```python
try:
    from memory_cortex_bridge import MemoryCortexBridge  # ← wrong path, now in agent/
    bridge = MemoryCortexBridge()
    result = bridge.offload_if_needed()
except Exception:
    pass  # Silently fails forever — code runs but does nothing
```

**Detection:**
```bash
# Find catch-all exception blocks that swallow imports
grep -rn "except Exception:" ~/.hermes/plugins/*/**.init**.py agent/ hermes_cli/plugins.py
# For each, check if the try block contains imports that might fail
```

**Self-import anti-pattern:**
```python
# In agent/memory_cortex_bridge.py:
def some_function():
    from memory_cortex_bridge import MemoryCortexBridge  # ← no agent. prefix
    bridge = MemoryCortexBridge()
```

This works by accident (module already in sys.modules) but breaks refactoring. Always use the full path: `from agent.memory_cortex_bridge import MemoryCortexBridge`.

**Detection:**
```bash
grep -rn "from \w\+ import" agent/ | grep -v "from agent\." | grep -v "from hermes_cli" | grep -v "from tools\."
```

**Files to check:**
- `hermes_cli/plugins.py` — `get_pre_tool_call_block_message()` often accumulates dead code
- `agent/*.py` — self-imports inside functions
- `~/.hermes/plugins/*/**.init**.py` — stale import paths after module moves

## After Audit
- Propagate fixes: `cp` plugin to all `~/.hermes-profiles/*/plugins/evey-tool-intelligence/`
- Restart gateway to activate
- Save checkpoint
- Run stress test (50+ calls) to populate iteration data
- Verify iteration engine reports healthy=True before declaring done
- **Upgrade active DELETE-mode DBs to WAL** (any with >100 rows)
- **Quarantine toxic tips** (confidence < 0.3 with high downvotes)
- **Document empty tables**: decide whether to build write paths or drop dead infrastructure
