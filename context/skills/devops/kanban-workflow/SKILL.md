---
name: kanban-workflow
title: Hermes Kanban Workflow — Orchestration and Worker Patterns
description: |
  Complete guide for Hermes Kanban task orchestration and worker execution.
  Covers decomposition playbooks, specialist routing, worker lifecycles,
  handoff patterns, retry diagnostics, and edge cases. For both orchestrator
  profiles and dispatched workers.
triggers:
  - When using Hermes Kanban for multi-agent task management
  - When playing orchestrator role routing work to specialists
  - When spawned as a kanban worker needing lifecycle guidance
  - When the user says "kanban", "orchestrate", "dispatch", "worker"
category: devops
---

# Hermes Kanban Workflow

## Overview

Hermes Kanban enables multi-agent coordination through a shared task board.
Orchestrators decompose work and route it to specialist workers; workers execute
tasks and report progress through a standardized lifecycle.

---

## Section 1: Orchestrator Playbook

### When to Use the Board (vs. Just Doing the Work)

Create Kanban tasks when any of these are true:

1. **Multiple specialists are needed.** Research + analysis + writing is three profiles.
2. **The work should survive a crash or restart.** Long-running, recurring, or important.
3. **The user wants visibility.** They want to see what's in flight, what's blocked, what's done.
4. **Parallelism matters.** Two things can happen at the same time.
5. **The orchestrator shouldn't do the work.** If the orchestrator is also the worker, you don't need Kanban — just do the work.

### Anti-Temptation Rules

**Rule 1: Don't do the work yourself**
The orchestrator's job is routing, not execution. If you find yourself writing code, researching, or analyzing, you've slipped into worker mode. Stop. Create a task. Dispatch a worker.

**Rule 2: Don't create tasks for yourself**
If you're the orchestrator AND the only available worker, just do the work directly. Kanban overhead is wasteful for single-agent scenarios.

**Rule 3: Decompose, don't execute**
When a user asks for something complex, decompose it into 3-7 tasks on the board, then dispatch workers. Don't try to execute the whole thing in your own context.

### Decomposition Patterns

**Pattern: Research → Analysis → Synthesis**
```
Task 1: Research topic X (researcher profile)
Task 2: Analyze findings and identify gaps (analyst profile)
Task 3: Write summary and recommendations (writer profile)
```

**Pattern: Parallel Implementation**
```
Task 1: Implement backend API (backend profile)
Task 2: Implement frontend UI (frontend profile)
Task 3: Write tests for both (tester profile)
```

**Pattern: Sequential Dependency**
```
Task 1: Design schema (architect profile) → blocks Task 2
Task 2: Implement schema (backend profile) → blocks Task 3
Task 3: Write migration (devops profile)
```

### Specialist Roster Conventions

| Profile | Skills | Typical Tasks |
|---------|--------|---------------|
| Researcher | web, search | Information gathering, fact-checking |
| Analyst | data-science | Data analysis, pattern identification |
| Coder | terminal, file | Implementation, bug fixes |
| Tester | terminal, file | QA, test writing, regression testing |
| Writer | file | Documentation, summaries, reports |
| DevOps | terminal, web | Deployment, infrastructure, monitoring |

### Task Creation Template

```yaml
kanban_create:
  title: "Clear, actionable title"
  description: |
    Context: What the user wants and why
    Deliverable: What the worker should produce
    Acceptance: How to verify it's correct
    Files: Paths to relevant files
    Constraints: Time limits, quality bars, forbidden approaches
  profile: "coder"  # Which specialist profile
  skills: ["terminal", "file"]  # Tools the worker needs
  priority: high  # high / medium / low
```

---

## Section 2: Worker Lifecycle

### The 6 Steps

1. **Orient** — Read the task, understand the context, ask clarifying questions if needed
2. **Work** — Execute the task using available tools
3. **Heartbeat** — Report progress every 5 minutes or after significant milestones
4. **Block** — If stuck, report the block immediately with details
5. **Complete** — Deliver the result, verify acceptance criteria
6. **Handoff** — Pass context to the next worker or orchestrator

### Workspace Handling

Your workspace kind determines how you should behave inside `$HERMES_KANBAN_WORKSPACE`:

| Kind | What it is | How to work |
|---|---|---|
| `git` | Cloned repo | Branch, commit, push. Leave a clean working tree. |
| `shared` | Shared directory | Coordinate with other workers. Use file locks if needed. |
| `isolated` | Private directory | Work freely. No coordination needed. |

### Good Handoff Shapes

**Shape 1: File + Summary**
```
Delivered: src/feature.py (implemented and tested)
Summary: Added user authentication with bcrypt hashing. 3/3 tests passing.
Next: Frontend login form needs to call this API.
```

**Shape 2: Data + Context**
```
Delivered: /tmp/research-findings.json
Summary: Found 5 relevant papers. Key insight: approach X outperforms Y by 23%.
Next: Analyst should validate these findings against our constraints.
```

**Shape 3: Block + Diagnosis**
```
Blocked: Cannot connect to database
Diagnosis: Connection string missing port. Tried 5432 (default) — connection refused.
Needs: DevOps to verify database is running and accessible.
```

### Retry Diagnostics

When a task fails and needs retry:

1. **Log what was tried** — commands run, files modified, errors encountered
2. **Identify the failure mode** — transient (retry) vs. permanent (fix needed)
3. **Adjust the approach** — different tool, different file, different strategy
4. **Report the adjustment** — so the orchestrator knows why the retry is different

### Edge Cases

**Case 1: Task is too big**
If a task takes >30 minutes, it's too big. The worker should:
1. Report progress at 15-minute mark
2. Suggest decomposition into sub-tasks
3. Continue with the portion that fits in time

**Case 2: Task is unclear**
If acceptance criteria are ambiguous:
1. Ask clarifying questions immediately (don't guess)
2. Propose a specific interpretation
3. Wait for orchestrator confirmation before proceeding

**Case 3: Tools unavailable**
If a required tool is missing or broken:
1. Report the missing tool immediately
2. Propose alternative approaches using available tools
3. Don't silently work around — the orchestrator needs to know

**Case 4: Context window pressure**
If the task generates large artifacts (logs, data files):
1. Summarize in the heartbeat
2. Link to the full artifact (file path)
3. Don't paste megabytes into the chat

## Pitfalls

- **Orchestrator doing worker work:** The most common failure mode. If you're writing code, you've failed as orchestrator.
- **Workers not asking questions:** Guessing leads to wrong deliverables. Always clarify ambiguous requirements.
- **Missing heartbeats:** Orchestrator assumes no news is good news. Report blocks immediately.
- **Poor handoffs:** "Done" is not enough. Include what was done, where it lives, and what's next.
- **Tool mismatch:** Giving a researcher terminal access or a coder only web tools. Match skills to task needs.

## References

- `references/orchestrator-decomposition-templates.md` — Ready-to-use decomposition patterns
- `references/worker-handoff-examples.md` — Good and bad handoff examples
- `references/kanban-dispatch-commands.md` — CLI commands for kanban operations
