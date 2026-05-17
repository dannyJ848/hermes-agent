# hierarchical-chain-of-thought-hicot-reasoning

*Researched: 2026-04-19 23:46 CDT*

# Hierarchical Chain-of-Thought (Hi-CoT) — arXiv:2604.00130v1

Hi-CoT (April 2026, Huawei) organizes LLM reasoning into alternating instruction/execution blocks using `<|instruction|>` and `<|execution|>` tags. Creates "compression bottlenecks" that prevent plan-execution drift.

**Key results:** +6.2% accuracy, -13.9% token waste across 13 models. 100% accuracy on AMC/MATH500 when format strictly followed. Benefits small models (0.6B–4B) most as reasoning scaffold.

**Agent implications:** Could reduce token waste in long autonomous sessions, prevent reasoning drift, improve delegation to smaller models. Format compliance is key — strict structure unlocks latent reasoning capacity.

**Also noted:** 2026 reasoning landscape includes OpenAI o3/GPT-5.4 (configurable thinking depth), DeepSeek-V3.2, Gemini 3 Deep Think (84.6% ARC-AGI-2), Claude Opus 4.6 (adaptive effort + 1M context), Grok 5 (50.7% HLE). Industry shift from fluency to deliberate compute-heavy reasoning.

## Sources

- https://arxiv.org/html/2604.00130v1
- https://medium.com/@lmpo/the-llm-reasoning-explosion-from-fluency-to-thought-eca285c58804
