# MT-GRPO-Tool-Calling-Training

*Researched: 2026-04-10 05:22 CDT*

# Multi-Turn RL for Tool-Calling Agents (MT-GRPO + GTPO)

**Paper:** arXiv:2604.02869v1 (Apr 2026)
**Authors:** Modecrua et al., Amity Research Center

## Key Contributions
1. **First MT-GRPO + GTPO hybrid** for training tool-calling agents on realistic multi-turn tasks
2. **Iterative Reward Calibration (IRC)** — methodology for designing per-turn rewards using empirical discriminative analysis of rollout data
3. **Dead Turn Gradient Focusing** — technique to handle turns that don't contribute to learning signal
4. **Advantage misalignment fix** — GTPO hybrid advantage formulation eliminates the misalignment problem

## Critical Finding: Dense Rewards Can Hurt
Naïvely designed dense per-turn rewards **degrade performance by up to 14 percentage points** due to misalignment between reward discriminativeness and advantage direction.

Sparse rewards accidentally work because:
- Learning rate accounts for 70% of the performance gap
- Gradient focusing accounts for 25%
- Advantage misalignment accounts for 5%

## Results on Tau-Bench (Airline)
| Model | Before RL | After RL | Δ |
|-------|-----------|----------|---|
| Qwen3.5-4B | 63.8% | 66.7% | +2.9pp |
| Qwen3-30B-A3B | 58.0% | 69.5% | +11.5pp |
| GPT-4.1 | — | 49.4% | — |
| GPT-4o | — | 42.8% | — |
| Claude Sonnet 4.5 | — | 70.0% | — |

The trained 4B model exceeds GPT-4.1 despite being ~50× smaller.

## Relevance to Hermes Agent
- **Tool-calling RL training** directly applicable to improving Hermes's tool dispatch accuracy
- **IRC methodology** could be used to calibrate reward signals for tool selection training
- **Multi-turn credit assignment** is the core challenge we face in agent training (Atropos environments)
- **Dead turn focusing** — we observe similar issues where some tool calls don't contribute useful signal


## Sources

- https://arxiv.org/html/2604.02869v1
