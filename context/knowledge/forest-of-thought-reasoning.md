# forest-of-thought-reasoning

*Researched: 2026-04-14 18:16 CDT*

# Forest-of-Thought (FoT): Scaling Test-Time Compute for LLM Reasoning

**Source:** ICML 2025, Zhenni Bi et al., Huawei Noah's Ark Lab

## Key Innovation
Forest-of-Thought (FoT) integrates **multiple reasoning trees** with collective decision-making, going beyond single-pass methods (CoT, ToT, GoT) that may fail to revisit flawed reasoning paths.

## Core Components
1. **Sparse Activation** — Selects only the most relevant reasoning paths per tree, improving efficiency
2. **Dynamic Self-Correction** — Real-time error detection and correction during reasoning
3. **Consensus-Guided Decision Making** — Aggregates across multiple trees to optimize correctness

## Why It Matters
- Single-pass reasoning (CoT/ToT) can't recover from early wrong steps
- FoT's multi-tree approach provides natural error correction through diversity
- Sparse activation prevents compute blowup from multiple trees
- Published at ICML 2025, 123 citations

## Relevance to Agent Systems
- Applicable to tool-calling agents where reasoning chains can diverge
- Self-correction strategy mirrors what autonomous agents need (catching tool dispatch errors mid-chain)
- Sparse activation is analogous to agent skill selection — only use relevant capabilities per task
- Could improve delegation routing by evaluating multiple model candidates in parallel trees

## Comparison
| Method | Passes | Correction | Structure |
|--------|--------|------------|-----------|
| CoT | Single | None | Linear chain |
| ToT | Single | Branch eval | Tree |
| GoT | Single | Feedback loops | Graph |
| **FoT** | **Multi** | **Dynamic** | **Forest (multi-tree)** |


## Sources

- https://arxiv.org/html/2412.09078v5
- https://icml.cc/virtual/2025/poster/46117
