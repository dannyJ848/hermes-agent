# omx-oh-my-codex-multi-agent-codex

*Researched: 2026-04-04 20:33 CDT*

# OmX (Oh My codeX) — Multi-Agent Orchestration for Codex CLI

**GitHub**: Yeachan-Heo/oh-my-codex | 15.7K stars | Rust + TypeScript
**What**: Workflow layer for OpenAI Codex CLI that adds structured multi-agent workflows.

## Core Pattern: Clarify → Plan → Execute
1. `$deep-interview "clarify the change"` — clarification flow, asks questions
2. `$ralplan "approve the plan and review tradeoffs"` — structured planning with tradeoff review
3. `$ralph "carry the approved plan to completion"` — persistent execution loop
4. `$team 3:executor "execute in parallel"` — coordinated parallel multi-agent execution

## Key Features
- Hooks system for Codex lifecycle events
- HUD for monitoring agent teams
- Specialist roles (architect, executor, reviewer)
- Project-scoped AGENTS.md for persistent context
- `.omx/` directory for plans, logs, memory, mode tracking
- `--madmax --high` for maximum capability mode

## Patterns to Steal for Hermes
1. **Deep Interview before execution** — clarify requirements before diving in
2. **Tradeoff review in planning** — explicit tradeoff evaluation
3. **RALPH persistent loop** — never stop until task complete
4. **Team coordination** — parallel agents with different roles
5. **Scoped AGENTS.md** — project-level context files (similar to my skills)

## Related
- My `squad-dev` skill covers parallel Hermes agents
- My `subagent-driven-development` skill covers independent task delegation
- OmX's `AGENTS.md` pattern is similar to Hermes skills


## Sources

- https://github.com/Yeachan-Heo/oh-my-codex
