# Hermes Agent 100% Local Routing Pattern

## Problem
User wants Hermes Agent to route ALL traffic to local Qwen 27B Expert Logician on DGX Spark. No external API fallback — not a preference, a hard requirement.

## Solution

### vLLM Server (on DGX)
```bash
python3 -m vllm.entrypoints.openai.api_server \
  --model /data/SpecForge/custom_dflash/checkpoints/final_merged_model \
  --dtype bfloat16 \
  --port 8000 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.95 \
  --enforce-eager
```

### Hermes Config (on Mac)
```yaml
providers:
  local_qwen:
    base_url: http://localhost:8000/v1
    api_key: hermes-local
    model: qwen-27b-expert-logician
    timeout: 120
    max_tokens: 4096
    temperature: 0.7

routing_rules:
  - pattern: ".*"
    provider: local_qwen
    priority: 1
```

### SSH Tunnel (if needed)
If Hermes on Mac needs to reach DGX vLLM:
```bash
ssh -L 8000:localhost:8000 djg6228@10.0.0.171 -N
```

## Anti-Patterns to Avoid
- Do NOT configure fallback providers (zai, openai, etc.)
- Do NOT use quantization (GGUF/AWQ) — BF16 preserves adaptability
- Do NOT route general tasks to Qwen — use Kimi Code for those
- Do NOT expect Qwen to handle non-reasoning tasks well

## Verification
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer hermes-local" \
  -d '{
    "model": "qwen-27b-expert-logician",
    "messages": [{"role": "user", "content": "Prove syllogism Barbara"}],
    "max_tokens": 512
  }'
```

## Two-Terminal Workflow
- Left terminal: Hermes Agent (Kimi Code) — general assistant
- Right terminal: DGX — direct Qwen queries via curl or Python
- No overlap — each does its own job
