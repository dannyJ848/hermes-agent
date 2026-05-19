# memento-skills-self-evolving-agents

*Researched: 2026-04-14 19:12 CDT*

## Memento-Skills: RL-Based Self-Evolving Agent Skills

**Paper:** arXiv:2603.18743 | **Framework:** Open-source

Agents rewrite their own skill artifacts (prompts, code) without retraining the base LLM. Uses RL-based behavioral routing instead of semantic similarity. Key insight: skill retrieval should optimize for downstream execution utility, not text similarity.

Results: +13.7% on GAIA, +20.8% on HLE benchmarks. Skills grow from 5 seeds to 235 through autonomous mutation.

**Applicable to Hermes:** Our skill_manage system could adopt the mutation loop pattern — detect skill failures, auto-patch, verify with synthetic tests. The behavioral router concept could improve our skill loading accuracy.

## Sources

- https://venturebeat.com/orchestration/new-framework-lets-ai-agents-rewrite-their-own-skills-without-retraining-the
- https://arxiv.org/abs/2603.18743
