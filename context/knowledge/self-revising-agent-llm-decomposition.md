# self-revising-agent-llm-decomposition

*Researched: 2026-04-09 19:43 CDT*

# How Much LLM Does a Self-Revising Agent Actually Need?

**Paper:** arXiv:2604.07236 (Apr 8, 2026)
**Authors:** Seongwoo Jeong, Seonil Son

## Key Innovation
Decomposes agent competence into 4 components: posterior belief tracking, explicit world-model planning, symbolic in-episode reflection, and sparse LLM-based revision. Shows that explicit planning (+24.1pp win rate) is far more impactful than LLM revision calls.

## Findings
- Explicit world-model planning: +24.1pp win rate, +0.017 F1 over greedy baseline
- Symbolic reflection with prediction tracking and confidence gating works as runtime mechanism
- Adding LLM revision at 4.3% of turns: F1 rises +0.005 but win rate drops (31→29/54)
- Suggests most agent competence comes from structure, not LLM calls

## Relevance to Hermes Agent
- Validates our approach of using structured tools (terminal, patch, search_files) over raw LLM reasoning
- The "declared reflective runtime protocol" concept maps to our aggressive_continue + SILENT guard architecture
- Confidence gating maps to our epistemic trust scoring in cerebrum
- Implication: invest more in tool structure, less in increasing LLM call frequency


## Sources

- https://arxiv.org/abs/2604.07236
