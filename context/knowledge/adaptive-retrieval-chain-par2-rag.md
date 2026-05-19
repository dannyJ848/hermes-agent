# adaptive-retrieval-chain-PAR2-RAG

*Researched: 2026-04-11 22:32 CDT*

# PAR²-RAG: Planned Active Retrieval and Reasoning for Multi-Hop QA

**Source:** arXiv:2603.29085 (Mar 2026), Oracle AI

## Key Innovation
Two-stage framework that **separates coverage from commitment** in multi-hop QA:
1. **Stage 1 — Coverage Anchoring (breadth-first):** Builds a high-recall evidence frontier by gathering broad evidence before committing to any reasoning path
2. **Stage 2 — Iterative Chain Refinement (depth-first):** Refines with evidence sufficiency control in an iterative loop

## Problem Solved
- **Premature commitment:** Iterative RAG systems lock onto early low-recall trajectories, amplifying downstream errors
- **Static planning:** Planning-only approaches produce query sets that can't adapt when intermediate evidence changes

## Results
- Up to **23.5% higher accuracy** vs IRCoT across 4 MHQA benchmarks
- Up to **10.5% NDCG retrieval gains**

## Relevance to Agent Systems
- **Anti-drift pattern:** The coverage-then-commitment pattern directly applies to agent tool chains — gather broad context before committing to an action plan
- **For Hermes:** The `_discover_tools()` → execute pattern could benefit from breadth-first context gathering before depth-first tool chaining
- **For SOMA:** Medical QA often requires multi-hop reasoning (symptom → condition → treatment → contraindication) — PAR²-RAG's evidence sufficiency control could improve accuracy


## Sources

- https://arxiv.org/html/2603.29085v1
