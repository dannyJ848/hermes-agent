# Qwen XML Tool Calling Incompatibility with vLLM

Date: 2026-05-18
Models affected: Qwen2.5-27B-Uncensored, Qwen3.6-27B-Uncensored, D-Flash variants
Root cause: Model outputs XML tool calls, vLLM expects JSON

## Problem

Qwen Uncensored models (especially D-Flash tuned variants) output tool calls in XML format:

```xml
<tool_call>
  <function name="web_search">
    <arguments>
      <query>recent AI news</query>
    </arguments>
  </function>
</tool_call>
```

But vLLM's tool parsers expect OpenAI-compatible JSON:

```json
{
  "tool_calls": [
    {
      "id": "call_123",
      "type": "function",
      "function": {
        "name": "web_search",
        "arguments": "{\"query\": \"recent AI news\"}"
      }
    }
  ]
}
```

This causes silent failures where:
1. Hermes sends tools to the model
2. Model returns XML in the content field
3. vLLM doesn't parse it as tool_calls
4. Hermes sees no tool_calls and treats it as text response
5. Tool execution never happens

## Solutions (in order of preference)

### 1. Use qwen3_xml parser (if available)

Some vLLM builds support XML parsing:

```bash
vllm serve ... \
  --tool-call-parser qwen3_xml \
  --enable-auto-tool-choice
```

**Rarely available.** Most vLLM containers don't include this parser.

### 2. Text-based tool execution (recommended workaround)

Disable auto tool choice, parse tools from text output manually:

```yaml
# In Hermes config or profile
model:
  tool_use_enforcement: text  # or disable auto tool_choice
```

Or in vLLM API calls, omit `tool_choice: auto` and parse the XML from `content` field yourself.

### 3. Use standard Qwen-Instruct (not Uncensored)

Standard Qwen2.5/3.6-Instruct models output JSON tool calls correctly:

```bash
# Use base instruct model, not uncensored
--model Qwen/Qwen2.5-27B-Instruct
```

Tradeoff: Loses uncensored/D-Flash tuning benefits.

### 4. Custom middleware wrapper

Insert a text-processing layer between Hermes and vLLM that:
1. Intercepts model output
2. Detects XML tool calls
3. Converts to JSON format
4. Returns modified response to Hermes

Example Python wrapper:
```python
def xml_to_json_tool_calls(content: str) -> list:
    """Parse Qwen XML tool calls and convert to OpenAI JSON format."""
    import re
    tool_calls = []
    # Parse <tool_call><function name="X">...</function></tool_call>
    pattern = r'<tool_call>\s*<function\s+name="([^"]+)">\s*<arguments>(.*?)</arguments>\s*</function>\s*</tool_call>'
    for match in re.finditer(pattern, content, re.DOTALL):
        name = match.group(1)
        args_xml = match.group(2)
        # Convert XML args to JSON
        args = {}
        for arg_match in re.finditer(r'<(\w+)>([^<]+)</\1>', args_xml):
            args[arg_match.group(1)] = arg_match.group(2)
        tool_calls.append({
            "id": f"call_{len(tool_calls)}",
            "type": "function",
            "function": {
                "name": name,
                "arguments": json.dumps(args)
            }
        })
    return tool_calls
```

## Verification

Test if tool calling works:

```bash
curl -s http://10.0.0.171:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "merged-lora",
    "messages": [{"role": "user", "content": "Search for recent AI news"}],
    "tools": [{"type": "function", "function": {"name": "web_search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}],
    "tool_choice": "auto",
    "max_tokens": 200
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
msg = d.get('choices',[{}])[0].get('message',{})
tc = msg.get('tool_calls',[])
content = msg.get('content','')
print('tool_calls:', json.dumps(tc, indent=2) if tc else 'NONE')
print('content:', content[:200])
print('HAS_XML:', '<tool_call>' in content)
"
```

**If `HAS_XML: True` and `tool_calls: NONE`**: The model outputs XML but vLLM doesn't parse it. Use workaround #2 or #4.

## References

- vLLM tool calling docs: https://docs.vllm.ai/en/latest/features/tool_calling.html
- Qwen tool calling format: https://huggingface.co/Qwen/Qwen2.5-27B-Instruct
