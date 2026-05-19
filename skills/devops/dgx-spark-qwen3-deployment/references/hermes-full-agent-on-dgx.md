# Full Hermes Agent on DGX — Complete Setup Pattern

## Use Case

User wants to run the COMPLETE Hermes Agent (not just inference) on the DGX Spark, using the locally-trained Qwen model as the primary LLM provider. This is different from the hub-and-spoke pattern where MacBook runs Hermes and DGX runs vLLM only.

## Architecture

```
MacBook Hermes (existing)
  - Default cloud provider (GLM-5.1 / Z.AI)
  - All existing tools, plugins, memory
  - Independent instance

DGX Spark Hermes (new)
  - Local Qwen model as primary provider
  - Same source code as MacBook (rsync'd)
  - Separate config, separate memory DB
  - Can run simultaneously with MacBook instance
```

## One-Time Setup Procedure

### Step 1: Sync Hermes Source from MacBook to DGX

```bash
# ON MACBOOK
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.pytest_cache' --exclude='venv' --exclude='.venv' \
  --exclude='datasets' --exclude='temp_vision_images' \
  ~/hermes-agent/ djg6228@spark-85e8.local:/data/SpecForge/hermes-agent/
```

### Step 2: Create Python Venv on DGX

```bash
# ON DGX (via SSH)
cd /data/SpecForge/hermes-agent
python3 -m venv venv
source venv/bin/activate
pip install -e . --quiet
```

### Step 3: Create DGX-Specific Config

**Working config format (May 14, 2026):**

```bash
# ON DGX
mkdir -p ~/.hermes
cat > ~/.hermes/config.yaml << 'EOF'
model:
  provider: custom
  base_url: http://localhost:8000/v1
  api_key: not-needed
  default: merged-lora
  chat_template_kwargs:
    enable_thinking: true

providers:
  custom:
    api: http://localhost:8000/v1
    api_key: not-needed
    models:
      merged-lora:
        context_length: 262144
        supports_tools: true
        supports_reasoning: true
      Qwen3.6-27B-Uncensored:
        context_length: 262144
        supports_tools: true
        supports_reasoning: true
EOF
```

**Key differences from provider-slug pattern:**
- `provider: custom` (not `provider: local-dgx`)
- `base_url` at top-level `model:` (not nested under providers)
- `chat_template_kwargs` for thinking mode at model level
- Provider name under `providers:` is `custom` matching `model.provider`

**Why this format:** Hermes v0.13.0 resolves providers differently than earlier versions. The `custom` provider is built-in and uses `base_url` directly. Named provider slugs (`local-dgx`, `spark-bf16`) require explicit registration in the providers map AND matching `model.provider` — if mismatched, you get `AuthError: Unknown provider`.

**Anti-pattern to avoid:**
```yaml
# WRONG — causes "Unknown provider 'local-dgx'"
model:
  provider: local-dgx
providers:
  local-dgx:
    api: http://localhost:8000/v1
```

```yaml
# WRONG — base_url missing at model level
model:
  provider: custom
providers:
  custom:
    api: http://localhost:8000/v1
```

### Step 4: Start vLLM with Local Model

```bash
# ON DGX
source /data/SpecForge/hermes-agent/venv/bin/activate

vllm serve /data/SpecForge/custom_dflash/checkpoints/final_model_merged \
  --dtype bfloat16 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.85 \
  --port 8000 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen \
  &
```

### Step 5: Verify Hermes Can Talk to Model

```bash
# ON DGX
source /data/SpecForge/hermes-agent/venv/bin/activate
python3 -c "
from hermes_cli.plugins import get_plugin_manager
from hermes_cli.config import load_config
cfg = load_config()
print(f'Model: {cfg.model.default}')
print(f'Provider: {cfg.model.provider}')
print(f'Base URL: {cfg.model.base_url}')
"
```

### Step 6: Launch Hermes CLI on DGX

```bash
# ON DGX
source /data/SpecForge/hermes-agent/venv/bin/activate
hermes chat
```

## Key Differences from Hub-and-Spoke

| Aspect | Hub-and-Spoke | Full Agent on DGX |
|--------|--------------|-------------------|
| Hermes code location | MacBook only | Both MacBook AND DGX |
| Model serving | DGX vLLM only | DGX vLLM + Hermes agent |
| Primary provider | MacBook: GLM-5.1 (cloud) | DGX: local Qwen |
| Tool execution | MacBook tools | DGX tools (may differ) |
| Memory/DB | MacBook ~/.hermes/ | DGX ~/.hermes/ (separate) |
| Use case | MacBook agent with local inference fallback | Dedicated DGX agent for model testing |

## Pitfalls

1. **Config isolation** — DGX `~/.hermes/config.yaml` must NOT reference MacBook paths
2. **Memory DB separation** — DGX `~/.hermes/` starts empty; no memory from MacBook transfers
3. **Tool availability** — DGX may lack MacBook-specific tools (Apple ecosystem, etc.)
4. **vLLM must be running BEFORE Hermes starts** — or model calls will fail
5. **Port conflicts** — if MacBook also runs vLLM via SSH tunnel, ensure different ports
6. **Terminal tool `[Command interrupted]`** — if SSH commands fail with exit 130, use `execute_code` with `subprocess.run()` instead

## Verification Checklist

- [ ] `~/hermes-agent/` exists on DGX with same files as MacBook
- [ ] `venv/bin/python` exists and can import `hermes_agent`
- [ ] `~/.hermes/config.yaml` points to `http://localhost:8000/v1`
- [ ] vLLM is running on port 8000 with the local model
- [ ] `hermes chat` starts without errors on DGX
- [ ] First message to the model gets a response
