---
name: autobrowse-execution-analysis
version: 1.0
description: "Autobrowse self-improvement system — captures execution traces, detects waste patterns, synthesizes actionable tips, and graduates winners to skills. 4-module pipeline (tracer→analyzer→synthesizer→graduator) wired into distillation plugin. R191, May 2026."
trigger: "When discussing autobrowse modules, execution trace analysis, waste pattern detection, or the R191 self-improvement pipeline."
---

# Autobrowse Execution Analysis System

A 4-module pipeline that proactively improves agent performance by analyzing execution traces, detecting inefficiency patterns, and converting them into actionable behavioral tips.

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   TRACER    │───→│  ANALYZER   │───→│ SYNTHESIZER │───→│  GRADUATOR  │
│  (capture)  │    │  (detect)   │    │  (generate) │    │  (promote)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## Modules

### 1. autobrowse_tracer.py (9.4KB)
**Role**: Capture every tool call with metadata into CortexDB

**Records per call**:
- tool_name, model_used, input/output size, tokens
- execution_time_ms, status (success/error/redundant/suboptimal)
- error_type, error_message, input/output preview
- task_context, step_number, session_id

**Key methods**:
- `record_call(tool_name, model_used, input_data, output_data, execution_time_ms, status, ...)` — called from post_tool_call in distillation plugin. **NOT `record_tool_call`**.
- `build_injection()` — warns about high error rate (>30%) or redundant calls
- `get_stats()` — aggregates recent traces for injection hints

**Method name gotcha**: The method is `record_call()`, not `record_tool_call()`. Calling the wrong name gives `AttributeError: 'AutobrowseTracer' object has no attribute 'record_tool_call'`.

**Wiring** (in `~/.hermes/plugins/distillation/__init__.py`):
```python
# R191: Autobrowse trace capture
if _ab_tracer:
    try:
        status_flag = "success" if status != "error" else "error"
        _ab_tracer.record_call(
            tool_name=tool_name,
            model_used=os.environ.get("HERMES_LAST_MODEL", "unknown"),
            input_data=str(args)[:500] if args else '',
            output_data=str(result)[:500] if result else '',
            execution_time_ms=float(os.environ.get("HERMES_LAST_LATENCY_MS", 0)),
            status=status_flag,
            error_type=error.__class__.__name__ if error else None,
            error_message=str(error)[:300] if error else None,
        )
    except Exception:
        pass
```

### 2. autobrowse_analyzer.py (11KB)
**Role**: Detect waste patterns in execution traces

**Pattern types detected**:
- `redundant_loop` — same tool called >2x with similar input
- `suboptimal_model` — expensive model used for simple tool
- `token_waste` — large input/output with minimal result
- `failure_cluster` — repeated errors on same tool/domain
- `tool_mismatch` — wrong tool selected for task type

**Model cost ranking** (lower = cheaper):
```python
MODEL_COST_RANK = {
    "phi-3": 1, "local": 1, "nomic": 1,
    "glm-5.1": 2, "gemini-flash": 2, "nemotron-free": 2,
    "mimo-v2-pro": 3, "claude-sonnet": 4, "claude-opus": 5,
    "gpt-4": 5, "deepseek-v4-pro": 4,
}
```

**Tool complexity mapping**:
- SIMPLE_TOOLS: web_search, web_extract, web_research, read_file, search_files
- COMPLEX_TOOLS: delegate_task, delegate_with_model, claude_bridge_task, execute_code

**Key methods**:
- `analyze_traces(traces)` — returns list of WastePattern dataclasses
- `build_injection()` — injects top pattern recommendations into prompt

### 3. autobrowse_synthesizer.py (9.9KB)
**Role**: Convert waste patterns into WHEN/DO tips + maintain strategy.md

**Tip generation**:
- Maps pattern_type → domain (efficiency, cost_optimization, reliability)
- Maps pattern_type → tool recommendation
- Generates "WHEN condition, DO action" format tips
- Confidence threshold: 0.6 (skip low-confidence patterns)

**Strategy.md maintenance**:
- File: `~/subconscious/strategy.md`
- Compounds across sessions — running scratchpad of learned strategies
- Updated after each analysis cycle

**Key methods**:
- `generate_tips(patterns)` — converts patterns to tip dicts. **NOT `synthesize_from_patterns`**.
- `update_strategy(patterns, context)` — appends to strategy.md
- `_persist_tips(tips)` — inserts into CortexDB (produces duplicate key errors for existing tips — this is normal)

**Method name gotcha**: The method is `generate_tips()`, not `synthesize_from_patterns()`. Calling the wrong name gives `AttributeError: 'AutobrowseSynthesizer' object has no attribute 'synthesize_from_patterns'`.

### 4. autobrowse_graduator.py (10KB)
**Role**: Track tip survival and promote winners through lifecycle stages

**Promotion thresholds**:
```python
PROMOTION_THRESHOLDS = {
    "activate": {"applications": 5, "min_elo": 1100},
    "module": {"applications": 10, "min_elo": 1200},
    "skill": {"applications": 20, "min_elo": 1300},
}
```

**Lifecycle tracking**:
- applications, successes, failures per tip_id
- first_seen timestamp, promoted_to stage
- Elo lookup from CortexDB for promotion decisions

**Key methods**:
- `record_application(tip_id, success)` — called when tip is applied. **Takes `tip_id: str` and `success: bool`, NOT a dict**. Returns nothing; graduator tracks internally.
- `check_promotions()` — returns list of tips ready for promotion
- `build_injection()` — injects promotion status hints

**Method signature**: `record_application(self, tip_id: str, success: bool)`. Passing a dict or extra kwargs gives `TypeError: record_application() got an unexpected keyword argument 'context'`.

## CRITICAL: Hermes Core Hook Gap (RESOLVED 2026-05-09)

**Status: FIXED** — The hook signature mismatch that blocked all autobrowse capture has been resolved.

### Original Problem (pre-2026-05-09)
Hermes core `invoke_hook` in `model_tools.py` passes kwargs to `post_tool_call` hooks:
- `tool_name`, `args`, `result`, `task_id`, `session_id`, `tool_call_id`, `duration_ms`

The distillation plugin's `_on_post_tool_call` expected:
- `tool_name`, `args`, `result`, `status` (required), `error` (optional)

Python raised `TypeError: missing required positional argument: 'status'` on every tool call. This was silently swallowed by the try/except in `invoke_hook`, making the failure invisible. The hook appeared registered but NEVER FIRED.

### Fix Applied (2026-05-09)
Modified all 4 hook functions in `~/.hermes/plugins/distillation/__init__.py`:
- Added `**kwargs` to all hook signatures
- Made `status` optional with default `""`
- Added derive-status-from-result logic: `status = "error" if kwargs.get("result") is None or (isinstance(result, dict) and "error" in result) else "success"`
- Added `[autobrowse]` log lines for visibility

### Post-Fix Verification
After fix: 25 calls → 14 patterns → 14 tips → strategy.md updated. Pipeline verified live.

### NEW Pitfall: Stale Pipeline Detection (2026-05-09)
Even with the hook fix working, the pipeline can go idle. Check for activity in **BOTH** databases:

**Primary live capture: `tool_intelligence.db`** (NOT `cerebrum_memory.db`)
```python
import sqlite3
from pathlib import Path

# Check tool_intelligence.db — where live hooks write
tidb = sqlite3.connect(Path.home() / ".hermes" / "tool_intelligence.db")
c = tidb.cursor()
c.execute("SELECT COUNT(*) FROM tool_calls WHERE timestamp > ?", (time.time() - 86400,))
print('tool calls 24h (live):', c.fetchone()[0])
c.execute("SELECT tool_name, timestamp FROM tool_calls ORDER BY timestamp DESC LIMIT 5")
for row in c.fetchall():
    print(f'  {row[0]}: {datetime.fromtimestamp(row[1]).strftime("%H:%M:%S")}')
tidb.close()

# Check cerebrum_memory.db — old cortex sync path (often stale)
conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM tool_call_log WHERE created_at > datetime('now', '-24 hours')")
print('tool calls 24h (cerebrum):', c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM distilled_tips WHERE created_at > datetime('now', '-24 hours')")
print('new tips 24h:', c.fetchone()[0])
conn.close()
```

**CRITICAL**: The distillation plugin writes to `tool_intelligence.db` via `_record_tool_call_cortex()`. The `cerebrum_memory.db` `tool_call_log` table is a separate sync path that may lag or stall independently.

**If `tool_intelligence.db` shows no recent calls after a busy session, the hook has stopped firing.**

Common causes of post-fix staleness:
1. **Hermes core updated** — new `invoke_hook` signature, plugin hooks need re-audit
2. **Plugin disabled/re-enabled** — hooks re-registered but with old signatures
3. **Session restart** — `_call_counter` reset, analysis trigger (`% 20 == 0`) missed
4. **CortexDB locked** — writes fail silently, traces accumulate in memory then lost

**Recovery**: Re-run hook signature audit against current `model_tools.py`:
```bash
grep -A 5 "invoke_hook.*post_tool_call" ~/.hermes/model_tools.py
```

## References

- `references/hermes-core-hook-gap.md` — Full technical details of the hook gap and fix
- `~/.hermes/knowledge/autobrowse-hook-signature-fix.md` — Session-specific fix log

## Plugin Integration

All 4 modules are wired into `~/.hermes/plugins/distillation/__init__.py` at R191 block:

**Imports** (~line 2550):
```python
from autobrowse_tracer import get_instance as _get_ab_tracer
from autobrowse_analyzer import get_instance as _get_ab_analyzer
from autobrowse_synthesizer import get_instance as _get_ab_synth
from autobrowse_graduator import get_instance as _get_ab_grad
```

**Analysis trigger** (every 20 calls, ~line 3415):
```python
if _ab_tracer and _ab_analyzer and _ab_synth and _call_counter % 20 == 0 and _call_counter > 0:
    try:
        traces = _ab_tracer.get_recent_traces(20)
        if len(traces) >= 20:
            patterns = _ab_analyzer.analyze_traces(traces)
            if patterns:
                tips = _ab_synth.generate_tips(patterns)
                _ab_synth.update_strategy(patterns, str(tool_name)[:200])
    except Exception:
        pass
```

**Pre-LLM injections** (~line 3561):
Each module's `build_injection()` is called in sequence, producing hints like:
- `[AUTO-BROWSE] Error rate 45% in recent traces. Consider verification steps.`
- `[AUTO-BROWSE] 4 redundant calls detected. Check for repeated tool use.`
- `[AUTO-BROWSE] redundant_loop: Consider batching similar requests.`

## Singleton Pattern

All modules use thread-safe singletons:
```python
_INSTANCES: Dict[str, "ClassName"] = {}
_LOCK = threading.Lock()

def get_instance(session_id: str = "default") -> "ClassName":
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = ClassName(session_id)
        return _INSTANCES[session_id]
```

## Files
- `~/subconscious/autobrowse_tracer.py` — trace capture
- `~/subconscious/autobrowse_analyzer.py` — pattern detection
- `~/subconscious/autobrowse_synthesizer.py` — tip generation + strategy.md
- `~/subconscious/autobrowse_graduator.py` — tip lifecycle + promotion
- `~/subconscious/strategy.md` — running strategy scratchpad

## Verification

See `references/pipeline-smoke-test.md` for a complete end-to-end test recipe that exercises all 4 modules with expected outputs and common gotchas.
- `scripts/stale-pipeline-check.py` — health check script for detecting idle pipeline (checks cerebrum_memory.db; for live capture check tool_intelligence.db instead)

## References
- `references/hermes-core-hook-gap.md` — Full technical details of the hook gap and fix
- `~/.hermes/knowledge/autobrowse-hook-signature-fix.md` — Session-specific fix log

## Relationship to Training Gym

Autobrowse is the **runtime self-improvement** layer — it operates during normal agent execution, not during dedicated training rounds. It complements the training gym:
- **Training gym**: Heavy research→build→distill cycles (R168+ rounds)
- **Autobrowse**: Lightweight continuous trace analysis between training rounds

Both feed tips into the same CortexDB and Elo flywheel system.
