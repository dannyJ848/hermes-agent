---
name: hermes-local-inference-wiring
version: 1.0
category: devops
description: Wire a local inference server (vLLM, TGI, llama.cpp, Ollama) into Hermes Agent with multi-profile architecture. Zero-disruption to existing cloud model.
tags: [hermes, vllm, inference, profiles, local-llm]
---

# Wire Local Inference Server to Hermes Agent

When you have a local inference server (vLLM on DGX Spark, llama.cpp on a GPU rig, TGI, Ollama, etc.) and want to use it through Hermes Agent WITHOUT disrupting your existing cloud model setup.

## Architecture

**Pattern A: Hub-and-Spoke (MacBook brain + local server throat)**

The local server is NEVER a second Hermes instance. It's just an OpenAI-compatible API endpoint.

```
MacBook Hermes (brain)          Local Server (throat)
  - ALL agent logic             - Pure inference server
  - ALL tools & plugins         - /v1/chat/completions only
  - ALL memory & context        - No Hermes code runs here
  - Routes via /model switch    - No tools, no plugins
```

**Pattern B: Full Hermes on Local Server (COMPLETE agent instance)**

If the user explicitly asks to "clone Hermes" or "run the full Hermes harness" on the local server, they want the COMPLETE agent. In this case:
1. Sync Hermes source code to the server
2. Set up Python venv
3. Configure server-specific `config.yaml` pointing to local model
4. Sync skills, knowledge, and memory from MacBook
5. The server Hermes instance is SEPARATE from MacBook — both run independently

See `dgx-spark-qwen3-deployment` skill Section 2.1 for the full sync procedure.

## Quick Setup (5 Steps)

### 1. Create Hermes Profiles

```bash
# Create isolated profiles that clone everything from default
hermes profile create <profile-name> --clone     # e.g., spark-speed
hermes profile create <profile-name-bf16> --clone # e.g., spark-quality
```

The `--clone` flag copies: config.yaml, .env, SOUL.md, memories/MEMORY.md, memories/USER.md, and syncs bundled skills. Plugins are SHARED (not duplicated) from `~/.hermes/plugins/`.

### 2. Edit Profile Configs

Edit `~/.hermes/profiles/<profile-name>/config.yaml`:

```yaml
model:
  base_url: http://SERVER_IP_PLACEHOLDER:8000/v1   # placeholder, patched later
  default: <model-name-on-server>                    # e.g., Qwen/Qwen3.6-35B-A3B
  provider: <custom-provider-slug>                   # e.g., local-bf16
  api_mode: chat_completions
  api_key: not-needed                                # local = no auth
```

Use `SERVER_IP_PLACEHOLDER` as a sentinel — the wiring script replaces it with the real IP on launch day.

### 3. Add Provider to Default Config (for /model switching)

Add the local server as a provider in `~/.hermes/config.yaml` so you can switch mid-session:

```python
import yaml

with open(os.path.expanduser("~/.hermes/config.yaml")) as f:
    cfg = yaml.safe_load(f)

if 'providers' not in cfg or cfg['providers'] is None:
    cfg['providers'] = {}

cfg['providers']['<provider-slug>'] = {
    'api': 'http://<SERVER_IP>:<PORT>/v1',
    'api_key': 'not-needed',
    'name': '<provider-slug>',
    'models': {
        '<model-name>': {
            'context_length': 262144,
            'supports_tools': True,
            'supports_reasoning': True,
        },
    },
}

# CRITICAL: Do NOT change model.default or model.provider
# Your cloud model (e.g., GLM-5.1) stays primary

with open(config_path, 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
```

### 4. Create Wiring Script

The wiring script:
1. Adds providers to default config.yaml (for /model switch)
2. Patches profile configs with real server IP (replaces SERVER_IP_PLACEHOLDER)
3. Optionally sets up SSH tunnel for remote servers
4. Verifies everything works

Key pattern for patching profiles:
```bash
sed -i.bak "s|SERVER_IP_PLACEHOLDER|${SERVER_IP}|g" ~/.hermes/profiles/<name>/config.yaml
```

### 5. Launch

```bash
hermes chat              # Cloud model (default, smart)
<profile-name> chat     # Local model (free, private, fast)
```

All profiles can run simultaneously in separate terminals. Each is an isolated AIAgent instance with its own model setting.

Mid-session switching:
```
/model --provider <provider-slug> <model-name>   # Switch to local
/model <cloud-model-name>                        # Switch back
```

## Multi-Train Architecture (Zero API Cost)

If training the local model:

- **Training = BF16** (full precision for gradients, FP8 loses too much)
- **Inference = FP8** for speed, **BF16** for quality
- **SFT**: inference stays UP (no vLLM needed for training). You can chat during SFT.
- **GRPO**: inference PAUSES (vLLM needs 85% GPU for GRPO sampling). Use cloud model during these windows.
- **Self-play loop**: SFT → GRPO → Eval → Merge LoRA → new base → quantize FP8 → repeat
- **Stop condition**: eval plateaus (3 rounds with <0.5% improvement)

No cloud API teacher needed. GRPO is self-play — model generates, execution verifies, policy updates. Training data on disk = $0/round.

## Pitfalls

1. **Profile configs have SPARK_IP_PLACEHOLDER** — must be patched with real IP before use. The wiring script handles this.

2. **Self-manager handoff code may reference missing attributes** — If you see `AttributeError: 'HermesCLI' object has no attribute '_vprint'` or `log_prefix` during startup, the self-manager auto-resume code in `cli.py` references attributes/methods that don't exist yet in `__init__`. Fix: add the missing attribute/method right after `self.verbose` assignment (or wherever it first needs to be available). Example fixes:
   - `_vprint`: add as method after `__init__` — `def _vprint(self, message, *, force=False): if force or self.verbose: print(message)`
   - `log_prefix`: add as attribute — `self.log_prefix = "[hermes] "` right after `self.verbose`

2. **Plugins are SHARED, not per-profile** — all profiles use `~/.hermes/plugins/`. Plugin changes affect all profiles.

3. **PluginContext API (v0.20+)** — if upgrading from an older hermes-agent, plugin `register()` now receives a `PluginContext` object, not a dict. Old `ctx["key"] = callback` fails with "PluginContext does not support item assignment". Fix: `if isinstance(ctx, dict): ctx["key"]=val else: ctx.register_hook("key", callback)`.

4. **GRPO and serving can't share GPU** — during GRPO training, vLLM needs 85% VRAM for sampling. Inference serving must pause. SFT doesn't have this constraint.

5. **Multiple vLLM instances on same GPU** — don't try it. One vLLM instance per GPU. Use different ports for different quant levels (BF16 on :8000, FP8 on :8001).

6. **Profile sessions are isolated** — conversation history is per-profile. If you want to continue a conversation, use the same profile.

7. **Wrapper scripts at ~/.local/bin/** — `hermes profile create` auto-generates these. `spark-speed` → `exec hermes -p spark-speed "$@"`.

8. **Hermes probes /v1/models before chat completions** — Your local server MUST implement `GET /v1/models` and `GET /v1/models/{model_id}`. Without these, Hermes will silently fail or timeout. Even a minimal FastAPI server needs these endpoints. See `dgx-spark-qwen3-deployment/references/qwen35-vl-merged-model-vllm-incompatibility.md` for a working example.

9. **vLLM cannot load Qwen3.5-VL merged models** — If your model was trained from a vision-language base (Qwen3.5-VL) and merged, vLLM will fail with visual weight mismatches. Use transformers + FastAPI fallback, or retrain from text-only base. See `dgx-spark-qwen3-deployment/references/qwen35-vl-merged-model-vllm-incompatibility.md`.

10. **Slow transformers inference is acceptable for batch work** — If your only option is transformers (no vLLM), generation will be ~1-2 tok/s on DGX Spark. This is fine for overnight benchmarks, dataset generation, or non-interactive tasks. Don't try to use it for interactive chat.

11. **Context length vs speed tradeoff** — Reducing `--max-model-len` from 262K to 32K saves ~37GB GPU memory and improves concurrency from 4x to 27x, with zero quality loss. For agent workloads, 32K handles 99% of use cases. See `dgx-spark-qwen3-deployment/references/vllm-lora-serving-speed-context-optimization-may14-2026.md` for benchmarks.

12. **Batch inference is quality-neutral** — vLLM's continuous batching processes each request independently. No quality loss, just better GPU utilization.

13. **Hermes requires minimum 64K context window** — Even if your model supports less, Hermes validates `context_length >= 64000`. Set BOTH vLLM `--max-model-len` and Hermes config `context_length` to at least 65536. If you set 32K in vLLM but Hermes config says 64K, the API will accept requests but vLLM will truncate at 32K, causing silent context loss. Keep them in sync.

14. **Context length vs speed tradeoff on GB10** — At 64K context, GPU memory is ~75GB (vs ~59GB at 32K). Concurrency drops from 27x to ~14x. For Hermes deployments, 64K is the practical minimum. 128K gives more headroom at ~85GB. 262K (max) uses ~96GB with only 4x concurrency.

15. **vLLM tool calling requires correct parser flag** — For Qwen3.5/3.6 models, use `--tool-call-parser qwen3_xml` (NOT `qwen25`). Also requires `--enable-auto-tool-choice`. Without these, Hermes "auto" tool_choice returns HTTP 400. See `qwen27b-dgx-deployment:references/vllm-lora-tool-calling-config-may14-2026.md` for full configuration.

16. **NEVER disable Hermes safety guardrails for local inference** — When wiring local vLLM, do NOT disable `tirith_enabled`, `warnings_enabled`, or `hard_stop_enabled` in Hermes config. The user explicitly corrected this: "keep all those safety parameters as they were they stop you from wasting tokens." Safety guardrails prevent token-wasting loops. Always keep original settings: `tirith_enabled: true`, `warnings_enabled: true`, `warn_after: {exact_failure: 2, same_tool_failure: 3, idempotent_no_progress: 2}`, `hard_stop_after: {exact_failure: 5, same_tool_failure: 8, idempotent_no_progress: 5}`. If you already disabled them, restore immediately.

16. **Serve base model + LoRA adapter, NOT merged weights** — Qwen3.5 merged models trigger `Qwen3_5Config` (vision-language) which vLLM cannot load. Serve base model with `--enable-lora --lora-modules name=/path/to/adapter` instead.

## Verification Patterns (No SSH Required)

When you can reach the vLLM API but cannot SSH to the host (common with DGX Spark behind NAT/firewall), verify functionality via pure HTTP:

### Verify vLLM is responding:
```bash
curl -s http://SERVER_IP:8000/v1/models | python3 -c "import sys,json; d=json.load(sys.stdin); print([m['id'] for m in d.get('data',[])])"
# Should list: base model ID and LoRA adapter name (e.g., "merged-lora")
```

### Verify tool calling works (qwen3_xml parser):
```bash
curl -s http://SERVER_IP:8000/v1/chat/completions \
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
tc = d.get('choices',[{}])[0].get('message',{}).get('tool_calls',[])
print('tool_calls:', json.dumps(tc, indent=2) if tc else 'NONE')
print('content:', d.get('choices',[{}])[0].get('message',{}).get('content','')[:200])
"
# Should show: tool_calls with name="web_search" and arguments containing a query
```

### Verify context window:
```bash
curl -s http://SERVER_IP:8000/v1/models | python3 -c "import sys,json; d=json.load(sys.stdin); m=d.get('data',[{}])[0]; print(f\"max_model_len: {m.get('max_model_len','NOT SET')}\")"
# Should show: max_model_len matching your --max-model-len flag (e.g., 131072)
```

### Verify chat completions work:
```bash
curl -s http://SERVER_IP:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "merged-lora", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 5, "temperature": 0.1}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content','no-content'))"
# Should show: model response (may include thinking prefix for Qwen3.6)
```

**Note:** Qwen3.6 with thinking enabled outputs reasoning before the actual answer. Short `max_tokens` may only capture the thinking prefix ("Here's a thinking process:"). Use longer `max_tokens` or disable thinking via `chat_template_kwargs: {enable_thinking: false}` to get direct answers.
