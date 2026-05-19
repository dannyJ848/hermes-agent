# multi-turn-rl-tool-calling-agents-2026

*Researched: 2026-04-10 19:40 CDT*

# Multi-Turn RL for Tool-Calling Agents with Iterative Reward Calibration

**Source:** arXiv:2604.02869v1 (Apr 2026) — Amity Research and Application Center

## Key Findings

### MT-GRPO + GTPO for Agentic Tool-Calling
First application of MT-GRPO (Multi-Turn Group Relative Policy Optimization) combined with GTPO (Generalized Token-level Policy Optimization) for training tool-calling agents on realistic multi-turn tasks (Tau-Bench airline benchmark).

### Critical Discovery: Dense Rewards Can Degrade Performance
Naïvely designed dense per-turn rewards **degrade performance by up to 14 percentage points** due to misalignment between reward discriminativeness and advantage direction. This is counterintuitive — more reward signal ≠ better training.

### Iterative Reward Calibration (IRC)
A methodology for designing per-turn rewards using empirical discriminative analysis of rollout data. Key insight: rewards must be calibrated against actual rollout behavior, not designed from intuition.

### GTPO Hybrid Advantage
Eliminates the advantage misalignment problem by combining group-normalized advantages with token-level policy optimization.

### Results
- **Qwen3.5-4B**: 63.8% → 66.7% (+2.9pp) — exceeds GPT-4.1 (49.4%) and GPT-4o (42.8%) despite being ~50× smaller
- **Qwen3-30B-A3B MoE**: 58.0% → 69.5% (+11.5pp) — approaching Claude Sonnet 4.5 (70.0%)
- Trained models produce **50% fewer turns, 65% faster, 3.5× less verbose** while achieving perfect tool argument selection

### Why Sparse Rewards Work (Ablation)
- Learning rate: 70% of the gap
- Gradient focusing: 25%
- Advantage misalignment: 5%

## Relevance to Hermes/SOMA
- Directly applicable to Hermes agent RL training (Atropos environments)
- The IRC methodology could improve Hermes distillation pipeline reward design
- Demonstrates that small models (4B) can beat frontier models with proper RL training
- MT-GRPO pattern could be used for Hermes multi-turn tool-calling training


## Sources

- https://arxiv.org/html/2604.02869v1
