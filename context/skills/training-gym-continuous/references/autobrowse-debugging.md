# Autobrowse Debugging — May 8, 2026

## Problem
Autobrowse tracer buffer was empty (0 traces) despite being wired in the distillation plugin.

## Root Causes Found

### 1. Silent exception swallowing
The original code used `except Exception: pass` on trace capture, hiding any failures.

**Fix:** Added debug logging:
```python
except Exception as e:
    logger.warning(f"Autobrowse trace capture failed: {e}")
```

### 2. Analysis trigger fired every call (not every 20)
The original condition was `if _ab_tracer and _ab_analyzer and _ab_synth:` — this fires on EVERY tool call, not every 20. The analyzer ran constantly with <20 traces, producing no patterns.

**Fix:** Changed to `_call_counter % 20 == 0 and _call_counter > 0`:
```python
if _ab_tracer and _ab_analyzer and _ab_synth and _call_counter % 20 == 0 and _call_counter > 0:
```

### 3. Undefined `user_message` in post_tool_call context
The analysis block referenced `user_message` which doesn't exist in `_on_post_tool_call` scope. This would have raised NameError (swallowed by `except Exception: pass`).

**Fix:** Use `tool_name` as fallback context:
```python
_ab_synth.update_strategy(patterns, str(tool_name)[:200])
```

### 4. Added success logging
```python
logger.info(f"Autobrowse: analyzed {len(traces)} traces, found {len(patterns)} patterns, generated {len(tips)} tips")
```

## Verification
Direct module test (bypassing plugin) confirmed pipeline works:
- 25 simulated traces → stats captured
- Analyzer → 2 redundant_loop patterns detected
- Synthesizer → 2 efficiency tips generated

## Plugin wiring location
`~/.hermes/plugins/distillation/__init__.py` lines ~3398-3430 (R191 block)

## Files involved
- `~/.hermes/plugins/distillation/__init__.py` — plugin hooks
- `~/subconscious/autobrowse_tracer.py` — trace capture
- `~/subconscious/autobrowse_analyzer.py` — pattern detection
- `~/subconscious/autobrowse_synthesizer.py` — tip generation
- `~/subconscious/autobrowse_graduator.py` — tip promotion
- `~/subconscious/strategy.md` — cross-session scratchpad
