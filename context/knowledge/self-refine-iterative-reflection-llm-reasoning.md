# self-refine-iterative-reflection-LLM-reasoning

*Researched: 2026-04-05 11:16 CDT*

# Self-Refine and Iterative Reflection Patterns for LLM Reasoning

**Sources:**
- Madaan et al. (NeurIPS 2023) — "Self-Refine: Iterative Refinement with Self-Feedback" (arXiv 2303.17651)
- SSR: Socratic Self-Refine (OpenReview) — extends Self-Refine with Socratic questioning
- Multi-Agent Reflection via RL (ICML 2025) — actor-critic LLM system for iterative refinement

## Core Pattern: Self-Refine

1. **Generate** → **Feedback** → **Refine** loop, all using the same LLM
2. No supervised training, no RL, no additional data required
3. ~20% absolute improvement across 7 diverse tasks (dialog, math reasoning, etc.)
4. Works even on GPT-4 — state-of-the-art models benefit from self-refinement
5. Key: the model acts as generator, critic, and refiner in sequence

## Extensions

- **Socratic Self-Refine (SSR)**: Adds Socratic questioning to the feedback step, consistently outperforms standard iterative refinement baselines across 5 reasoning benchmarks and 3 LLMs
- **Multi-Agent Reflection via RL (ICML 2025)**: Trains actor-critic LLM system to iteratively refine answers using direct preference learning on self-generated data — RL-optimized reflection

## Relevance to Hermes/Evey Agent

- Evey already has `reflect_on_output` tool which implements a basic Self-Refine pattern (draft → critique → improve)
- **Enhancement opportunity**: Add Socratic questioning phase — instead of just critiquing output, ask targeted questions that expose assumptions and gaps
- **The self-evaluation-loop skill** references Self-Refine + Reflexion — this confirms the pattern is well-established and effective
- **Practical**: After any delegation, run a lightweight reflection step asking "What assumptions might be wrong? What evidence supports this?" before accepting the result

## Sources

- https://arxiv.org/abs/2303.17651
- https://openreview.net/forum?id=QLL1EWSsxS
- https://icml.cc/virtual/2025/poster/46364
