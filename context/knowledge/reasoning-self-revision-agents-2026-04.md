# reasoning-self-revision-agents-2026-04

*Researched: 2026-04-09 20:39 CDT*

# Reasoning: Self-Revision & Tree-Structured Agent Policy (Apr 2026)

## Paper 1: How Much LLM Does a Self-Revising Agent Actually Need?
- **arXiv:** 2604.07236 (Apr 8-9, 2026)
- **Authors:** Sungwoo Jung, Seonil Son
- **Key Insight:** Externalizing reflection into inspectable runtime structure reveals that explicit world-model planning gives +24.1pp win rate. LLM revision at 4.3% of turns yields marginal F1 improvement (+0.005) while slightly reducing win rate.
- **Implication for Hermes:** Over-using LLM calls for revision. Symbolic confidence-gated reflection could handle most stop-detection decisions, reserving LLM for ~4% of cases needing generative revision.

## Paper 2: T-STAR — Reason in Chains, Learn in Trees
- **arXiv:** 2604.07165 (Apr 8, 2026)
- **Authors:** Yu Li, Sizhe Tang, Tian Lan  
- **Key Insight:** Consolidates independent trajectories into a Cognitive Tree. Back-propagates rewards for variance-reduced step-level advantage. Thought Grafting contrasts success/failure branches at divergence points. Surgical Policy Optimization uses Bradley-Terry loss at critical steps.
- **Implication for Hermes:** Distillation should identify critical divergence points in tool-call sequences and focus tip extraction on those steps rather than averaging across entire trajectories.

## Synthesis: Not all reasoning steps are equally important. Confidence-gated reflection + tree-based trajectory analysis + surgical optimization could significantly reduce wasted LLM calls while improving distillation quality.

## Sources

- https://arxiv.org/abs/2604.07236
- https://arxiv.org/abs/2604.07165
