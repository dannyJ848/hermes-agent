# F-String JSON Prompt Trap

## The Problem

When building LLM prompts that contain JSON examples inside Python f-strings, the curly braces in the JSON conflict with f-string format specifiers.

```python
# CRASHES: ValueError — Invalid format specifier
prompt = f"Respond with JSON: {\"robustness\": 75, \"verdict\": \"STRONG\"}"
# Python interprets everything after the colon as a format specifier
```

## Why It Happens

F-strings parse `{...}` as format expressions. JSON uses `{...}` for objects. When JSON keys/values contain colons, Python treats the colon as a format specifier separator.

## Solutions (in order of preference)

### 1. Use `%` Formatting (Safest for JSON)
```python
prompt = """Respond with JSON: {"robustness": 75, "verdict": "STRONG"}
Condition: %s
Recommendation: %s""" % (condition, recommendation)
```

### 2. Double-Brace Escape in F-Strings
```python
prompt = f"Respond with JSON: {{\"robustness\": 75, \"verdict\": \"STRONG\"}}"
# Double {{ and }} to escape f-string parsing
```

### 3. Use `str.format()` with Named Placeholders
```python
prompt = """Respond with JSON: {"robustness": 75, "verdict": "STRONG"}
Condition: {condition}
Recommendation: {rec}""".format(condition=condition, rec=recommendation)
```

### 4. Separate JSON Template from Variables
```python
json_template = '{"robustness": 75, "verdict": "STRONG"}'
prompt = f"Respond with this format: {json_template}\nCondition: {condition}"
```

## When Each Applies

| Method | Best For | Avoid When |
|--------|----------|------------|
| `%` formatting | Simple variable substitution | Complex nested structures |
| Double-brace | Single JSON example in prompt | Multiple nested objects |
| `str.format()` | Named placeholders, readability | Quick one-liners |
| Separate template | Reusable JSON schemas | Inline prompts |

## Real-World Impact

This bug blocked the adversarial batch in Enhancement Cycle 4. Five tips went untested until the formatting method was switched from f-string to `%` formatting.

**Rule:** When a prompt contains both JSON examples AND variable substitution, default to `%` formatting or `str.format()`. Never use bare f-strings with inline JSON.
