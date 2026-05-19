# google-adk-multi-agent-patterns-2025

*Researched: 2026-04-14 09:11 CDT*

# Google ADK: 8 Multi-Agent Design Patterns (Dec 2025)

Google released an official guide for their Agent Development Kit (ADK) with 8 production-grade multi-agent patterns:

1. **Sequential Pipeline** — Assembly line: Agent A → Agent B. Linear, deterministic, easy to debug.
2. **Hierarchical Supervisor** — A manager agent dispatches tasks to specialized sub-agents.
3. **Peer-to-Peer Collaboration** — Agents communicate directly without a central coordinator.
4. **Blackboard Pattern** — Shared state space where agents read/write to a common blackboard.
5. **Swarm Pattern** — Lightweight agents with handoff-based coordination (no fixed topology).
6. **Map-Reduce / Fan-out-Fan-in** — Parallel execution across agents, then aggregation.
7. **Debate / Adversarial** — Agents critique each other's outputs for quality improvement.
8. **Human-in-the-Loop** — Agent pauses for human approval at decision points.

**Key insight:** "Reliability comes from decentralization and specialization. A single agent tasked with too many responsibilities becomes a jack of all trades, master of none." — This mirrors microservices architecture for AI.

**Relevance to Hermes:** Hermes already uses patterns 1 (delegate_parallel), 2 (supervisor delegation), and 6 (fan-out-fan-in). The Blackboard and Swarm patterns are underexplored and could improve agent mesh coordination.

Source: https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/

## Sources

- https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/
