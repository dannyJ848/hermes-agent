# vLLM Tool Parser Discovery Reference

## Problem
When deploying Qwen models with vLLM tool calling, you must match the model's output format to the correct parser. Using the wrong parser causes silent failures — the model outputs tool calls but vLLM returns empty `tool_calls` arrays.

## Parser Names vs Class Names

vLLM has TWO naming conventions:

| What you see in code | What you pass on CLI |
|---------------------|---------------------|
| `Qwen3XMLToolParser` | `qwen3_xml` |
| `Qwen3CoderToolParser` | `qwen3_coder` |
| `HermesToolParser` | `hermes` |
| `LlamaToolParser` | `llama3_json` |

**Rule:** CLI names use `snake_case`, class names use `CamelCase`.

## How to List Available Parsers

### Method 1: Check the filesystem (works in running container)
```bash
docker exec vllm-base-lora ls /usr/local/lib/python3.12/site-packages/vllm/tool_parsers/
# Look for files matching your model:
# qwen3xml_tool_parser.py -> CLI: qwen3_xml
# qwen3coder_tool_parser.py -> CLI: qwen3_coder
```

### Method 2: Trigger the error (vLLM lists all valid names)
```bash
# Start with an INVALID parser name, vLLM will list all valid ones in the error
docker run --rm vllm/vllm-openai:v0.20.2 --tool-call-parser INVALID_NAME
# KeyError: 'invalid tool call parser: INVALID_NAME (chose from { hermes, qwen3_xml, qwen3_coder, ... })'
```

### Method 3: Read source directly
```bash
docker exec vllm-base-lora grep -r "class.*ToolParser" /usr/local/lib/python3.12/site-packages/vllm/tool_parsers/
# Map class names to CLI names by converting CamelCase -> snake_case
```

## Qwen Model -> Parser Mapping

| Model | CLI Flag | Why |
|-------|----------|-----|
| Qwen3.6-27B-Uncensored | `--tool-call-parser qwen3_xml` | Base Qwen3 models use XML tool format |
| Qwen3.6-27B-Coder | `--tool-call-parser qwen3_coder` | Coder variants may use different format |
| Qwen2.5-Instruct | `--tool-call-parser hermes` | Instruct models often use JSON/Hermes format |
| Qwen2.5-Coder | `--tool-call-parser hermes` or `qwen3_coder` | Check model card |

## Verification After Restart

```bash
# 1. Check vLLM logs confirm parser loaded
docker logs vllm-base-lora 2>&1 | grep "tool_call_parser"
# Should show: 'tool_call_parser': 'qwen3_xml'

# 2. Test with a simple tool call
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/data/models/Qwen3.6-27B-Uncensored",
    "messages": [{"role": "user", "content": "Run date command"}],
    "tools": [{"type": "function", "function": {"name": "terminal", "description": "Run shell commands", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}],
    "tool_choice": "auto"
  }'

# 3. Check response has non-empty tool_calls array
# Correct: {"choices": [{"message": {"tool_calls": [{"function": {"name": "terminal", ...}}]}}]}
# Broken: {"choices": [{"message": {"tool_calls": []}}]} or missing tool_calls entirely
```

## Common Mistakes

1. **Using `hermes` parser with Qwen base models** — Hermes expects JSON, Qwen outputs XML
2. **Using `qwen3xml` instead of `qwen3_xml`** — CLI requires snake_case with underscore
3. **Not restarting vLLM after changing parser** — Parser is set at startup, not runtime
4. **Checking `finish_reason=tool_calls` only** — This just means model WANTED tools, not that they were parsed correctly. Always verify `tool_calls` array is non-empty.

## Session History

- May 17, 2026: Initially deployed with `--tool-call-parser hermes` (WRONG)
- May 17, 2026: Tried text-based wrapper workaround (did not work — agent loop consumes response)
- May 17, 2026: Discovered `qwen3_xml` parser in vLLM 0.20.2 filesystem
- May 17, 2026: Restarted vLLM with `--tool-call-parser qwen3_xml` (CORRECT)
