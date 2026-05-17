# skillclaw-collective-skill-evolution

*Researched: 2026-04-10 09:13 CDT*

# SkillClaw: Collective Skill Evolution for Multi-Agent Ecosystems

**Source:** AMAP-ML/SkillClaw (GitHub, April 2026)
**Paper:** arXiv:2604.08377

## Core Technique
SkillClaw evolves reusable skills from real agent session data using a **3-stage LLM workflow**: Summarize → Aggregate → Execute. It intercepts agent API calls via a local proxy, records session artifacts, and periodically runs evolution to distill patterns into shareable `SKILL.md` files.

## Architecture Components
1. **Client Proxy** — Local API proxy (`/v1/chat/completions`, `/v1/messages`) that intercepts requests, records session artifacts, syncs skills with shared storage
2. **Workflow Evolve Server** — Fixed 3-stage pipeline (Summarize → Aggregate → Execute) that reads session data, evolves skills, writes them back
3. **Agent Evolve Server** — Autonomous agent-driven alternative using an OpenClaw agent with full tool access to analyze patterns and write evolved skill files

## Key Innovation
Skills evolve **collectively** across a group of agents. Real-world experience from multiple users is distilled into shared skills, enabling continuous improvement across the entire agent cluster without manual intervention.

## Results
On WildClawBench, SkillClaw significantly improved Qwen3-Max's performance under limited group interaction — "not by using a bigger model, but by leveraging smarter experience."

## Relevance to Hermes
- The **3-stage evolution pipeline** (Summarize → Aggregate → Execute) maps directly to Hermes's distillation workflow
- The **proxy-based interception** pattern could enhance Hermes's trajectory saving and session analysis
- The **collective evolution** concept applies to multi-profile Hermes deployments sharing skills via `~/.hermes/skills/`
- The `SKILL.md` format is identical to Hermes's existing skill format, making integration trivial

## Sources

- https://github.com/AMAP-ML/SkillClaw
- https://arxiv.org/abs/2604.08377
