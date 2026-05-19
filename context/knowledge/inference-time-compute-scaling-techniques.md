# inference-time-compute-scaling-techniques

*Researched: 2026-04-07 01:00 CDT*

# Inference-Time Compute Scaling for LLM Reasoning

**Date:** 2025-01 (Raschka overview), 2025-07 (FoT at ICML)
**Domain:** LLM Reasoning, Inference Optimization

## Overview

Inference-time scaling (also called test-time scaling, inference-compute scaling) allocates more compute/time during inference to improve model performance — without changing model weights. This has become the dominant paradigm alongside training-time scaling.

## Category Taxonomy (Raschka, Jan 2026)

1. **Chain-of-Thought Prompting** — Structured step-by-step reasoning in prompts
2. **Self-Consistency** — Sample multiple reasoning paths, take majority vote
3. **Best-of-N Ranking** — Generate N candidates, rank and select best
4. **Rejection Sampling with Verifier** — Generate candidates, verify correctness, reject bad ones (uses outcome/process reward models)
5. **Self-Refinement** — Model iteratively critiques and improves its own output
6. **Search Over Solution Paths** — Tree/graph search (DFS, BFS, MCTS) over reasoning space

## Forest-of-Thought (FoT) — ICML 2025

**Authors:** Bi, Han, Liu, Tang, Wang (2025)

Key innovation beyond Tree-of-Thought:
- Integrates **multiple reasoning trees** for collective decision-making
- **Sparse activation** selects most relevant reasoning paths (efficiency)
- **Dynamic self-correction** for real-time error fixing during reasoning
- **Consensus-guided decision-making** optimizes both correctness and compute

Addresses ToT limitation: single-pass reasoning that can't revisit flawed paths.

## Key Insight for Agents

Inference-time compute scaling is essentially what autonomous agents already do — multiple tool calls, self-reflection, retry loops. The formalization helps us understand:

1. **Best-of-N → delegation_parallel**: Generate multiple solutions, pick best
2. **Self-Refinement → self-evaluation-loop skill**: Critique and improve
3. **Search → autonomous_decide + task decomposition**: Explore solution space
4. **Verifiers → validate_output**: Score delegation results before trusting

## Practical Takeaway

Raschka reports that with proper inference-time scaling techniques, a base model can go from ~15% to ~52% accuracy on reasoning benchmarks — a 3.5x improvement with no weight changes. This suggests that for agent systems, investing in better orchestration (more inference steps, verification, search) can yield outsized returns compared to simply using a larger model.


## Sources

- https://magazine.sebastianraschka.com/p/categories-of-inference-time-scaling
- https://proceedings.mlr.press/v267/bi25a.html
