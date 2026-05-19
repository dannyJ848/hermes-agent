# DeepSeek API — Structured Output Discovery

## Discovery Date: 2026-05-09
## Session: Enhancement Cycle 4-6

## The Problem

`deepseek-v4-pro` (reasoning model) **cannot produce structured JSON** even with `response_format={"type": "json_object"}`.

## API Response Structure

```python
# Payload with response_format
resp = requests.post("https://api.deepseek.com/chat/completions", json={
    "model": "deepseek-v4-pro",
    "messages": [{"role": "user", "content": "Return JSON: {\"test\": 123}"}],
    "response_format": {"type": "json_object"}
})

data = resp.json()
msg = data['choices'][0]['message']

# msg structure:
{
    'role': 'assistant',
    'content': '',           # ALWAYS EMPTY for v4-pro
    'reasoning_content': 'We are asked to return JSON...'  # Prose reasoning
}
```

## The Reasoning Trap

v4-pro outputs its chain-of-thought in `reasoning_content`. It thinks about JSON but never formats the final answer as JSON in `content`. The `_extract_json_from_text()` method in `llm_judge.py` tries to parse JSON from the reasoning prose, but the reasoning is narrative — not structured.

## Verified Fix

Use `deepseek-chat` (non-reasoning) for all structured JSON tasks:

```python
# CORRECT — returns valid JSON in content
judge = LLMJudge(model="deepseek-chat")
result = judge._call_llm(
    messages=[{"role": "user", "content": 'Return JSON: {"robustness": 75}'}],
    response_format={"type": "json_object"}
)
# result: '{"robustness": 75}' — parseable
```

## Cost Comparison

| Model | Input | Output | JSON Reliable? |
|-------|-------|--------|----------------|
| deepseek-v4-pro | $0.109/M | $0.218/M | **NO** |
| deepseek-chat | $0.14/M | $0.28/M | **YES** |

## When to Use Which

| Task | Model | Why |
|------|-------|-----|
| Open-ended reasoning, comparison, critique | v4-pro | Better reasoning quality |
| Structured JSON, adversarial validation, Elo judging | chat | Reliable parseable output |
| Tip quality scoring | chat | Needs JSON verdict |
| Prompt fragment comparison | chat | Needs JSON winner |

## Migration Path

1. Check all `LLMJudge` instantiations in codebase
2. Change `model="deepseek-v4-pro"` → `model="deepseek-chat"` for JSON tasks
3. Keep v4-pro for `compare_tips()` and other open-ended evaluations
