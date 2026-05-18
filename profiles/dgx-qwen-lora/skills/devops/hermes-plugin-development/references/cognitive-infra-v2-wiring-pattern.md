# Cognitive Infrastructure V2 Wiring Pattern

**Session:** 2026-05-09  
**Context:** Wiring 5 novel cognitive systems into `~/.hermes/plugins/distillation/__init__.py`

## The Problem

User built 5 cognitive systems in `~/subconscious/cognitive_infrastructure_v2.py`:
- InjectionGovernorV2 — drop logging + feedback loop
- CreditAssigner — tip-to-outcome correlation
- SessionEndExtractor — auto-extract lessons on session close
- ToolIntelligenceRouter — active routing before tool selection
- AutoSkillCron — monthly autonomous skill generation

But they were **not producing data** — tables remained empty because the systems were built but not wired into the live agent loop.

## User Correction

> "what's the point of building anything if you're not wiring it in?"
> "remember you can re-write the hermes code"

## The Solution

### Step 1: Import with Graceful Degradation

```python
# At top of plugin __init__.py (after existing imports, before hook functions)
_COGNITIVE_INFRA_V2 = False
try:
    import sys
    _subconscious_path = os.path.expanduser("~/subconscious")
    if _subconscious_path not in sys.path:
        sys.path.insert(0, _subconscious_path)
    from cognitive_infrastructure_v2 import (
        get_governor_v2, get_credit_assigner,
        get_session_extractor, get_tool_router, get_auto_skill
    )
    _COGNITIVE_INFRA_V2 = True
except Exception as _civ2_err:
    pass  # Silently fail — don't break existing hooks
```

**Why this pattern:**
- Plugin loads even if `~/subconscious/` module is broken
- Existing behavior preserved when flag is False
- No external dependencies required for plugin to function

### Step 2: Wire into Existing Hooks

**pre_llm_call — Tool Router + Governor:**
```python
def _on_pre_llm_call(user_message: str, context: dict = None, **kwargs) -> Optional[str]:
    # ... existing injection logic ...
    
    # Cognitive Infrastructure V2: Tool Intelligence Router
    if _COGNITIVE_INFRA_V2 and user_message:
        try:
            tr = get_tool_router()
            weak_tools = ["cronjob", "delegate_parallel"]
            for tool in weak_tools:
                if tool in str(user_message).lower():
                    rec = tr.recommend(tool)
                    if rec.get("warning"):
                        injection_lines.append((f"[WARNING: {rec['warning']}]", 0))
                        injected_count += 1
            
            # Log injection attempt to governor — MUST be after final_lines is assembled
            # Wrong: calling gov.log_attempt before injection_lines is populated = empty logs
            # Correct: log after trim_to_budget, before returning
            if injection_lines:
                gov = get_governor_v2()
                gov.turn_number += 1
                for line, priority in injection_lines:
                    injected = line in final_lines
                    drop_reason = "" if injected else "budget"
                    gov.log_attempt(
                        tip_id=0, condition=line[:200], priority=priority,
                        injected=injected, drop_reason=drop_reason,
                        chars_used=len(line), lines_used=len(final_lines)
                    )
        except Exception:
            pass
    
    # ... rest of existing logic ...
```

**post_tool_call — Credit Assigner + Router:**
```python
def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                        status: str = "", error: str = "", **kwargs) -> Optional[dict]:
    # ... existing logic ...
    
    # Cognitive Infrastructure V2: Credit Assigner
    if _COGNITIVE_INFRA_V2:
        try:
            ca = get_credit_assigner()
            ca.record_outcome(tool_name, is_success, error)
        except Exception:
            pass
    
    # Cognitive Infrastructure V2: Tool Router
    if _COGNITIVE_INFRA_V2:
        try:
            tr = get_tool_router()
            tr.log_decision(tool_name, "proceed" if is_success else "caution",
                           "success" if is_success else f"failure:{error[:50]}")
        except Exception:
            pass
```

**session_end — Session Extractor:**
```python
def _on_session_end(session_id: str = "", tool_calls: list = None, **kwargs) -> Optional[dict]:
    """Session end: extract lessons and save to rapid_learnings."""
    
    if _COGNITIVE_INFRA_V2:
        try:
            se = get_session_extractor()
            se.session_id = session_id or os.environ.get("HERMES_SESSION_ID", "default")
            # Fallback to _current_chain if core doesn't pass tool_calls
            calls = tool_calls if tool_calls else _current_chain
            lessons = se.extract(calls)
            if lessons:
                se.save_lessons(lessons)
                return {"lessons_extracted": len(lessons), "status": "ok"}
        except Exception:
            pass
    
    return None
```

### Step 3: Verify Wiring

```bash
# 1. Syntax check
python3 -c "import py_compile; py_compile.compile('~/.hermes/plugins/distillation/__init__.py', doraise=True)"

# 2. Import test (lightweight, no full agent load)
python3 -c "
import sys
sys.path.insert(0, '/Users/dannygomez/subconscious')
sys.path.insert(0, '/Users/dannygomez/.hermes/plugins/distillation')
import __init__ as d
print('Cognitive infra v2:', d._COGNITIVE_INFRA_V2)
print('Hooks:', hasattr(d, '_on_pre_llm_call'), hasattr(d, '_on_post_tool_call'), hasattr(d, '_on_session_end'))
"

# 3. Data flow verification (after live tool calls)
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM skill_rewards;"
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM tool_routing_decisions;"
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM tip_injection_attempts;"
```

## Key Lessons

1. **Build → Wire → Verify** — Never build the next system until the current one is verified
2. **Use `_FLAG` pattern** — All external imports must have a boolean flag with graceful fallback
3. **Wrap in try/except** — External module crashes must not break the original plugin
4. **Use `**kwargs`** — Hook signatures must absorb all kwargs from `invoke_hook`
5. **Derive missing data** — Core may not pass all params; derive from available data
6. **Fallback to plugin state** — When core doesn't pass data (e.g. `tool_calls`), use plugin globals like `_current_chain`

## Anti-Patterns Avoided

| Anti-Pattern | Why Wrong | What We Did Instead |
|-------------|-----------|---------------------|
| Cron jobs to call module | 17% success, no session state | Patched live hooks |
| New plugin with duplicate hooks | Fragmented, harder to debug | Extended existing plugin |
| Standalone scripts | Never integrated, dead code | Hook wiring in `__init__.py` |
| Building without verifying | Tables empty, user frustration | Verified with `SELECT COUNT(*)` |

## Files from This Session

- `~/subconscious/cognitive_infrastructure_v2.py` — 5 novel systems
- `~/subconscious/cognitive_infrastructure_hooks.py` — Hook wiring module
- `~/subconscious/tool_intelligence_integration.py` — Active routing
- `~/.hermes/plugins/distillation/__init__.py` — **4 patches** (import block, pre_llm, post_tool, session_end)
