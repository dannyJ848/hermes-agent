# Wiring Cognitive Infrastructure V2 into Distillation Plugin

**Session:** 2026-05-09  
**Goal:** Activate 5 novel cognitive systems built in Cycle 6 by patching the live distillation plugin  
**Plugin:** `~/.hermes/plugins/distillation/__init__.py` (7128 lines)  
**External module:** `~/subconscious/cognitive_infrastructure_v2.py`  

## Systems Being Wired

| System | Hook | What it does |
|--------|------|-------------|
| InjectionGovernorV2 | pre_llm_call | Drop logging + feedback loop |
| CreditAssigner | post_tool_call | Tip-to-outcome correlation |
| SessionEndExtractor | session_end | Auto-extract lessons on close |
| ToolIntelligenceRouter | pre_llm_call | Active routing warnings |
| AutoSkillCron | N/A (cron) | Monthly skill generation |

## Step 1: Add Import Block

Location: After existing imports, around line 90  
Pattern: `_FLAG = False` with silent fallback

```python
# ── Cognitive Infrastructure V2 (Cycle 6) ──
_COGNITIVE_INFRA_V2 = False
try:
    import sys
    _subconscious_path = os.path.expanduser("~/subconscious")
    if _subconscious_path not in sys.path:
        sys.path.insert(0, _subconscious_path)
    from cognitive_infrastructure_v2 import (
        get_governor_v2, get_credit_assigner, get_session_extractor,
        get_tool_router, get_auto_skill
    )
    _COGNITIVE_INFRA_V2 = True
except Exception as _civ2_err:
    pass  # Silently fail — don't break existing hooks
```

## Step 2: Wire pre_llm_call Hook

Location: Before injection line collection, around line 3693  
Adds: ToolIntelligenceRouter warnings + CreditAssigner bridge setup

```python
# ── Cognitive Infrastructure V2: Tool Intelligence Router ──
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
    except Exception:
        pass

# ── Cognitive Infrastructure V2: Credit Assigner bridge ──
_civ2_credit_bridge = {}
```

## Step 3: Wire post_tool_call Hook

Location: After existing credit assignment, around line 3349  
Adds: CreditAssigner.record_outcome + ToolRouter.log_decision

```python
# ── Cognitive Infrastructure V2: Credit Assigner ──
if _COGNITIVE_INFRA_V2:
    try:
        ca = get_credit_assigner()
        ca.record_outcome(tool_name, is_success, error)
    except Exception:
        pass

# ── Cognitive Infrastructure V2: Tool Router ──
if _COGNITIVE_INFRA_V2:
    try:
        tr = get_tool_router()
        tr.log_decision(tool_name, "proceed" if is_success else "caution",
                        "success" if is_success else f"failure:{error[:50]}")
    except Exception:
        pass
```

## Step 4: Wire Injection Bridge

Location: After injection result is assembled, before dedup check, around line 7038  
Purpose: Connect the plugin's `_injected_tips_this_turn` to CreditAssigner

```python
result = "\n".join(final_lines)

# ── Cognitive Infrastructure V2: Record injected tips for credit assignment ──
if _COGNITIVE_INFRA_V2:
    try:
        ca = get_credit_assigner()
        for tool_name, tip_ids in _injected_tips_this_turn.items():
            for tip_id in tip_ids:
                ca.record_injection(tool_name, tip_id)
    except Exception:
        pass
```

## Step 5: Add session_end Hook

Location: Bottom of file, after adversarial batch function  
New function: `_on_session_end`

```python
def _on_session_end(session_id: str = "", tool_calls: list = None, **kwargs) -> Optional[dict]:
    """Session end: extract lessons and save to rapid_learnings."""
    if _COGNITIVE_INFRA_V2 and tool_calls:
        try:
            se = get_session_extractor()
            se.session_id = session_id or os.environ.get("HERMES_SESSION_ID", "default")
            lessons = se.extract(tool_calls)
            if lessons:
                se.save_lessons(lessons)
                return {"lessons_extracted": len(lessons), "status": "ok"}
        except Exception:
            pass
    return None
```

## Verification Steps

1. **Syntax check:**
   ```bash
   python3 -c "import py_compile; py_compile.compile('plugin.py', doraise=True)"
   ```

2. **Import test:**
   ```bash
   cd ~/.hermes/plugins/distillation && python3 -c "
   import sys; sys.path.insert(0, '/Users/dannygomez/subconscious')
   import __init__ as dist
   print('Cognitive infra v2 enabled:', dist._COGNITIVE_INFRA_V2)
   print('Tool router:', dist.get_tool_router() is not None)
   print('Credit assigner:', dist.get_credit_assigner() is not None)
   print('Session extractor:', dist.get_session_extractor() is not None)
   "
   ```

3. **Data flow test:**
   ```python
   from cognitive_infrastructure_v2 import get_credit_assigner
   ca = get_credit_assigner()
   ca.record_injection("execute_code", 12345)
   ca.record_outcome("execute_code", True, "")
   # Verify: SELECT COUNT(*) FROM skill_rewards should increase
   ```

## Key Pitfalls from This Session

- **CreditAssigner needs record_injection BEFORE record_outcome** — the post_tool_call hook only writes if the pre_llm_call hook recorded pending tips first. The bridge at line 7038 solves this.
- **Hook signature mismatch** — `_on_session_end` must have `**kwargs` because `invoke_hook` may pass extra parameters. Without it, the hook silently fails.
- **Don't test by loading the full plugin** — the distillation plugin is 7128 lines and times out on import. Test components individually via `execute_code`.
- **Cron jobs are not the answer** — the cronjob tool has 17% success. Wire into live hooks instead.

## Files Modified

- `~/.hermes/plugins/distillation/__init__.py` — 4 patches (import block, pre_llm_call, post_tool_call, injection bridge, session_end hook)
- `~/subconscious/cognitive_infrastructure_v2.py` — already existed, now being called
- `~/subconscious/cognitive_infrastructure_hooks.py` — hook wiring module
- `~/subconscious/tool_intelligence_integration.py` — active routing module
