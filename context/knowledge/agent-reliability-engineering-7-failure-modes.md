# agent-reliability-engineering-7-failure-modes

*Researched: 2026-04-07 09:28 CDT*

# Agent Reliability Engineering: 7 Failure Modes

## Source: Galileo AI (Nov 2025) + Composio 2025 Agent Report

### Key Insight: Error Propagation is the Real Killer
Not the diversity of failure modes, but cascading errors: Memory → Reflection → Planning → Action chain means one corrupted input poisons all downstream decisions.

### The 7 Failure Modes
1. **Specification/Design Failures** — ambiguous requirements cascade into every action
2. **Tool Misuse** — agents exceed intended permissions or call wrong parameters
3. **Memory Corruption** — poisoned context propagates through all subsequent steps
4. **Reflection Failures** — agents don't recognize their own errors
5. **Planning Failures** — broken subtask decomposition
6. **Action Execution Errors** — tool calls with wrong parameters/formats
7. **Error Propagation** — early mistakes compound through the chain

### Mitigation Patterns
- **Constraint-based checks**: Convert plain-language specs into testable assertions
- **Retries with backoff**: For transient errors in tool calls
- **Alternate tool redundancy**: Backup tools when primary fails
- **Input validation**: Pre-check parameters before dispatch
- **Observability**: Structured tracing across the full agent decision chain

### Relevance to Hermes
Hermes's aggressive_continue + checkpoint chain addresses error propagation (Mode 7). The self-awareness module detects text-only stops (Mode 6). Missing: structured input validation before tool dispatch (Mode 6 prevention) and memory corruption detection (Mode 3).


## Sources

- https://galileo.ai/blog/agent-failure-modes-guide
- https://composio.dev/content/why-ai-agent-pilots-fail-2026-integration-roadmap
