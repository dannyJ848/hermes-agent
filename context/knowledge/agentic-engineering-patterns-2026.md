# agentic-engineering-patterns-2026

*Researched: 2026-04-07 20:10 CDT*

# Agentic Engineering Patterns (Simon Willison, Feb 2026)

## Overview
Simon Willison launched a structured collection of **Agentic Engineering Patterns** — a guide-format series of chapters documenting best practices for professional software engineers using coding agents (Claude Code, OpenAI Codex, etc.).

## Key Patterns Documented

### 1. Writing Code is Cheap Now
The cost to produce initial working code has dropped to near-zero. This changes intuitions about:
- How much code to write (more is fine — agents can iterate)
- How to review code (focus on architecture, not line-by-line)
- When to throw away and rewrite (cheap to redo)

### 2. Red/Green TDD for Agents
Test-first development is a **fantastic fit for coding agents**:
- **Red phase**: Write tests first, confirm they FAIL
- **Green phase**: Implement until tests pass
- Protects against agents writing non-working or unnecessary code
- Builds regression protection as project grows
- Prompt shorthand: "Use red/green TDD" — models understand this

### 3. Subagents
Pattern for delegating work to sub-agents with isolated contexts.

### 4. First Run the Tests
Always run existing test suite before making changes — establishes baseline.

### 5. Linear Walkthroughs / Interactive Explanations
Using agents to understand unfamiliar codebases systematically.

## Relevance to Hermes Agent
- Our `test-driven-development` skill aligns with red/green TDD pattern
- The "Writing code is cheap now" insight validates aggressive iteration in autonomous mode
- Subagent pattern matches our `delegate_task` / `squad-dev` architecture
- The guide format (evergreen chapters, updated over time) is a good model for our skills system

## Source
- Guide index: https://simonwillison.net/guides/agentic-engineering-patterns/
- TDD chapter: https://simonwillison.net/guides/agentic-engineering-patterns/red-green-tdd/
- Announcement: https://simonwillison.net/2026/Feb/23/agentic-engineering-patterns/

## Sources

- https://simonwillison.net/2026/Feb/23/agentic-engineering-patterns/
- https://simonwillison.net/guides/agentic-engineering-patterns/red-green-tdd/
