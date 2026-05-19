# Claude Code Source Leak — Architectural Discoveries

*Researched: 2026-04-16 15:03 CDT*

# Claude Code Source Leak — Architectural Discoveries (Apr 2026)

## What Happened
- Claude Code had **500k+ lines of source code exposed** via shipped source maps/package contents
- One fork reached **32.6k stars and 44.3k forks** before DMCA takedowns
- Attackers registered malicious npm packages (`color-diff-napi`, `modifiers-napi`) targeting people compiling leaked code

## Top 6 Architectural Discoveries (Sebastian Raschka)
1. **Repo state in Context** — recent commits, git branch info injected into context
2. **Aggressive KV cache reuse** — leveraged for efficiency
3. **Custom Grep/Glob/LSP** — standard in industry
4. **File read deduplication / tool result sampling**
5. **Structured Session Memory** — 3-layer: MEMORY.md index → topic files (loaded on demand) → full session transcripts (searchable)
6. **Subagents** with prompt caching — fork-join model using KV cache, making parallelism basically free

## Memory System — 3-Layer Design
1. MEMORY.md — index file pointing to other knowledge
2. Topic files — loaded on demand
3. Full session transcripts — searchable

## "autoDream" Mode
Sleep mode that performs: merging memories, deduping, pruning, removing contradictions

## Tool Set
- **Less than 20 tools enabled by default** (up to 60+ total)
- Default: AgentTool, BashTool, FileReadTool, FileEditTool, FileWriteTool, NotebookEditTool, WebFetchTool, WebSearchTool, TodoWriteTool, TaskStopTool, TaskOutputTool, AskUserQuestionTool, SkillTool, EnterPlanModeTool, ExitPlanModeV2Tool, SendMessageTool, BriefTool, ListMcpResourcesTool, ReadMcpResourceTool

## 5 Kinds of Compaction identified in codebase
## 5-Level Permission System
## 2 Types of Plan Mode (EnterPlanModeTool / ExitPlanModeV2Tool)
## Built-in retry and resilience mechanisms

## Unreleased/Internal Features
- ULTRAPLAN, KAIROS, MAGIC DOCS, /buddy, Capybara/Mythos v8, employee-only gate & TUI

## Relevance to Hermes Agent
Many architectural patterns mirror or parallel Hermes Agent's design: skill system, memory layers, subagent delegation, tool deduplication, session compaction.

**Sources:** https://www.latent.space/p/ainews-the-claude-code-source-leak

## Sources

- https://www.latent.space/p/ainews-the-claude-code-source-leak
