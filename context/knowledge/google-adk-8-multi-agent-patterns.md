# google-adk-8-multi-agent-patterns

*Researched: 2026-04-18 21:04 CDT*

# Google ADK: 8 Essential Multi-Agent Patterns

**Source:** Google Developers Blog (Dec 2025, Shubham Saboo)

Google's Agent Development Kit (ADK) defines 8 canonical multi-agent patterns with direct code primitives:

1. **Sequential Pipeline** (`SequentialAgent`) — Linear A→B→C. Uses `output_key` for shared `session.state` pass-through.
2. **Coordinator/Dispatcher** — Central router delegates to specialist sub-agents via `AutoFlow` (LLM-driven based on agent descriptions).
3. **Parallel Fan-Out/Gather** (`ParallelAgent`) — Concurrent agents write to unique state keys to avoid race conditions. Synthesizer aggregates.
4. **Hierarchical Decomposition** (`AgentTool`) — Wraps sub-agent as a callable function for the parent. Key for exceeding single-agent context limits.
5. **Generator & Critic** (`LoopAgent` + `SequentialAgent`) — Pass/Fail quality gate. Loop exits on critic approval.
6. **Iterative Refinement** (`LoopAgent`) — Qualitative improvement loop with `max_iterations` hard limit + `escalate=True` early exit.
7. **Human-in-the-Loop** — Custom `approval_tool` pauses execution for human authorization on high-stakes actions.
8. **Composite Patterns** — Real systems combine multiple patterns (e.g., Coordinator→Parallel→Generator/Critic).

**Key insight:** `session.state` is the shared whiteboard. Descriptive `output_key` naming prevents cross-agent state collisions. `AgentTool` is the critical primitive for hierarchical decomposition — treats entire sub-agent workflows as single function calls.

## Sources

- https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/
