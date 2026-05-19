# hermes-agent-press-coverage-april-2026

*Researched: 2026-04-13 16:59 CDT*

# Hermes Agent Press Coverage — April 2026

## LinkedIn Feature Article (Apr 10, 2026)
- **43,700 GitHub stars** in under two months since Feb 25, 2026 release
- Reached **v0.8.0 on April 8, 2026** with **1,000+ merged PRs**
- MIT-licensed, open-source autonomous agent framework
- Key differentiator vs OpenClaw: **Hermes compounds** (persistent memory + skill learning) vs OpenClaw starts fresh each conversation

## Nous Research Company Details
- Founded 2023 by Jeffrey Quesnelle (CEO), Karan Malhotra, Teknium, Shivani Mitra
- Hermes model family: **50M+ downloads**
- HQ: Saratoga, California
- Funding: ~$70M total
  - Paradigm led **$50M Series A** (April 2025), valuation: **$1 billion**
  - Seed ~$20M from Distributed Global, OSS Capital, Delphi Ventures, Together AI CEO Vipul Reddy, Solana co-founder Raj Gokal

## GEPA Integration (Technical)
- GEPA = Genetic-Pareto prompt optimization (UC Berkeley, Stanford, MIT, Databricks)
- ICLR 2026 Oral presentation
- Uses natural language reflection to diagnose failures, proposes targeted prompt mutations
- **100-500 evaluations** vs GRPO's typical **10,000+**
- Integrated via `hermes-agent-self-evolution` repo (DSPy + GEPA → skill optimization)
- After solving complex task → writes Markdown skill file → stores in SQLite (FTS5 + LLM summarization) → loads relevant skill next time
- **No model weights modified** — only prompts and skill documents evolve

## Sources

- https://www.linkedin.com/pulse/hermes-agent-nous-research-self-improving-open-source-developers-gly1c
- https://nousresearch.com/releases/
