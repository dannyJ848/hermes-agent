# gepa-reflective-prompt-evolution

*Researched: 2026-04-07 00:51 CDT*

# GEPA: Reflective Prompt Evolution Can Outperform RL

**Paper:** arXiv:2507.19457 (ICLR 2026 Oral)
**Authors:** Lakshya A Agrawal, Shangyin Tan, et al. (UC Berkeley, Stanford — Matei Zaharia, Omar Khattab groups)
**Submitted:** July 2025, revised Feb 2026

## Core Idea
GEPA (Genetic-Pareto) is a prompt optimizer that uses **natural language reflection** instead of scalar rewards + policy gradients. It samples trajectories (reasoning, tool calls, outputs), reflects in natural language to diagnose problems, proposes and tests prompt updates, and combines lessons from a **Pareto frontier** of its own attempts.

## Key Results
- **Outperforms GRPO by 6% average, up to 20%** on 6 tasks
- Uses **up to 35x fewer rollouts** than GRPO
- **Outperforms MIPROv2 by >10%** (e.g., +12% on AIME-2025)
- Promising results as inference-time search for code optimization
- Can turn **just a few rollouts into large quality gains**

## Why It Matters for Agent Design
1. **No model weights needed** — works with API-only models (like our setup)
2. **Richer learning signal** — natural language reflection > sparse scalar rewards
3. **Evolutionary + Pareto** — maintains diverse candidates, not just the best one
4. **Composable** — optimizes any text parameter: prompts, code, agent architectures
5. **ICLR 2026 Oral** — top-tier validation, from the DSPy/Berkeley ecosystem

## Connection to Our Work
- Directly applicable to optimizing Hermes agent prompts without fine-tuning
- Could replace manual prompt engineering for tool schemas, system prompts
- The "reflective" approach mirrors our self-improvement loops but with formal optimization
- From the same group as DSPy — likely integrates with DSPy pipelines

## Code
Available at: https://github.com/gepa-ai/gepa
Mintlify docs: https://mintlify.com/gepa-ai/gepa/quickstart


## Sources

- https://arxiv.org/abs/2507.19457
- https://medium.com/@sankalpsbahad/gepa-reflective-prompt-evolution-why-optimizing-prompts-can-beat-reinforcement-learning-85867f705f12
- https://mintlify.com/gepa-ai/gepa/quickstart
