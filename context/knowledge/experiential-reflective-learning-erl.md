# experiential-reflective-learning-erl

*Researched: 2026-04-14 20:40 CDT*

# Experiential Reflective Learning (ERL) — ICLR 2026

**Paper:** arXiv:2603.24639 | Authors: Allard et al. | ICLR 2026 MemAgents Workshop

## Key Idea
Self-improvement framework where agents reflect on task trajectories/outcomes to generate **heuristics** (actionable lessons). At test time, relevant heuristics are retrieved and injected into context.

## Results
- +7.8% over ReAct baseline on Gaia2 benchmark
- Outperforms few-shot trajectory prompting — abstractions transfer better than raw examples
- Single-attempt reflection is sufficient for effective self-improvement

## Critical Ablation Insights
1. **Selective retrieval is essential** — not all heuristics apply everywhere
2. **Abstracted heuristics > raw trajectory examples** for transfer
3. **One pass is enough** — no need for iterative refinement of the same experience

## Relevance to Hermes Agent
Our `distilled_tips` table + `research_to_distillation.py` pipeline is architecturally identical to ERL. The key validation: our approach of distilling tips from experience and injecting them into context is academically proven to work. The ablation confirms selective retrieval (which we do via relevance scoring) is critical.

## Action Items
- Verify our tip retrieval is selective enough (not injecting all tips)
- Consider adding a "relevance gate" that only injects tips above a confidence threshold
- The +7.8% improvement validates the entire distillation pipeline investment

## Sources

- https://arxiv.org/abs/2603.24639
