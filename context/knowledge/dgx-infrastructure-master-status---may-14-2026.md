# DGX Infrastructure Master Status - May 14 2026

*Researched: 2026-05-14 21:39 CDT*

# DGX Infrastructure Master Status - May 14, 2026 18:30 UTC

## vLLM Inference Server
- **Status:** RUNNING
- **Container:** `vllm-merged` (docker)
- **Base model:** `/data/models/Qwen3.6-27B-Uncensored/`
- **LoRA adapter:** `/data/SpecForge/custom_dflash/checkpoints/final_model/` (r=256, alpha=512)
- **Endpoint:** http://localhost:8000/v1
- **Context:** 131,072 tokens
- **Tool calling:** ENABLED (`--enable-auto-tool-choice --tool-call-parser qwen3_xml`)
- **GPU memory:** ~55GB model + ~5GB LoRA + KV cache
- **Models served:**
  - `/data/models/Qwen3.6-27B-Uncensored` (base)
  - `merged-lora` (base + LoRA adapter)

## Hermes Agent (DGX)
- **Status:** CONFIGURED, 97 tools active
- **Config:** `~/.hermes/config.yaml`
- **Context length:** 131,072 (updated from 65,536)
- **Model:** `merged-lora` via custom provider
- **Endpoint:** http://localhost:8000/v1
- **Tools:** 97 (all browser, web_search, web_extract, web_research operational)
- **Node.js:** `/home/djg6228/node/bin/node` (for browser automation)
- **Plugins:** 35 enabled Evey plugins

## Training Pipeline
- **Status:** STOPPED (user requested inference mode)
- **Can resume:** `sudo systemctl start qwen-training`
- **Last config:** LoRA r=256, seq=1024, batch=1, grad_accum=4, all 3 tiers
- **Prior training:** 10k steps on FrankenV8-distilled Qwen 27B
- **Merged model:** `/data/SpecForge/custom_dflash/checkpoints/final_model_merged/`

## Distillation/Learning Pipeline
- **Status:** FIXED AND RUNNING
- **Daemon:** `dgx-learning.service`
- **Experiences:** 247 (all have lessons after backfill)
- **Distilled tips:** 59 (up from 7)
- **Export:** Hourly to `/data/SpecForge/custom_dflash/datasets/hermes_sessions/`
- **Key fix:** Extract lessons from ALL experiences (not just failures)

## File Sync
- **MacBook:** 1,756 core Python files
- **DGX:** 1,766 files (all synced + 2 DGX-specific)
- **10 new agent modules:** synced from MacBook (May 13)

## Critical Paths
- Hermes root: `/data/SpecForge/hermes-agent/`
- Config: `~/.hermes/config.yaml`
- Experience DB: `~/.hermes/cerebrum_memory.db`
- Distillation daemon: `/data/SpecForge/hermes-agent/scripts/dgx_distillation_daemon.py`
- vLLM base model: `/data/models/Qwen3.6-27B-Uncensored/`
- LoRA adapter: `/data/SpecForge/custom_dflash/checkpoints/final_model/`
- Node.js: `/home/djg6228/node/bin/node`

## Key Learnings (May 14)
1. **Tool calling parser:** `qwen3_xml` (not `qwen25`)
2. **Context length:** Must update BOTH vLLM (`--max-model-len`) AND Hermes config (`context_length`)
3. **PyTorch environment:** ALWAYS use system Python for training (train-venv has CPU-only torch)
4. **Distillation:** Must extract lessons from successes, not just failures
5. **SSH file transfer:** NEVER use heredocs — use base64 encoding
6. **Shell escaping:** Inline f-strings with newlines fail through SSH

## Commands
```bash
# Check vLLM status
docker ps | grep vllm
docker logs vllm-merged | tail -20

# Check Hermes tools
hermes tools | wc -l

# Check distillation daemon
systemctl status dgx-learning

# Resume training
sudo systemctl start qwen-training

# Restart vLLM with tool calling
docker stop vllm-merged && docker rm vllm-merged
docker run -d --name vllm-merged --runtime nvidia --gpus all -p 8000:8000 \
  -v /data/models:/data/models \
  -v /data/SpecForge/custom_dflash/checkpoints/final_model:/data/checkpoints/final_model \
  vllm/vllm-openai:latest \
  --model /data/models/Qwen3.6-27B-Uncensored \
  --enable-lora --lora-modules merged-lora=/data/checkpoints/final_model \
  --max-lora-rank 256 --max-model-len 131072 \
  --tensor-parallel-size 1 --gpu-memory-utilization 0.95 \
  --enable-auto-tool-choice --tool-call-parser qwen3_xml
```
