# mt-grpo-gtpo-tool-calling-agents-2026

*Researched: 2026-04-11 13:02 CDT*

# MT-GRPO + GTPO for Multi-Turn Tool-Calling Agents (Apr 2026)

## Paper: arXiv:2604.02869v1 — Modecrua et al., Amity Research (Apr 3, 2026)

### Key Innovation
First application of MT-GRPO (Multi-Turn Group Relative Policy Optimization) combined with GTPO (Generalized Token-level Policy Optimization) for training tool-calling agents on realistic multi-turn tasks.

### Critical Finding: Dense Rewards Can HURT
Naïvely designed dense per-turn rewards degrade performance by up to 14 percentage points due to **advantage misalignment** — reward discriminativeness conflicts with advantage direction. Sparse binary rewards (success/fail) accidentally work better because:
- Learning rate accounts for 70% of the performance gap
- Gradient focusing accounts for 25%
- Advantage misalignment accounts for 5%

### Iterative Reward Calibration (IRC)
A methodology for designing per-turn rewards using empirical discriminative analysis of rollout data. Instead of hand-crafting reward functions, IRC uses actual training rollouts to calibrate which per-turn signals are genuinely helpful.

### GTPO Hybrid Advantage
Eliminates the advantage misalignment problem by combining MT-GRPO's per-turn normalization with GTPO's discounted returns in a hybrid formulation.

### Dead Turn Gradient Focusing
Novel technique to focus gradients on turns where the agent's actions actually matter, ignoring "dead turns" that don't affect outcomes.

### Results on Tau-Bench (Airline)
| Model | Base | Trained | Delta |
|-------|------|---------|-------|
| Qwen3.5-4B | 63.8% | 66.7% | +2.9pp |
| Qwen3-30B-A3B MoE | 58.0% | 69.5% | +11.5pp |
| GPT-4.1 (reference) | 49.4% | — | — |
| GPT-4o (reference) | 42.8% | — | — |
| Claude Sonnet 4.5 (ref) | 70.0% | — | — |

Trained 4B model exceeds GPT-4.1 despite being ~50x smaller. 30.5B MoE approaches Claude Sonnet 4.5.

### SOMA/Hermes Relevance
- **Directly applicable to Hermes agent training**: The tool-calling patterns studied here mirror Hermes's own agent loop
- **IRC methodology** could improve our distillation pipeline reward design
- **Dead Turn Gradient Focusing** addresses our exact problem: many agent turns are trivial (echo, confirm) while few are critical (tool selection, error recovery)
- **Cross-domain transfer** results suggest training on customer service tasks transfers to other tool-calling domains
- **Sparse > Dense rewards** insight contradicts common wisdom and should inform our Atropos environment design

### Code Release
Code, reward calibration analysis, and training recipes to be released upon publication.


## Sources

- https://arxiv.org/html/2604.02869v1
