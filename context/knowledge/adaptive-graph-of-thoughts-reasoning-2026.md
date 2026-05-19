# adaptive-graph-of-thoughts-reasoning-2026

*Researched: 2026-04-14 15:35 CDT*

# Adaptive Graph of Thoughts (AGoT) — Advanced LLM Reasoning (2025-2026)

## Overview
Adaptive Graph of Thoughts (AGoT) is a test-time reasoning technique that unifies Chain-of-Thought (CoT), Tree of Thoughts (ToT), and graph-based reasoning structures. Published Feb 2025 (arXiv:2502.05078).

## Key Innovation
Unlike fixed CoT (linear chain) or ToT (tree), AGoT dynamically decomposes problems into sub-problems forming a **Directed Acyclic Graph (DAG)**. It selectively expands only necessary sub-problems, reducing unnecessary computation.

## Performance
- GPT-4o: **+46.2%** on GPQA Diamond (hard scientific reasoning)
- **+400%** on Game of 24 math puzzle vs baseline
- No additional training required — works at test time

## 2026 Prompting Landscape (Key Techniques)
1. **Adaptive Graph of Thoughts (AGoT)** — Dynamic DAG decomposition
2. **Self-Consistency CoT** — Consensus building across multiple reasoning paths
3. **Tree of Thoughts (ToT)** — Branching exploration with evaluation of partial results
4. **Least-to-Most** — Hierarchical decomposition for sequential workflows
5. **Latent CoT** — Token-efficient internal reasoning without explicit output

## Context Engineering vs Prompt Engineering
Major 2026 trend: separation of 'System Instructions' (fixed constraints, output formats, personas) from 'User Prompts' (questions + data). "Context Engineering" is replacing "Prompt Engineering" as the dominant paradigm.

## Relevance to Agent Self-Improvement
- AGoT could improve agent planning by dynamically choosing reasoning structure per task
- DAG-based decomposition maps well to multi-step tool calling
- Selective expansion = efficient token usage (critical for long sessions)


## Sources

- https://dev.classmethod.jp/en/articles/talked-about-the-recent-prompting-kr/
- https://galileo.ai/blog/chain-of-thought-prompting-techniques
