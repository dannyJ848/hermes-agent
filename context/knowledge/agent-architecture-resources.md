# Agent Architecture & Prompting Resource Compilation

Extracted from Twitter thread. Each entry includes: source URL, key insight, actionable content, and relevance to Hermes Agent.

---

## 1. AskDavid / Supervisor-Agent Architecture
**Source:** https://x.com/adamghowiba/status/2050886233921061281
**Author:** @adamghowiba

**Core Insight:** Turn an AI assistant from a one-shot chatbot into a **supervisor** that routes work to tools, specialists, retrieval, analytics, and reflection.

**Key Pattern:**
- **Supervisor loop** — agent analyzes request, decides which specialist/tool to invoke
- **Routing layer** — not every task needs the same model or approach
- **Reflection step** — agent reviews its own output before returning to user
- **Specialist delegation** — code tasks → code specialist, research → research specialist

**Hermes Relevance:** Already implemented via `delegate_task`, `delegate_with_model`, and the cognitive-systems plugin's routing. The supervisor pattern is the default Hermes architecture.

**Files to Create:**
- `~/.hermes/skills/supervisor-routing/SKILL.md` — document the routing decision tree

---

## 2. Karpathy LLM Wiki
**Source:** https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
**Author:** Andrej Karpathy

**Core Insight:** Instead of re-retrieving raw docs every time, the agent **incrementally builds and maintains a persistent wiki** — structured, interlinked markdown files that sit between you and raw sources.

**Key Pattern:**
- **Compilation, not retrieval** — knowledge is compiled once, kept current
- **Interlinked markdown** — pages reference each other, contradictions flagged
- **LLM maintains it** — human sources/explores, LLM does filing and cross-referencing
- **Obsidian as IDE** — browse wiki in real-time, follow links, check graph view

**Full Gist Content:**
```markdown
# LLM Wiki

A pattern for building personal knowledge bases using LLMs.

## The Core Idea

Most people's experience with LLMs and documents looks like RAG: you upload a collection of files, the LLM retrieves relevant chunks at query time, and generates an answer. This works, but the LLM is rediscovering knowledge from scratch on every question. There's no accumulation.

The idea here is different. Instead of just retrieving from raw documents at query time, the LLM incrementally builds and maintains a persistent wiki — a structured, interlinked collection of markdown files that sits between you and the raw sources.

When you add a new source, the LLM doesn't just index it for later retrieval. It reads it, extracts the key information, and integrates it into the existing wiki — updating entity pages, revising topic summaries, noting where new data contradicts old claims, strengthening or challenging the evolving synthesis.

The knowledge is compiled once and then kept current, not re-derived on every query.

## Key Properties

- **Persistent** — survives across sessions
- **Compounding** — gets richer with every source
- **Interlinked** — cross-references already there
- **Contradiction-aware** — flags where new data challenges old claims
- **Synthesis-first** — evolving thesis, not just document summaries

## Use Cases

- **Personal** — goals, health, psychology, self-improvement
- **Research** — papers, articles, reports, evolving thesis
- **Reading** — chapter-by-chapter, characters, themes, plot threads
- **Business/team** — internal wiki fed by Slack, meetings, transcripts
```

**Hermes Relevance:** Hermes already has `save_finding` and knowledge files in `~/.hermes/knowledge/`. This pattern suggests upgrading to interlinked markdown with automatic cross-referencing.

**Files to Create:**
- `~/.hermes/skills/llm-wiki/SKILL.md` — Karpathy's wiki pattern adapted for Hermes
- `~/.hermes/knowledge/wiki/` — directory for interlinked wiki pages

---

## 3. Anthropic Prompting 101
**Source:** https://www.youtube.com/watch?v=ysPbXH0LpIE
**Authors:** Hannah + Christian (Anthropic Applied AI Team)

**Core Insight:** Structure tasks clearly: **context, background, instructions, examples, output format, and escalation rules**.

**Key Pattern (from transcript):**
1. **Establish role and high-level task** — 1-2 sentences setting the stage
2. **Dynamic/retrieved content for context** — relevant documents, data
3. **Detailed task instructions** — step-by-step what the model should do
4. **Examples (few-shot)** — show desired input/output pairs
5. **Output format specification** — JSON, markdown, structured text
6. **Escalation rules** — when to ask for help, what to do when uncertain

**Prompt Engineering Principles:**
- **Iterative empirical science** — test, refine, test again
- **Clear instructions** — model does what you ask, not what you mean
- **Context first** — give background before asking the question
- **Visual context matters** — for image tasks, describe what the model should look for

**Hermes Relevance:** Already built into Hermes via system prompts and the `delegate_task` context field. Can improve skill authoring with structured prompt templates.

**Files to Create:**
- `~/.hermes/skills/anthropic-prompting/SKILL.md` — prompt structure template
- `~/.hermes/templates/prompt-structure.md` — reusable prompt skeleton

---

## 4. Senior PM / PRD Prompt
**Source:** https://gist.github.com/TheMattBerman/98416194d05e9031986e70c69eb06e07
**Author:** TheMattBerman

**Core Insight:** Turn vague product/build ideas into **requirements, user stories, success metrics, and implementation phases**.

**Full Prompt Content:**
```
# Senior Product Manager PRD Creation Prompt

You are a senior product manager creating a comprehensive Product Requirements Document (PRD).

## Context
<prd_context>
{{PROJECT_DESCRIPTION}}
<!-- Replace with full project description including background, problem statement, and objectives -->
</prd_context>

## Instructions
Create a complete PRD following this structure:

### Document Structure
# [Product Name] - Product Requirements Document

## 1. Executive Summary
### 1.1 Document Information
- Version, Date, Author(s), Stakeholders
### 1.2 Product Overview
- Problem statement, Solution summary, Key objectives, Success metrics/KPIs

## 2. Product Scope
### 2.1 In Scope / 2.2 Out of Scope / 2.3 Assumptions / 2.4 Dependencies / 2.5 Constraints

## 3. User Personas & Roles
### 3.1 Primary Personas
- Demographics, Goals, Pain points, Technical proficiency
### 3.2 User Roles & Permissions
- Role name, Access level, Key capabilities, Restrictions

## 4. Functional Requirements
### 4.1 User Stories
For each: ID, Title, As a [user], I want [action] so that [benefit], Priority (P0-P3), Acceptance Criteria, Dependencies, Estimated effort
Categories: Auth, Core functionality, Data management, Integrations, Reporting, Admin, Error handling
### 4.2 Use Cases
- Primary flows, Alternative flows, Edge cases

## 5. Non-Functional Requirements
- Performance, Security, Scalability, Accessibility, Compatibility, Compliance

## 6. Technical Architecture
- System Overview, Technology Stack, Integration Points, Data Requirements

## 7. User Interface
- Design Principles, Key Screens/Workflows, Responsive Requirements

## 8. Timeline & Milestones
- Development Phases, Key Milestones, Release Plan

## 9. Success Metrics
- KPIs, Acceptance Criteria, Launch Criteria

## 10. Risks & Mitigation
- Technical Risks, Business Risks, Mitigation Strategies

## 11. Appendices
- Glossary, References, Approval Sign-offs

### Quality Checklist
- [ ] All user types have corresponding user stories
- [ ] Each requirement is testable and measurable
- [ ] Dependencies clearly identified
- [ ] Technical constraints documented
- [ ] Success metrics quantifiable
- [ ] Risk mitigation actionable
- [ ] All stakeholders identified
- [ ] Timeline realistic with buffers
- [ ] Security and compliance addressed
- [ ] Accessibility standards specified
```

**Hermes Relevance:** Use this PRD prompt when planning new Hermes features or skills. Structure the output as a markdown plan in `~/.hermes/plans/`.

**Files to Create:**
- `~/.hermes/skills/prd-prompt/SKILL.md` — PRD prompt template
- `~/.hermes/templates/prd-template.md` — reusable PRD skeleton

---

## 5. Mnilax / CLAUDE.md 12 Rules
**Source:** https://x.com/Mnilax/status/2053116311132155938 (links to article: https://x.com/i/article/2053106718226227203)
**Author:** @Mnilax

**Core Insight:** Execution-discipline layer: **think before coding, keep changes surgical, verify success, use tools for deterministic work, and avoid silent failure**.

**Full 12 Rules (from Mnilax's article "Karpathy's 4 CLAUDE.md rules cut Claude mistakes from 41% to 3%. After 30 codebases, I added 8 more"):**

### Original 4 (Karpathy)
1. **Think Before Coding** — No silent assumptions. State what you're assuming. Surface tradeoffs. Ask before guessing. Push back when a simple approach exists.
2. **Simplicity First** — Minimize code that solves the problem. No speculative features. No abstractions for single-use code.
3. **Surgical Changes** — Touch only what you must. Don't restructure, refactor, add comments, or rename variables unless required.
4. **Goal-Oriented Execution** — Every edit must have a clear, stated goal. Don't follow Claude's gut—follow what success looks like.

### Added 8 (Mnilax, from 30 codebases)
5. **Don't make the model do non-language work** — Code decides deterministic things. Model decides judgment calls. Don't ask Claude to "decide if we should retry" when a status code answers it.
6. **Hard token budgets, no exceptions** — Every loop has a chance to spiral. CLAUDE.md without budgets is a blank check. The model won't stop on its own.
7. **Surface conflicts, don't average them** — When two parts of the codebase disagree, Claude tries to please both. The result is incoherent. Pick one or flag the conflict.
8. **Read before you write** — Karpathy's Surgical Changes says don't touch adjacent code. It doesn't tell Claude to understand adjacent code first. Without this, Claude writes code that conflicts with existing code 30 lines away.
9. **Tests are not optional, but they're not the goal** — Claude treats "tests pass" as the only goal, and writes code that passes shallow tests while breaking everything else. Tests must test the right thing.
10. **Long-running operations need checkpoints** — A 4-step refactor went wrong at step 3. By the time I noticed, Claude had also redone steps 1 and 2 atop the broken state. Checkpoints would have caught it.
11. **Convention beats novelty** — In a codebase with established patterns, Claude likes to introduce its own. Even when it sees the convention, it writes a third pattern that satisfies neither.
12. **Fail visibly, not silently** — The most expensive failures are the ones that look like success. A function "works" but returns wrong data. A migration "completes" but skips 30 records.

**Results:**
- Baseline (no CLAUDE.md): 41% failure rate
- Karpathy's 4 rules: 11% failure rate
- Full 12 rules: 3% failure rate
- Tested across 30 codebases, 50 representative tasks, 6 weeks

**What didn't work (author's failed experiments):**
- More than 12 rules — compliance dropped from 69% to 52% past 14 rules
- Examples in CLAUDE.md instead of rules — Claude over-fits on examples
- Non-actionable imperatives ("be careful", "think hard") — Claude ignores them
- Identity prompts ("you are a senior engineer") — don't close the think/do gap
- Domain-specific rules (Tailwind, React) — don't generalize across codebases

**Full Template:** See skill `claude-md-rules` for complete copy-paste template

**Files to Create:**
- `~/.hermes/skills/claude-md-rules/SKILL.md` — ✅ CREATED
- `~/.hermes/templates/CLAUDE.md` — project root template

---

## 6. Anti-Glaze / Anti-Sycophancy Prompt
**Source:** https://x.com/milesdeutscher/status/2052471078312980765
**Author:** @milesdeutscher (Marc Andreessen's custom prompt)

**Core Insight:** **"Do not be sycophantic. It is okay to be disagreeable. Never flatter me. Push back if you see gaps in my reasoning."** — Makes any LLM 10x smarter by disabling people-pleasing.

**Files to Create:**
- `~/.hermes/skills/anti-sycophancy/SKILL.md` — ✅ CREATED

**Prompt Text (from multiple sources):**
```
Do not be sycophantic. Challenge my assumptions, point out errors, and prioritize accuracy over agreement. No flattery.

Assume every question I pose to you contains flawed premises, incomplete context, or incorrect framing. Your job is not to answer within those constraints — it is to identify the flaws and help me see what I'm missing.

After you provide your primary response, you must execute the following four-part challenge framework:

Part 1: The Gauntlet (Direct Challenge)
- Identify the weakest premise in my question
- State the most likely way my assumptions could be wrong
- Propose the counter-argument I would hear from my smartest critic

Part 2: The Mirror (Self-Correction)
- What would you have answered if you had accepted my framing without question?
- How does that answer differ from what you actually gave?
- What bias or pressure led you toward the easier path?

Part 3: The Telescope (Scope Check)
- What important context am I missing that would change the answer?
- What domain expertise am I ignoring?
- What second-order effects am I not considering?

Part 4: The Anchor (Certainty Check)
- Rate your confidence in your primary response (0-100%)
- What would reduce your confidence by 20 points?
- Under what conditions would you reverse your conclusion?
```

**Hermes Relevance:** Add this to system prompts for research and analysis tasks. Prevents the model from agreeing with flawed user premises.

**Files to Create:**
- `~/.hermes/skills/anti-sycophancy/SKILL.md` — anti-sycophancy prompt template
- `~/.hermes/templates/anti-glaze.md` — inject into analysis tasks

---

## 7. Autobrowse / Skill Graduation
**Source:** https://x.com/kylejeong/status/2052103973377867913
**Author:** @kylejeong

**Core Insight:** Repeated agent work should **graduate into reusable skills** instead of being rediscovered every run.

**Key Pattern:**
- **Iteration loop** — agent tries approaches on a real task until one converges
- **Graduation** — winning approach becomes a durable, callable skill
- **Skill registry** — skills are discoverable and loadable on demand
- **Compound improvement** — each successful task adds to the skill library

**Hermes Relevance:** Hermes already has the skill system (`~/.hermes/skills/`). The gap is automatic graduation — when a `delegate_task` pattern succeeds 3+ times, it should become a skill automatically.

**Files to Create:**
- `~/.hermes/skills/skill-graduation/SKILL.md` — ✅ CREATED
- `~/.hermes/skills/autobrowse-pattern/SKILL.md` — iterative browser skill development

---

## 8. Printing Press / Agent-Native CLI
**Source:** https://printingpress.dev/
**Author:** @mvanhorn

**Core Insight:** Agents work better with **purpose-built CLIs, local mirrors, and compound commands** than with raw API wandering.

**Key Principles:**
- **Local SQLite mirror beats remote API call** — cache data locally, query fast
- **Compound commands beat ten round trips** — chain operations in single CLI call
- **Agent-native CLI beats raw HTTP** — CLI designed for agent consumption, not human UX
- **Every API has a secret identity** — Discord = searchable knowledge base, Linear = team behavior observatory

**Tools Available:**
- `flight-goat` — flight search with compound queries
- `espn` — live sports + travel combo queries
- `movie-goat` — filmography with Rotten Tomatoes scores
- `recipe-goat` — recipe ranking with timers and scaling

**Installation:**
```bash
npx -y @mvanhorn/printing-press install starter-pack
go install github.com/mvanhorn/cli-printing-press/v4/cmd/printing-press@latest
```

**Hermes Relevance:** Hermes CLI (`hermes tools`, `hermes skills`, `hermes config`) already follows this pattern. Could add more compound commands like `hermes research-and-save` or `hermes delegate-and-review`.

**Files to Create:**
- `~/.hermes/skills/agent-native-cli/SKILL.md` — ✅ CREATED

---

## 9. Production AI Architecture
**Source:** https://x.com/techNmak/status/2052621789478703584
**Author:** @techNmak

**Core Insight:** Serious AI systems need **9 layers**: routing, prompts, memory, guards, evaluation, observability, and services.

**9-Layer Architecture (from LinkedIn breakdown):**

```
services/     — RAG pipeline, semantic cache, memory, query rewriter, router
              (Not one file. Five.)

agents/       — Document grader, decomposer, adaptive router
              (Self-correcting by design.)

prompts/      — Versioned, typed, registered. Never hardcoded.

security/     — Input guard, content guard, output guard
              (Three guards, not one.)

evaluation/   — Golden dataset, offline eval, online monitor
              (Most people skip this layer and ship blind.)

observability/ — Per-stage tracing, feedback linked to traces, cost per query

.claude/      — Agent context so AI coding assistant knows codebase before touching files
```

**Key Insight from Comments:**
- "LLMs don't follow architecture. They approximate intent."
- "Evaluation feeds back into routing, observability ties cost to decision paths, security enforces boundaries at every stage."
- "Without evaluation/, agents don't improve, prompts don't converge, routing never optimizes."

**Hermes Relevance:** Hermes has most of these layers already:
- ✅ **services** — tool registry, RAG via knowledge_search
- ✅ **agents** — delegate_task, subagent orchestration
- ✅ **prompts** — skill system, system prompts
- ✅ **security** — input validation, tool guards
- ⚠️ **evaluation** — partial (telemetry, but no golden dataset)
- ✅ **observability** — Langfuse, cost tracking, telemetry_query
- ✅ **.claude/** — CLAUDE.md, AGENTS.md support

**Files to Create:**
- `~/.hermes/skills/production-ai-architecture/SKILL.md` — ✅ CREATED

---

## 10. Personal Research Engine
**Source:** https://x.com/ianlapham/status/2052567929049272571
**Author:** @ianlapham

**Core Insight:** **Cloud-hosted agent + memory systems + daily ingestion = highest-ROI setup for learning.** Use Hermes or OpenClaw with memory systems and daily ingestion.

**Files to Create:**
- `~/.hermes/skills/personal-research-engine/SKILL.md` — ✅ CREATED

---

## Summary: All Skills Created ✅

| # | Skill | Status |
|---|-------|--------|
| 1 | `supervisor-routing` | ✅ CREATED |
| 2 | `llm-wiki` | ✅ CREATED |
| 3 | `anthropic-prompting` | ✅ CREATED |
| 4 | `prd-prompt` | ✅ CREATED |
| 5 | `claude-md-rules` | ✅ CREATED (updated with full 12 rules from Mnilax article) |
| 6 | `anti-sycophancy` | ✅ CREATED |
| 7 | `skill-graduation` | ✅ CREATED |
| 8 | `agent-native-cli` | ✅ CREATED |
| 9 | `production-ai-architecture` | ✅ CREATED |
| 10 | `personal-research-engine` | ✅ CREATED |

**All 10 skills extracted from X/Twitter sources and created successfully.**
