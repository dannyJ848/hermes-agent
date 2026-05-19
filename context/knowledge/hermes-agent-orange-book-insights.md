# hermes-agent-orange-book-insights

*Researched: 2026-04-10 09:14 CDT*

# Hermes Agent Orange Book - Key Insights for Training Gym

## Source: alchaincyf/hermes-agent-orange-book (1.3K stars, PDF extracted to 1847 lines)

## Learning Loop Architecture (§03)
Five-step closed loop with causal relationships:
1. **Memory Curation** → actively decides what to remember (not passive)
2. **Autonomous Skill Creation** → distills complex task solutions into reusable Skills
3. **Skill Self-Improvement** → feedback from use modifies the Skill itself
4. **FTS5 Cross-Session Recall** → searches historical memory, loads only relevant parts
5. **User Modeling** (Honcho) → infers preferences, habits, goals from behavior

**Key insight**: Memory feeds Skill creation → Skill usage generates new memories → triggers Skill improvement → better results → more accurate profiling → better next curation. POSITIVE FEEDBACK LOOP.

## Three-Layer Memory (§04)
Corresponds to cognitive science memory types:
- **Session Memory** (Episodic) → "What happened?" — SQLite + FTS5, on-demand retrieval
- **Persistent Memory** (Semantic) → "Who are you?" — Durable state distilled from conversations
- **Skill Memory** (Procedural) → "How to do things?" — Methodologies and operating procedures

**Key insight**: On-demand FTS5 retrieval > load-everything approach. Context usage stays constant regardless of history volume.

## Skill System (§05)
Three sources: Bundled (40+), Agent-Created (grows with usage), Skills Hub (community)
- **agentskills.io standard** — interoperable across 30+ tools (Claude Code, Cursor, etc.)
- **Self-improvement mechanism**: Execute → Collect Feedback → Update Skill → Next execution uses new version
- **Key distinction**: Traditional memory = accumulation of conversation logs. Hermes memory = distillation of experience. "One is a video tape, the other is a notebook."

## Self-Improvement Boundaries (§17)
**Ceiling insight**: "The ceiling isn't technical — it's the feedback signal."
- Without human feedback, agent can only use self-evaluation criteria
- "Self-improvement makes agents run faster in a known direction. But the direction itself still needs a human to set."
- **Sweet spot**: Let agent self-improve on the "how," while human owns the "what" and the "don't"

## Practical Patterns
- Mitchell Hashimoto pattern: "every time agent makes mistake, add rule to CLAUDE.md" — Hermes automates this
- Skill files are readable markdown diffs — auditable self-improvement
- Memory is file-level portable (~/.hermes/) — no cloud dependency
- Forgetting mechanism needed: "Outdated experience fading away is what keeps it from polluting current judgment"

## Multi-Agent (§15)
- Orchestrator doesn't need to be "smarter" than workers — needs to be good at decomposition and routing
- Sequential Pipeline, Parallel Fan-out, MapReduce, Iterative Refinement patterns


## Sources

- https://github.com/alchaincyf/hermes-agent-orange-book
