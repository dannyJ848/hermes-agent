---
name: ollama-local-hermes
version: 1.0
created: 2026-04-16
description: Run Hermes Agent fully local with zero token cost using Ollama. Covers config wiring, model key format gotchas, Qwen3 thinking mode, and context length overrides.
tags: [ollama, local-inference, hermes, zero-cost, qwen3, config]
---

# Ollama Local Hermes Agent

Run the full Hermes Agent locally using Ollama — zero token cost, no API keys needed, fully private.

## Architecture

```
Mac M2 Air 24GB (or better)
+--------------------------------------+
|  Hermes Agent (run_agent.py)          |
|  model: qwen3:14b                     |
|  base_url: localhost:11434/v1         |
|                                       |
|  Ollama server (port 11434)           |
|  +- qwen3:14b    (8.6GB)             |
|  +- deepseek-r1   (8.4GB)            |
|  +- llama3.1:8b   (4.6GB)            |
|  +- nomic-embed   (0.3GB)            |
+--------------------------------------+
```

## Prerequisites

- Mac with Apple Silicon, 24GB+ RAM recommended
- Ollama installed: `brew install ollama` or from https://ollama.com
- At least one model pulled: `ollama pull qwen3:14b`

## Step 1: Install Ollama and Pull Models

```bash
# Install if not already
brew install ollama

# Start server
ollama serve &

# Pull recommended models
ollama pull qwen3:14b        # Best reasoning, 8.6GB
ollama pull deepseek-r1:14b  # Deep chain-of-thought, 8.4GB
ollama pull llama3.1:8b      # Fast general purpose, 4.6GB
```

Model comparison for M2 Air 24GB:

| Model | Size | Speed | Best For | Context | RAM Usage |
|-------|------|-------|----------|---------|-----------|
| qwen3:14b | 8.6GB | ~8 t/s | Best reasoning + coding | 32K* | ~18GB |
| deepseek-r1:14b | 8.4GB | ~6 t/s | Deep reasoning chains | 128K | ~18GB |
| llama3.1:8b | 4.6GB | ~15 t/s | Fast general chat | 128K | ~12GB |
| deepseek-r1:7b | 4.4GB | ~12 t/s | Medium reasoning | 128K | ~12GB |

*Ollama reports 40960 but can be overridden in config (see Step 3)

## Step 2: Verify Ollama API

Ollama exposes an OpenAI-compatible endpoint at `http://localhost:11434/v1`:

```bash
# Quick health check
curl http://localhost:11434/api/tags | python3 -c "
import sys, json
models = [m['name'] for m in json.load(sys.stdin).get('models', [])]
print(f'Available: {models}')
"

# Test inference (OpenAI-compatible format)
curl -s -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3:14b","messages":[{"role":"user","content":"Say hello."}],"max_tokens":50}'
```

## Step 3: Configure config.yaml

### CRITICAL GOTCHA: Model key format

Ollama model names use **colons** (e.g., `qwen3:14b`), NOT dashes. The config.yaml
`providers.local.models` keys MUST use colons because Hermes does an exact string
match: `_cp_models.get(self.model, {})` where `self.model` comes from the CLI `--model` flag.

```yaml
# ~/.hermes/config.yaml

providers:
  local:
    api: http://localhost:11434/v1
    api_key: ollama
    name: local
    models:
      "qwen3:14b":          # MUST use colons, MUST quote in YAML
        context_length: 131072
      "qwen3:8b":
        context_length: 131072
      "deepseek-r1:14b":
        context_length: 131072
```

### Why context_length override is required

Ollama reports Qwen3:14b's context window as 40,960 tokens, but Hermes requires
a minimum of 64,000. Setting `context_length: 131072` in config overrides the
auto-detected value. Ollama supports extending context via `num_ctx` at runtime.

### YAML colon-in-key syntax

Model keys with colons must be quoted in YAML:
- CORRECT: `"qwen3:14b":`
- WRONG: `qwen3:14b:` (YAML parse error)
- WRONG: `qwen3-14b:` (model name mismatch -- Ollama uses colons)

## Step 4: Launch Script

Save as `~/Desktop/hermes-local.sh`:

```bash
#!/bin/bash
set -e

# Ensure Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Starting Ollama server..."
    ollama serve &
    sleep 3
fi

# Check model is available
if ! curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
models = [m['name'].split(':')[0] for m in json.load(sys.stdin).get('models', [])]
if 'qwen3' not in models:
    print('MISSING: qwen3:14b not found. Run: ollama pull qwen3:14b')
    sys.exit(1)
print('Model ready: qwen3:14b')
" 2>/dev/null; then
    exit 1
fi

echo ""
echo "============================================"
echo "  Hermes + Qwen3-14B (LOCAL, ZERO cost)"
echo "============================================"

cd ~/hermes-agent
source venv/bin/activate
python3 run_agent.py \
    --model qwen3:14b \
    --base-url http://localhost:11434/v1 \
    --api-key ollama \
    "$@"
```

IMPORTANT: Do NOT use `$0.00` in echo -- bash interprets `$0` as the script path.
Use literal text like "ZERO cost" or "FREE" instead.

## Step 5: Pre-flight Verification

Before launching, verify the config resolves correctly:

```python
import yaml
from hermes_cli.config import get_compatible_custom_providers

with open("/Users/YOURUSER/.hermes/config.yaml") as f:
    cfg = yaml.safe_load(f)

cp = get_compatible_custom_providers(cfg)
for entry in cp:
    if "11434" in entry.get("base_url", ""):
        models = entry.get("models", {})
        print(f"Provider: {entry['name']}")
        print(f"  base_url: {entry['base_url']}")
        print(f"  models: {models}")
        # Simulate run_agent.py lookup
        model_cfg = models.get("qwen3:14b", {})
        ctx = model_cfg.get("context_length")
        print(f"  context_length for qwen3:14b: {ctx}")
        assert ctx and ctx >= 64000, f"context_length {ctx} below 64K minimum!"
```

## Pitfalls and Gotchas

### 1. Model key colon vs dash (MOST COMMON BUG)

Config keys MUST match Ollama model names exactly:
- CORRECT: `"qwen3:14b":` in config, matches `self.model = "qwen3:14b"` from CLI
- WRONG: `qwen3-14b:` -- key mismatch, context_length lookup returns `{}`, falls back to Ollama's reported 40960, then ValueError "below minimum 64,000"

The error trace:
```
run_agent.py L1384: _cp_model_cfg = _cp_models.get(self.model, {})
# self.model = "qwen3:14b" (from --model flag)
# _cp_models = {"qwen3-14b": {...}}  <-- MISMATCH, returns {}
```

### 2. Context length below 64K minimum

Ollama reports model context windows from model metadata. Qwen3:14b reports
40,960 which is below Hermes's required 64,000 minimum. The config override
is checked at run_agent.py L1340-1366 (first priority) then custom_providers
L1368-1405 (second priority). Either path works, but config is simpler.

Error: `ValueError: Model qwen3:14b has a context window of 40,960 tokens, which is below the minimum 64,000`

### 3. Qwen3 thinking mode

Qwen3 models use "thinking mode" by default:
- Chain-of-thought goes in `reasoning` (or `reasoning_content`) field
- Actual answer goes in `content` field
- With low `max_tokens` (e.g. 50), ALL tokens go to reasoning and `content` is empty

Example response:
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "4",
      "reasoning": "Okay, the user is asking What is 2+2?..."
    }
  }]
}
```

To disable thinking for simple tasks: prefix prompt with `/no_think`
For agent use: Hermes reads `content` only, so thinking mode works fine as long
as max_tokens is generous enough (2000+ for non-trivial tasks).

### 4. API key "ollama" warning

Hermes warns: `Warning: API key appears invalid or missing (got: 'ollama...')`
This is cosmetic -- Ollama does not require a real API key. The `--api-key ollama`
placeholder satisfies the HTTP header requirement.

### 5. Bash $0 variable in echo

Never use `$0.00` in shell scripts -- bash expands `$0` to the script's path.
`echo "Cost: $0.00"` prints `Cost: /Users/.../hermes-local.sh.00`
Use literal text: `echo "Cost: FREE -- all local inference"`

### 6. Distillation plugin load error

`Failed to load plugin 'distillation': 'PluginContext' object does not support item assignment`
This is a known plugin bug unrelated to local inference. Non-blocking for basic usage.

### 7. M2 Air 24GB RAM budget

- OS uses ~6GB
- Qwen3:14b uses ~8.6GB model + ~9GB inference state = ~18GB total
- Leaves ~6GB headroom
- With 128K context, very long conversations may cause swap
- Monitor: `sysctl vm.swapusage` -- if swap > 20GB, reduce active models

### 8. Speed comparison

| Setup | Speed | Cost |
|-------|-------|------|
| FriendliAI GLM-5.1 (cloud) | ~108 t/s | $1.40/$4.40 per M tokens |
| Ollama qwen3:14b (local) | ~8 t/s | $0.00 |
| Ollama llama3.1:8b (local) | ~15 t/s | $0.00 |

Local is ~13x slower but free. Best for: private data, unlimited usage,
offline operation, avoiding API rate limits.

## Verification Checklist

```bash
# 1. Ollama running
curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
m = [x['name'] for x in json.load(sys.stdin)['models']]
print(f'{len(m)} models found')
"

# 2. Inference works
curl -s -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3:14b","messages":[{"role":"user","content":"2+2?"}],"max_tokens":200}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'])"

# 3. Config resolves correctly (see Step 5)

# 4. Launch Hermes
bash ~/Desktop/hermes-local.sh
```
