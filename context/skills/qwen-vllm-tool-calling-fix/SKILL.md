---
name: qwen-vllm-tool-calling-fix
description: Fix Qwen tool calling with vLLM when model outputs XML format but parser expects JSON
category: devops
version: 1.0
---

# Qwen vLLM Tool Calling Fix

## Problem

Qwen3.6-27B-Uncensored generates tool calls in XML format (`<tool_call><function=name><parameter=name>value</parameter></function></tool_call>`) but vLLM's default Hermes parser expects JSON. This causes empty `tool_calls` arrays and the agent cannot execute tools.

## Root Cause

**WRONG:** `--tool-call-parser hermes` — expects JSON, fails on XML  
**CORRECT:** `--tool-call-parser qwen3_xml` — vLLM 0.20.2+ has a built-in parser for Qwen's XML format

## The Fix (Single Flag Change)

Restart vLLM with the correct parser:

```bash
docker run -d --name vllm-base-lora --gpus all --runtime nvidia -p 8000:8000 \
  -v /data:/data vllm/vllm-openai:v0.20.2 \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  # ... other args
```

**Available Qwen parsers in vLLM 0.20.2:**
- `qwen3_xml` — for Qwen3 base models (Qwen3.6-27B-Uncensored, etc.)
- `qwen3_coder` — for Qwen3 Coder variants

List all available parsers:
```bash
docker exec vllm-base-lora python3 -c \
  "from vllm.tool_parsers import ToolParserManager; print([p.__name__ for p in ToolParserManager.tool_parsers])"
# Or check error on invalid parser — vLLM lists all valid names
```

## What Was Wrong Before

The text-based wrapper at `/tmp/autonomous_runner_v2.py` was a workaround that **did not work**. The Hermes agent loop consumes responses internally; by the time `main()` returns, vLLM has already returned `finish_reason=tool_calls` with an empty `tool_calls` array. The wrapper's `parse_tool_calls()` found nothing in `final_response`.

Evidence from broken logs:
```
finish_reason=tool_calls model=/data/models/Qwen3.6-27B-Uncensored ... tool_turns=0
```

**`tool_turns=0` means ZERO tools executed despite the model wanting to call tools.**

## Verification

After restart with `qwen3_xml`, check if tool calls are actually executing:

```bash
# CORRECT check: look for tool_turns > 0
grep "tool_turns=[1-9]" /tmp/hermes_auto_v2.txt

# WRONG check (always passes even when broken):
# grep "finish_reason=tool_calls"  — this just means model WANTED to call tools

# Check for empty tool_calls array (the bug):
grep "tool_turns=0" /tmp/hermes_auto_v2.txt | wc -l
```

## Config Requirement

Model name must be full path in `config.yaml`: `/data/models/Qwen3.6-27B-Uncensored`

## vLLM Error Location (when using wrong parser)

`/usr/local/lib/python3.12/site-packages/vllm/tool_parsers/hermes_tool_parser.py` line 114 — JSONDecodeError on XML input

## Model Inventory on DGX (as of May 2026)

| Model | Tool Calling | Notes |
|-------|-------------|-------|
| Qwen3.6-27B-Uncensored | ✅ With `qwen3_xml` parser | XML format, needs correct parser |
| Qwen3.5-27B-DFlash | ❓ Unknown | Draft model for speculative decoding |
| Qwen36-FrankenV8-FullFT | ❓ Unknown | Custom fine-tune |
| Qwen27B-ExpertLogician | ❓ Unknown | LoRA+SAE+distillation result |