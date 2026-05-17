# GEPA prompt optimization production insights

*Researched: 2026-04-06 20:43 CDT*

# GEPA (Genetic-Pareto) Prompt Optimization — Production Insights

## Overview
GEPA is a gradient-free prompt optimizer introduced at ICLR 2026. It uses **natural language reflection** rather than policy gradients to adapt prompts. Built on DSPy framework.

## Key Performance Claims
- Outperforms GRPO by up to **20%** while using **35x fewer model rollouts**
- Outperforms MIPROv2 by **12% accuracy** on AIME-2025 benchmark
- 189 citations (as of early 2025 paper)

## How GEPA Works (Core Loop)
1. **Trajectory sampling**: Generate outputs on a batch of examples
2. **Reflection**: LLM analyzes failures and proposes improvements
3. **Crossover/evolution**: Genetic-style combination of successful prompt variants
4. **Pareto selection**: Multi-objective optimization (accuracy vs. cost, etc.)

## Production Findings (Decagon, March 2026)
- Applied to a **supervisor model** that analyzes conversations and produces structured judgments with reasoning traces
- Ran **19+ ablation experiments** to find optimal configuration
- Key insight: configuration decisions matter enormously — conventional wisdom about prompt optimization is often wrong
- Test-driven approach critical: define evaluation metrics before optimizing

## Relevance to Hermes Agent
- GEPA could optimize system prompts, tool-calling instructions, and skill documents
- The genetic crossover approach shines for **multi-agent systems** (optimize prompts across agents simultaneously)
- Could be applied to refine Hermes' personality, delegation prompts, and reasoning traces
- 35x fewer rollouts than GRPO makes it practical for our budget constraints

## Integration Path
1. Install `pip install gepa` (3.2k GitHub stars, active development)
2. Define evaluation metrics for agent tasks (tool call accuracy, task completion, cost efficiency)
3. Run GEPA on core system prompts as optimization targets
4. Use Pareto mode to balance quality vs. token cost

## Sources
- Paper: arxiv.org/abs/2507.19457
- GitHub: github.com/gepa-ai/gepa (3.2k stars)
- Production blog: decagon.ai/blog/optimizing-gepa-for-production
- Pydantic AI integration: pydantic.dev/articles/prompt-optimization-with-gepa

## Sources

- https://github.com/gepa-ai/gepa
- https://decagon.ai/blog/optimizing-gepa-for-production
- https://arxiv.org/abs/2507.19457
