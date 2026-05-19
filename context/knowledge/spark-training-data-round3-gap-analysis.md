# spark-training-data-round3-gap-analysis

*Researched: 2026-04-17 21:23 CDT*

# DGX Spark Training Data Round 3 — Complete Gap Analysis

## What We Have (Rounds 1-2)
- **Reasoning**: NuminaMath-CoT (73K), OpenR1-Math-220k, Bespoke-Stratos-17k, OpenThoughts2-1M, Sky-T1 (47GB total)
- **Tool-Calling**: ToolACE, tool-calling-mix, BitAgent, When2Call, Agent-FLAN, glaive, xlam-60k (3.1GB)
- **Medical**: BioInstructQA, MedInstruct, MedReason, OpenMed-Mega/Qwen3/Trinity-Mini (17GB)
- **Code**: CodeAct, Code-Feedback, APPS, CodeContests (17GB)
- **Multimodal**: LLaVA-OneVision subset, etc. (39GB)
- **Exec-Verified**: rStar-Coder, Eurus2 (67GB)
- **Formal Proofs**: LeanDojo, Lean4-Mathlib, ProofNet (232MB)
- **Logic**: LogiQA/LogicNLI (919MB)
- **Agent Coding**: Claude Code distill (1.2MB)
- **Eval**: Benchmark data (142MB)
- **TOTAL**: ~193GB, ~7.93M examples

## Critical Gaps + New Datasets (Round 3)

### TIER 1: MUST HAVE (fills structural gaps)

| Dataset | HF Path | Size | What It Fills |
|---------|---------|------|---------------|
| **PRM800K** | tasksource/PRM800K | 3GB / 280K step labels | STEP-LEVEL supervision (not just answer-level) — teaches SOUND reasoning |
| **AM-R1-Distilled-1.4M** | a-m-team/AM-DeepSeek-R1-Distilled-1.4M | 8GB / 1.4M | DeepSeek-R1 long CoT traces across ALL domains |
| **OpenMathInstruct-2** | nvidia/OpenMathInstruct-2 | 30GB / 14M | Code-interleaved math solutions — Python + reasoning combined |
| **OpenCodeInterpreter-DS** | m-a-p/OpenCodeInterpreter-DS | 5GB / 364K | Write-run-debug cycles with REAL execution feedback |
| **SWE-rebench-OpenHands** | nebius/SWE-rebench-openhands-trajectories | 20GB / 67K | Real SWE agent trajectories from Qwen3-Coder |
| **Nemotron-Post-Training** | nvidia/Nemotron-Post-Training-Dataset-v1 | 50GB / 25M | NVIDIA's full SFT+RL stack — math/code/STEM/general |

### TIER 2: HIGH VALUE (fills volume gaps)

| Dataset | HF Path | Size | What It Fills |
|---------|---------|------|---------------|
| **OpenThoughts3-1.2M** | open-thoughts/OpenThoughts3-1.2M | 15GB / 1.2M | 850K math + 250K code + 100K science (structured) |
| **UltraInteract SFT** | openbmb/UltraInteract_sft | 4GB | Code execution feedback + preference pairs |
| **SWE-Gym** | SWE-Gym/SWE-Gym | 2GB / 2.4K | RL-able SWE environment (first of its kind) |
| **HuatuoGPT-o1** | FreedomIntelligence/medical-o1-reasoning-SFT | 2GB / 50K | GPT-4o verified MEDICAL REASONING chains |
| **MedReason** | UCSC-VLAA/MedReason | 3GB | Faithful medical reasoning (explainable) |

### TIER 3: NICE TO HAVE (fills edge cases)

| Dataset | HF Path | Size | What It Fills |
|---------|---------|------|---------------|
| **miniF2F** | wellecks/minif2f_isabelle | 50MB / 488 | Multi-proof-assistant (Lean+Isabelle+Coq) |
| **PutnamBench** | amitayusht/PutnamBench | 100MB / 640 | University-level competition with Lean 4 |
| **BBH** | lukaemon/bbh | 10MB / 5.75K | 23 hard reasoning tasks |
| **ARC-AGI** | lordspline/arc-agi | 500MB | Abstract reasoning (pattern induction) |
| **AgentTrek** | xlangai/AgentTrek | 1.8GB | Web agent trajectories |
| **Magicoder-OSS** | ise-uiuc/Magicoder-OSS-Instruct-75K | 500MB / 75K | Open-source code instructions |
| **WebInstruct** | TIGER-Lab/WebInstructFull | 5GB | General web instruction data |
| **Clinical Reasoning** | mamachang/medical-reasoning | 1GB | Real clinical vignettes |

## Why Each Gap Matters

### 1. PROCESS SUPERVISION (PRM800K + OpenMathInstruct-2)
Our current math data has correct ANSWERS but the REASONING PATHS may be unsound. Models can learn to pattern-match to the right answer with spurious logic. PRM800K has human-annotated step-level labels. OpenMathInstruct-2 has code-interleaved solutions where each step can be execution-verified. This is the #1 quality gap.

### 2. R1-STYLE LONG COT (AM-R1-Distilled-1.4M + OpenThoughts3-1.2M)
Our current reasoning data is mostly short-answer CoT. These have long, detailed thinking traces with reflection, backtracking, and self-verification — the STRUCTURE that matters more than content correctness. Structure > content (corrupting structure drops 12-14%, content only 3-4%).

### 3. WRITE-RUN-DEBUG CYCLES (OpenCodeInterpreter-DS + UltraInteract)
Our code data is mostly "here's a problem, here's a solution." Real coding involves writing code, running it, seeing errors, and fixing them. These are the ONLY datasets with actual execution feedback loops.

### 4. REAL AGENT TRAJECTORIES (OpenHands-SWE + SWE-Gym)
Our agent data is mostly single-turn tool calls. SWE-rebench has 67K multi-turn agent trajectories from Qwen3-Coder doing real SWE tasks. SWE-Gym is the first RL-able environment for SWE agents. This is the #1 gap for making Qwen3.6 a real agent.

### 5. MEDICAL REASONING (HuatuoGPT-o1 + MedReason)
Medical is only 1.6% of our data by volume but should be 10-15% of training mix. These datasets add verified medical CHAINS OF REASONING (not just Q&A), including differential diagnosis, evidence evaluation, and treatment justification.

### 6. NVIDIA STACK (Nemotron Post-Training 25M)
This is NVIDIA's complete SFT data that produced their state-of-the-art reasoning model. Covers math, code, STEM, and general reasoning. 25M samples is orders of magnitude more than any other single dataset.

## Download Script
`~/dgx-spark-prep/download-round3.sh`
Usage: `bash download-round3.sh` or `bash download-round3.sh --dry-run`

## Estimated Total After Round 3
- Current: 193GB, ~7.93M examples
- After Round 3: ~340GB, ~57M examples (7x more data)
- Big driver: Nemotron 25M + OpenMathInstruct-2 14M


## Sources

- https://huggingface.co/datasets/tasksource/PRM800K
- https://huggingface.co/datasets/nvidia/OpenMathInstruct-2
- https://huggingface.co/datasets/a-m-team/AM-DeepSeek-R1-Distilled-1.4M
- https://huggingface.co/datasets/open-thoughts/OpenThoughts3-1.2M
- https://huggingface.co/datasets/m-a-p/OpenCodeInterpreter-DS
- https://huggingface.co/datasets/openbmb/UltraInteract_sft
- https://huggingface.co/datasets/nebius/SWE-rebench-openhands-trajectories
- https://huggingface.co/datasets/SWE-Gym/SWE-Gym
- https://huggingface.co/datasets/nvidia/Nemotron-Post-Training-Dataset-v1
- https://huggingface.co/datasets/FreedomIntelligence/medical-o1-reasoning-SFT
- https://huggingface.co/datasets/UCSC-VLAA/MedReason
- https://huggingface.co/datasets/xlangai/AgentTrek
