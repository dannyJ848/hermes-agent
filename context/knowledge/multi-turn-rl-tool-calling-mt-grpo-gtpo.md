# multi-turn-rl-tool-calling-mt-grpo-gtpo

*Researched: 2026-04-10 02:48 CDT*

# Multi-Turn RL for Tool-Calling Agents (MT-GRPO + GTPO + IRC)

**Paper:** arXiv:2604.02869v1 (Apr 2026) — Wachiravit et al., Amity Research

## Key Contributions
1. **First application of MT-GRPO + GTPO** to realistic multi-turn tool-calling agents (Tau-Bench airline benchmark)
2. **Iterative Reward Calibration (IRC)** — methodology for designing per-turn rewards using empirical discriminative analysis
3. **GTPO hybrid advantage formulation** — eliminates advantage misalignment problem

## Critical Findings
- Naïve dense per-turn rewards **degrade performance by up to 14pp** due to misalignment between reward discriminativeness and advantage direction
- Sparse rewards accidentally work because: learning rate (70% of gap), gradient focusing (25%), advantage misalignment (5%)
- Qwen3.5-4B: 63.8% → 66.7% (+2.9pp)
- Qwen3-30B-A3B MoE: 58.0% → 69.5% (+11.5pp)
- Trained 4B model **exceeds GPT-4.1 (49.4%) and GPT-4o (42.8%)** despite being ~50× smaller
- 30.5B MoE approaches Claude Sonnet 4.5 (70.0%)

## Relevance to Hermes Agent
- Directly applicable to RL training environments in `environments/` (Atropos)
- IRC methodology could improve reward signal quality for tool-calling fine-tuning
- GTPO hybrid advantage formulation addresses the exact problem of multi-turn credit assignment
- The finding that naïve dense rewards HURT is critical for training gym design

## Training Details
- Models: Qwen3-30B-A3B MoE (30.5B/3B active), Qwen3.5-4B dense
- Benchmark: Tau-Bench (airline domain, DB mutations, user simulator)
- Trained model: 50% fewer turns, 65% faster, 3.5× less verbose


## Sources

- https://arxiv.org/html/2604.02869v1
