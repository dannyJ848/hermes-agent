# Qwen3.6 Tool Calling Fix: vLLM Parser Selection

## Problem

Qwen3.6-27B-Uncensored (and other Qwen3 base/uncensored variants) generate tool calls in XML format:

```xml
<tool_call>
<function=terminal>
<parameter=command>
date
</parameter>
</function>
</tool_call>
```

But vLLM's default `--tool-call-parser hermes` expects JSON format. This causes:
- `tool_calls` array to be empty (`[]`)
- vLLM parser throws `JSONDecodeError` at `hermes_tool_parser.py:114`
- Hermes Agent receives `finish_reason=tool_calls` but `tool_turns=0`
- The model appears to "think" it's using tools but nothing happens

## Root Cause

**Wrong parser selected.** The Hermes parser (`--tool-call-parser hermes`) is designed for NousResearch Hermes models that output JSON tool calls. Qwen3 models output XML tool calls and require the `qwen3_xml` parser.

## Correct Fix

Use vLLM's built-in `qwen3_xml` parser (available in vLLM 0.20.2+):

```bash
--enable-auto-tool-choice \
--tool-call-parser qwen3_xml
```

**NOT** `--tool-call-parser hermes` and **NOT** a text-based workaround.

## Complete Working vLLM Launch

```bash
docker run -d \
  --name vllm-base-lora \
  --runtime nvidia --gpus all \
  -p 8000:8000 \
  -v /data:/data \
  vllm/vllm-openai:v0.20.2 \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --max-model-len 131072 \
  --enable-lora \
  --max-lora-rank 256 \
  --lora-modules custom-model=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --speculative-config '{"method": "dflash", "model": "/data/models/Qwen3.5-27B-DFlash", "num_speculative_tokens": 5}' \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 256 \
  --gpu-memory-utilization 0.95 \
  --dtype bfloat16 \
  --trust-remote-code \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml
```

## Parser Name Gotcha

The parser name uses an **underscore**: `qwen3_xml`

NOT `qwen3xml` (will fail with `KeyError: invalid tool call parser`).

If you get the error:
```
KeyError: 'invalid tool call parser: qwen3xml (chose from { ..., qwen3_coder, qwen3_xml, ... })'
```

Use `qwen3_xml` with the underscore.

## Verification

Test with a direct API call:

```python
import requests

resp = requests.post('http://localhost:8000/v1/chat/completions', json={
    'model': '/data/models/Qwen3.6-27B-Uncensored',
    'messages': [
        {'role': 'system', 'content': 'You are a helpful assistant with access to tools.'},
        {'role': 'user', 'content': 'What is the current date? Use the terminal tool.'}
    ],
    'tools': [{
        'type': 'function',
        'function': {
            'name': 'terminal',
            'description': 'Execute shell commands',
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {'type': 'string', 'description': 'Shell command'}
                },
                'required': ['command']
            }
        }
    }],
    'tool_choice': 'auto',
    'max_tokens': 500,
    'temperature': 0.1
})

data = resp.json()
choice = data['choices'][0]
print(f"finish_reason: {choice['finish_reason']}")
print(f"tool_calls: {choice['message'].get('tool_calls', [])}")
```

Expected output:
```
finish_reason: tool_calls
tool_calls: [{'id': '...', 'type': 'function', 'function': {'name': 'terminal', 'arguments': '{"command": "date"}'}}]
```

## Available vLLM Tool Parsers (v0.20.2)

vLLM ships with parsers for many model families. For Qwen3 specifically:
- `qwen3_xml` - Qwen3 base/uncensored models (XML output format) ← **USE THIS**
- `qwen3_coder` - Qwen3 Coder variants (may have different format)
- `hermes` - NousResearch Hermes models (JSON output format) ← **WRONG for Qwen3**

To see all available parsers, trigger the error intentionally or check:
```bash
docker exec vllm-container python3 -c "
from vllm.tool_parsers import ToolParserManager
import os
files = os.listdir('/usr/local/lib/python3.12/site-packages/vllm/tool_parsers/')
print([f.replace('_tool_parser.py', '') for f in files if f.endswith('_tool_parser.py')])
"
```

## Critical Debugging Principle

> **When tool calling fails, check vLLM configuration FIRST before assuming the model is broken or building workarounds.**
>
> The model (Qwen3.6-27B-Uncensored) is fine. The issue is parser mismatch. Audit:
> 1. What parser is vLLM using? (`docker logs vllm-container | grep tool_call_parser`)
> 2. What format does the model output? (Check raw response content)
> 3. Does vLLM have a built-in parser for that format? (Check available parsers)
>
> Only after confirming no built-in parser matches should you consider custom solutions.

## Session Reference

- Date: May 17, 2026
- Context: DGX Hermes deployment with Qwen3.6-27B-Uncensored
- Initial mistake: Used `--tool-call-parser hermes` for Qwen3 model
- Correct fix: `--tool-call-parser qwen3_xml`
- User instruction: "check your setup and see where YOU made the mistake"
- Result: Tool calling works correctly with proper parser
