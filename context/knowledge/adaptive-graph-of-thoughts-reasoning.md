# adaptive-graph-of-thoughts-reasoning

*Researched: 2026-04-14 08:56 CDT*

# AGoT: Adaptive Graph of Thoughts (Feb 2025)

## Finding
New reasoning technique "Adaptive Graph of Thoughts" (AGoT) from arXiv:2502.05078 dynamically decomposes LLM reasoning into DAG-structured sub-problems at test time. No training required.

## Key Results
- +46.2% on GPQA Diamond with GPT-4o
- +400% on Game of 24 vs baseline
- Unifies CoT, ToT, and GoT approaches

## Why It Matters
Fixed reasoning structures (chains, trees) fail on complex multi-faceted problems. AGoT adapts structure to problem complexity — selectively expanding only necessary branches. This is directly applicable to autonomous agent task planning.

## 2026 Trend: Context Engineering > Prompt Engineering
The article also notes a paradigm shift: "Context Engineering" is replacing "Prompt Engineering" — separating system instructions (constraints, formats, personas) from user prompts (questions, data). This aligns with Hermes's architecture (system prompt vs user messages).

## Sources
- arXiv:2502.05078
- https://dev.classmethod.jp/en/articles/talked-about-the-recent-prompting-kr/

## Sources

- https://dev.classmethod.jp/en/articles/talked-about-the-recent-prompting-kr/
- https://arxiv.org/abs/2502.05078
