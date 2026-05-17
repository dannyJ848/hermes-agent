# agent-engineering-patterns-2026

*Researched: 2026-04-11 20:52 CDT*

# Agent Engineering Patterns 2026

## Anthropic Agent Autonomy Research (Feb 2026)
- Claude Code autonomous sessions nearly doubled from ~25min to 45min in 3 months
- Experienced users auto-approve 40%+ vs new users 20% — trust increases with familiarity
- Claude Code pauses for clarification 2x more often than humans interrupt it (agent-initiated oversight)
- Software engineering = 50% of agentic tool calls on public API
- Emerging usage in healthcare, finance, cybersecurity
- Key insight: existing models are capable of MORE autonomy than they exercise in practice — the bottleneck is deployment patterns, not capabilities
- Recommendation: post-deployment monitoring infrastructure and human-AI interaction paradigms for managing autonomy + risk

## SitePoint 6 Core Agentic Design Patterns (Mar 2026)
1. **Reflection** — Self-critique loops (agent reviews own output)
2. **Tool Use** — Grounding agents in real world via structured schemas
3. **Planning** — Decompose then execute (chain-of-thought before action)
4. **Multi-Agent Collaboration** — Specialized agents coordinating
5. **Orchestrator-Worker** — Dynamic task decomposition at runtime
6. **Evaluator-Optimizer** — Test-driven agent development (agent writes tests, runs them, fixes)

## Key Trend: Flow Engineering > Prompt Engineering
The shift is from crafting perfect prompts to designing flows (multi-step tool-call pipelines with branching logic). Agents are state machines, not chatbots.

## Relevance to Hermes/SOMA
- Hermes already implements Reflection (self-critique via cerebrum), Planning (autonomous_decide), Multi-Agent (delegate_task), and Evaluator-Optimizer (test-driven dev skills)
- Gap: Orchestrator-Worker pattern (dynamic task decomposition) — Hermes's cron loop is more rigid
- Anthropic's finding that models can handle more autonomy than deployed suggests Hermes's aggressive_continue architecture is directionally correct


## Sources

- https://www.anthropic.com/news/measuring-agent-autonomy
- https://www.sitepoint.com/the-definitive-guide-to-agentic-design-patterns-in-2026/
