# anthropic-context-engineering-agents

*Researched: 2026-04-16 09:05 CDT*

# Anthropic: Effective Context Engineering for AI Agents

**Date:** September 29, 2025 | **Author:** Anthropic Engineering Team

## Key Concept: Context Engineering > Prompt Engineering
Context engineering focuses on holistic management of the "attention budget" to ensure AI agents remain steerable over long horizons. Every unnecessary token depletes the finite attention budget.

## Core Strategies

### 1. System Prompts — Goldilocks Zone
- Avoid hardcoding brittle if-else logic
- Avoid vague high-level fluff
- Use specific heuristics flexible enough for model intelligence
- Structure with XML tags or Markdown headers

### 2. Tool Design
- Tools define agent's action space — bloated toolsets create "ambiguous decision points"
- If a human can't decide which tool to use, an agent won't either
- Tools should return token-efficient information

### 3. Dynamic Context: Just-in-Time (JIT) > Pre-inference RAG
- Hold lightweight identifiers (file paths, URLs, IDs) instead of full datasets
- Progressive disclosure: agent uses tools to incrementally discover context
- Hybrid: drop critical files into context, let agent fetch others autonomously

### 4. Long-Horizon Strategies
- **Compaction:** Summarize history, reinitiate new window. Preserve decisions, discard redundant tool outputs.
- **Structured Note-Taking:** Agent writes to external file (NOTES.md) to track state across context resets
- **Sub-agent Architectures:** Noisy exploration in sub-agents, return only distilled summary to lead agent

## Key Takeaway
"As models improve, they require less prescriptive engineering and can manage their own context more effectively." Start minimal, add instructions only when failure modes identified.

## Relevance to Hermes Agent
Hermes already implements many of these patterns: cerebrum memory compaction, skill system (structured note-taking), delegation (sub-agent architecture), and progressive disclosure via skills on-demand. Anthropic's framework validates our architecture.

## Sources

- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
