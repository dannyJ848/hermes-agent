# autobrowse-hook-signature-fix

*Researched: 2026-05-09 10:30 CDT*

# Autobrowse Pipeline Fix — 2026-05-09

## Problem
The autobrowse self-improvement pipeline (tracer → analyzer → synthesizer → graduator) was fully built but never captured real tool calls. The distillation plugin's hooks appeared registered but silently failed on every invocation.

## Root Cause
Hermes core `invoke_hook` in `model_tools.py` passes specific kwargs to `post_tool_call` hooks:
- `tool_name`, `args`, `result`, `task_id`, `session_id`, `tool_call_id`, `duration_ms`

The distillation plugin's `_on_post_tool_call` expected:
- `tool_name`, `args`, `result`, `status` (required), `error` (optional)

Python raised `TypeError: missing required positional argument: 'status'` on every tool call. This was silently swallowed by the try/except in `invoke_hook`, making the failure invisible.

## Fix Applied
Modified all 4 hook functions in `~/.hermes/plugins/distillation/__init__.py`:

1. `_on_post_tool_call`: `status: str = ""` + `**kwargs`, with status derivation from result
2. `_on_pre_tool_call`: Added `**kwargs`
3. `_on_pre_llm_call`: Added `**kwargs`
4. `_on_post_api_request`: `latency_ms: float = 0` + `**kwargs`

Added `[autobrowse]` log lines for visibility.

## Verification
Live test: 25 simulated tool calls → 14 patterns detected → 14 tips generated → `autobrowse_strategy.md` updated.

## Key Lesson
When debugging Hermes plugin hooks, always verify the exact kwargs `invoke_hook` passes match the hook's signature. Add `**kwargs` defensively to all hook callbacks.


## Sources

- ~/.hermes/plugins/distillation/__init__.py
- /Users/dannygomez/hermes-agent/model_tools.py
