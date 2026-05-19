# llm-reasoning-paradigms-taxonomy

*Researched: 2026-04-19 18:00 CDT*

# LLM Reasoning Paradigms: Three-Tier Taxonomy

Three fundamental paradigms of LLM reasoning:

## 1. Prompting-Based (No training)
- CoT (+30-40% math), ToT (branching), GoT (non-linear, 95% sorting), Self-Consistency (majority voting), ReAct (reason+act), Least-to-Most, PoT (executable code)

## 2. Training-Based (Parameter changes)
- RLHF (alignment beats scale), PRMs (step-level reward, 78.2% vs 72.4% outcome), STaR (self-improve on correct reasoning), o1/DeepSeek-R1 (AIME: GPT-4 12% → o1 74%)

## 3. Multi-Agent (Collective intelligence)
- AutoGen, MetaGPT (85.9% code gen), Multi-Agent Debate, MAKER (1M+ steps zero errors). 5 agents at 1% error → 10⁻⁶ ensemble error.

## Key Insight
Test-time compute: 14x smaller models outperform large models with more reasoning time (Google DeepMind 2024).

## Hermes Relevance
ReAct is Hermes's core paradigm. council_decide implements multi-agent debate. PRMs could enhance reasoning quality evaluation.

## Sources

- https://medium.com/@joszhang16/reasoning-in-llms-evolution-from-chain-of-thought-to-multi-agent-systems-part-2-taxonomy-of-5a7a3cdc01ed
