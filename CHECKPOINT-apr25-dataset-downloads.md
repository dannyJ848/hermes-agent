# Qwen3.6 Hyper-Logician Dataset Download Checkpoint

**Date:** 2026-04-25T22:44:04.401593

## Mac Disk Status

- Total: 926GB
- Used: 781GB
- Available: 113GB
- Datasets: 202GB

## Downloaded Datasets

### TIER1
- [x] SYNTHETIC-2 (23GB)
- [x] DASD-Thinking (23GB)
- [x] ToolMind (3.7GB)
- [x] Reasoning-Core (3.1GB)
- [x] Hermes-Agent-Traces (1.5GB)
- [x] Qwen36-plus-trajectories (88MB)
- [x] ART-Abductive (8.8MB)
- [x] CounterBench (1.6MB)
- [x] CLadder (67MB)
- [x] MR-GSM8K (4.3MB)

### TIER2
- [x] AM-DeepSeek-R1-0528 (64GB)
- [x] Llama-Nemotron-PT (66GB)
- [x] AgentNet (12GB)
- [x] Mixture-of-Thoughts (5.7GB)
- [x] NuminaMath-LEAN (75MB)

## In Progress

- [ ] KodCode-V1 (tier2, ~20GB)
- [ ] Synthea (tier3, ~50GB)
- [ ] EHRSHOT (tier3, ~10GB)
- [ ] LeanDojo (tier4, ~5GB)
- [ ] DeepSeek-Prover (tier4, ~1GB)
- [ ] CausalProbe (tier4, ~2GB)
- [ ] METER (tier4, ~2GB)
- [ ] RAVEN (tier6, ~5GB)
- [ ] GTBench (tier6, ~2GB)

## Not Downloaded

### Repo Not Found
- [ ] SciAgentGym
- [ ] FoVer-PRM
- [ ] KodCode-AI/kodcode (fixed to KodCode/KodCode-V1)

### Insufficient Disk Space
- [ ] CLIMB (50GB)
- [ ] PK-DB (2GB)

## DGX Spark Training

- PID: 146221
- Step: ~4257/9999 (43%)
- Loss: ~5.0-7.0
- GPU: 96%, 71C
- vLLM: NOT RUNNING (GPU dedicated to training)

## Files Created

- ~/Desktop/QWEN36_HYPERLOGICIAN_PIPELINE.md
- ~/Desktop/stage1_cold_start_sft.py
- ~/Desktop/download_datasets.py
- ~/Desktop/sync_datasets_to_spark.sh

## Resume Instructions

1. Check active downloads: `ps aux | grep snapshot_download`
2. Check disk: `df -h /System/Volumes/Data`
3. Check DFlash: `ssh djg6228@10.0.0.171 'ps -p 146221'`
4. Missing datasets to research/download later: CLIMB, PK-DB, SciAgentGym, FoVer
