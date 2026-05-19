# mars-multi-agent-reasoning-2026

*Researched: 2026-04-12 13:05 CDT*

# MARS: Multi-Agent Review System for LLM Reasoning (2026)

## Summary
MARS (Multi-Agent Review System) is a role-based collaboration framework for LLM reasoning that achieves comparable accuracy to Multi-Agent Debate (MAD) while reducing token usage by ~50%.

## Architecture
1. **Author Agent** — generates initial solution
2. **Reviewer Agents** — provide decisions + comments independently (no cross-reviewer communication)
3. **Meta-Reviewer Agent** — integrates feedback, makes final decision, guides revision

## Key Innovation
Eliminates costly reviewer-to-reviewer interactions. Reviewers work independently rather than in round-table debate format. This controls resource consumption while maintaining reasoning quality.

## Results
- Matches MAD accuracy across multiple benchmarks
- ~50% reduction in token usage
- Tested with multiple LLMs
- Code: https://github.com/xwang97/MARS

## Relevance to Hermes
- Could optimize delegation_parallel and council_decide patterns
- Meta-reviewer role mirrors how we use mixture_of_agents aggregator
- Independent review pattern is more token-efficient than debate
- Applicable to code review and research synthesis workflows

## Source
arXiv:2509.20502v2, Indiana University / Oregon Health & Science University, Mar 2026

## Sources

- https://arxiv.org/html/2509.20502v2
