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
--tool-call-parser hermes
```

The `--tool-call-parser hermes` flag tells vLLM to use the Hermes-format tool calling parser (based on the NousResearch Hermes model format).

## Complete Working Example

```bash
docker run -d \
  --name vllm-hermes-compatible \
  --runtime nvidia --gpus all \
  -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/SpecForge/custom_dflash/checkpoints \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
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
  --tool-call-parser hermes
```

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

## Without Tool Calling (Fallback)

If tool calling cannot be enabled, configure Hermes to disable tool use:
```yaml
agent:
  tool_use_enforcement: disabled
```

But this significantly reduces Hermes capabilities. Always prefer enabling tool calling on vLLM.

## Session Reference

- Date: May 16, 2026
- Context: DGX Hermes deployment with Qwen3.6-27B-Uncensored + dynamic LoRA
- Error observed: HTTP 400 on first Hermes request to vLLM
- Fix: Added `--enable-auto-tool-choice --tool-call-parser hermes` to vLLM startup
