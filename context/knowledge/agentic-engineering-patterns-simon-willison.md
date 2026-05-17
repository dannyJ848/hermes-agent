# agentic-engineering-patterns-simon-willison

*Researched: 2026-04-07 18:22 CDT*

# Agentic Engineering Patterns (Simon Willison, Feb 2026)

## Summary
Simon Willison launched a structured collection of "Agentic Engineering Patterns" — coding practices for getting best results from coding agents (Claude Code, OpenAI Codex). This is the first systematic attempt to formalize the discipline.

## Key Patterns
1. **Writing code is cheap now** — The central challenge: cost to produce initial working code has dropped to near zero. This breaks existing intuitions about code economics.
2. **Red/Green TDD** — Test-first development helps agents write more succinct, reliable code with minimal extra prompting.
3. **Ongoing** — Willison plans 1-2 new chapters per week, book-shaped but evergreen (updated over time).

## Distinction
- **Vibe coding**: Non-programmers using LLMs, paying no attention to code
- **Agentic engineering**: Professional engineers using agents to amplify existing expertise

## Relevance to Hermes
- Hermes already implements many of these patterns (tool-call loops, verification after writes)
- The "writing code is cheap" insight validates the build-test-iterate skill approach
- TDD pattern aligns with Hermes's verify-after-write discipline

## Source
- https://simonw.substack.com/p/agentic-engineering-patterns
- https://simonwillison.com/tags/ai-assisted-programming/ (345+ posts)


## Sources

- https://simonw.substack.com/p/agentic-engineering-patterns
