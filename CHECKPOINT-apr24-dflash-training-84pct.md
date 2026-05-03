# Checkpoint: apr24-dflash-training-84pct
# Saved: 2026-04-24 ~13:00
# Context: DGX Spark Qwen3.6-27B DFlash custom training pipeline

## Current State
- **Hidden state generation**: 8441/10000 samples (84.4% complete)
- **Process**: PID 39401 on DGX Spark (running since 10:31 AM)
- **Location**: /data/SpecForge/custom_dflash/hidden_states_full/*.pt
- **ETA**: ~3 hours to completion

## Auto-Actions Queued
1. When 10000 samples reached → auto-start Phase 2 training
2. Training script: /data/SpecForge/custom_dflash/phase2_train_draft.py
3. Output: /data/models/Qwen3.6-27B-DFlash-Custom/

## Key Files
- Phase 1: /data/SpecForge/custom_dflash/resume_phase1.py
- Phase 2: /data/SpecForge/custom_dflash/phase2_train_draft.py
- Convert: /data/SpecForge/custom_dflash/convert_dflash_v2.py
- vLLM serve: switch-model.sh (DFlash model path)

## DGX Spark Status
- vLLM: qwen3.6-27b-uncensored on port 8000 (eager mode)
- GPU: ~95% util, 262K context
- Caffeinate: running on Mac (PID 63411)

## Resume Instructions
1. Check status: `ls /data/SpecForge/custom_dflash/hidden_states_full/*.pt | wc -l`
2. If < 10000: process still running, wait
3. If == 10000: run phase2_train_draft.py
4. After training: convert + integrate into vLLM

## Context Dependencies
- sglang-venv at /data/sglang-venv
- Target model: /data/models/Qwen3.6-27B-Uncensored
- Datasets: UltraChat 10k samples (cached)
