# qwen-vllm-tool-calling-compatibility

*Researched: 2026-05-17 00:38 CDT*

## Qwen3.6-27B-Uncensored Tool Calling Issue

**Problem**: Qwen3.6-27B-Uncensored generates tool calls in XML-like format (`<tool_call><function=name><parameter=...>`) but vLLM's Hermes parser expects JSON format (`{"name": "...", "arguments": {...}}`). This causes the `tool_calls` array to be empty even though the model outputs tool-calling text.

**vLLM Error**: `JSONDecodeError: Expecting value: line 2 column 1 (char 1)` in `hermes_tool_parser.py` line 114.

**Evidence**:
- Model output: `<tool_call>\n<function=calculator>\n<parameter=expression>\n2+2\n</parameter>\n</function>\n</tool_call>`
- Expected by parser: `{"name": "calculator", "arguments": {"expression": "2+2"}}`
- Result: `tool_calls: []` (empty array)

**Workaround**: Text-based tool execution wrapper (`/tmp/autonomous_runner_v2.py`) that:
1. Disables vLLM tool calling (`enabled_toolsets=''`)
2. Parses Qwen's XML format manually with regex
3. Executes tools directly via subprocess

**Solutions to explore**:
1. Use Qwen2.5-Instruct or Qwen3-Instruct variant that supports OpenAI function calling
2. Create custom vLLM tool parser for Qwen's XML format
3. Fine-tune Qwen on Hermes tool format
4. Use text-based tool execution (current workaround)

**Config requirement**: Model name must be full path `/data/models/Qwen3.6-27B-Uncensored` in config.yaml, not just `Qwen3.6-27B-Uncensored`.

**Files**:
- Working wrapper: `/tmp/autonomous_runner_v2.py`
- Log: `/tmp/hermes_auto_v2.txt`
- vLLM parser: `/usr/local/lib/python3.12/site-packages/vllm/tool_parsers/hermes_tool_parser.py`

**Status**: Autonomous mode running in screen session `hermes_auto` with manual tool execution.

## Sources

- DGX deployment session May 17 2026
- vLLM logs
- Qwen model output analysis
