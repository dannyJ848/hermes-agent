# vLLM Tool Calling Requirements for Hermes Integration

## Problem

When Hermes Agent connects to vLLM for local inference, it sends requests with `tool_choice: "auto"` by default. If vLLM is not configured with tool calling support, this produces:

```
HTTP 400: "auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set
```

This prevents Hermes from using the local vLLM endpoint entirely.

## Required vLLM Flags

For Hermes Agent compatibility, vLLM MUST be started with:

```bash
--enable-auto-tool-choice \
--tool-call-parser <PARSER_NAME>
```

## CRITICAL: Parser Must Match Model Family

The `--tool-call-parser` must match the **model's output format**, not just "hermes" by default.

| Model Family | Parser | Output Format |
|-------------|--------|---------------|
| Nous Hermes, Llama 3.1+ Instruct | `hermes` | JSON |
| **Qwen3 base/uncensored** | **`qwen3_xml`** | **XML** |
| Qwen3 Coder | `qwen3_coder` | XML (Coder variant) |
| DeepSeek V3 | `deepseek_v3` | JSON |
| Mistral | `mistral` | JSON |
| InternLM2 | `internlm` | JSON |

### Common Mistake

Using `--tool-call-parser hermes` with Qwen3 models:
```bash
# WRONG for Qwen3 — causes empty tool_calls array
--tool-call-parser hermes
```

Qwen3 outputs XML tool calls like:
```xml
<tool_call>
<function=terminal>
<parameter=command>date</parameter>
</function>
</tool_call>
```

The Hermes parser expects JSON and fails with `JSONDecodeError`, producing empty `tool_calls`.

### Correct for Qwen3

```bash
# CORRECT for Qwen3
--tool-call-parser qwen3_xml
```

## Complete Working Example (Qwen3)

```bash
docker run -d \
  --name vllm-hermes-compatible \
  --runtime nvidia --gpus all \
  -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/SpecForge/custom_dflash/checkpoints \
  -e CUDA_VISIBLE_DEVICES=0 \
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

## How to Identify the Right Parser

1. **Check what format the model outputs**: Send a test request and inspect raw response content
2. **List available vLLM parsers**:
   ```bash
   docker exec vllm-container ls /usr/local/lib/python3.12/site-packages/vllm/tool_parsers/
   ```
   Each `_tool_parser.py` file corresponds to a parser name (remove suffix, replace `_` with parser naming convention).
3. **Trigger error for full list**: Use a wrong parser name and vLLM will list all valid options in the `KeyError` message.

## Verification

Test tool calling works:
```bash
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/data/models/Qwen3.6-27B-Uncensored",
    "messages": [{"role": "user", "content": "What is the weather?"}],
    "tools": [{"type": "function", "function": {"name": "get_weather", "description": "Get weather", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}}}],
    "tool_choice": "auto"
  }'
```

Verify response contains non-empty `tool_calls` array.

## Debugging Empty tool_calls

If `finish_reason: tool_calls` but `tool_calls: []`:

1. Check vLLM parser: `docker logs vllm-container | grep tool_call_parser`
2. Check model output format: inspect raw response `content` field
3. Verify parser matches format (JSON parser + XML output = empty array)
4. **DO NOT build text-based workarounds until confirming no built-in parser exists**

## Without Tool Calling (Fallback)

If tool calling cannot be enabled, configure Hermes to disable tool use:
```yaml
agent:
  tool_use_enforcement: disabled
```

But this significantly reduces Hermes capabilities. Always prefer enabling correct tool calling on vLLM.

## Session Reference

- Date: May 16-17, 2026
- Context: DGX Hermes deployment with Qwen3.6-27B-Uncensored + dynamic LoRA
- Initial error: HTTP 400 on first Hermes request to vLLM (missing flags)
- Second error: Empty tool_calls with `--tool-call-parser hermes` on Qwen3
- Correct fix: `--tool-call-parser qwen3_xml` for Qwen3 models
- User instruction: "check your setup and see where YOU made the mistake"
