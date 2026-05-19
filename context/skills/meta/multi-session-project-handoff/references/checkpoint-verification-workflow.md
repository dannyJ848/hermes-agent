# Checkpoint Verification Workflow

When loading a session checkpoint (especially for DGX inference deployments), follow this verification sequence.

## Trigger
User says: "Load checkpoint X and verify all persistence layers" or "I just completed a major deployment, load checkpoint and verify..."

## Step-by-Step Verification

### 1. Load Checkpoint
```bash
# The checkpoint label should be descriptive:
# Format: dgx-{deployment-type}-{status}-{date}
# Example: dgx-inference-deployment-complete
```

### 2. Verify vLLM Inference Server
```bash
# Check model list
DGX_IP="10.0.0.171"
curl -s "http://${DGX_IP}:8000/v1/models"

# Expected: merged-lora model available with max_model_len: 131072
```

### 3. Verify Chat Completions Work
```bash
curl -s "http://${DGX_IP}:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model": "merged-lora", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 5, "temperature": 0.1}'
```

### 4. Verify Tool Calling
```bash
curl -s "http://${DGX_IP}:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "merged-lora",
    "messages": [{"role": "user", "content": "Search for recent AI news"}],
    "tools": [{"type": "function", "function": {"name": "web_search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}],
    "tool_choice": "auto",
    "max_tokens": 200
  }'

# Verify response contains tool_calls array with function name and arguments
```

### 5. Verify Hermes Config
```bash
# Check context_length matches vLLM max_model_len
grep "context_length:" ~/.hermes/config.yaml | head -1

# Check spark-bf16 provider is configured
grep -A10 "spark-bf16:" ~/.hermes/config.yaml

# Expected: context_length 131072 (or higher), supports_tools: true
```

### 6. Verify Knowledge Base Connectivity
```bash
# Check if hindsight/cerebrum are reachable
# If local: sqlite3 ~/.hermes/cerebrum_memory.db ".tables"
# If remote: ssh to DGX and check
```

### 7. Report Status Summary

Format:
```
**[System] — [STATUS]**
  Detail: [specific finding]
  Detail: [specific finding]
```

Example:
```
**vLLM Server (DGX Spark)** — OPERATIONAL
  Model: Qwen3.6-27B-Uncensored + LoRA adapter (merged-lora)
  Endpoint: http://10.0.0.171:8000/v1
  Context: 131,072 tokens
  Tool Parser: qwen3_xml — VERIFIED WORKING

**Hermes Config** — INTACT
  spark-bf16 provider configured
  Local context_length: 131072

**Knowledge Base** — UNREACHABLE
  hindsight: Connection refused
  cerebrum: "no such table: distilled_tips"
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| vLLM not responding | Daemon stopped, port wrong, firewall | `sudo systemctl start vllm-merged` or check port |
| merged-lora not in model list | LoRA adapter not loaded | Check vLLM startup args for --lora-modules |
| Tool calls empty | max_tokens too low, temperature too low | Increase max_tokens to 200+, temperature to 0.7 |
| context_length mismatch | Hermes config != vLLM max_model_len | Update both to same value (131072) |
| SSH permission denied | Wrong key, wrong user, key not on remote | Check `ls ~/.ssh/id_*`, verify key is on remote |
| Knowledge base unreachable | Service down, network issue, schema mismatch | Check service status, verify table schema |

## SSH Key Discovery

When SSH fails, check keys in this order:
```bash
ls ~/.ssh/id_*          # List all keys
# Prefer ed25519 over rsa
# Try: ssh -i ~/.ssh/id_ed25519 user@host
# Try: ssh -i ~/.ssh/id_rsa user@host
```

**Pitfall:** Many modern systems use `id_ed25519` not `id_rsa`. Always check before assuming.
