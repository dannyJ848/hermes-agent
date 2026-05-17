# llm-reasoning-taxonomy-2026

*Researched: 2026-04-20 03:00 CDT*

# LLM Reasoning Approaches Taxonomy

Three paradigms dominate LLM reasoning:

1. **Prompting-Based** (CoT, ToT, GoT, ReAct, Self-Consistency) — no parameter changes, immediate deployment
2. **Training-Based** (RLHF, PRMs, STaR, specialized models like o1/DeepSeek-R1) — bakes reasoning into weights
3. **Multi-Agent** (AutoGen, MetaGPT, MAKER) — collective intelligence through ensemble

Key finding: Test-time compute scaling lets 14x smaller models match large ones. ReAct remains the standard agent framework. Graph of Thoughts (95% on sorting) significantly outperforms linear CoT (62%). Process Reward Models outperform outcome-only supervision on MATH (78.2% vs 72.4%).

## Sources

- https://medium.com/@joszhang16/reasoning-in-llms-evolution-from-chain-of-thought-to-multi-agent-systems-part-2-taxonomy-of-5a7a3cdc01ed
