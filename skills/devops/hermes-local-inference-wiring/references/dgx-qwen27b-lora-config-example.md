# DGX Qwen 27B + LoRA Config Example

Date: 2026-05-18
Model: Qwen3.6-27B-Uncensored + FrankenV8 LoRA (rank 256) + D-Flash
GPU: NVIDIA GB10 (Blackwell) on DGX Spark
Container: ghcr.io/aeon-7/vllm-dflash:latest

## Hermes Config (BF16 Only — No Quantization)

### Main config.yaml provider entry:
```yaml
providers:
  spark-bf16:
    api: http://10.0.0.171:8000/v1
    api_key: not-needed
    name: spark-bf16
    models:
      merged-lora:
        context_length: 32768
        supports_tools: true
        supports_reasoning: true
      qwen3.6-27b-uncensored:
        context_length: 32768
        supports_tools: true
        supports_reasoning: true
```

### Profile config (~/.hermes/profiles/dgx-qwen-lora/config.yaml):
```yaml
model:
  base_url: http://10.0.0.171:8000/v1
  default: merged-lora
  provider: spark-bf16
  api_key: not-needed
  dtype: bfloat16
```

## vLLM Launch Command (DGX)

```bash
docker run -d --name vllm-bf16 \
  --gpus all --privileged --ipc host --network host \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/checkpoints \
  -e VLLM_MARLIN_USE_ATOMIC_ADD=1 \
  --entrypoint python3 \
  ghcr.io/aeon-7/vllm-dflash:latest \
  -m vllm.entrypoints.openai.api_server \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --port 8000 --host 0.0.0.0 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.8 \
  --max-cudagraph-capture-size 256 \
  --enable-auto-tool-choice --tool-call-parser qwen3_coder \
  --load-format fastsafetensors \
  --attention-backend flashinfer \
  --enable-prefix-caching --enable-chunked-prefill \
  --dtype bfloat16 \
  --enable-lora --max-lora-rank 256 \
  --lora-modules merged-lora=/data/checkpoints/final_model
```

**Critical flags:**
- `--dtype bfloat16` — BF16 weights, no quantization
- `--enable-lora --max-lora-rank 256` — LoRA serving
- `--lora-modules merged-lora=/path/to/adapter` — Names the LoRA
- `--tool-call-parser qwen3_coder` — May need adjustment for XML output (see qwen-xml-tool-calling-incompatibility.md)

## Launch Commands

```bash
# Using profile (recommended)
dgx-qwen-lora chat

# Direct
hermes chat --provider spark-bf16 --model merged-lora

# Mid-session switch
/model --provider spark-bf16 merged-lora
```

## DGX Details (from session history)
- IP: 10.0.0.171
- User: djg6228
- Pass: 6228
- SSH: sshpass -p '6228' ssh djg6228@10.0.0.171
