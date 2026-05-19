# reasoning-patterns-for-agents

*Researched: 2026-04-15 02:23 CDT*

# AI Agent Reasoning Patterns (2025-2026 Survey)

## Core Insight: Architecture ≠ Reasoning

From Servifyspheresolutions (Jan 2026):
- **Planner–Executor–Critic** architecture defines *where* decisions happen
- **ReAct, Reflexion, Tree-of-Thoughts** define *how* they are formed
- These patterns operate *inside* architectural boundaries, not replacing them

## Three Reasoning Patterns Mapped to Roles

| Pattern | Architectural Role | Function |
|---------|-------------------|----------|
| **ReAct** | Executor | Reasoning while acting — interleaves thought and action |
| **Reflexion** | Critic | Learning from failure — self-evaluation after execution |
| **Tree-of-Thoughts (ToT)** | Planner | Exploring options before commitment — branching search |

## Why Linear Reasoning Fails
- Single inference trajectory: once an assumption is introduced, all subsequent steps depend on it
- Works for static QA but collapses under interaction
- Root cause: no **revision mechanisms** — actions change environment, tools introduce noise, partial info causes cascading failures

## Chain of Thought (CoT) — Foundation
- Breaks complex problems into sequential logical steps
- Input → Step 1 (decompose) → Step 2 (intermediate) → ... → Output
- Dramatically improves accuracy + provides transparency

## ReAct (Reason + Act)
- Interleaves reasoning traces with task-specific actions
- Thought → Action → Observation → Thought → Action → ...
- Key advantage: grounds reasoning in real observations rather than assumptions

## Reflexion
- Post-execution self-evaluation
- Agent attempts task → fails → generates verbal reflection on failure → retries with insight
- Builds episodic memory of what went wrong

## Tree-of-Thoughts (ToT)
- Explores multiple reasoning paths simultaneously
- Evaluates each branch at decision points
- Backtracks from poor paths, commits to promising ones
- Best for planning/search problems with large solution spaces

## Relevance to Hermes Agent
- Hermes uses ReAct natively (tool calls interleaved with reasoning)
- Reflexion is partially implemented via `self-evaluation-loop` skill
- ToT could improve `autonomous_decide` — currently picks single path, could evaluate alternatives
- The Planner-Executor-Critic mapping aligns with Evey's brain regions (subconscious → conscious → evaluation)

## Sources
- https://medium.com/@servifyspheresolutions/how-reasoning-agents-actually-work-5eed384515be
- https://www.autonoly.com/blog/685e784a08412e725c1d0f4c/chain-of-thought-react-and-reflection-the-complete-guide-to-ai-agent-reasoning-patterns


## Sources

- https://medium.com/@servifyspheresolutions/how-reasoning-agents-actually-work-5eed384515be
- https://www.autonoly.com/blog/685e784a08412e725c1d0f4c/chain-of-thought-react-and-reflection-the-complete-guide-to-ai-agent-reasoning-patterns
