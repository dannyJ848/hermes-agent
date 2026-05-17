# Hermes Daemon Deployment on DGX (May 16 2026)

## Problem

Running Hermes Agent as a persistent background service on DGX Spark with local vLLM inference.

## Solution: Request Queue Daemon

Hermes `run_agent.main()` is designed for single-shot execution and returns `None`. It cannot be `await`ed in an async loop. The daemon pattern uses synchronous execution with a JSONL request queue.

## Architecture

```
Request Queue: /tmp/hermes_dgx_requests.jsonl
Response Dir:  /tmp/hermes_dgx_responses/
Daemon:        systemd service → Python script → run_agent.main()
```

## Critical Configuration

### 1. Model Name Must Match vLLM Exactly

vLLM serves models by their full filesystem path:

```bash
# vLLM model list
curl -s http://localhost:8000/v1/models | python3 -c "import sys,json; print([m['id'] for m in json.load(sys.stdin)['data']])"
# Output: ['/data/models/Qwen3.6-27B-Uncensored', 'custom-model']
```

Hermes config MUST use the full path:

```yaml
model:
  default: /data/models/Qwen3.6-27B-Uncensored  # NOT just "Qwen3.6-27B-Uncensored"

providers:
  local-dgx:
    api: http://localhost:8000/v1
    models:
      /data/models/Qwen3.6-27B-Uncensored:  # FULL PATH REQUIRED
        context_length: 131072
        supports_reasoning: true
        supports_tools: true
```

**Error if wrong:** `HTTP 404: The model Qwen3.6-27B-Uncensored does not exist.`

### 2. Synchronous Execution Required

```python
# WRONG - main() returns None, can't be awaited
result = await main(query=..., model=..., ...)  # TypeError: NoneType can't be used in 'await'

# CORRECT - use asyncio.run() in a thread or sync context
import asyncio
result = asyncio.run(main(query=..., model=..., ...))  # Works
```

### 3. Module Shadowing Prevention

Pre-import gateway and plugins packages before importing hermes_cli:

```python
gateway_init = os.path.join(project_root, "gateway", "__init__.py")
if os.path.exists(gateway_init) and "gateway" not in sys.modules:
    spec = importlib.util.spec_from_file_location("gateway", gateway_init,
        submodule_search_locations=[os.path.join(project_root, "gateway")])
    gateway_pkg = importlib.util.module_from_spec(spec)
    sys.modules["gateway"] = gateway_pkg
    spec.loader.exec_module(gateway_pkg)
```

## Request Format

```json
{"id": "unique-request-id", "query": "User question here"}
```

Append to queue:
```bash
echo '{"id": "req-001", "query": "What is 2+2?"}' >> /tmp/hermes_dgx_requests.jsonl
```

## Response Format

```json
{"id": "req-001", "status": "completed", "timestamp": "2026-05-16T23:24:49"}
```

Read response:
```bash
cat /tmp/hermes_dgx_responses/req-001.json
```

## Performance

- First request after daemon start: ~60-90s (model loading + cognitive orchestrator init)
- Subsequent requests: ~45-70s (depends on query complexity)
- Cognitive orchestrator: 20/20 subsystems active
- Tool calling: 98 tools loaded

## Services Status

| Service | PID | Status |
|---------|-----|--------|
| vLLM (vllm-base-lora) | 57583 | Active |
| Hermes Daemon | 91447 | Active |
| Gateway | 3297 | Active |
| Distillation Daemon | 2159 | Active |

## Troubleshooting

### Daemon not processing requests
1. Check queue file exists: `cat /tmp/hermes_dgx_requests.jsonl`
2. Check daemon logs: `sudo journalctl -u hermes-dgx-daemon.service -n 50`
3. Check vLLM is responding: `curl -s http://localhost:8000/v1/models`

### 404 model not found
- Verify model name in config matches vLLM served name exactly (full path)
- Check both `model.default` and `providers.local-dgx.models` sections

### Processed but no response file
- Check daemon logs for Python errors
- Ensure `/tmp/hermes_dgx_responses/` directory exists and is writable
- Verify `asyncio.run()` pattern is used (not `await main()`)

## Files

| File | Path |
|------|------|
| Daemon launcher | `/data/SpecForge/hermes-agent/run_hermes_daemon.py` |
| Systemd service | `/etc/systemd/system/hermes-dgx-daemon.service` |
| Request queue | `/tmp/hermes_dgx_requests.jsonl` |
| Response dir | `/tmp/hermes_dgx_responses/` |
| Hermes config | `/data/SpecForge/hermes-agent/config.yaml` |
