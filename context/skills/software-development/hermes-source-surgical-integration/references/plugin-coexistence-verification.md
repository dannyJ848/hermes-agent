# Plugin Coexistence Verification — July 2026

## Context
After integrating cognitive-systems plugin alongside the bundled learning-brain plugin, both register overlapping hooks. This reference documents the verification pattern.

## Verification Output

```
Plugin loaded: True
on_session_start: 2 handler(s)
  - on_session_start_hook        [learning-brain]
  - _on_session_start_handler    [cognitive-systems]
pre_tool_call: 4 handler(s)
  - pre_tool_call_hook           [learning-brain]
  - _pre_tool_call_handler       [cognitive-systems]
  - _on_pre_tool_call            [other]
  - on_pre_tool_call             [other]
post_tool_call: 4 handler(s)
  - post_tool_call_hook          [learning-brain]
  - _post_tool_call_handler      [cognitive-systems]
  - _on_post_tool_call           [other]
  - on_post_tool_call            [other]
on_session_end: 2 handler(s)
  - on_session_end_hook          [learning-brain]
  - _on_session_end_handler      [cognitive-systems]
pre_llm_call: 3 handler(s)
  - _pre_llm_call_handler        [cognitive-systems]
  - _on_pre_llm_call             [other]
  - on_pre_llm_call              [other]
post_llm_call: 1 handler(s)
  - _post_llm_call_handler       [cognitive-systems]
post_api_request: 1 handler(s)
  - _on_post_api_request         [cognitive-systems]
```

## Key Finding
Both plugins coexist safely. The Hermes plugin manager fires all handlers in sequence for each hook event. No conflicts detected.

## Python Environment Note
Must use venv python3 (3.11.14), not system python3 (3.8.8):
```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 -c "..."
```
