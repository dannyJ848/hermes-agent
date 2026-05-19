---
name: dgx-spark-qwen3-deployment
version: 3.6.0
description: Complete deployment playbook for Qwen3.6-35B-A3B and Qwen3.6-27B on NVIDIA DGX Spark — maximum BF16 optimization, SM121 kernel fix, SFT+GRPO training pipeline with execution verification, TurboQuant KV cache (VERIFIED build), EAGLE-3 auto-pipeline, HermesAgent-20 eval, Atropos agent RL, post-training evaluation patterns (lm-eval-harness + direct Python fallback, silent death recovery, terminal backgrounding), SGLang alternative deployment, and all known speed stacks.
trigger: When setting up a DGX Spark, deploying Qwen3.6, configuring local inference for Hermes, optimizing MoE performance on Blackwell/GB10, or running post-training evaluation benchmarks.
tags: [dgx-spark, qwen3.6, local-inference, blackwell, moe, optimization, fine-tuning, hermes-deployment, evaluation, lm-eval]
---
     8|     8|
     9|     9|# DGX Spark + Qwen3.6-35B-A3B Deployment Playbook
    10|    10|
    11|    11|## Hardware Specs
    12|    12|
    13|    13|| Spec | Value |
    14|    14||---|---|
    15|    15|| SoC | GB10 Grace Blackwell Superchip |
    16|    16|| CPU | 20 ARM (10x Cortex-X925 @ 4GHz + 10x Cortex-A725) |
    17|    17|| GPU | ~1 PFLOP FP4 sparse (~RTX 5070 Ti class compute) |
    18|    18|| Memory | 128GB unified LPDDR5x (CPU+GPU shared, zero copy) |
    19|    19|| Bandwidth | 273 GB/s (primary inference bottleneck) |
    20|    20|| Storage | 4TB NVMe |
    21|    21|| Networking | 2x QSFP ConnectX-7 (200 Gbps RDMA, dual Spark cluster) |
    22|    22|| Power | 240W via USB-C PD |
    23|    23|| OS | Ubuntu 24.04 aarch64 |
    24|    24|| CUDA | 13.0 (driver 580+) |
    25|    25|
    26|    26|## Model: Qwen3.6-35B-A3B
    27|    27|
    28|    28|| Property | Value |
    29|    29||---|---|
    30|    30|| Total params | 35B (3B activated per token - MoE) |
    31|    31|| Experts | 256 total, 8 routed + 1 shared |
    32|    32|| BF16 size | ~70GB |
    33|    33|| FP8 size | ~35GB |
    34|    34|| Context | 262K native, extends to 1M |
    35|    35|| Vision | Built-in vision encoder (MMMU: 81.7) |
    36|    36|| License | Apache 2.0 |
    37|    37|| Tool calling | Native (qwen3_coder parser, 97-100/100 ToolCall-15) |
    38|    38|| Thinking | Native reasoning with preservation across turns |
    39|    39|
    40|    40|## Performance Summary Table (Community-Verified, Apr 17 2026)
    41|    41|
    42|    42|| Config | Decode (tok/s) | 262K Context? | Quality | Source | Best For |
    43|    43||---|---|---|---|---|---|
    44|    44|| BF16, stock vLLM (NO SM121 kernels) | 13 | Yes | 100% | troy.e.davis NVIDIA forum | AVOID — broken |
    45|    45|| BF16, SM121 native kernels | 31-35 | Yes | 100% | adadrag, hellohal2064 | Quality baseline |
| BF16 + SM121 + MTP-3 | 40-49 | Yes | 100% | hellohal2064, albond | Medical, DEFAULT |
| BF16 + SM121 + MTP-2 + MaxPerf 7-layer | 58-66 | Yes | 100% | spark-maxperf.sh (this playbook) | Agentic, BEST single-Spark |
| BF16 + SM121 + DFlash + enforce-eager (verified Apr 21) | 40.7 | Yes | 100% | Apr 21 live test on GB10 | 24/7 deploy, ONLY safe config |
| **FP8 + DFlash (Qwen3.5-27B-DFlash draft, num_tokens=5, verified May 15)** | **~16.9** | Yes | ~99% | **DGX Spark live test** | **Best speed/quality for 27B dense** |
| FP8 + DFlash (Qwen3.5-27B-DFlash draft, num_tokens=16, earlier test) | ~16.7 | Yes | ~99% | DGX Spark live test | Superseded by num_tokens=5 |
| FP8 + SM121 + MTP-3 (single Spark) | 52-54 | Yes | ~99% | cosinus NVIDIA forum | Coding, agent |
| FP8 + MTP-3, dual Spark (TP2) | 64-78 | Yes | ~99% | serapis NVIDIA forum | Production |
|| SGLang + triton + no CUDA graphs (verified Apr 22) | 28 | Yes | 100% | Pre-built image test | Alternative, needs EAGLE-3 for speed |
|| SGLang + EAGLE-3 (community claim) | 60 | Yes | ~99% | Reddit r/LocalLLaMA | Needs trained draft model |
|| DFlash (z-lab 0.5B drafter) on B200 | 100-150+ | Yes | ~99% | z-lab + AEON-7 | NOT achievable on GB10 |

    53|    53|| PrismQuant 4.75bpp (compressed-tensors) | 50-55 | Yes | ~99.4% | rdtand/HF | 22GB, memory-efficient |
    54|    54|| Hybrid INT4+FP8 + MTP | 100+ | Yes | ~96% | phuongncn speed hack | Max vLLM speed |
    55|    55|
**Systemd service for auto-start on boot:**

```bash
# /etc/systemd/system/vllm-dflash.service
[Unit]
Description=vLLM DFlash Inference Server
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/docker run -d \
  --name vllm-merged \
  --runtime nvidia \
  --gpus all \
  -p 8000:8000 \
  -v /data:/data \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e VLLM_LOGGING_LEVEL=INFO \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --reasoning-parser qwen3, --kv-cache-dtype fp8_e5m2, --load-format fastsafetensors,
  --speculative-config '{"method":"dflash","model":"/data/models/Qwen3.5-27B-DFlash","num_speculative_tokens":5}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 128
ExecStop=/usr/bin/docker stop -t 30 vllm-merged
ExecStopPost=/usr/bin/docker rm -f vllm-merged

[Install]
WantedBy=multi-user.target
```

Install and enable:
```bash
sudo cp /tmp/vllm-dflash.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vllm-dflash.service
sudo systemctl start vllm-dflash.service
```

Status: `sudo systemctl status vllm-dflash.service`

**CRITICAL:** Stock vllm image ships WITHOUT SM121 cubins. 13→49 tok/s (3.65x)
with native kernel build. See Phase 1.2 Option B for build instructions.
Full optimization guide: knowledge/dgx-spark-qwen3-6-maximum-bf16-optimization.md
    59|    59|
## Phase 1: Day-1 Deployment

### 1.0 ONE-COMMAND FULLY AUTOMATED DEPLOYMENT

```bash
# ON THE SPARK — plug in, run this, walk away:
bash spark-day1.sh --macbook <MacBook-IP> --usb     # USB-C (45min transfer)
bash spark-day1.sh --macbook <MacBook-IP>           # WiFi (8+ hrs transfer)
bash spark-day1.sh --skip-transfer                   # No MacBook data
bash spark-day1.sh --resume                          # Skip completed steps
```

Handles ALL of Phase 1 in parallel: hardware verify, system packages, Docker,
NVIDIA toolkit, Python venv, MacBook transfer (318GB), model downloads (106GB),
Nemotron (203GB), Docker images, 13 HF kernels, Atropos, SM121 patches,
vLLM BF16+FP8 deployment, perf verification, HermesAgent-20 eval, health check.

Scripts: spark-day1.sh (main), macbook-transfer-helper.sh (MacBook prep),
QUICKREF.md (printable reference card).

**Optimized vLLM deployment script (May 15, 2026):**
```bash
bash scripts/deploy_vllm_optimized.sh
```
This script deploys the verified optimal configuration for Qwen3.6-27B:
- FP8 weights + BF16 KV cache
- n-gram speculative decoding (5 tokens)
- Chunked prefill + CUDA graphs + torch.compile
- NO prefix caching (disabled for hybrid models)
- 32768 batched tokens, 128 max concurrent sequences
- ~6.5 tok/s single-stream, ~200+ tok/s at 128 concurrent

See `references/vllm-systematic-optimization-may15-2026.md` for the full
benchmarking methodology and verified configuration details.
    79|    79|
    80|    80|#### Finding the Spark on Your Network (If You Don't Know the IP)
    81|    81|
    82|    82|The Spark is headless — no display, no keyboard. If the manual gives an mDNS
    83|    83|hostname (e.g., `spark-85e8.local`), resolve it directly:
    84|    84|
    85|    85|```bash
    86|    86|# MacBook
    87|    87|ping -c 1 spark-85e8.local              # Resolves to e.g. 10.0.0.171
    88|    88|ifconfig | grep "inet "                 # Check your subnet (e.g. 10.0.0.x)
    89|    89|for i in $(seq 1 254); do ping -c 1 -W 1 10.0.0.$i >/dev/null 2>&1 && echo "10.0.0.$i UP"; done
    90|    90|```
    91|    91|
    92|    92|Pattern: ping sweep your subnet → try mDNS `.local` hostname from manual →
    93|    93|resolve via DNS. The Spark usually shows up as the unknown active host that
    94|    94|isn't your router, phone, or MacBook.
    95|    95|
    96|    96|### 1.1 Initial Spark Setup
    97|    97|
    98|    98|```bash
    99|    99|sudo apt update && sudo apt upgrade -y
   100|   100|sudo apt install -y docker.io docker-compose-plugin
   101|   101|sudo usermod -aG docker $USER
   102|   102|newgrp docker
   103|   103|# NVIDIA container toolkit
   104|   104|curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
   105|   105|curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
   106|   106|sudo apt update && sudo apt install -y nvidia-container-toolkit
   107|   107|sudo nvidia-ctk runtime configure --runtime=docker
   108|   108|sudo systemctl restart docker
   109|   109|nvidia-smi
   110|   110|```
   111|   111|
### 1.2 BF16 Primary Config (Quality Mode)

**vLLM 0.20.2+ recommended for Qwen3.6-27B (May 2026):**

The stock `vllm/vllm-openai:latest` image (0.20.2+) now includes native SM121 support,
FlashAttention v2, and working speculative decoding. No need for custom AEON-7 image
for basic deployments:

```bash
docker run -d --name vllm-merged \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data:/data \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --reasoning-parser qwen3, --kv-cache-dtype fp8_e5m2, --load-format fastsafetensors,
  --speculative-config '{"method":"ngram","num_speculative_tokens":5}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 16384 \
  --max-num-seqs 128
```

**Key changes from earlier configs:**
- **Removed `--enable-prefix-caching`** — Qwen3.6 hybrid architecture (48 Mamba + 16 attention layers) reports `is_prefix_caching_supported: False`. The flag causes 0% hit rate and log spam. See `references/hybrid-model-prefix-caching-limitations.md`.
- **Increased `--max-num-batched-tokens` from 8192 → 16384** — Better batching for concurrent requests without quality loss.
- **Reduced `--max-num-seqs` from 256 → 128** — More realistic for single-user agent workloads; reduces scheduling overhead.

**Performance benchmarks (vLLM 0.20.2, Qwen3.6-27B + LoRA, May 14 2026):**

| Concurrent Requests | Throughput (tok/s) | Latency (s/req) |
|--------------------:|-------------------:|----------------:|
| 1 | 6.6 | 7.5 |
| 4 | 26.6 | 4.5 |
| 8 | 49.0 | 4.9 |
| 16 | 80.9 | 5.9 |
| 32 | 143.2 | 6.7 |
| 64 | 200.1 | 9.6 |
| 128 | 203.6 | 18.9 |
| 200 | 198.9 | 30.2 |

**Sweet spot:** 64-128 concurrent requests for maximum throughput (~200 tok/s).
Beyond 128, throughput plateaus due to GPU saturation.

**Tool calling verification:**
```bash
# Forced tool call (2-5s)
curl http://localhost:8000/v1/chat/completions \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"Use web_search to find weather in Tokyo"}],"tools":[{"type":"function","function":{"name":"web_search","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}}],"tool_choice":{"type":"function","function":{"name":"web_search"}}}'

# Auto tool call (25-30s — model reasons before calling)
curl http://localhost:8000/v1/chat/completions \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"Use web_search to find weather in Tokyo"}],"tools":[{"type":"function","function":{"name":"web_search","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}}],"tool_choice":"auto"}'
```

Both return proper `tool_calls` array with correct function name and arguments.

**Startup timeline (vLLM 0.20.2, first boot):**
1. Container start: instant
2. Model shard loading: ~3 min (15 shards × ~12s each)
3. Drafter model load: instant (n-gram needs no separate model)
4. torch.compile: ~66s (cached on subsequent boots)
5. CUDA graph capture: ~74s
6. Total to ready: ~5-6 minutes

**For AEON-7 DFlash image (advanced deployments):**

Use pre-built DFlash image directly:

```bash
# PRIMARY: Pull AEON-7 DFlash image (SM121 + DFlash + FlashInfer + TurboQuant)
docker pull ghcr.io/aeon-7/vllm-dflash:latest
docker tag ghcr.io/aeon-7/vllm-dflash:latest vllm-spark:tq
```

# FALLBACK: Same image tagged as base (AEON-7 image is all-in-one)
docker tag ghcr.io/aeon-7/vllm-dflash:latest vllm-spark:base

# COMMUNITY FALLBACKS:
docker pull hellohal2064/vllm-qwen3.5-gb10:latest
docker pull scitrera/dgx-spark-sglang:0.5.9-t5
```

**CRITICAL: Native MTP (Multi-Token Prediction) weights exist in Qwen3.6-27B but are NOT automatically used by vLLM.**

The checkpoint contains 15 MTP weights (`mtp.fc.weight`, `mtp.layers.0.*`, etc.) and `text_config.mtp_num_hidden_layers: 1`. However, vLLM 0.20.2 only auto-enables MTP speculative decoding when `model_type == "qwen3_5_mtp"` or `"qwen3_next_mtp"`. The Qwen3.6-27B checkpoint uses `model_type: qwen3_5`, which triggers n-gram speculative decoding instead.

**To enable native MTP (20-40% speedup over n-gram):**

Option A — Temporary config patch (test only):
```bash
# Backup original config
cp /data/models/Qwen3.6-27B-Uncensored/config.json /data/models/Qwen3.6-27B-Uncensored/config.json.bak

# Patch model_type to trigger MTP auto-detection
python3 -c '
import json
with open("/data/models/Qwen3.6-27B-Uncensored/config.json") as f:
    config = json.load(f)
config["model_type"] = "qwen3_5_mtp"
with open("/data/models/Qwen3.6-27B-Uncensored/config.json", "w") as f:
    json.dump(config, f, indent=2)
'

# Launch vLLM with MTP speculative decoding
docker run -d --name vllm-merged \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data:/data \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_xml \
  --reasoning-parser qwen3, --kv-cache-dtype fp8_e5m2, --load-format fastsafetensors,
  --speculative-config '{"method":"mtp","num_speculative_tokens":1}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 16384 \
  --max-num-seqs 128
```

Option B — Permanent config update (recommended):
```bash
# The model_type change is safe because vLLM's qwen3_5_mtp handler
# is backward-compatible with qwen3_5 checkpoints
# MTP weights are loaded if present, ignored if absent
python3 -c '
import json
with open("/data/models/Qwen3.6-27B-Uncensored/config.json") as f:
    config = json.load(f)
config["model_type"] = "qwen3_5_mtp"
with open("/data/models/Qwen3.6-27B-Uncensored/config.json", "w") as f:
    json.dump(config, f, indent=2)
print("Updated model_type to qwen3_5_mtp")
'
```

**Verification:**
```bash
# Check logs for MTP initialization
docker logs vllm-merged | grep -i mtp
# Should show: "Loading MTP weights..." or similar

# Check speculative config
curl -s http://localhost:8000/v1/models | python3 -c 'import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2))'
```

**Note:** MTP speculative decoding with `num_speculative_tokens=1` is the sweet spot for Qwen3.6-27B. Higher values (2-3) may cause acceptance rate collapse. Monitor with:
```bash
docker logs vllm-merged | grep -i "speculative"
```
If your merged model was trained from `Qwen/Qwen3.5-VL` (vision-language base), vLLM will fail with visual weight mismatches even though transformers loads it fine. Use transformers + FastAPI fallback or retrain from text-only base. See `references/qwen35-vl-merged-model-vllm-incompatibility.md` for full details, error signatures, and workarounds (GGUF quantization, visual weight stripping, etc.).

**WORKAROUND: Serve base model + LoRA adapter separately (May 14, 2026)**
If the merged model fails in vLLM but the base model loads fine, serve the base model with `--enable-lora` and load the adapter as a LoRA module. This preserves all post-training weights without needing to merge:

```bash
docker run -d --name vllm-merged \
  --gpus all --privileged --ipc host --network host \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/checkpoints \
  -e VLLM_MARLIN_USE_ATOMIC_ADD=1 \
  --entrypoint python3 \
  ghcr.io/aeon-7/vllm-dflash:latest \
  -m vllm.entrypoints.openai.api_server \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --port 8000 --host 0.0.0.0 \
  --max-model-len 262144 --gpu-memory-utilization 0.8 \
  --max-cudagraph-capture-size 256 \
  --enable-auto-tool-choice --tool-call-parser qwen3_coder \
  --kv-cache-dtype fp8_e5m2 --load-format fastsafetensors \
  --attention-backend flashinfer --enable-prefix-caching \
  --enable-chunked-prefill --dtype bfloat16 \
  --enable-lora --max-lora-rank 256 \
  --lora-modules merged-lora=/data/checkpoints/final_model
```

**Key flags:**
- `--enable-lora` — Required for LoRA serving
- `--max-lora-rank 256` — Must match or exceed your LoRA rank (default is 16, which fails for r=256)
- `--lora-modules merged-lora=/path/to/adapter` — Names the LoRA module; use `merged-lora` as model ID in API calls
- `--dtype bfloat16` — Keep BF16 for quality (FP8 weight quantization fails with torch.compile pickling errors on this model)
- **Omit `--reasoning-parser qwen3`** — Causes content to be null; Hermes needs content in standard field
- `--kv-cache-dtype fp8_e5m2` — Safe for KV cache (different from weight FP8)

**API usage:**
```bash
# Use the LoRA adapter
curl http://localhost:8000/v1/chat/completions \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"Hello"}]}'

# Use the base model (no LoRA)
curl http://localhost:8000/v1/chat/completions \
  -d '{"model":"/data/models/Qwen3.6-27B-Uncensored","messages":[{"role":"user","content":"Hello"}]}'
```

**Context length optimization for agent workloads (May 14, 2026):**

The model's `max_position_embeddings` is 262144, but agent workloads rarely need more than 32K:
- Training seq_len: 1024 tokens
- Typical agent turn: 512-2048 tokens
- Long code analysis: 4096-8192 tokens
- 32K handles 99% of use cases; 64K handles 99.9%

Reducing `--max-model-len` from 262144 to 32768:
- Saves ~30-40GB GPU memory (96GB → ~59GB)
- Improves concurrency: 4.3x → 27.5x concurrent requests
- Zero quality loss
- Faster inference (less KV cache overhead)

**Recommended for Hermes/agent deployments:** `--max-model-len 32768`

**Speed benchmarks (BF16 + FP8 KV, May 14 2026):**
| Mode | Speed | Memory |
|------|-------|--------|
| No thinking | ~20 tok/s | ~96GB |
| With thinking | ~4-8 tok/s | ~96GB |

**Batch inference is quality-neutral:** vLLM uses continuous batching — each request is processed independently. Zero quality loss, just better GPU utilization.

**Qwen3.6 thinking mode control (May 14, 2026):

Qwen3.6 has native thinking support via `<think>` (ID 248068) and `</think>` (ID 248069) tokens. The thinking behavior is controlled via `chat_template_kwargs`:

```bash
# Enable thinking (default) — model outputs reasoning before answer
curl http://localhost:8000/v1/chat/completions \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"What is 2+2?"}],"chat_template_kwargs":{"enable_thinking":true}}'

# Disable thinking — direct answer without reasoning
curl http://localhost:8000/v1/chat/completions \
  -d '{"model":"merged-lora","messages":[{"role":"user","content":"What is 2+2?"}],"chat_template_kwargs":{"enable_thinking":false}}'
```

**vLLM FP8 weight quantization — WORKING in vLLM 0.20.2+ (May 2026 update):**

Earlier failures were from torch.compile pickling incompatibilities in vLLM 0.19.x.
With vLLM 0.20.2, FP8 weight quantization works correctly on Qwen3.6:

```bash
--quantization fp8 --kv-cache-dtype auto --dtype bfloat16
```

**Verified working config (May 14 2026, Qwen3.6-27B):**
```bash
docker run -d --name vllm-merged \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data:/data \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora \
  --lora-modules merged-lora=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --max-lora-rank 256 \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.90 \
  --enable-auto-tool-choice --tool-call-parser qwen3_xml \
  --enable-prefix-caching --enable-chunked-prefill \
  --speculative-config '{"method":"ngram","num_speculative_tokens":5}' \
  --quantization fp8 \
  --kv-cache-dtype auto \
  --dtype bfloat16 \
  --max-num-batched-tokens 8192 \
  --max-num-seqs 256
```

**Key observations:**
- Model loads with CutlassFP8ScaledMMLinearKernel (confirmed in logs)
- Tool calling works correctly (tested with forced and auto tool_choice)
- No quality degradation observed in benchmarks
- ~1.5x speedup over BF16 weights (from reduced memory bandwidth)

**Earlier failure modes (vLLM 0.19.x, now resolved):**
1. `ValueError: fp8_e5m2 kv-cache is not supported with fp8 checkpoints` — fixed
2. `PicklingError: Can't pickle <function launcher>` — fixed in 0.20.2

**Quality note:** FP8 weights are "effectively lossless" per arXiv 2411.02355v2
(across Llama-3.1 family, <0.3% accuracy drop). For critical tool-calling workloads,
monitor for subtle errors over time — if observed, revert to BF16 weights + FP8 KV cache.

**Hermes config for thinking mode:**
```yaml
model:
  default: merged-lora
  provider: custom
  chat_template_kwargs:
    enable_thinking: true  # or false
```

**vLLM reasoning parser behavior:**
- Without `--reasoning-parser`: Thinking content appears in `content` field (raw model output)
- With `--reasoning-parser qwen3`: Thinking moves to `reasoning` field, `content` may be null
- **Recommendation:** Omit `--reasoning-parser` for Hermes integration — Hermes expects content in `content` field

**Speed impact:** Thinking mode is ~5-10x slower (generates reasoning tokens before answer). For Hermes agent training, thinking quality matters more than speed.
   128|   128|
   129|   129|The AEON-7 DFlash image includes: DFlash speculative decoding compiled in, FlashInfer v0.6.8 with SM121 support, GDN Triton allocator fixes, NVFP4 NaN guard, CUTLASS FP4 GEMM autotuning. Built on vLLM with TurboQuant KV cache compression (PR #38479),
   130|   130|FlashInfer v0.6.8 with SM121 tile filtering + NVFP4 group GEMM, NGC PyTorch 26.03 base,
   131|   131|5 cherry-picked PRs (Triton decode OOB, BF16 FP8 cast, TQ backend selection,
   132|   132|hybrid model support for Qwen3.5/3.6, FA3/FA4 prefill paths).
   133|   133|
   134|   134|**Fallback chain:** AEON-7 DFlash → community hellohal2064 → custom SM121 build → stock vllm-openai
   135|   135|
   136|   136|**CRITICAL FLAG for GDN hybrid models:** Add `--max-cudagraph-capture-size 256` to
   137|   137|all vLLM serve commands. Default 512 exceeds Mamba cache size on Qwen3.6 GDN hybrid
   138|   138|(30 GDN layers + 10 attention layers) and causes fatal assertion failures.
   139|   139|
   140|   140|docker run with AEON-7 image on port 8000:
   141|   141|Key flags: --max-model-len 262144, --gpu-memory-utilization 0.8,
   142|   142|--max-cudagraph-capture-size 256,
   143|   143|--enable-auto-tool-choice, --tool-call-parser qwen3_coder,
   144|   144|--reasoning-parser qwen3, --kv-cache-dtype fp8_e5m2, --load-format fastsafetensors,
   145|   145|--attention-backend flashinfer, --enable-prefix-caching,
   146|   146|--enable-chunked-prefill,
   147|   147|VLLM_MARLIN_USE_ATOMIC_ADD=1.
   148|   148|Image: ghcr.io/aeon-7/vllm-dflash:latest (tagged vllm-spark:tq)
   149|   149|Expected: ~50 tok/s short context, ~25-35 at 100K+. Full 262K. 100% quality.
   150|   150|
**TurboQuant KV Cache Options:**
| Mode | Flag | Compression | Best For |
|---|---|---|---|
| FP8 | --kv-cache-dtype fp8 | 2x | Default, safest |
| TQ monkey-patch | Python package (0xSero/turboquant) | 4.4x | **27B DENSE ONLY** — pip install, no rebuild |
| TQ k8v4 | --kv-cache-dtype turboquant_k8v4 | 2-4x | BLOCKED on 35B-A3B (GDN hybrid) |
| TQ 4bit | --kv-cache-dtype turboquant_4bit_nc | 3.8x | BLOCKED on 35B-A3B (GDN hybrid) |
| TQ 3bit | --kv-cache-dtype turboquant_3bit_nc | 4.9x | BLOCKED on 35B-A3B (GDN hybrid) |

**CRITICAL DISTINCTION:**
- **35B-A3B (GDN hybrid):** TurboQuant vLLM-native presets are BLOCKED. GDN layers (30/40) lack uniform attention, so boundary layer protection fails. Use `fp8_e5m2` instead.
- **27B (Dense):** TurboQuant WORKS via `0xSero/turboquant` Python monkey-patch package. Installs into AEON-7 image without rebuild. All 64 attention layers compressible. See `references/apr22-qwen36-27b-migration-findings.md` Section 13 for Dockerfile, entrypoint, and build instructions.

Use `--kv-cache-dtype auto` to let vLLM pick the best available mode
(may default to fp8 on hybrid models where TQ is blocked).
   166|   166|
   167|   167|### 1.3 FP8 Speed Config (Coding/Agent Mode)
   168|   168|
   169|   169|Same as BF16 but model Qwen/Qwen3.6-35B-A3B-FP8 on port 8001.
   170|   170|Expected: ~64 tok/s peak. ~1% quality loss.
   171|   171|
   172|   172|### 1.4 Hybrid INT4+FP8 Max Speed Config
   173|   173|
   174|   174|```bash
   175|   175|git clone https://github.com/phuongncn/asus-gx10-qwen35-speed-hack.git
   176|   176|bash run-hybrid.sh
   177|   177|```
   178|   178|Expected: 100+ tok/s. ~4% quality loss. Check repo issues for Qwen3.6 compat.
   179|   179|
### 1.5 Auxiliary Models (Co-Host)

Qwen3-Embedding-0.6B on port 8002 (1.5GB overhead)
Qwen3-Reranker-0.6B on port 8003 (1.5GB overhead)
Qdrant vector DB on port 6333
LiteLLM router on port 4000

### 1.6 SGLang Alternative Inference Engine (GB10-Verified)

SGLang works on DGX Spark via a community pre-built Docker image. It is NOT faster than vLLM+DFlash for Qwen3.6 without EAGLE-3 speculative decoding, but it is a viable alternative.

**Official Docker image:** `lmsysorg/sglang:latest` (11.8 GB, updated 2026-05-05)
- Pull: `docker pull lmsysorg/sglang:latest`
- Requires ~12GB disk space + model size
- Available tags: `latest`, `deepep`, `v{version}`
- Docker Hub: https://hub.docker.com/r/lmsysorg/sglang

**Pre-built image for GB10:** `scitrera/dgx-spark-sglang:0.5.8-t5`
- SGLang 0.5.8, PyTorch 2.10.0, CUDA 13.1.1, Triton 3.6.0
- Includes SM121a patches that standard SGLang installations lack

**Working launch command:**
```bash
docker run -d --name sglang-dgx --gpus all --privileged --ipc host --network host \
  -v /data/models:/root/.cache/huggingface \
  scitrera/dgx-spark-sglang:0.5.8-t5 \
  sglang serve \
    --model-path /root/.cache/huggingface/Qwen3.6-35B-A3B-Uncensored \
    --port 8000 --host 0.0.0.0 \
    --mem-fraction-static 0.95 \
    --max-running-requests 512 \
    --chunked-prefill-size 65536 \
    --disable-cuda-graph \
    --attention-backend triton
```

**Required flags for GB10:**
- `--disable-cuda-graph` : Avoids illegal memory access on sm_121a (SGLang #19799)
- `--attention-backend triton` : FlashInfer backend crashes with `cudaErrorNoKernelImageForDevice` on SM121a

**Performance:** ~28 tok/s sustained (vs vLLM+DFlash at ~42 tok/s)

**Why it is slower:** CUDA graphs are disabled (major perf hit) and Triton attention backend is used instead of FlashInfer.

**Speedup paths:**
1. **EAGLE-3 speculative decoding:** Train or obtain a draft model. Reddit reports 60 tok/s with SGLang+EAGLE-3 on DGX Spark.
2. **N-gram speculative decoding:** Zero training, generate ngram model from corpus. Best for repetitive text.

**CRITICAL: SGLang does NOT support hybrid Mamba/SSD models (May 15, 2026)**

Qwen3.6-27B uses a hybrid architecture (48 Mamba/SSD layers + 16 attention layers, `Qwen3_5ForConditionalGeneration` class). SGLang v0.5.11 silently **hangs indefinitely during weight loading** — "Load weight begin" freezes at ~52GB memory with no error. The `sglang::scheduler` process holds ~100GB GPU memory and does NOT release it on `docker rm -f`. Manual `kill -9` required.

**Affected models:** Qwen3.6-27B-Uncensored, Qwen3.5-VL, any `Qwen3_5ForConditionalGeneration` architecture
**Working alternative:** vLLM 0.20.2+ fully supports hybrid architectures

See `references/sglang-qwen36-hybrid-mamba-incompatibility.md` for full details, verification steps, and cleanup procedures.

**Docker Compose deployment (official image):**
```yaml
services:
  sglang:
    image: lmsysorg/sglang:latest
    container_name: sglang
    volumes:
      - ${HOME}/.cache/huggingface:/root/.cache/huggingface
    restart: always
    network_mode: host
    privileged: true
    environment:
      - HF_TOKEN=<secret>
    entrypoint: python3 -m sglang.launch_server
    command: --model-path /data/models/Qwen3.6-27B-Uncensored --host 0.0.0.0 --port 30000
    ulimits:
      memlock: -1
      stack: 67108864
    ipc: host
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:30000/health || exit 1"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**DO NOT use standard sglang-venv on host.** It fails with: CPU-only PyTorch → Triton ptxas `sm_121a` error → FlashInfer kernel image missing → custom PyTorch overwrite. See `references/apr21-performance-audit-findings.md` for full failure chain.

**Build from source:** NVIDIA forum guide at https://forums.developer.nvidia.com/t/build-sglang-from-source-on-blackwell-pro-6000-dgx-spark/360785 — compile `sgl-kernel` with `TORCH_CUDA_ARCH_LIST="12.1a"`.

### 1.7 LiteLLM Router Config

   189|   189|Routes: qwen-bf16 -> local Spark, qwen-fp8 -> Spark FP8, fallback -> FriendliAI
   190|   190|routing_strategy: usage-based-routing-v2
   191|   191|
## Phase 2: Hermes Integration

See `references/inference-acceleration-plan-may14-2026.md` for the **complete research findings** on Qwen3.6-27B inference acceleration — DFlash speculative decoding, prefix caching, chunked prefill, FP8 quantization, and continuous batching tuning. Includes expected speedups, risk assessment, and phased rollout plan.

See `references/vllm-systematic-optimization-may15-2026.md` for the **systematic vLLM config optimization methodology** — baseline measurement, config variation, quality verification, rollback on degradation. Includes benchmark script, verified configs, and failure modes for Qwen3.6-27B.

See `references/ssh-access-troubleshooting-may14-2026.md` for diagnosing SSH permission denied errors, no-SSH diagnostics via HTTP API, and recovery procedures when DGX Spark SSH access is lost.

See `references/vllm-stuck-after-inactivity-may15-2026.md` for diagnosing and fixing vLLM containers that appear running but stop processing requests after 4+ hours idle.

See `references/dgx-hermes-complete-deployment-may14-2026.md` for the COMPLETE step-by-step deployment guide covering source sync, plugin config, credential sync, Node.js ARM64 install, tool verification, iteration pipeline fix, and systemd service setup.

See `references/vllm-lora-serving-speed-context-optimization-may14-2026.md` for full vLLM LoRA serving pattern, speed benchmarks, context optimization, and Hermes config.

See `references/vllm-context-window-upgrade-pattern.md` for upgrading vLLM context window (e.g., 64K → 128K) — requires full container restart, not just config change. Includes LoRA path verification and startup timeline.

See `references/qwen36-mtp-speculative-decoding-discovery.md` for native MTP (Multi-Token Prediction) weights found in Qwen3.6-27B — how to enable them for 20-40% speedup over n-gram speculative decoding.

See `references/vllm-systematic-optimization-may15-2026.md` for the **systematic vLLM config optimization methodology** — baseline measurement, config variation, quality verification, rollback on degradation. Includes benchmark script, verified configs, and failure modes for Qwen3.6-27B.

See `references/hybrid-model-prefix-caching-limitations.md` for why prefix caching shows 0% hit rate on Qwen3.6 hybrid models — `is_prefix_caching_supported: False` is architecture-determined, not a config issue. Includes verification commands and alternative speedup paths.

See `references/vllm-speedup-landscape-may15-2026.md` for the complete vLLM speedup/feature matrix as of May 2026 — what's working, what's not, what's coming in vLLM roadmap Q2 2026 (Model Runner V2, P-EAGLE, DFlash, FA4 status, SGLang comparison).

See `references/dflash-lora-optimization-deep-dive-may16-2026.md` for the **complete research on running base + dynamic LoRA + speculative decoding at high speed** — why vLLM can't deliver (issue #6912), SGLang as the best alternative (+29% throughput with S-LoRA), num_speculative_tokens sweet spot (8 for 25-30% acceptance), and three deployment options (SGLang, optimized vLLM, hybrid approach).

See `references/eagle3-qwen36-investigation-may15-2026.md` for the **EAGLE-3 speculative decoding investigation on Qwen3.6-27B** — why it doesn't work, what was tried, and what would be needed to make it work. Key finding: vLLM 0.20.2 lacks `Eagle3Qwen3ForCausalLM` support; Qwen3.6's non-standard attention dims break Llama-based EAGLE-3 drafts.

See `references/vllm-stuck-after-inactivity-may15-2026.md` for diagnosing and fixing vLLM containers that appear running but stop processing requests after 4+ hours idle.

See `references/dgx-hermes-complete-deployment-may14-2026.md` for the COMPLETE step-by-step deployment guide covering source sync, plugin config, credential sync, Node.js ARM64 install, tool verification, iteration pipeline fix, and systemd service setup.

See `references/dgx-hermes-old-process-cleanup-may16-2026.md` for cleaning up old Hermes processes after deploying the module shadowing fix.

See `references/dgx-hermes-service-setup-may16-2026.md` for systemd service setup with module shadowing fix wrapper script, auto-restart after power cycles, and vLLM tool calling flags for Hermes compatibility.

See `references/dgx-hermes-terminal-ssh-config-may16-2026.md` for configuring DGX Hermes to execute terminal commands on MacBook via SSH — SSH key setup, Hermes terminal backend config, and verification.

See `references/dgx-hermes-cognitive-orchestrator-init-may16-2026.md` for initializing the cognitive orchestrator with all 20 subsystems — the orchestrator does NOT auto-load, must be explicitly initialized with an agent instance.

See `references/dgx-hermes-full-agent-toolset-config.md` for the COMPLETE toolset configuration guide — how to get 97 tools instead of the default 21 on DGX Hermes. Covers plugin config format, config file location, API credential sync, and Node.js installation for browser automation.

See `references/dgx-hermes-full-system-verification.md` for the complete post-deployment verification guide — full system test script, subsystem inventory, common issues, and vLLM health check.

See `references/dgx-hermes-file-sync-verification.md` for verifying that ALL MacBook files are present on DGX after sync, with automated health check script.

See `references/dgx-hermes-tool-registration-check-fn-may14-2026.md` for the four barriers to full tool coverage and debugging commands.

See `references/dgx-hermes-config-location-and-format.md` for the critical config file location pitfall — Hermes reads from `~/.hermes/config.yaml`, NOT the repo directory, and the dict vs list plugin format issue.

See `references/shell-escaping-ssh-script-transfer.md` for the base64 encoding pattern — the only reliable way to transfer multi-line scripts with quotes/newlines through SSH.

See `references/shell-escaping-ssh-script-transfer-extended.md` for the full pattern including `execute_code` string literal pitfalls, terminal tool guardrails (5-failure hard stop, background process blocking), and recovery strategies.

See `references/ssh-python-script-transfer-patterns.md` for the complete decision tree — when to use single-quoted heredocs vs base64 encoding vs scp transfer vs Python one-liners. Includes anti-patterns and verification commands.

See `references/dgx-iteration-pipeline-fix-may14-2026.md` for fixing stuck distillation daemons — the lesson extraction was only processing failures, missing 97% of experiences.

See `references/dgx-hermes-full-sync-verification.md` for verifying the complete Hermes source code sync to DGX with all cognitive systems, tools, and training pipelines.

See `references/dgx-hermes-module-shadowing-fix-may16-2026.md` for fixing Python module shadowing when `hermes_cli/gateway.py` conflicts with the `gateway/` package directory. Use `importlib.util` pre-import pattern or rename the shadowing file.

See `references/vision-preserving-lora-merge-may16-2026.md` for merging LoRA adapters into Qwen3.5/3.6 multimodal models while preserving vision encoder and projector weights. Standard `merge_and_unload()` strips vision components.

### 2.0 Hermes Source Sync to DGX (When DGX Has No Hermes)

If the DGX does not yet have Hermes Agent source code, you must sync it from the MacBook before wiring inference. This is a ONE-TIME setup.

**Prerequisites:**
- MacBook has Hermes at `~/hermes-agent/` (verified working install)
- DGX has Python 3.11+ and CUDA working (`python3 -c "import torch; print(torch.cuda.is_available())"` → `True`)
- DGX has sufficient disk space (~200MB for Hermes source, plus venv packages)

**Sync procedure:**

```bash
# ON MACBOOK — one-shot rsync (excludes build artifacts, keeps source lean)
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.pytest_cache' --exclude='venv' --exclude='.venv' \
  --exclude='datasets' --exclude='temp_vision_images' \
  ~/hermes-agent/ djg6228@spark-85e8.local:/data/SpecForge/hermes-agent/
```

**DGX venv setup:**
```bash
# ON DGX (via SSH)
cd /data/SpecForge/hermes-agent
python3 -m venv venv
source venv/bin/activate
pip install -e . --quiet
```

**Verification:**
```bash
# ON DGX
source /data/SpecForge/hermes-agent/venv/bin/activate
python3 -c "from hermes_cli.plugins import get_plugin_manager; print('Hermes OK')"
```

**Pitfall — Terminal tool `[Command interrupted]` (exit 130):**
If the `terminal` tool fails with exit code 130 on SSH commands, the terminal backend may be broken. Use `execute_code` with `subprocess.run()` instead, or write a setup script locally and scp it to DGX.

**Pitfall — DGX disk space:**
If DGX `/` partition is low on space, the venv may fail to install. Check `df -h` first. Hermes source + venv needs ~500MB minimum.

**CRITICAL: `hermes_cli/cron.py` shadows the `cron` package (May 15, 2026)**

After syncing Hermes source to DGX, the `cron` module import fails with:
```
ModuleNotFoundError: No module named 'cron.scheduler'
```

**Root cause:** `hermes_cli/cron.py` shadows the `cron` package. When Python resolves `import cron.scheduler`, it finds `hermes_cli/cron.py` first (via PYTHONPATH), which has no `scheduler` submodule.

**Fix:** Rename the CLI file and update all imports:
```bash
cd /data/SpecForge/hermes-agent
mv hermes_cli/cron.py hermes_cli/cron_cmd.py
# Update import in main.py: from .cron import → from .cron_cmd import
# Update import in tests/hermes_cli/test_cron.py: from hermes_cli.cron import → from hermes_cli.cron_cmd import
```

**Verification:**
```bash
cd /data/SpecForge/hermes-agent
venv/bin/python -c "import cron.scheduler; print('OK')"
```

This fix is REQUIRED for the Hermes gateway and distillation daemon to start.

### 2.1 Architecture: Hub-and-Spoke vs Full Hermes on DGX

**Pattern A: Hub-and-Spoke (MacBook brain + DGX throat)**

DGX is NOT a second Hermes — it's a vLLM inference server ONLY.
ALL agent logic (tools, plugins, context injection, skills, memory, cron)
stays on the MacBook. DGX just answers /v1/chat/completions calls.

MacBook Hermes (GLM-5.1) = BRAIN (all agent logic)
  |--> /model --provider dgx-fp8 ...  (speed, :8001, free)
  |--> /model --provider dgx-bf16 ... (quality, :8000, free)
  |--> /model zai-org/GLM-5.1           (default, smart)
DGX Qwen3.6 (vLLM) = THROAT (inference only, no Hermes code)

**Pattern B: Full Hermes on DGX (COMPLETE agent instance)**

If the user explicitly asks to "clone Hermes to DGX" or "run the full Hermes harness on DGX", they want the COMPLETE agent (not just inference). In this case:
1. Sync source (Section 2.0)
2. Set up venv
3. Configure DGX-specific `config.yaml` pointing to local model path
4. **CRITICAL: Deploy real-time learning apparatus BEFORE declaring model "ready"** — see `agent-cognitive-infrastructure` skill Section "Real-Time Learning Apparatus Deployment Pattern"
5. The DGX Hermes instance uses the local Qwen model as its primary provider
6. MacBook Hermes and DGX Hermes are SEPARATE instances — no hub-and-spoke

**Full Hermes sync procedure (May 14, 2026):**

When the user wants the FULL Hermes experience on DGX (skills, knowledge, memory, everything):

```bash
# ON MACBOOK — sync skills, knowledge, memory to DGX
tar czf /tmp/hermes-skills-sync.tar.gz -C ~/.hermes skills/ knowledge/
tar czf /tmp/hermes-memory-sync.tar.gz -C ~/.hermes cerebrum_memory.db
scp /tmp/hermes-skills-sync.tar.gz djg6228@spark:/tmp/
scp /tmp/hermes-memory-sync.tar.gz djg6228@spark:/tmp/
```

```bash
# ON DGX — extract and configure
cd /tmp
tar xzf hermes-skills-sync.tar.gz -C ~/.hermes/
tar xzf hermes-memory-sync.tar.gz -C ~/.hermes/

# Hermes Config for DGX
# ... rest of config ...
```

**CRITICAL: Toolset configuration for full DGX Hermes**

DGX Hermes defaults to only 21 tools if `enabled_toolsets` is not configured. To get the full ~90+ tool complement:

```yaml
# In /data/SpecForge/hermes-agent/config.yaml
agent:
  enabled_toolsets: all  # OR list specific ones
```

Without this, only "safe" tools (no external credentials needed) are loaded:
- Loaded: delegate_task, execute_code, memory, patch, process, read_file, search_files, session_search, skill_manage, skill_view, skills_list, terminal, todo, vision_analyze, write_file, x_search, x_tweet_fetch, x_user_tweets
- Missing: browser_*, web_search, web_extract, cronjob, kanban_*, send_message, ha_*, image_generate, rl_*, spotify_*, discord_*, feishu_*, yb_*, etc.

**Verification:**
```bash
cd /data/SpecForge/hermes-agent
venv/bin/python -c "from model_tools import get_tool_definitions; tools = get_tool_definitions(); print(f'Total tools: {len(tools)}')"
# Should show 90+ with enabled_toolsets: all
# Shows 21 with default/minimal config
```

**CRITICAL: Hermes requires minimum 64K context window.** Even though 32K is sufficient for 99% of agent workloads, Hermes' validation enforces `context_length >= 64000`. Set both vLLM and Hermes config to 64K (65536):

```bash
# vLLM launch (use 64K, not 32K)
--max-model-len 65536
```

```yaml
# Hermes config (~/.hermes/config.yaml)
model:
  provider: custom
  base_url: http://localhost:8000/v1
  api_key: not-needed
  default: merged-lora
  context_length: 65536  # REQUIRED: Hermes minimum is 64K
  chat_template_kwargs:
    enable_thinking: true

providers:
  custom:
    api: http://localhost:8000/v1
    api_key: not-needed
    models:
      merged-lora:
        context_length: 65536  # REQUIRED: Hermes minimum is 64K
        supports_tools: true
        supports_reasoning: true
```

**Error if context < 64K:**
```
ValueError: Model merged-lora has a context window of 32,768 tokens,
which is below the minimum 64,000 required by Hermes Agent.
Choose a model with at least 64K context, or set model.context_length
in config.yaml to override.
```

**Context length trade-offs on GB10:**
| Context | GPU Memory | Concurrency | Hermes Compatible |
|---------|-----------|-------------|-------------------|
| 32K | ~59GB | 27.5x | ❌ Below minimum |
| 64K | ~75GB | 13.8x | ✅ Minimum |
| 128K | ~85GB | 6.9x | ✅ |
| 262K | ~96GB | 4.3x | ✅ Maximum |

# Add hermes to PATH
echo 'export PATH=/data/SpecForge/hermes-agent/venv/bin:$PATH' >> ~/.bashrc
echo 'export HERMES_CONFIG=/home/djg6228/.hermes/config.yaml' >> ~/.bashrc

# Create wrapper alias
echo 'alias hermes-dgx="cd /data/SpecForge/hermes-agent && source venv/bin/activate && hermes"' >> ~/.bashrc
```

**Result:**
- DGX has full Hermes codebase at `/data/SpecForge/hermes-agent/`
- All 85+ skills synced from MacBook
- All 1000+ knowledge files synced
- Cerebrum memory DB synced
- Local Qwen3.6-27B + FrankenV8 LoRA as primary model
- Thinking mode enabled by default
- Can run `hermes-dgx --model merged-lora` on DGX terminal
- MacBook Hermes stays independent — both run simultaneously

**User preference (May 2026):** When choosing between model training and Hermes skill accumulation, prioritize Hermes tinkering. Train the model first only when:
- Datasets are ready and transferred
- Training config is verified
- Hermes has a working inference endpoint (even if quantized)
- The user explicitly asks for training before Hermes work

The user values "tinkering with hermes" over blocking the GPU for days with training.

**CRITICAL: Real-time learning apparatus is prerequisite for "running" a model**

The user will NOT consider a model "ready to run" unless it has real-time learning wired into every turn. This means:
1. Cerebrum DB initialized and synced
2. Learning hooks patched into model_tools.py and run_agent.py
3. Distillation daemon running as systemd service
4. Session exporter writing training data
5. Tool count verified (90+ tools, not 21)

See `agent-cognitive-infrastructure` skill for the full deployment pattern.

**CRITICAL: HERMES_CONFIG conflict when DGX has both MacBook and native configs (May 15, 2026)**

After syncing Hermes to DGX, `~/.bashrc` may contain MULTIPLE `HERMES_CONFIG` exports:
```bash
export HERMES_CONFIG=/data/SpecForge/hermes-agent/config.yaml  # DGX native (full plugins)
export HERMES_CONFIG=/home/djg6228/.hermes/config.yaml         # MacBook minimal (21 tools)
```

The LAST export wins. If the MacBook minimal config is last, Hermes loads only 21 tools instead of 90+.

**Fix:** Remove duplicate, symlink DGX config to standard location:
```bash
# Remove conflicting line from ~/.bashrc
sed -i '/HERMES_CONFIG=\/home\/djg6228\/.hermes\/config.yaml/d' ~/.bashrc

# Symlink DGX config to standard location
mv ~/.hermes/config.yaml ~/.hermes/config.yaml.backup
ln -s /data/SpecForge/hermes-agent/config.yaml ~/.hermes/config.yaml

# Create convenience wrapper
cat > /usr/local/bin/hermes-dgx << 'EOF'
#!/bin/bash
export HERMES_CONFIG=/data/SpecForge/hermes-agent/config.yaml
exec /data/SpecForge/hermes-agent/venv/bin/hermes "$@"
EOF
chmod +x /usr/local/bin/hermes-dgx
```

**Verification:**
```bash
hermes-dgx plugins list | grep 'enabled' | wc -l
# Should show 40 (not 21)
```

**Pitfall:** Even with correct config, running `hermes status` may hang because learning-brain plugin tries to use DeepSeek API. Use `hermes plugins list` instead for quick verification.

### 2.2 Wiring Script (ONE COMMAND)

bash ~/dgx-spark-prep/wire-spark-to-hermes.sh <SPARK_IP>
bash ~/dgx-spark-prep/wire-spark-to-hermes.sh --tunnel <SPARK_IP>  # SSH tunnel

Adds spark-fp8 and spark-bf16 providers to ~/.hermes/config.yaml
WITHOUT changing default GLM-5.1 provider. Patches profile configs
(replaces SPARK_IP_PLACEHOLDER with real IP). Creates backups.
   214|   214|
   215|   215|### 2.3 Multi-Profile Launch (Simultaneous Sessions)
   216|   216|
   217|   217|Four isolated Hermes profiles, all can run at once:
   218|   218|
   219|   219|  hermes chat          -> GLM-5.1 (smart, default, FriendliAI)
   220|   220|  spark-speed chat     -> Qwen3.6 FP8 (fast, free, local :8001)
   221|   221|  spark-quality chat   -> Qwen3.6 BF16 (quality, free, local :8000)
   222|   222|  training-gym chat    -> GLM-5.1 (existing training profile)
   223|   223|
   224|   224|Profile setup (one-time):
   225|   225|  hermes profile create spark-speed --clone
   226|   226|  hermes profile create spark-quality --clone
   227|   227|  Then edit each profile config.yaml:
   228|   228|    spark-speed: model.default=Qwen/Qwen3.6-35B-A3B-FP8, provider=spark-fp8, base_url=http://SPARK_IP_PLACEHOLDER:8001/v1
   229|   229|    spark-quality: model.default=Qwen/Qwen3.6-35B-A3B, provider=spark-bf16, base_url=http://SPARK_IP_PLACEHOLDER:8000/v1
   230|   230|  wire-spark-to-hermes.sh patches SPARK_IP_PLACEHOLDER -> real IP
   231|   231|
   232|   232|Spark vLLM uses continuous batching — handles concurrent requests.
   233|   233|
   234|   234|### 2.4 Dual-Training: GLM-5.1 + Qwen3.6 Simultaneously
   235|   235|
   236|   236|GLM-5.1 (teacher) runs on FriendliAI cloud = generates distillation data
   237|   237|Qwen3.6 (student) trains on Spark GPU = LoRA/GRPO
   238|   238|Different hardware = truly simultaneous, no GPU sharing needed.
   239|   239|
   240|   240|  dual-training-orchestrator.sh --mode distill    # Teacher generates data
   241|   241|  dual-training-orchestrator.sh --mode sft         # Student SFT on distilled data
   242|   242|  dual-training-orchestrator.sh --mode grpo        # Student GRPO trains
   243|   243|  dual-training-orchestrator.sh --mode continuous  # Full loop: distill->sft->grpo->eval->repeat
   244|   244|  dual-training-orchestrator.sh --mode status     # Show current state
   245|   245|
   246|   246|GPU CONSTRAINT: During GRPO, vLLM sampling server needs 85% Spark GPU.
   247|   247|Inference serving (:8000/:8001) PAUSES. GLM-5.1 still works (cloud).
   248|   248|During SFT, no vLLM needed, inference stays up.
   249|   249|
   250|   250|Continuous loop: Teacher generates -> SFT learns -> GRPO improves -> eval -> repeat.
   251|   251|Each round student gets smarter. Gap narrows over time.
   252|   252|
   253|   253|### 2.5 SSH Tunnel (if remote)
   254|   254|
   255|   255|autossh -M 0 -f -N -L 8000:localhost:8000 -L 8001:localhost:8001 -L 6333:localhost:6333 user@SPARK_IP
   256|   256|
   257|   257|wire-spark-to-hermes.sh --tunnel sets this up and updates config to localhost.
   258|   258|
   259|   259|### 2.6 Kill Z.AI Max Plan
   260|   260|
   261|   261|Cancel at https://z.ai/subscribe 3+ days before renewal.
   262|   262|Remove Z.AI coding endpoint from .env.
   263|   263|
   264|   264|## Phase 3: Optimization Stack
   265|   265|
   266|   266|### 3.1 Hugging Face Kernel Hub (GAME CHANGER for Spark)
   267|   267|
   268|   268|**Before:** Compiling FlashAttention-3 from source needs 96GB RAM, 10min-hours,
   269|   269|CMAKE flag debugging, and you repeat for EACH kernel.
   270|   270|**After:** `pip install kernels` + one line of Python. Auto-detects your exact
   271|   271|Python, PyTorch, CUDA version, and GPU arch (SM121). Downloads pre-compiled
   272|   272|binary in seconds.
   273|   273|
   274|   274|```bash
   275|   275|pip install kernels
   276|   276|python3 -c "from kernels import get_kernel; fa3 = get_kernel('kernels-community/flash-attn3')"
   277|   277|```
   278|   278|
   279|   279|13 CRITICAL kernels for Qwen3.6 on SM121 (Blackwell GB10):
   280|   280|
   281|   281|| Kernel | Downloads | Purpose |
   282|   282||---|---|---|
   283|   283|| flash-attn3 | 286K | Blackwell-native attention — BIGGEST speedup |
   284|   284|| vllm-flash-attn3 | 37K | vLLM's serving fork of FA3 |
   285|   285|| flash-mla | 855 | Multi-head Latent Attention (Qwen3.5/3.6 MoE USES THIS) |
   286|   286|| scattermoe | 0 | MoE scatter-to-expert routing — critical for MoE |
   287|   287|| paged-attention | 721 | vLLM PagedAttention KV cache management |
   288|   288|| fp8-fbgemm | 0 | FP8 inference kernel |
   289|   289|| activation | 58K | Fused GELU/SiLU/Swish |
   290|   290|| rmsnorm | 226 | RMSNorm (Qwen uses this, not LayerNorm) |
   291|   291|| rotary | 1.5K | RoPE position embeddings (Qwen) |
   292|   292|| deep-gemm | 194 | Optimized GEMM for Blackwell |
   293|   293|| triton-layer-norm | 12K | Triton-optimized layer norm |
   294|   294|| liger-kernels | 106 | Fused LoRA training kernels |
   295|   295|| triton-kernels | 1.6K | General Triton kernels |
   296|   296|
   297|   297|All 13 pre-downloadable on Day 1 (deploy-spark-day1.sh Step 2.7).
   298|   298|One failed kernel download is non-fatal — vLLM falls back to built-in implementation.
   299|   299|Kernels MUST download on the Spark (not MacBook) — binaries are GPU/arch-specific.
   300|   300|
   301|   301|Full catalog: https://huggingface.co/kernels-community (56+ kernels as of Apr 2026)
   302|   302|
### 3.2 DFlash Speculative Decoding (Block Diffusion, z-lab)

```bash
# DFlash is ENABLED BY DEFAULT in all launch scripts (Apr 19 audit).
# DFlash is the PRIMARY speculative decoding method for Qwen3.6. Requires the AEON-7 DFlash image or a vLLM build with DFlash support.
# Disable with: DFLASH=false ./spark-day1.sh

# DFlash model already downloaded by spark-day1.sh (line 506, gated repo)
# vLLM flag injected automatically:
# --speculative-config method=dflash model=/data/models/Qwen3.6-35B-A3B-DFlash num_speculative_tokens=15
```

Block diffusion model (0.5B params, NOT LSTM). Generates 15 draft tokens in a
single forward pass. Claims 6x lossless speedup, 2.5x faster than EAGLE-3.
Accept length 5-7 on Qwen3.6. If DFlash + GDN hybrid breaks, validation tests
catch it — just set DFLASH=false for instant safe fallback (no speculative decoding).

**Systemd service for auto-start on boot:**
```bash
# Install service (one-time)
bash scripts/install-systemd-service.sh

# Or manually:
sudo cp /tmp/vllm-dflash.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vllm-dflash.service
sudo systemctl start vllm-dflash.service
```

See `scripts/install-systemd-service.sh` for the full service definition.

**VERIFIED on Qwen3.6-27B with Qwen3.5-27B-DFlash draft (May 15, 2026):**
The `z-lab/Qwen3.6-27B-DFlash` model is gated, but `z-lab/Qwen3.5-27B-DFlash` is public
and works as a draft model for Qwen3.6-27B:

```bash
# Download public draft model
python3 -c 'from huggingface_hub import snapshot_download; snapshot_download(repo_id="z-lab/Qwen3.5-27B-DFlash", local_dir="/data/models/Qwen3.5-27B-DFlash")'

# Deploy with DFlash
--speculative-config '{"method":"dflash","model":"/data/models/Qwen3.5-27B-DFlash","num_speculative_tokens":16}'
```

**Results:** 18.36 tok/s (+179% vs n-gram baseline), 24.2% acceptance rate, lossless quality.
See `qwen27b-dgx-deployment:references/vllm-dflash-deployment-may15-2026.md` for full details.
   319|   319|
**N-gram speculative decoding WORKS in vLLM 0.20.2+ (May 2026 update).**
Earlier reports of corruption were from vLLM 0.19.x. With vLLM 0.20.2, n-gram speculative
decoding is stable on Qwen3.6-27B and Qwen3.6-35B-A3B:

```bash
--speculative-config '{"method":"ngram","num_speculative_tokens":5}'
```

**Verified performance (Qwen3.6-27B, vLLM 0.20.2, May 14 2026):**
- Draft acceptance rate: 60-85% (varies by prompt)
- Mean acceptance length: 2-5 tokens
- Zero quality degradation (lossless)
- No authentication required (unlike DFlash/EAGLE-3)

**DFlash speculative decoding VERIFIED on Qwen3.6-27B (May 15, 2026):**

The `z-lab/Qwen3.6-27B-DFlash` model is gated (403 Forbidden), but `z-lab/Qwen3.5-27B-DFlash`
is public and works as a draft model for Qwen3.6-27B:

**VERIFIED on Qwen3.6-27B with Qwen3.5-27B-DFlash draft (May 15-16, 2026):**
The `z-lab/Qwen3.6-27B-DFlash` model is gated, but `z-lab/Qwen3.5-27B-DFlash` is public
and works as a draft model for Qwen3.6-27B:

```bash
# Download public draft model
python3 -c 'from huggingface_hub import snapshot_download; snapshot_download(repo_id="z-lab/Qwen3.5-27B-DFlash", local_dir="/data/models/Qwen3.5-27B-DFlash")'

# Deploy with DFlash (tuned num_tokens=5 for 54-60% acceptance)
--speculative-config '{"method":"dflash","model":"/data/models/Qwen3.5-27B-DFlash","num_speculative_tokens":5}'
```

**Results:** 16.9 tok/s (+156% vs n-gram baseline 6.6 tok/s), 34.3% acceptance rate, lossless quality.
See `qwen27b-dgx-deployment:references/vllm-dflash-deployment-may15-2026.md` for full details.

**Dynamic LoRA + DFlash optimization (May 16, 2026):**

When serving base model + dynamic LoRA with DFlash speculative decoding, the optimal
`num_speculative_tokens` is **5** (not 16). Testing with values 4, 5, 6, 8:

| num_tokens | Acceptance Rate | Per-Position Breakdown | Verdict |
|-----------|-----------------|------------------------|---------|
| 4 | 40-57% | pos1: 71-90%, pos2: 48-75%, pos3: 39-55%, pos4: 25-35% | Good but misses pos5 gains |
| **5** | **54-60%** | pos1: 71-90%, pos2: 48-75%, pos3: 39-55%, pos4: 25-35%, pos5: 14-30% | **Optimal — best throughput** |
| 6 | 54-60% | Same as 5, pos6: 0% always | No benefit over 5 |
| 8 | 54-60% | Same as 5, pos6-8: 0% always | Wastes verification cycles |

**Key finding:** Position 6+ always has 0% acceptance because the draft model diverges
after ~5 tokens. Adding more speculative tokens wastes GPU verification cycles without
improving throughput.

**Per-position acceptance pattern (after warm-up):**
- pos1: 71-90% (nearly always accepted)
- pos2: 48-75% (good alignment)
- pos3: 39-55% (moderate alignment)
- pos4: 25-35% (declining)
- pos5: 14-30% (marginal but still positive contribution)
- pos6+: 0% (never accepted — draft diverges)

**Command to test acceptance rates:**
```bash
docker logs vllm-base-lora 2>&1 | grep -E "SpecDecoding|speculative"
```

**vLLM launch with dynamic LoRA + DFlash (verified May 16, 2026):**
```bash
docker run -d --name vllm-base-lora \
  --runtime nvidia --gpus all -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints:/data/SpecForge/custom_dflash/checkpoints \
  -e CUDA_VISIBLE_DEVICES=0 \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --max-model-len 131072 \
  --enable-lora \
  --max-lora-rank 256 \
  --lora-modules custom-model=/data/SpecForge/custom_dflash/checkpoints/final_model \
  --speculative-config '{"method": "dflash", "model": "/data/models/Qwen3.5-27B-DFlash", "num_speculative_tokens": 5}' \
  --max-num-batched-tokens 32768 \
  --max-num-seqs 256 \
  --gpu-memory-utilization 0.95 \
  --dtype bfloat16 \
  --trust-remote-code \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

**CRITICAL: `--enable-auto-tool-choice` and `--tool-call-parser` are REQUIRED for Hermes integration.**

Without these flags, Hermes will fail with:
```
HTTP 400: "auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set
```

This error is non-retryable and will abort the agent session immediately.

**Tuned `num_speculative_tokens` (May 15, 2026):**

| num_tokens | Throughput | Acceptance Rate | Verdict |
|------------|-----------|-----------------|---------|
| **5** | **16.9 tok/s** | **34.3%** | **Optimal — best throughput/acceptance balance** |
| 16 | 16.7 tok/s | 11.9% | Higher throughput but poor acceptance |
| 12 | 15.2 tok/s | 13.8% | Lower throughput despite higher acceptance |
| 20 | 15.2 tok/s | 8.0% | Worse than 16 |
| 24 | 14.6 tok/s | 6.8% | Too many rejected tokens |

Why 5 is optimal: Lower `num_speculative_tokens` dramatically improves acceptance rate (34% vs 12%) because the draft model aligns well for only ~2-3 tokens on average before divergence. While 16 draft tokens verifies more in parallel, the cascading rejections beyond position 3 waste verification cycles. With 5 tokens, most drafts are fully accepted, giving better effective throughput. This was verified with real agent prompts (not synthetic benchmarks).

**Context length trade-offs (May 15, 2026):**

| max_model_len | Throughput | Acceptance | GPU Memory | Concurrency | Use Case |
|---------------|-----------|------------|------------|-------------|----------|
| 131072 | **16.9 tok/s** | **34.3%** | ~85GB | 6.9x | **Default — best throughput** |
| 262144 | **8.5 tok/s** | **37.1%** | ~96GB | 3.8x | Long context — 50% speed penalty |

Doubling context from 131K → 262K reduces throughput by ~50% because KV cache memory is allocated for the full context window, leaving less memory for batching. Use 131K for default agent workloads; switch to 262K only when explicitly needed.

**vLLM 0.20.2 `speculative-config` format (dict, NOT old CLI flags):**
```bash
# CORRECT (vLLM 0.20.2+):
--speculative-config '{"method":"ngram","num_speculative_tokens":5}'
--speculative-config '{"method":"dflash","model":"/path/to/draft","num_speculative_tokens":16}'

# INCORRECT (old format, removed in 0.20.x):
--speculative-model [ngram] --num-speculative-tokens 5
```

**EAGLE-3 speculative decoding is NOT viable for Qwen3.6-27B (May 15, 2026):**

Three independent blockers prevent EAGLE-3 from working:

1. **Missing architecture support:** vLLM 0.20.2 supports `Eagle3LlamaForCausalLM`, `Eagle3Qwen3vlForCausalLM`, etc. but **NOT** `Eagle3Qwen3ForCausalLM`. The existing `eagle3-qwen3-draft` model uses this unsupported architecture.

2. **Config validation failure:** Qwen3.6-27B uses non-standard attention dimensions (hidden_size=5120, num_heads=24, head_dim=256, but 5120 ≠ 24×256). vLLM's Llama config validator rejects this for `LlamaForCausalLMEagle3` drafts. The specdrift community draft (`Dogacel/specdrift-qwen3.6-27b-eagle3`) has correct weight shapes but fails validation.

3. **Weight name mismatch:** Faking the architecture as `Eagle3Qwen3vlForCausalLM` loads `llama_eagle3.py` which expects Llama-style weight names (`qkv_proj`, `gate_up_proj`), but Qwen3-style drafts use separate projections (`q_proj`, `k_proj`, `v_proj`, `gate_proj`, `up_proj`). Results in `KeyError: 'hidden_norm.weight'`.

**To make EAGLE-3 work you'd need:**
- Train a custom EAGLE-3 draft using the speculators library with vLLM's hidden state generator
- OR patch vLLM to add `Eagle3Qwen3ForCausalLM` support (requires model class + config handling)
- OR convert draft weights to Llama-compatible format (non-trivial, changes model behavior)

**Current status:** DFlash is the only working speculative decoding method for Qwen3.6-27B. See `references/eagle3-qwen36-investigation-may15-2026.md` for full investigation details.

**Note:** n-gram is less effective on highly creative/diverse text (acceptance drops
to 20-40%). Best for repetitive patterns, code, structured output. DFlash or EAGLE-3
still recommended for maximum speedup when available.

**Historical note (pre-0.20.2):** ngram/suffix speculative decoding WAS broken on
Qwen3.6 GDN hybrid (vLLM #39273), producing silently corrupted output. Fixed in 0.20.2.
   323|   323|
   324|   324|See gotchas #71-72, #89 for full details.
   325|   325|
   326|   326|### 3.3 PrismQuant Mixed-Precision Quantization (NEW)
   327|   327|
   328|   328|Measurement-driven mixed-precision quantizer specifically tested on Qwen3.6-35B-A3B.
   329|   329|Achieves **22GB disk size at 4.75bpp with only -0.56pp quality loss** vs BF16
   330|   330|(uniform NVFP4 loses -2.21pp at 24GB).
   331|   331|
   332|   332|**Key advantages:**
   333|   333|- Zero custom infrastructure — standard `compressed-tensors` checkpoint
   334|   334|- MTP/speculative decoding heads already quantized — `--speculative-config method=mtp` works OOTB
   335|   335|- Direct HF download, standard vLLM serve
   336|   336|
   337|   337|**Pre-built:** `rdtand/Qwen3.6-35B-A3B-PrismQuant-4.75bit-vllm`
   338|   338|**GitHub:** `RobTand/PrismQuant`
   339|   339|
   340|   340|Use when you need concurrent models or larger KV cache headroom on the 128GB Spark.
   341|   341|
   342|   342|### 3.4 FlashKDA on Blackwell (SM121a) — RESEARCH STATUS
   343|   343|
   344|   344|**FlashKDA** (Moonshot's CUDA kernel for Kimi Delta Attention) compiles and runs
   345|   345|on GB10/Blackwell **ONLY with `sm_121a` gencode** — the 'a' suffix enables CUTLASS
   346|   346|TMA (`CUTE_ARCH_TMA_SM90_ENABLED`) which is required for the kernel.
   347|   347|
   348|   348|**Build flags for setup.py:**
   349|   349|```python
   350|   350|arch_flags.extend(["-gencode", "arch=compute_121a,code=sm_121a"])
   351|   351|```
   352|   352|
   353|   353|**Numerical validation on SM121a (bfloat16):**
   354|   354|- avg_rtol: 1.85e-08
   355|   355|- max_rtol: 2.37e-06
   356|   356|- avg_atol: 3.54e-08
   357|   357|- max_atol: 0.125 (acceptable for bfloat16 attention)
   358|   358|
   359|   359|**CRITICAL: FlashKDA is NOT compatible with Qwen3.6's GDN architecture.**
   360|   360|The gating formulations are fundamentally different:
   361|   361|
   362|   362|| Property | FlashKDA (Kimi Delta Attention) | Qwen3.6 GDN (FLA/vLLM) |
   363|   363||---|---|---|
   364|   364|| g shape | `[B,T,H,K]` (per-dim) | `[B,T,H]` (per-head) |
   365|   365|| g activation | `lower_bound * sigmoid(exp(A_log)·(g + dt_bias))` | `-exp(A_log)·softplus(a + dt_bias)` |
   366|   366|| decay base | `2^g` (exp2) | `e^g` (exp) |
   367|   367|| beta | pre-sigmoid (kernel applies) | post-sigmoid (already activated) |
   368|   368|
   369|   369|**Consequences:**
   370|   370|- No drop-in kernel swap possible without changing model behavior
   371|   371|- vLLM's vendored FLA ops and pip `flash-linear-attention` (0.4.2) have **no FlashKDA integration**
   372|   372|- PR #852 ("Add flash-kda support for gated delta rule prefill") is **not in public repos**
   373|   373|
   374|   374|**Practical path forward:**
   375|   375|- FlashKDA is a **strategic asset for future training runs** — train a Delta Attention
   376|   376|  model from scratch with FlashKDA-native gating, then serve with the optimized kernel
   377|   377|- For Qwen3.6 serving today, use DFlash (Section 3.2) which gives ~1.3x speedup safely
   378|   378|
   379|   379|**What does NOT work:**
   380|   380|- `sm_121` (non-a): TMA assertion failure (`CUTE_ARCH_TMA_SM90_ENABLED` undefined)
   381|   381|- `sm_120a`: `no kernel image available` — SM121 cannot run SM120a binaries
   382|   382|
   383|   383|### 3.5 LongSpec / OWL Speculative Decoding (for 150K+ Context)
   384|   384|
   385|   385|For sustained high-context agentic workflows, LSTM-based speculative drafters
   386|   386|outperform MTP/Eagle-3. Offload the drafter to the Grace CPU via
   387|   387|`--speculative-draft-device cpu`, reserving GPU VRAM for massive KV cache.
   388|   388|
   389|   389|**Off-the-shelf:** `sail/longspec-QwQ-32B-Preview`
   390|   390|**Custom training:** `longspec/train/train_drafter.py --drafter_arch lstm`
   391|   391|**Base model:** `cyankiwi/Qwen3.5-35B-A3B-AWQ-4bit` (1M context, Marlin kernels)
   392|   392|**SGLang launch:** `--speculative-algo HOWL --speculative-draft-device cpu`
   393|   393|
   394|   394|See `references/apr21-optimization-and-abliteration-update.md` for full config.
   395|   395|
   396|   396|### 3.6 MTP Speculative Decoding (CURRENTLY DISABLED)
   397|   397|
   398|   398|**IMPORTANT:** MTP is currently DISABLED due to vLLM bug #38182/#39680.
   399|   399|MTP reduces Qwen3.6 generation throughput by 62.5% despite 96.6% acceptance
   400|   400|rate. Root cause: KV cache manager force-drops last matched block, collapsing
   401|   401|prefix cache hit rate from 92% to 71%. See gotcha #65.
   402|   402|
   403|   403|**When vLLM merges the fix, the MTP sweet spot is:**
   404|   404|MTP-2: 58.6 avg / 63.0 peak
   405|   405|MTP-3: 63.9 avg / 67.8 peak (BEST)
   406|   406|MTP-4: 52.9 avg (acceptance collapses, DON'T USE)
   407|   407|
   408|   408|3 lines commented out in spark-maxperf.sh. Re-enable when #38182 is resolved.
   409|   409|
   410|   410|## Phase 4: Fine-Tuning Pipeline
   411|   411|
   412|   412|### 4.0 Abliteration (Remove Refusals Before Training)
   413|   413|
   414|   414|**CRITICAL:** Don't download pre-uncensored GGUF models (HauhauCS etc). They're
   415|   415|247GB of lossy quantized weights that degrade LoRA/GRPO training quality. Instead,
   416|   416|run norm-preserving biprojected abliteration on the base BF16 model directly on Spark.
   417|   417|
   418|   418|```bash
   419|   419|bash ~/dgx-spark-prep/abliterate-qwen3.sh                    # Full abliteration
   420|   420|bash ~/dgx-spark-prep/abliterate-qwen3.sh --alpha 0.8        # Gentler
   421|   421|bash ~/dgx-spark-prep/abliterate-qwen3.sh --measure-only     # Just measure refusal dirs
   422|   422|```
   423|   423|
   424|   424|**Quick Drop-In Alternative (No GPU Compute Needed):**
   425|   425|If you want an uncensored model immediately without running abliteration:
   426|   426|- `huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated` — BF16 safetensors, vLLM-compatible, direct `--model` replacement.
   427|   427|- `HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive` — GGUF only, 0/465 refusal rate.
   428|   428|- `Youssofal/Qwen3.6-35B-A3B-Abliterated-Heretic-GGUF` — GGUF.
   429|   429|
   430|   430|**Verify Abliteration Status:**
   431|   431|```bash
   432|   432|# Check if abliterated output directory exists
   433|   433|ls -d /data/models/*abliterat* 2>/dev/null || echo "No local abliterated checkpoint"
   434|   434|
   435|   435|# Check model file modification times
   436|   436|stat -c "%y %n" /data/models/Qwen3.6-35B-A3B/*.safetensors | head -5
   437|   437|# If ALL timestamps match original download date → STOCK (not abliterated)
   438|   438|# If config.json or .safetensors files were modified after download → abliteration applied
   439|   439|```
   440|   440|
   441|   441|- ~15 min GPU compute, 0 extra downloads
   442|   442|- Produces TRUE BF16 safetensors (no quantization artifacts)
   443|   443|- Tunable alpha (1.0 = full uncensored, 0.5 = gentle)
   444|   444|- Can re-run after each training round to re-abliterate merged models
   445|   445|- Output: /data/models/Qwen3.6-35B-A3B-Uncensored
   446|   446|- Automatically runs as Phase 0 in dual-training-orchestrator.sh
   447|   447|- Based on: huggingface.co/blog/grimjim/norm-preserving-biprojected-abliteration
   448|   448|- Uses: github.com/jim-plus/llm-abliteration
   449|   449|
### 4.1 LoRA Config

lora_rank: 256, lora_alpha: 512, lora_dropout: 0.05
target_modules: q_proj, v_proj, k_proj, o_proj, gate_proj, up_proj, down_proj
gradient_checkpointing: true (MANDATORY on unified memory, use_reentrant=False)
gradient_accumulation_steps: 16, per_device_train_batch_size: 1
learning_rate: 2e-4, bf16: true

**Note:** r=256 fits on GB10 with gradient checkpointing enabled. GPU memory: ~62GB during training (model 54GB + LoRA 5GB + activations/gradients/optimizer ~3GB). The earlier r=256 "failure" was due to CPU-only PyTorch in train-venv, not actual OOM. Always use system Python (`/usr/bin/python3`) for training.
   457|   457|
### 4.2 Training Data Sources

**Internal data:** Cortex tips (elo > 1800), Cortex experiences (confidence > 0.7),
UWorld explanations (2,958 cards), First Aid notes, NBME data.

**Downloaded datasets** (~340GB total at ~/dgx-spark-prep/training-data/):

REASONING (80GB+) — rank 64-128 for LoRA:
- bespokelabs/Bespoke-Stratos-17k (120MB, 17K DeepSeek-R1 traces)
- open-r1/OpenR1-Math-220k (12GB, 220K math CoT)
- open-thoughts/OpenThoughts2-1M (7.7GB, 1M math/science/code/puzzles)
- AI-MO/NuminaMath-CoT (1.1GB, 73K competition math)
- NovaSky-AI/Sky-T1_data_17k (256MB, 17K reasoning distillation)
- **[R3] tasksource/PRM800K (3GB, 280K STEP-LEVEL human labels — teaches SOUND reasoning)**
- **[R3] nvidia/OpenMathInstruct-2 (30GB, 14M code-interleaved math solutions)**
- **[R3] a-m-team/AM-DeepSeek-R1-Distilled-1.4M (8GB, 1.4M R1 long CoT traces)**
- **[R3] open-thoughts/OpenThoughts3-1.2M (15GB, 850K math + 250K code + 100K science)**
- **[R3] lukaemon/bbh (10MB, 5.75K hard reasoning tasks)**
- **[R3] lordspline/arc-agi (500MB, abstract pattern reasoning)**
- **[R3] nvidia/Nemotron-Post-Training-Dataset-v1 (50GB, 25M multi-domain SFT+RL)**
- **[R3] TIGER-Lab/WebInstructFull (5GB, web-derived instruction data)**

TOOL CALLING (3.1GB):
- Yhyu13/ToolBench_toolllama_G123_dfs (1.9GB, 188K multi-turn tool use)
- glaiveai/glaive-function-calling-v2 (259MB, ~100K FC pairs)
- tryumanshow/ToolACE-Qwen-cleaned (7.9MB, **Qwen-native FC format**)
- Team-ACE/ToolACE (35MB, 26K diverse APIs)
- gorilla-llm/berkeley-function-calling-leaderboard (11MB, eval only)
- DeepNLP/Agent-Function-Calling-Open-Dataset (38MB, live agent traces)

MEDICAL (17GB+):
- casey-martin/MedInstruct (large medical instruction)
- UCSC-VLAA/MedReason (large faithful medical reasoning)
- OpenMed-Mega/Qwen3/Trinity-Mini (aggregate medical datasets)
- BioInstructQA (biomedical instruction QA)
- **[R3] FreedomIntelligence/medical-o1-reasoning-SFT (2GB, 50K GPT-4o verified medical CoT)**
- **[R3] UCSC-VLAA/MedReason (3GB, faithful explainable medical reasoning)**
- **[R3] mamachang/medical-reasoning (1GB, real clinical vignettes with reasoning)**

CODE (17GB+):
- deepmind/code_contests (7.1GB, 13K competitive programming)
- BAAI/TACO (6.7GB, 26K algorithmic problems)
- **[R3] ise-uiuc/Magicoder-OSS-Instruct-75K (500MB, open-source code instructions)**

## Phase 5: Post-Training Evaluation (lm-eval-harness on GB10)

### 5.0 Verified Benchmark Results (May 2026, Qwen 27B BF16)

| Benchmark | Score | Runtime | Task Type | Reliability |
|-----------|-------|---------|-----------|-------------|
| MMLU | 86.57% | ~4h 43m | loglikelihood | ✅ Reliable |
| GSM8K | 66.19% | ~12h | generate_until | ⚠️ Needs max_new_tokens patch |
| HumanEval | 82.93% pass@1 | ~44m | generate_until | ⚠️ Needs HF_ALLOW_CODE_EVAL=1 + --confirm_run_unsafe_code |
| BBH | TBD | ~50-80h | generate_until | ⚠️ Very long, monitor for silent death |
| ARC | TBD | TBD | loglikelihood | ✅ Reliable |
| WinoGrande | TBD | TBD | loglikelihood | ✅ Reliable |

### 5.1 CRITICAL: generation_config.json Overrides ALL Token Limits

After patching task YAML and using `--gen_kwargs`, GSM8K still used `max_new_tokens=32768`. The root cause was the model's `generation_config.json`:

```bash
cat /path/to/merged/generation_config.json
# {"max_new_tokens": 32768, ...}
```

**Hierarchy of max_new_tokens resolution (strongest to weakest):**
1. **Model `generation_config.json`** — loaded by transformers, overrides everything
2. **Task YAML `generation_kwargs`** — only effective if model config doesn't specify
3. **CLI `--gen_kwargs`** — overridden by both above

**Fix:** Patch `generation_config.json` directly:
```bash
cat > /path/to/merged/generation_config.json << 'EOF'
{
  "bos_token_id": <your_bos>,
  "do_sample": true,
  "eos_token_id": [<your_eos>],
  "max_new_tokens": 512,
  "pad_token_id": <your_pad>,
  "temperature": 1.0,
  "top_p": 1.0
}
EOF
```

After patching, verify in logs:
```
gsm8k: Using gen_kwargs: {'until': ['Question:', '</s>', '<|im_end|>'], 'do_sample': False, 'temperature': 0.0, 'max_new_tokens': 512}
[transformers] Both `max_new_tokens` (=512) and `max_length`... `max_new_tokens` will take precedence.
```

**Impact:** Without this fix, generate_until tasks on GB10 are 60x slower (30s/it with 32K tokens vs ~0.5s/it with 512 tokens) and much more likely to OOM or die silently.

**Note:** Even with generation_config.json patched, lm-eval-harness may still show warnings:
```
[transformers] Both `max_new_tokens` (=512) and `max_length`(=1093) seem to have been set. `max_new_tokens` will take precedence.
```
This is NORMAL and SAFE. The `max_length` comes from the task YAML (prompt length + max_new_tokens), and `max_new_tokens` from generation_config.json takes precedence. The warning is informational, not an error.

### 5.2 HumanEval Requirements

HumanEval is marked as UNSAFE in lm-eval-harness. Two requirements:

1. **Environment variable:** `export HF_ALLOW_CODE_EVAL=1`
2. **CLI flag:** `--confirm_run_unsafe_code`

Without BOTH, the task fails immediately after model load with:
```
ValueError: Attempted to run task: humaneval which is marked as unsafe. Set confirm_run_unsafe_code=True to run this task.
```

### 5.3 BBH Performance Reality

BBH is a generate_until task with 6511 examples. At ~30-45s per example on GB10:
- **Estimated runtime: 50-80 hours**
- This is NORMAL for a 27B model on single GB10
- Do NOT kill prematurely — progress counter is trustworthy

### 5.4 SSH Background Process Spawning (Hermes Terminal Tool)

**Hermes terminal tool FAILS with `&`, `nohup`, `setsid`, or `disown` in foreground SSH.**

Errors encountered:
- `Foreground command uses shell-level background wrappers`
- `necho` parsing bug (corrupted output)
- Process starts but terminal hangs waiting for it

**Reliable pattern:** Write script on remote host, then run via single ssh command that captures PID:

```bash
# Step 1: Write script on remote host via SSH printf
cat > /tmp/start_benchmark.sh <> 'EOF'
#!/bin/bash
cd /data/SpecForge/custom_dflash
source eval_venv/bin/activate
export HF_ALLOW_CODE_EVAL=1
lm_eval --model hf --model_args pretrained=/data/SpecForge/custom_dflash/checkpoints/final_model_merged,dtype=bfloat16 --tasks humaneval --batch_size 1 --output_path /data/SpecForge/custom_dflash/evaluation_results/humaneval --device cuda --confirm_run_unsafe_code > /tmp/lm_eval_humaneval.log 2>&1 &
echo $!
EOF

# Step 2: Run script and capture PID
ssh djg6228@10.0.0.171 "bash /tmp/start_benchmark.sh > /tmp/humaneval.pid; cat /tmp/humaneval.pid"
# Returns: 1115296

# Step 3: Verify in follow-up
ssh djg6228@10.0.0.171 "ps aux | grep 1115296 | grep -v grep"
```

**Key points:**
- The `&` is INSIDE the script, not in the SSH command
- The script writes PID to a file for later checking
- `terminal(background=true)` is NOT needed if the remote process backgrounds itself
- The SSH command returns immediately (just echoes PID), so Hermes doesn't wait

### 6.5 Node.js Installation for Browser Tools (aarch64 DGX)

Browser tools require the `agent-browser` CLI (npm package). DGX Spark is aarch64 and Node.js is not pre-installed.

**Install Node.js binary (no sudo needed):**
```bash
cd /tmp
curl -fsSL https://nodejs.org/dist/v20.12.2/node-v20.12.2-linux-arm64.tar.xz -o node.tar.xz
tar -xf node.tar.xz
mv node-v20.12.2-linux-arm64 ~/node

# Verify
~/node/bin/node --version  # v20.12.2
~/node/bin/npm --version   # 10.5.0

# Install agent-browser
export PATH=$HOME/node/bin:$PATH
npm install -g agent-browser
agent-browser --version  # 0.27.0

# Add to PATH permanently
echo 'export PATH=/home/djg6228/node/bin:$PATH' >> ~/.bashrc
```

**Update systemd service:**
```ini
Environment=PATH=/home/djg6228/node/bin:/data/SpecForge/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin
```

**Verify browser tools:**
```bash
cd /data/SpecForge/hermes-agent
venv/bin/python -c "
from tools.browser_tool import check_browser_requirements
print(f'Browser requirements: {check_browser_requirements()}')
"
# Should show: True
```

**Pitfall:** The x86-64 Node.js binary will fail with "cannot execute binary file" on aarch64. Always use the `-linux-arm64` tarball. Verify with `file ~/node/bin/node` → should show `ARM aarch64`.

When MacBook disk is full (~100% capacity):
- Hermes terminal tool FAILS with `No space left on device`
- Cannot write temporary scripts to `/tmp/` or `/var/folders/`
- Cannot use `write_file` tool (writes to local disk first)

**Workaround:** Write scripts directly on remote host via SSH:
```bash
# Instead of: write_file(path="/tmp/script.sh") → fails
# Use: ssh host "cat > /tmp/script.sh << 'EOF'...EOF"
ssh djg6228@10.0.0.171 "printf '%s\n' '#!/bin/bash' 'cd /data/...' 'command' > /tmp/script.sh"
```

**Long-term fix:** Move large directories (`~/datasets`, `~/Downloads`) to external SSD.

### 5.6 NTFS/exFAT Cross-Platform SSD Workflow

**DGX (Ubuntu) ↔ MacBook SSD transfer workflow:**

| Format | DGX (Ubuntu) | MacBook | Recommendation |
|--------|-------------|---------|----------------|
| NTFS | ✅ Native read/write | ❌ Read-only (no native write) | Use for DGX-only storage |
| exFAT | ✅ Native read/write | ✅ Native read/write | **Best for cross-platform** |
| APFS | ❌ Not supported | ✅ Native | Mac-only |

**If SSD is NTFS and you need Mac write access:**
- `ntfs-3g` requires Linux (won't install on macOS via Homebrew)
- macOS experimental NTFS write (`mount -t ntfs -o rw`) is removed in recent versions
- Third-party tools (Mounty, macFUSE) may work but require kernel extensions and user approval

**Recommendation:** Reformat SSD to exFAT for seamless Mac ↔ DGX transfers. For DGX-only storage, NTFS is fine.

### 5.7 BBH Speed Degradation and Prioritization

BBH speed degrades over time — started at ~24s/it, dropped to 76s/it after 3h.
At degraded speed, BBH becomes impractical (5+ days). Run BBH LAST or skip.

**Verified May 2026 full benchmark results (Qwen 27B BF16 on GB10):**

| Benchmark | Score | Runtime | Task Type | Reliability |
|-----------|-------|---------|-----------|-------------|
| MMLU | 86.57% | ~4h 43m | loglikelihood | ✅ Reliable |
| GSM8K | 66.19% | ~12h | generate_until | ✅ With max_new_tokens=512 patch |
| HumanEval | 82.93% pass@1 | ~44m | generate_until | ✅ With HF_ALLOW_CODE_EVAL=1 + --confirm_run_unsafe_code |
| ARC Challenge | 60.24% | ~25m | loglikelihood | ✅ Reliable |
| WinoGrande | TBD | TBD | loglikelihood | ✅ Reliable |
| BBH | ⏸️ Skipped | ~50-80h | generate_until | ⚠️ Very long, monitor for silent death |

**Recommended evaluation order:**
1. MMLU (fast, reliable baseline)
2. ARC Challenge (fast, reliable)
3. WinoGrande (fast, reliable)
4. HumanEval (medium, needs safety flags)
5. GSM8K (long, needs generation_config.json patch)
6. BBH (very long, run last or skip)

See `references/post-training-evaluation-may2026-verified.md` for full prioritization strategy.

### 5.8 Silent Death on generate_until Tasks

**Loglikelihood tasks (MMLU, ARC, WinoGrande) complete reliably.**
**generate_until tasks (GSM8K, HumanEval, BBH) can SILENTLY DIE.**

Observed on Qwen 27B BF16 (51GB) GSM8K:
- Process reached 75% (984/1319) after ~10.5 hours
- Process vanished without error message, crash dump, or exception
- No partial results saved
- GPU went idle (0% utilization, 37°C)
- Likely cause: OOM or driver timeout on long-running generate_until tasks

**Mitigation:**
1. Run benchmarks individually (not chained)
2. Use direct Python evaluation for generate_until tasks
3. Monitor GPU temperature and utilization — sudden drop to 0% is death signal
4. Check for zombie processes before restarting: `ps aux | grep lm_eval | grep -v grep`

### 5.9 Concurrent Process Hazard

When restarting after silent death, ALWAYS verify no old processes are still running:

```bash
ps aux | grep -E 'lm_eval|python3.*benchmark' | grep -v grep
# If old process found, kill it
kill -9 <OLD_PID>
sleep 5
ps aux | grep -E 'lm_eval|python3.*benchmark' | grep -v grep || echo "Clean"
```

**Failure mode:** Old lm_eval process was zombie/defunct but still held GPU context.
New process started, both tried to load model simultaneously. System load spiked to 44+.
GPU context conflicts, extreme slowdown, potential hangs.

**Rule:** One benchmark at a time on GB10. No concurrent model loads.

### 5.10 Post-Training Dataset Management

After training completes, datasets are for archive only. Do NOT retrain on same data.
Move to external SSD (exFAT) and free local disk. See reference file for full strategy.

## Phase 7: LoRA Training on GB10 (Direct PEFT — Axolotl Incompatible)

### 7.0 Axolotl on GB10 — SEPARATE VENV REQUIRED

**UPDATE (May 2026):** Axolotl 0.16.1 CAN run on GB10, but requires a **separate virtual environment** with torch 2.8.0 (CPU-only axolotl dependency) plus CUDA torch installed afterward. The key is isolation — axolotl's torch 2.8.0 requirement conflicts with Hermes/eval_venv's torch 2.11.0+cu130.

**CRITICAL: Even with correct axolotl setup, the `train-venv` at `/home/djg6228/train-venv` has CPU-only PyTorch.** Always verify before training:
```bash
/usr/bin/python3 -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
# Should show: 2.11.0+cu130 and True
# If False, training will "deadlock" (actually fail CUDA initialization)
```

**Working pattern:**
```bash
# Create isolated training venv
python3 -m venv ~/train-venv
source ~/train-venv/bin/activate

# Install axolotl (pulls torch 2.8.0 CPU-only)
pip install axolotl

# OVERWRITE with CUDA torch (axolotl works with this)
pip uninstall -y torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# Fix axolotl bugs
touch ~/train-venv/lib/python3.12/site-packages/axolotl/telemetry/whitelist.yaml
echo 'organizations: []' > ~/train-venv/lib/python3.12/site-packages/axolotl/telemetry/whitelist.yaml
```

**Axolotl config pitfalls (May 2026):**
- `max_packed_sequence_len: 4096` → **DEPRECATED** — remove entirely, use `sample_packing: true` only
- Dataset format `type: input_output` with `{"input": "...", "output": "..."}` → **BROKEN in 0.16.1** — use `type: chat_template` with `{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`
- Missing `whitelist.yaml` → `FileNotFoundError` — create empty file with `organizations: []`
- `torch.cuda.get_device_capability()` called during config validation → needs CUDA torch installed

**Full details, conversion scripts, and error signatures:** `references/axolotl-gb10-training-may2026.md`

**Training launch script:** `templates/axolotl_training_launch.sh`

Write a direct training script using `transformers.Trainer` + `peft.LoraConfig` instead of axolotl:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model
from datasets import Dataset
import json

# Load model (bf16, device_map="auto")
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, torch_dtype=torch.bfloat16, device_map="auto", trust_remote_code=True)

# Configure LoRA
lora_config = LoraConfig(r=256, lora_alpha=512, target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"], lora_dropout=0.05, bias="none", task_type="CAUSAL_LM")
model = get_peft_model(model, lora_config)

# Load datasets (JSONL with {"input": "...", "output": "..."})
# Format as: "### Input:\n{input}\n\n### Response:\n{output}"
# Tokenize with truncation, pad to max_length
# Use DataCollatorForLanguageModeling(mlm=False)
# Trainer with bf16=True, gradient_accumulation_steps=4, etc.
```

**Key config for Qwen 27B on GB10:**
- LoRA r=256, alpha=512 (matches Franken V8 config)
- Target all linear projections (q/k/v/o/gate/up/down)
- batch_size=1, grad_accum=4, lr=2e-4
- sequence_len=4096, num_epochs=2
- bf16=True, tf32=True

### 7.3 Dataset Consolidation for Training

Raw datasets must be converted to JSONL with `{"input": "...", "output": "..."}` format.

**Tier 1 (reasoning):** Usually already in correct format. 2.15M records, 29GB typical.

**Tier 2 (mixed):** May have `messages` arrays, `tool_calls`, or other structured formats. Parse and extract user/assistant turns into input/output pairs.

**Tier 3 (health/Synthea):** Structured medical records (patients, conditions, encounters, medications). NOT in conversational format. Requires custom templates:
- Patient summary: "Generate a clinical summary for patient X with conditions Y, medications Z"
- Condition Q&A: "What is [condition] and how should it be managed?"
- Encounter notes: "Write a clinical encounter note for [visit type] on [date]"

**Synthea processing is SLOW** — 575K patients × 56M conditions = massive dataset. Sample patients (e.g., 50K) and generate 1-3 examples per patient. Expect hours of processing time.

### 7.4 Training Launch Pattern

```bash
# Write script to DGX via SSH
ssh djg6228@10.0.0.171 "cat > /data/SpecForge/custom_dflash/train_lora.py << 'PYEOF'
# ... training script ...
PYEOF"

# Run in background (script backgrounds itself, captures PID)
ssh djg6228@10.0.0.171 "source /data/SpecForge/custom_dflash/eval_venv/bin/activate && cd /data/SpecForge/custom_dflash && nohup python3 train_lora.py > /tmp/train.log 2>&1 & echo $! > /tmp/train.pid && cat /tmp/train.pid"

# Check progress
ssh djg6228@10.0.0.171 "tail -20 /tmp/train.log"
ssh djg6228@10.0.0.171 "nvidia-smi | grep -E 'GPU|Processes' -A 10"
```

### 7.5 CRITICAL: `low_cpu_mem_usage=False` for LoRA on Large Models (May 2026)

**When loading models >20B params with `device_map="auto"` for LoRA training, ALWAYS set `low_cpu_mem_usage=False`.**

Without this flag, `accelerate` offloads some layers to the "meta" device (lazy loading). LoRA's `get_peft_model()` creates adapter weights on the meta device, but the backward pass fails:

```
RuntimeError: Function MmBackward0 returned an invalid gradient at index 1
- expected device meta but got cuda:0
```

**Root cause:** Meta-device parameters have no actual memory backing. When backward tries to compute gradients for LoRA adapters attached to meta-device base weights, the gradient tensor lands on CUDA while the parameter is on meta.

**Fix:**
```python
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",  # or "auto"
    low_cpu_mem_usage=False,  # CRITICAL: prevents meta-device offloading
    trust_remote_code=True
)
```

**Trade-off:** Loading takes ~2x longer (all parameters copied to CPU first, then GPU), but training works correctly. On GB10 with 128GB unified memory, this is acceptable.

**Verified on Qwen 27B BF16 (51GB):**
- With `low_cpu_mem_usage=False`: Model loads in ~5 min, LoRA applies, forward+backward+optimizer all work
- With `low_cpu_mem_usage=True` (default): Model loads in ~30 sec, LoRA applies, backward fails immediately

**Memory impact:**
- `low_cpu_mem_usage=True`: ~4GB GPU allocated (most params on meta device)
- `low_cpu_mem_usage=False`: ~54GB GPU allocated (all params on GPU)

This is the CORRECT behavior for training — you want all parameters on GPU anyway.

**Full error analysis and reproduction:** See `references/meta-device-gradient-error-may13-2026.md` in the `qwen27b-training-pipeline` skill.

### 7.6 Direct PEFT Training vs Axolotl (May 2026)

**Axolotl is INCOMPATIBLE with GB10 for production training.** Despite being installable in an isolated venv, axolotl has critical issues:

1. **Config parsing bugs:** `gpu_memory_limit: 110Gi` causes `ValueError: size 110Gi is not in a valid format`
2. **Preprocessing timeouts:** Single-threaded tokenization of 2.15M examples takes 2+ hours before training starts
3. **Deprecated fields:** `max_packed_sequence_len` removed in 0.16.1 but still in docs
4. **Dataset format confusion:** `input_output` type broken, `chat_template` type works but poorly documented

**Recommended: Direct PEFT + transformers.Trainer**

Advantages:
- Full control over model loading (can set `low_cpu_mem_usage=False`)
- No preprocessing bottleneck — tokenize on-the-fly or pre-tokenize
- No config YAML parsing bugs
- Easier to add custom callbacks (telemetry, monitoring)
- Works with verified stack (torch 2.11.0+cu128, transformers, peft, bitsandbytes)

**Verified working direct training script:** See `templates/direct_peft_training.py`

Key components:
```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model, TaskType

# Load with CRITICAL flag
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH, torch_dtype=torch.bfloat16, device_map="cuda:0",
    low_cpu_mem_usage=False, trust_remote_code=True)

# Apply LoRA
lora_config = LoraConfig(
    r=256, lora_alpha=512,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM)
model = get_peft_model(model, lora_config)

# 8-bit AdamW optimizer
import bitsandbytes as bnb
optimizer = bnb.optim.AdamW8bit([p for p in model.parameters() if p.requires_grad], lr=2e-4)

# Training arguments
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR, num_train_epochs=2,
    per_device_train_batch_size=1, gradient_accumulation_steps=4,
    learning_rate=2e-4, warmup_steps=100, logging_steps=10,
    save_steps=500, bf16=True, tf32=True, optim="adamw_torch")
```

**Pre-tokenization for speed:**
For datasets >1M examples, pre-tokenize to disk to avoid on-the-fly tokenization overhead:
```python
# Pre-tokenize script (run once)
for line in jsonl_file:
    data = json.loads(line)
    text = format_chat(data["messages"])
    enc = tokenizer(text, truncation=True, max_length=4096, padding="max_length")
    write_preprocessed(enc)

# Training loads pre-tokenized data directly
```

**Training health monitoring:**
- Telemetry server on port 8080 serves `/metrics`, `/status`, `/health`
- GPU monitor daemon checks utilization, temperature, stale metrics
- Both run as background processes alongside training

See `references/direct-peft-training-may2026.md` for full script, error signatures, and monitoring setup.

## Phase 6: Troubleshooting

### 6.1 SSH Timeout Under Training Load