# Qwen XML Tool Format vs vLLM Hermes Parser Mismatch (May 17 2026)

## Problem

Qwen3.6-27B-Uncensored outputs tool calls in XML-like format:
```xml
<tool_call>
<function=calculator>
<parameter=expression>
2+2
</parameter>
</function>
</tool_call>
```

But vLLM's Hermes tool parser expects JSON format:
```json
{"name": "calculator", "arguments": {"expression": "2+2"}}
```

## Symptom

- vLLM logs show: `Error in extracting tool call from response` with `JSONDecodeError`
- Model returns `finish_reason=tool_calls` but `tool_calls=[]` (empty array)
- Model generates text describing tool usage but tools never execute
- Hermes agent shows "tool_turns=0" despite model claiming to use tools

## Verification

Test with curl:
```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "/data/models/Qwen3.6-27B-Uncensored",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "tools": [{"type": "function", "function": {"name": "calculator", "description": "Calculate math", "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}}]
  }'
```

Response will show:
- `content` field contains XML tool_call tags
- `tool_calls` array is empty
- `finish_reason: "stop"` (not "tool_calls")

## Root Cause

Qwen3.6 was trained on a different tool format than the OpenAI function calling format that vLLM's Hermes parser expects. The model understands tools conceptually but outputs them in its native XML format.

## Solutions

### Option 1: Text-Based Tool Execution (Recommended for Qwen3.6)

Disable native tool calling and parse the model's text output manually:

```python
import re
import subprocess

def parse_tool_calls(text):
    """Parse Qwen XML tool calls from model output."""
    tool_calls = []
    tool_pattern = r'<tool_call>\s*<function=(\w+)>\s*(.*?)</function>\s*</tool_call>'
    matches = re.findall(tool_pattern, text, re.DOTALL)
    
    for func_name, params_text in matches:
        params = {}
        param_pattern = r'<parameter=(\w+)>\s*(.*?)\s*</parameter>'
        param_matches = re.findall(param_pattern, params_text, re.DOTALL)
        for param_name, param_value in param_matches:
            params[param_name] = param_value.strip()
        
        tool_calls.append({'name': func_name, 'arguments': params})
    
    return tool_calls

def execute_tool(tool_name, arguments):
    if tool_name == 'terminal':
        cmd = arguments.get('command', '')
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
    elif tool_name == 'web_search':
        query = arguments.get('query', '')
        # Implement web search
        pass
    # ... other tools
```

### Option 2: Use Qwen2.5-Instruct or Hermes-Format Models

Models specifically fine-tuned for function calling (Qwen2.5-Instruct, Hermes-3, etc.) output proper JSON tool_calls that vLLM can parse.

### Option 3: Custom Tool Parser for vLLM

Develop a custom vLLM tool parser that understands Qwen's XML format. This requires modifying vLLM's tool parser pipeline.

## Impact on Autonomous Agents

When building autonomous agents with Qwen3.6:
- Native tool calling will NOT work
- Must use text-based tool execution
- Agent loop needs manual tool parsing between iterations
- Consider switching to Qwen2.5-Instruct for tool-heavy workloads

## Files

- `/tmp/autonomous_runner_v2.py` — Example text-based autonomous runner for DGX
