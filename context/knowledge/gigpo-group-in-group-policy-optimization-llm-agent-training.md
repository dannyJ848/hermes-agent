# GiGPO-Group-in-Group-Policy-Optimization-LLM-Agent-Training

*Researched: 2026-04-10 19:05 CDT*

# GiGPO: Group-in-Group Policy Optimization for LLM Agent Training

**Source:** arXiv 2505.10978v3, NeurIPS 2025
**Authors:** Lang Feng, Zhenghai Xue, Tingcong Liu, Bo An (Nanyang Technological University / Skywork AI)

## Core Innovation

GiGPO extends GRPO from single-turn to **multi-turn LLM agent training** with a two-level advantage estimation:

1. **Episode-level (macro):** Computes relative advantages across groups of complete trajectories (like vanilla GRPO)
2. **Step-level (micro):** Uses "anchor state grouping" — identifies repeated environment states across trajectories and groups actions taken from the same state for localized credit assignment

## Key Insight

Under identical tasks/initial conditions, many trajectories encounter the **same states** multiple times (revisiting rooms, webpages, game scenes). These shared states provide a natural basis for step-level group construction — no extra rollouts or value models needed.

## Results
- **ALFWorld:** >12% improvement over GRPO
- **WebShop:** >9% improvement over GRPO
- **QA tasks:** 42.1% (3B), 47.2% (7B)
- Same GPU memory, identical LLM rollout, minimal additional time cost
- Tested on Qwen2.5-1.5B/3B/7B-Instruct

## Properties
- **Critic-free** (no value model needed)
- **Low memory** overhead
- **Stable convergence**
- Fine-grained per-step credit signals

## Relevance to Hermes Agent
- Directly applicable to training Hermes for multi-turn tool use
- The "anchor state grouping" concept maps to repeated tool-call patterns (e.g., terminal → read_file → patch loops)
- Could improve credit assignment in Atropos RL environments
- Code: https://github.com/langfengQ/verl-agent

## Also Noted
- MERL TR2026-026: "Training Task Reasoning LLM Agents for Multi-turn Task Planning" — shows GRPO single-turn improvements provide a lower bound for multi-turn success
- 2025-2026 LLM development described as "dominated by reasoning models using RLVR and GRPO" (Raschka)


## Sources

- https://arxiv.org/html/2505.10978v3
- https://neurips.cc/virtual/2025/poster/118123
