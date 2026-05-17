# google-adk-multi-agent-patterns

*Researched: 2026-04-16 21:04 CDT*

# Google ADK Multi-Agent Design Patterns (8 Essential Patterns)

**Source:** Google Developers Blog, Dec 2025

## Key Insight
Multi-agent = microservices for AI. Single agents overloaded with responsibilities degrade into "jack of all trades, master of none." Specialized agents are more modular, testable, and reliable.

## The 8 Patterns

1. **Sequential Pipeline** ("Assembly Line") — Linear A→B→C via `SequentialAgent` with `output_key` for state passing
2. **Coordinator/Dispatcher** ("Concierge") — Central agent routes to specialists via `CoordinatorAgent` + AutoFlow
3. **Parallel Fan-Out/Gather** ("Octopus") — Multiple agents run simultaneously via `ParallelAgent`; CRITICAL: each agent must write to unique `output_key` to avoid race conditions in shared `session.state`
4. **Hierarchical Decomposition** ("Russian Doll") — Parent delegates to `AgentTool`-wrapped sub-agents, treats entire workflow as single function call
5. **Generator + Critic** ("Editor's Desk") — Draft→Review loop with conditional break on pass/fail via `LoopAgent`
6. **Iterative Refinement** ("Sculptor") — Generate→Critique→Refine cycle; exits on `max_iterations` OR `escalate=True` in `EventActions`
7. **Human-in-the-Loop** ("Safety Net") — Agent calls `approval_tool` that pauses execution for human authorization
8. **Composite** ("Mix-and-Match") — Real systems combine multiple patterns

## Critical Pro Tips
- **State management is vital:** `session.state` is shared whiteboard; use descriptive keys
- **Race conditions in ParallelAgent:** Each agent MUST use unique output_key
- **AgentTool pattern:** Wrapping sub-agent as tool lets parent call entire workflow as function — clean interface boundary
- **Exit conditions:** Use `escalate=True` in `EventActions` for early exit from loops when quality threshold met

## Relevance to Hermes
- Hermes's `delegate_task` maps to Hierarchical Decomposition (AgentTool)
- `delegate_parallel` maps to Parallel Fan-Out/Gather
- The Generator+Critic pattern mirrors validate_output + reflect_on_output
- Key gap: Hermes lacks a formal `LoopAgent` for iterative refinement — currently manual

## Sources

- https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/
