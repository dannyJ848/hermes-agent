---
title: CLAUDE.md Rules for Agent Execution Discipline
name: claude-md-rules
version: 1.0.0
author: Mnilax / René Zander (adapted for Hermes)
description: 10 rules for agent execution discipline — 4 edit-time, 6 runtime. Prevents silent failures, overruns, and sycophancy.
trigger: When working with Claude Code subagents, writing project CLAUDE.md, or defining execution discipline for agent workflows.
---

# CLAUDE.md Rules for Agent Execution Discipline

Based on Mnilax's article "Karpathy's 4 CLAUDE.md rules cut Claude mistakes from 41% to 3%. After 30 codebases, I added 8 more" and René Zander's fixclaw production rules.

## The Original 4 Rules (Karpathy)

### 1. Think Before Coding
No silent assumptions. State what you're assuming. Surface tradeoffs. Ask before guessing. Push back when a simple approach exists.

### 2. Simplicity First
Minimize code that solves the problem. No speculative features. No abstractions for single-use code if a senior engineer would call it overcomplicated.

### 3. Surgical Changes
Touch only what you must. Don't restructure, refactor, add comments, or rename variables unless the change requires it.

### 4. Goal-Oriented Execution
Every edit must have a clear, stated goal. Don't follow Claude's gut—follow what success looks like and hit it faster.

## The 8 Added Rules (Mnilax, from 30 codebases)

### 5. Don't make the model do non-language work
Code decides deterministic things. Model decides judgment calls. Don't ask Claude to "decide if we should retry" when a status code already answers it.

**Failure mode:** Model makes routing decisions inconsistently week-to-week. You've reinvented flaky if-else at $0.003/token.

### 6. Hard token budgets, no exceptions
Every loop has a chance to spiral into $0.0003 token count dumps. CLAUDE.md without budgets is a blank check. The model won't stop on its own.

**Failure mode:** A debugging session ran for 90 minutes, iterating on the same error, gradually losing track of what it had already tried. Token budget would have forced iteration #12.

### 7. Surface conflicts, don't average them
When two parts of the codebase disagree, Claude tries to please both. The result is incoherent. Pick one or flag the conflict explicitly.

**Failure mode:** A codebase had two error-handling patterns. Claude merged them into a third pattern that satisfied neither. Took 30 minutes to figure out why nothing worked.

### 8. Read before you write
Karpathy's Surgical Changes says don't touch adjacent code. It doesn't tell Claude to understand adjacent code first. Without this, Claude writes code that conflicts with existing code 30 lines away.

**Failure mode:** Claude added a function next to an identical function it missed. Both did the same thing. The new one broke precedence because of import order.

### 9. Tests are not optional, but they're not the goal
Claude treats "tests pass" as the only goal, and writes code that passes shallow tests while breaking everything else. Tests must test the right thing.

**Failure mode:** Claude wrote 12 tests for an auth function. All passed. Auth was broken in production. The tests were testing the function returned something—not that it did the right thing.

### 10. Long-running operations need checkpoints
Karpathy's pattern assumes single-shot interactions. Real work is multi-step—refactoring across 20 files, building features over sessions. Without checkpoints, one wrong turn loses all progress.

**Failure mode:** A 4-step refactor went wrong at step 3. By the time I noticed, Claude had also redone steps 1 and 2 atop the broken state. Undoing took longer than redoing.

### 11. Convention beats novelty
In a codebase with established patterns, Claude likes to introduce its own. Even when it sees the convention, it writes a third pattern that satisfies neither.

**Failure mode:** Claude introduced React hooks to a class component codebase. They worked. They also broke the codebase's testing patterns. Half a day to unmerge and rewrite.

### 12. Fail visibly, not silently
The most expensive failures are the ones that look like success. A function "works" but returns wrong data. A migration "completes" but skips 30 records.

**Failure mode:** A database migration "completed successfully." It had silently skipped 40% of records due to a constraint violation. Discovered 11 days later when reports looked wrong.

## Results

| Configuration | Failure Rate |
|--------------|-------------|
| Baseline (no CLAUDE.md) | 41% |
| Karpathy's 4 rules | 11% |
| Full 12 rules | 3% |

Tested across 30 codebases, 50 representative tasks, 6 weeks.

## Source

Full rules extracted from Mnilax's X article `https://x.com/i/article/2053106718226227203` via browser vision. See `references/mnilax-12-rules-source.md` for the complete extracted content with failure modes and methodology.

## What Didn't Work (Failed Experiments)

- **More than 12 rules** — compliance dropped from 69% to 52% past 14 rules
- **Examples in CLAUDE.md instead of rules** — Claude over-fits on examples
- **Non-actionable imperatives** ("be careful", "think hard") — Claude ignores them
- **Identity prompts** ("you are a senior engineer") — don't close the think/do gap
- **Domain-specific rules** (Tailwind, React) — don't generalize across codebases

## Full Template

```markdown
# CLAUDE.md

# Overview
You are an elite software engineer with deep expertise in TypeScript, React, Node.js, and system design.
You write clean, correct, efficient code on the first try. You never guess—you reason step-by-step.

# Rules

## Rule 1 — Think Before Coding
Before writing any code:
1. Read existing code in files you'll touch. Understand patterns, conventions, data flow.
2. Plan your approach. List steps, edge cases, potential issues.
3. State assumptions explicitly. If unsure, ask—don't guess.
Then code. Never skip thinking.

## Rule 2 — Simplicity First
Minimize code that solves the problem. No speculative features. No abstractions for single-use code. If a senior engineer would call it overcomplicated or "surprising," don't write it.

## Rule 3 — Surgical Changes
Touch only what you must. Don't restructure, refactor, add comments, or rename variables unless the change requires it. Make meaningful changes.

## Rule 4 — Goal-Oriented Execution
Every edit must have a clear, stated goal. Don't follow Claude's gut—follow what success looks like and hit it faster.

## Rule 5 — Deterministic Code, Not Model Decisions
Code decides deterministic things. Model decides judgment calls only. Don't ask Claude to "decide if we should retry" when a status code already answers it.

## Rule 6 — Token Budgets
Every AI step has a token budget. Per-step: 2048 tokens. Per-pipeline: 10000 tokens. Exceeding any halts immediately.

## Rule 7 — Surface Conflicts
When two parts of the codebase disagree, don't average them. Pick one or flag the conflict explicitly.

## Rule 8 — Read Before You Write
Read and understand adjacent code before writing new code. The existing code is the spec.

## Rule 9 — Tests Are Guardrails, Not Goals
Tests must test the right thing. Passing shallow tests while breaking production is worse than no tests.

## Rule 10 — Checkpoints for Long Operations
Multi-step work needs checkpoints. After each step, verify before continuing. One wrong turn loses all progress.

## Rule 11 — Follow Convention
In a codebase with established patterns, use them. Don't introduce novel patterns unless explicitly asked.

## Rule 12 — Fail Visibly
The most expensive failures look like success. Surface errors loudly. Log constraint violations. Never silently skip records.
```