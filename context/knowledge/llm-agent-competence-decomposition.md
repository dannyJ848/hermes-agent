# LLM-Agent-Competence-Decomposition

*Researched: 2026-04-09 12:21 CDT*

# How Much LLM Does a Self-Revising Agent Actually Need?

**Paper:** arXiv:2604.07236 (April 8, 2026)
**Authors:** Seongwoo Jeong, Seonil Son

## Key Finding
Decomposes agent competence into 4 components: posterior belief tracking, explicit world-model planning, symbolic in-episode reflection, and sparse LLM-based revision. Finding: explicit world-model planning gives +24.1pp win rate over greedy baseline. Adding LLM revision at 4.3% of turns yields marginal improvement (+0.005 F1) but slightly lower win rate.

## Relevance to Hermes
- Validates the approach of structuring agent behavior externally (skills, tools, memory) rather than relying purely on LLM reasoning
- The "declared reflective runtime protocol" concept maps to Hermes's tool-call structure + memory system
- Suggests that for RL training, world-model planning components may matter more than LLM revision quality
- The confidence gating + guarded revision actions pattern could improve Hermes's tool dispatch accuracy

## Sources

- https://arxiv.org/abs/2604.07236
