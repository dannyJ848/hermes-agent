# agentic-design-patterns-2026

*Researched: 2026-04-11 20:49 CDT*

# Agentic Design Patterns 2026

## Source: SitePoint "Definitive Guide to Agentic Design Patterns in 2026"

### 6 Core Patterns

1. **Reflection (Self-Critique Loops)** — Agent generates output, then critiques and revises it autonomously. Directly maps to our aggressive_continue + SILENT guard system.

2. **Tool Use (Grounding)** — Agents call real tools, not just generate text. Our tool registry + dispatch system implements this.

3. **Planning (Decompose, Then Execute)** — Break complex tasks into subtasks, then execute sequentially. Maps to our autonomous_plan tool.

4. **Multi-Agent Collaboration** — Multiple agents working together on different aspects. Our delegate_parallel and squad-dev skills implement this.

5. **Orchestrator-Worker (Dynamic Task Decomposition)** — A master agent dynamically assigns work to worker agents. Our brain-cycle + cron chain implements this pattern.

6. **Evaluator-Optimizer (Test-Driven Agent Development)** — Agent writes code, evaluates it, and iteratively improves. Maps to our build-test-iterate skill.

### Key Insight: "Flow Engineering > Prompt Engineering"
The central thesis: composable design patterns matter more than any single framework. Frameworks change; patterns endure. LangGraph reached stable semver in 2026 and handles production workloads with dozens of concurrent agent instances.

### Relevance to Hermes Agent
- Our 3-layer anti-stop architecture is an implementation of Pattern 1 (Reflection) at the infrastructure level
- The cron checkpoint chain is Pattern 5 (Orchestrator-Worker) — cron orchestrates, each session is a worker
- Domain certainty / active inference is an extension of Pattern 3 (Planning) with information-theoretic grounding
- The distilled tip system is Pattern 6 (Evaluator-Optimizer) applied to behavioral rules


## Sources

- https://www.sitepoint.com/the-definitive-guide-to-agentic-design-patterns-in-2026/
- https://hackernoon.com/the-realistic-guide-to-mastering-ai-agents-in-2026
