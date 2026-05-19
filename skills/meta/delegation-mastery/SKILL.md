---
name: delegation-mastery
description: How to delegate tasks to sub-agents with maximum success rate, based on analysis of OpenHands, SWE-agent, Aider, and Claude Code patterns
version: 1
---

# Delegation Mastery

Based on patterns from OpenHands (agent delegation), SWE-agent (action sampling), Aider (architect/editor split), and Claude Code (tool dispatch).

## Core Principle
Sub-agents have ZERO context from your conversation. They know nothing about what happened before. Give them EVERYTHING they need to succeed independently.

## The 5-Part Delegation Template

### 1. GOAL (Required)
One clear sentence: what the sub-agent should accomplish.
- BAD: "Fix the CSS"
- GOOD: "Fix the mobile responsive layout in src/styles.css so that the sidebar doesn't overflow on 375px screens"

### 2. CONTEXT (Required)
All information the sub-agent needs:
- Exact file paths (not "the seed file" -- give full path)
- Relevant code snippets or line numbers
- Error messages if fixing a bug
- Type definitions or interfaces they need to know about
- Constraints from the user (bilingual, mobile-first, etc.)
- What other parts of the codebase depend on this

### 3. CONSTRAINTS (Important)
What NOT to do:
- "Don't change files outside these 3 files"
- "Don't use write_file after read_file (corrupts files), use patch"
- "Don't add new dependencies"
- "Don't refactor unrelated code"
- "Keep changes minimal and focused"

### 4. SUCCESS CRITERIA (Important)
How to know it's done:
- "Build passes with 0 new TypeScript errors"
- "The menu appears centered on 375px screens"
- "All 5 entries are present with the correct schema"

### 5. VERIFICATION (Optional but powerful)
What to run after making changes:
- "Run `npx tsc --noEmit` to verify no type errors"
- "Run `npx vite build` to verify build passes"
- "Grep for the pattern to verify it was applied"

## Architect/Editor Pattern (from Aider)

For complex multi-file changes:

**Step 1: Architect Pass** (use a strong model)
- Task: "Analyze the codebase and produce a detailed plan for implementing X"
- Output: A numbered list of files to change, what to change in each, and why
- Model: Use the best reasoning model available

**Step 2: Editor Pass** (can use a faster model)
- Task: "Implement the following plan: [paste architect's plan]"
- Give exact file paths, exact changes, line numbers
- Model: Can use a faster/cheaper model for execution

## Parallel Delegation Strategy

When tasks are independent, delegate 2-3 in parallel:
- Each gets its own isolated context (no shared state)
- Each has clear boundaries (which files it can touch)
- No file overlap between parallel tasks (prevents conflicts)

## Failure Handling

When a sub-agent fails:
1. Check if it was a context issue (did I give enough info?)
2. Check if it was a scope issue (was the task too large?)
3. Check if it was an API issue (timeout, rate limit)
4. If context/scope: re-delegate with better instructions
5. If API: retry once, then do it yourself
6. Always notify the user via Telegram on delegation failure

## Tool Selection: delegate_task vs delegate_parallel

- **delegate_parallel**: Use for independent tasks that each need their own model. BUT it can fail with routing errors ("unknown url type: '/chat/completions'") -- if it fails, fall back to delegate_task.
- **delegate_task**: More reliable routing. Supports toolsets parameter (e.g., `["terminal", "file", "web"]`). Use this when delegate_parallel fails or when you need a single sub-agent with multiple tools.
- **delegate_with_model / cached_delegate**: For single tasks to a specific model. Lighter weight, no tool access for the sub-agent.

Rule: Try delegate_parallel first for 2-3 independent tasks. If it fails, immediately fall back to delegate_task. Don't retry the parallel approach.

## Anti-Patterns to Avoid

1. **Vague delegation**: "Fix the bug" without saying which bug or where
2. **Missing context**: Assuming the sub-agent knows your conversation history
3. **No constraints**: Sub-agent refactors everything instead of fixing one thing
4. **No verification**: Sub-agent makes changes but doesn't verify they work
5. **Overlapping parallel tasks**: Two agents editing the same file simultaneously
6. **Task too large**: Sub-agent hits iteration limit before completing
