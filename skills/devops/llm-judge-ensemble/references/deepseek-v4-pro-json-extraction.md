# DeepSeek V4 Pro JSON Extraction — Session Notes (May 9, 2026)

## Discovery

`deepseek-v4-pro` (reasoning model) **cannot produce structured JSON output** via the chat completions API, regardless of `response_format` or system prompts.

## Verified Behavior

Tested 5+ consecutive calls with `response_format={"type": "json_object"}`:

```python
payload = {
    "model": "deepseek-v4-pro",
    "messages": [{"role": "user", "content": 'Return JSON: {"test": 123}'}],
    "response_format": {"type": "json_object"}
}
```

Response structure:
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "",
      "reasoning_content": "We are asked to return JSON... [prose reasoning chain, no JSON]"
    }
  }]
}
```

- `content`: always `""` (empty string)
- `reasoning_content`: chain-of-thought prose explaining the reasoning
- `parsed` field: absent
- `finish_reason`: `"stop"` (not length-limited)

## Root Cause

V4 Pro is a **reasoning model** (like o1). Its architecture emits reasoning tokens into `reasoning_content` and final answers into `content`. But when the "final answer" is supposed to be JSON, the model instead emits its reasoning about what the JSON should contain — and never outputs the actual JSON object.

The `_extract_json_from_text()` fallback in `llm_judge.py` fails because:
1. The reasoning text ends with "I'll assign robustness 75" not `{`...
2. No JSON structure appears anywhere in the reasoning

## Workaround: Use deepseek-chat

`deepseek-chat` (non-reasoning) works correctly with `response_format`:

```python
judge = LLMJudge(model="deepseek-chat")
result = judge._call_llm(
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"}
)
# result = '{"robustness": 80, "verdict": "STRONG", ...}'
```

## Updated Routing Table

| Task Type | Model | Response Format | Result |
|-----------|-------|-----------------|--------|
| Open reasoning, comparison | `deepseek-v4-pro` | No format | Prose analysis in `content` |
| Structured JSON | `deepseek-v4-pro` | `json_object` | Empty `content`, prose reasoning |
| Structured JSON | `deepseek-chat` | `json_object` | Valid JSON in `content` |
| Quick eval, cost-sensitive | `deepseek-chat` | `json_object` | Valid JSON, ~2s latency |

## Files

- `~/subconscious/llm_judge.py` — `_call_llm()` method
- `~/.hermes/config.yaml` — provider config

## Session Reference

Confirmed in enhancement cycle 4 (2026-05-09) when adversarial batch testing failed 5x with UNKNOWN verdicts before switching to `deepseek-chat`.
