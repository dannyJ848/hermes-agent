# DGX Training Session State Snapshot (May 13, 2026)

## Purpose
Session state snapshot for resuming work across CLI sessions. Pre-tokenization status, verified stack, active PIDs, next steps.

## Current State

### Pre-tokenization (RUNNING)
- **PID:** 572146
- **Command:** `/home/djg6228/train-venv/bin/python /tmp/pre_tokenize.py`
- **Progress:** ~280k/2.15M tier1 examples (13% complete)
- **Rate:** ~5.5k examples/minute
- **Output:** `/data/SpecForge/custom_dflash/preprocessed/tier1_preprocessed.jsonl` (19GB)
- **ETA:** ~3 hours remaining

### Training Script (READY, NOT LAUNCHED)
- **Path:** `/data/SpecForge/custom_dflash/train_direct.py`
- **Type:** Direct PEFT + transformers.Trainer
- **Config:** LoRA r=256, alpha=512, lr=2e-4, 2 epochs, batch=1, grad_accum=4, seq_len=4096
- **Output:** `/data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/`

### Verified Working Stack
- **Model:** Qwen 27B BF16 at `/data/SpecForge/custom_dflash/checkpoints/final_model_merged`
- **GPU:** DGX Spark GB10 (130GB VRAM)
- **Critical fix:** `low_cpu_mem_usage=False` prevents meta-device gradient bugs
- **Verified:** Model loads (54GB), LoRA applies (1.275B trainable), forward+backward+8-bit AdamW all work
- **Attention:** SDPA (flash_attn not installed - CUDA 13.0 vs PT 12.8 mismatch)

### Active Services
- **Telemetry Server:** PID 575336, port 8080, endpoints: /health, /metrics, /status
- **GPU Monitor:** PID 579274, logs GPU util/memory/temp every 30s to /tmp/monitor2.out

### Benchmarks (COMPLETED)
- MMLU: 86.57% | GSM8K: 66.19% | HumanEval: 82.93%
- ARC: 60.24% | WinoGrande: 77.19% | BBH: skipped

### Failed Attempts
- **Axolotl:** Config parse error (`gpu_memory_limit: 110Gi` invalid format)
- **vLLM:** Vision artifacts in merged model config
- **flash_attn:** CUDA version mismatch (13.0 vs 12.8)

## Next Steps for New Session
1. Check pre-tokenization progress: `ssh djg6228@10.0.0.171 'ps -p 572146 && ls -lh /data/SpecForge/custom_dflash/preprocessed/'`
2. If complete, launch training: `cd /data/SpecForge/custom_dflash && ~/train-venv/bin/python train_direct.py`
3. Monitor: `curl http://10.0.0.171:8080/status`

## Key Paths
- Model: `/data/SpecForge/custom_dflash/checkpoints/final_model_merged`
- Datasets: `/data/SpecForge/custom_dflash/datasets/`
- Preprocessed: `/data/SpecForge/custom_dflash/preprocessed/`
- Output: `/data/SpecForge/custom_dflash/adapters/qwen27b-tiered-r256/`
- Training script: `/data/SpecForge/custom_dflash/train_direct.py`
- Session state: `/data/SpecForge/custom_dflash/SESSION_STATE.md`

## Files Created This Session
- `/data/SpecForge/custom_dflash/train_direct.py`
- `/data/SpecForge/custom_dflash/telemetry_server.py`
- `/data/SpecForge/custom_dflash/training_monitor.py`
- `/data/SpecForge/custom_dflash/SESSION_STATE.md`
- `/tmp/pre_tokenize.py`
- `/tmp/monitor2.py`
