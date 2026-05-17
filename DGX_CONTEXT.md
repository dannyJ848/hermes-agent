# DGX Hermes Context - May 17 2026

## Current State

### vLLM Server
- **Container**: vllm-base-lora
- **Model**: /data/models/Qwen3.6-27B-Uncensored
- **LoRA**: custom-model (r=256)
- **Speculative**: DFlash with Qwen3.5-27B-DFlash draft, num_speculative_tokens=5
- **Port**: 8000
- **Status**: RUNNING

### Autonomous Hermes
- **Screen session**: hermes_auto
- **Runner**: /tmp/autonomous_runner_v2.py
- **Log**: /tmp/hermes_auto_v2.txt
- **Mode**: Text-based tool execution (Qwen XML format)
- **Status**: RUNNING

## Known Issues

### Qwen Tool Calling
Qwen3.6-27B-Uncensored outputs XML tool format but vLLM Hermes parser expects JSON.
- **Error**: JSONDecodeError in hermes_tool_parser.py line 114
- **Workaround**: Text-based tool execution wrapper
- **Solutions to explore**:
  1. Use Qwen2.5-Instruct or Qwen3-Instruct with native function calling
  2. Create custom vLLM tool parser for Qwen XML format
  3. Fine-tune Qwen on Hermes tool format

## Full Capabilities Verified
- Local file write
- MacBook SSH access (10.0.0.125)
- Web access (DuckDuckGo)
- Browser automation (Playwright + Chromium)
- Git operations
- Docker management

## Config Requirements
- Model name must be full path: /data/models/Qwen3.6-27B-Uncensored
- vLLM requires: --enable-auto-tool-choice --tool-call-parser hermes
- User explicitly rejected systemd daemons - use screen/tmux only

## Speed Benchmarks
- With speculative decoding: ~6.2 tok/s
- Without speculative decoding: ~12 tok/s
- Acceptance rate: 40-68% with num_speculative_tokens=5

## Critical File Paths
- Autonomous runner: /tmp/autonomous_runner_v2.py
- Log file: /tmp/hermes_auto_v2.txt
- Request queue: /tmp/hermes_dgx_requests.jsonl
- vLLM parser: /usr/local/lib/python3.12/site-packages/vllm/tool_parsers/hermes_tool_parser.py

## Session Checkpoints
- Local: dgx-hermes-tool-calling-fix-may17

## Skills Created
- qwen-vllm-tool-calling-fix

## Knowledge Base
- qwen-vllm-tool-calling-compatibility.md
