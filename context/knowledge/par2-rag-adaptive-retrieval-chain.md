# PAR2-RAG-adaptive-retrieval-chain

*Researched: 2026-04-11 21:40 CDT*

# PAR²-RAG: Planned Active Retrieval and Reasoning for Multi-Hop QA

**Source:** arXiv:2603.29085v1 (Mar 2026), Oracle AI

## Core Innovation
Two-stage framework that **separates coverage from commitment** in retrieval:
1. **Stage 1 — Coverage Anchoring:** Breadth-first search to build a high-recall evidence frontier
2. **Stage 2 — Iterative Chain Refinement:** Depth-first refinement with evidence sufficiency control

## Key Problem Solved
**Premature commitment** — iterative retrieval systems lock onto early low-recall trajectories and amplify downstream errors. Planning-only approaches produce static query sets that can't adapt when intermediate evidence changes.

## Results
- Up to 23.5% higher accuracy vs IRCoT across 4 MHQA benchmarks
- Up to 10.5% NDCG retrieval improvement
- Uses GPT-5.2 in ablations

## Relevance to Hermes Agent
- **Distillation pipeline:** Multi-hop retrieval is analogous to our multi-step tool chains — premature commitment to a tool path amplifies errors
- **Knowledge graph queries:** Separating breadth-first coverage from depth-first commitment could improve KG traversal
- **Research chains:** When researching a topic, first gather wide evidence (coverage), then refine deep (commitment) rather than going deep on the first result

## 2026 RAG Landscape (from Techment)
- Cross-encoders, multi-stage retrieval, contextual filtering for higher precision
- Production-critical architecture shift from experimentation
- Emphasis on accuracy, compliance, real-time intelligence
- Vector databases + regulatory archives as trusted sources


## Sources

- https://arxiv.org/html/2603.29085v1
- https://www.techment.com/blogs/rag-in-2026/
