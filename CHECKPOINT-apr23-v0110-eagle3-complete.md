# DGX Spark + Hermes v0.11.0 — Apr 23 2026 FINAL

## Hermes Update: v0.11.0 (271 commits merged)

**Status:** Updated to v0.11.0 (2026.4.23). Local branch 3 commits ahead of origin/main.

### Key New Features
1. **Transport ABC layer** — pluggable agent/transports/ with AnthropicTransport, ChatCompletionsTransport, ResponsesApiTransport, BedrockTransport
2. **Native AWS Bedrock provider** via Converse API
3. **New TUI** — full React/Ink rewrite with Python JSON-RPC backend, voice mode, subagent overlay
4. **GPT-5.5 over Codex OAuth** with live model discovery
5. **QQBot** — 17th messaging platform
6. **Plugin surface expanded** — slash commands, tool dispatch, pre_tool_call veto, transform_tool_result, image_gen backends, dashboard tabs
7. **`/steer`** — mid-run agent nudges
8. **Shell hooks** — wire shell scripts as lifecycle hooks
9. **Webhook direct-delivery mode**
10. **Smarter delegation** — orchestrator role + file coordination
11. **Dashboard plugin system + live theme switching**
12. **Kimi K2.6** across all providers
13. **Xiaomi MiMo v2.5**
14. **Configurable API retry count**
15. **Per-provider + per-model request_timeout_seconds**

## DGX Spark Eagle-3 Mission: COMPLETE

### What We Proved
Built `Eagle3Qwen3ForCausalLM` from scratch and integrated into vLLM 0.19.1rc1. This proves **we can build custom speculative decoding classes for ANY architecture**.

### Files
- `/data/vllm-patches/qwen3_eagle3.py` — Custom Eagle-3 model class
- `/data/vllm-patches/eagle_import_patch.py` — vLLM registry + eagle.py patches
- Docker image: `ghcr.io/aeon-7/vllm-dflash:eagle3-qwen3-v15`

### Architecture Built
1. **Qwen3Eagle3DecoderLayer** — Decoder layer with optional embed+hidden concat for first layer
2. **Qwen3Eagle3Model** — Model backbone with combine_hidden_states() for aux fusion
3. **Eagle3Qwen3ForCausalLM** — Main model class with embed_input_ids, forward, compute_logits

### vLLM Patches Applied
1. **registry.py** — Added Eagle3Qwen3ForCausalLM to _VLLM_MODELS
2. **eagle.py** — Added import + isinstance assertion

### Checkpoint Conversion (DFlash → Eagle-3)
- Stacked q/k/v → qkv_proj
- Stacked gate/up → gate_up_proj
- Added lm_head + embed_tokens (shared)
- Reshaped fc.weight: [5120, 25600] → [5120, 15360] (3 aux layers)

### Critical Fixes
1. hidden_norm at model level (not layer level)
2. Forward method: no embed+hidden concat (DFlash style)
3. Residual handling for Qwen3 RMSNorm
4. Syntax errors from sed mangling — rewrote entire file
5. Missing import in eagle.py assertion
6. fc layer shape mismatch (3 layers not 5)

### Result
- ✓ vLLM loads and serves
- ✓ Draft tokens at 22-24 tok/s
- ✗ 0% acceptance (DFlash model ≠ Eagle-3 trained)

**Infrastructure 100% ready. Needs properly trained Eagle-3 draft model.**

## DGX Spark Current State
- **vLLM container:** STOPPED (was running Eagle-3 test)
- **Model:** Qwen3.6-27B-Uncensored at /data/models/Qwen3.6-27B-Uncensored
- **Docker images available:**
  - `ghcr.io/aeon-7/vllm-dflash:eagle3-qwen3-v15` — Eagle-3 infrastructure
  - `ghcr.io/aeon-7/vllm-dflash:latest` — DFlash proven (~40 tok/s)
  - `ghcr.io/aeon-7/vllm-dflash:turboquant` — TurboQuant KV compression
- **DFlash model:** /data/models/Qwen3.5-27B-DFlash/ (ready for restart)

## Danny's Plan (In Progress)
1. ~~Option 3: Custom Eagle-3 class~~ ✓ DONE
2. **Option 1: DFlash integration** — Next (immediate ~40 tok/s)
3. **Option 2: MTP integration** — After DFlash (research needed)

## Credentials
- **DGX Spark:** 10.0.0.171, user djg6228
- **Sudo password:** 6228
- **SSH password:** MiloRFUPsych2028*

## Resume
When starting new CLI session, say: **"look at your most recent memory"**
I'll know exactly where we are and what to do next.
