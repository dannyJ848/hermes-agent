# Adaptive Cortex v2 + Research Checkpoint

**Date:** 2026-04-25 23:48
**Session compressions:** 6 (CRITICAL — must restart CLI)
**Merged contexts:** apr25-dataset-downloads + apr25-research-deep-dive

---

## CONTEXT FROM OTHER CLI (Dataset Downloads)

### Mac Disk Status
- Total: 926GB, Used: 781GB, Free: 113GB (88% full)
- Datasets downloaded: 202GB across 15 datasets

### Downloaded (Tier 1 Complete)
SYNTHETIC-2 (23GB), DASD-Thinking (23GB), ToolMind (3.7GB), Reasoning-Core (3.1GB), Hermes-Agent-Traces (1.5GB), Qwen36-plus-trajectories (88MB), ART-Abductive (8.8MB), CounterBench (1.6MB), CLadder (67MB), MR-GSM8K (4.3MB)

### Downloaded (Tier 2 Partial)
AM-DeepSeek-R1-0528 (64GB), Llama-Nemotron-PT (66GB), AgentNet (12GB), Mixture-of-Thoughts (5.7GB), NuminaMath-LEAN (75MB)

### In Progress (9 downloads)
KodCode-V1 (~20GB), Synthea (~50GB), EHRSHOT (~10GB), LeanDojo (~5GB), DeepSeek-Prover (~1GB), CausalProbe (~2GB), METER (~2GB), RAVEN (~5GB), GTBench (~2GB)

### Blocked
- CLIMB (50GB) — insufficient disk
- PK-DB (2GB) — insufficient disk
- SciAgentGym — repo not found
- FoVer-PRM — repo not found

### Files
- ~/Desktop/QWEN36_HYPERLOGICIAN_PIPELINE.md
- ~/Desktop/stage1_cold_start_sft.py
- ~/Desktop/download_datasets.py
- ~/Desktop/sync_datasets_to_spark.sh

---

## CONTEXT FROM THIS CLI (Research + Cortex v2)

### Adaptive Cortex v2 Built (6 Subsystems)
1. Classic Cortex — 66K tips, Elo-rated
2. Adaptive Cortex — 57 skills mined, real-time learning
3. Tool Oracle — predictive selection
4. Reasoning Analyzer — quality scoring
5. Sequence Learner — chain optimization
6. Anomaly Detector — risk prediction

### Files Created (~/subconscious/)
cortex_access.py, cortex_flywheel.py, adaptive_cortex.py, tool_oracle.py, reasoning_analyzer.py, sequence_learner.py, anomaly_detector.py, cortex_unified.py, cortex_dashboard_v2.py, cortex_compat.py, cortex_schema.sql, migrate_to_cortex.py, ADAPTIVE_CORTEX_DESIGN.md, RESEARCH_REPORT_Apr25.md

### Plugin Integration
Wired into ~/.hermes/plugins/distillation/__init__.py
- _on_pre_tool_call() → uc.before_tool()
- _on_post_tool_call() → uc.after_tool()
- _on_pre_llm_call() → uc.build_injection()

### Cron Jobs Active
- cortex-flywheel (every 2h)
- cortex-consolidation (every 6h)
- cortex-quality-sweep (daily 9am)
- adaptive-cortex-daemon (every 30m)
- research-monitor (daily 9am) — NEW

---

## DEEP RESEARCH FINDINGS (7 Optimizations)

### Phase 1 (Highest Priority)
1. **Structured Reflection Protocol** — 5-step cycle (ASSESS/DIAGNOSE/PLAN/EVALUATE/METRICS)
2. **Reliability Surface Tracking** — 3D metrics (consistency k, robustness ε, fault tolerance λ)
3. **Dynamic Tool Chain Planning** — predictive planning with backup chains

### Phase 2 (This Week)
4. **Hierarchical Memory Bifurcation** — Working → Episodic → Semantic layers
5. **Entropy-Based Exploration** — semantic diversity measurement, deadlock breaking

### Phase 3 (Next Week)
6. **Failure Injection Training** — deliberate edge case testing
7. **Global Workspace Broadcast** — event-driven cross-system coordination

### Key Papers
HyperAgents arXiv:2603.19461, GWA arXiv:2604.08206, PALADIN arXiv:2509.25238, Structured Reflection arXiv:2509.18847, ReliabilityBench arXiv:2601.06112, DHSA arXiv:2510.24606, MSA arXiv:2603.23516, Agent Memory Survey arXiv:2512.13564

---

## DGX SPARK STATUS (From Other CLI)

- DFlash training PID 146221, step ~4257/9999 (43%), loss ~5-7, GPU 96%
- vLLM NOT RUNNING (GPU dedicated to training)
- Disk: 37% full (2.2TB free) — safe after cleanup
- Cron monitor: dflash-training-monitor (aebabdb1c4c6) every 30 min

---

## RESUME INSTRUCTIONS

1. **Start new CLI session** (6 compressions — must restart)
2. **Load this checkpoint** for full context
3. **Check DFlash training:** `ssh djg6228@10.0.0.171 'ps -p 146221'`
4. **Check dataset downloads:** `ps aux | grep snapshot_download`
5. **Check disk:** `df -h /System/Volumes/Data`
6. **Begin Phase 1 implementations:** Structured Reflection + Reliability Surface + Tool Chain Planning

---

## CRITICAL REMINDERS

- Memory is at 48,985/50,000 chars — DO NOT add more memory entries
- Use session_search for past session recall instead of memory
- DGX Spark sudo password: 6228
- Hermes gateway restart: `hermes gateway restart` (not `hermes restart`)
- Danny's directive: "Build anything and everything" — unlimited tool building authorized
- Stop at 16 compressions (currently at 6, ~10 remaining)
