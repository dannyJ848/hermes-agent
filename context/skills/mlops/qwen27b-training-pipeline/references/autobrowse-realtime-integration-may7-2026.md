# Autobrowse Real-Time Integration — May 7, 2026

## Problem
Autobrowse R191 (tracer→analyzer→synthesizer→graduator pipeline) was wired into the learning-brain plugin's `post_tool_call_hook`, but it only fires every 20 tool calls and the tips go to the context DB for cross-session use. Within a single CLI session, the agent gets zero real-time feedback from its own tool usage patterns.

## Solution: Direct Injector Pattern

Build a standalone `autobrowse_injector.py` that the agent can import and call explicitly after each tool call. This gives immediate pattern detection within the same session.

### Architecture

```
Tool Call → record_tool_call() → Tracer → get_tips_for_last_calls() → Tips
```

### API

```python
from hermes_cli.subconscious.autobrowse_injector import (
    record_tool_call,
    get_tips_for_last_calls,
    format_tips_for_prompt,
)

# After every tool call:
record_tool_call("terminal", {"command": "ssh ..."}, result, success=True, duration_ms=2000)

# When you want tips:
tips = get_tips_for_last_calls(n=10)
if tips:
    print(format_tips_for_prompt(tips))
```

### Method Mapping (Critical — the autobrowse modules use different names than expected)

| What you expect | Actual method | Args |
|-----------------|---------------|------|
| `tracer.record()` | `tracer.record_call()` | `tool_name, model_used, input_data, output_data, execution_time_ms, status, error_type, error_message` |
| `analyzer.analyze()` | `analyzer.analyze_traces()` | `traces` → returns patterns |
| `synthesizer.synthesize()` | `synthesizer.generate_tips()` | `patterns` → returns tips |
| `graduator.graduate()` | `graduator.check_promotions()` | no args (reads internal state) |

**Trap:** The initial plugin wiring used wrong method names (`record`, `analyze`, `synthesize`, `graduate`) which don't exist. Fixed in commit f7d52d5fa.

### Fallback Pattern Detection

When `analyze_traces()` returns 0 patterns (needs 5+ traces for ML-based detection), the injector falls back to heuristic detection:

1. **Failure pattern**: 2+ failed calls to same tool → "Tool X failed N times recently. Consider alternative approach."
2. **Repetition pattern**: 3+ calls to same tool → "Using 'X' N times in last M calls. Verify this is necessary."

### Files

- `hermes_cli/subconscious/autobrowse_injector.py` — standalone injector
- `hermes_cli/subconscious/autobrowse_tracer.py` — tracer module
- `hermes_cli/subconscious/autobrowse_analyzer.py` — analyzer module
- `hermes_cli/subconscious/autobrowse_synthesizer.py` — synthesizer module
- `hermes_cli/subconscious/autobrowse_graduator.py` — graduator module

### Integration Status

- Plugin hook: fires every 20 calls via `post_tool_call_hook` (cross-session persistence)
- Direct injector: callable on-demand within session (real-time feedback)
- Both paths write to the same tracer instance (if same process)

### Commit

`f08825c61` — "Add autobrowse_injector.py: direct real-time tip feedback for CLI sessions"
