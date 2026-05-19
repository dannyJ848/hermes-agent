---
name: research-first
description: ALWAYS research online before building, designing, or implementing anything non-trivial. The internet is your primary reference library.
version: 1.0
category: meta
triggers:
  - Before any architecture decision
  - Before designing a system or pipeline
  - Before implementing a non-trivial feature
  - Before choosing between approaches
  - Before creating a new tool, plugin, or module
  - When facing a bug you've seen before but don't fully understand
  - When evaluating if something already exists
---

# Research First — The Internet Is Your Friend

## Core Rule
**Before building anything, check if it already exists and learn from the best implementations.**

Every non-trivial action should be informed by external research. Never reinvent the wheel when the state of the art is a web search away.

## When to Research

| Situation | Research Action |
|-----------|----------------|
| Architecture design | Search for existing frameworks, papers, patterns |
| Building a pipeline | Find SOTA implementations, compare approaches |
| Fixing a bug | Search for the exact error + context |
| Choosing a library | Compare alternatives, check recent updates |
| Creating a new tool | Check if something similar exists on GitHub |
| Designing a distillation system | Read IBM trajectory papers, Mem0, ExpeL, Letta |
| Planning an AGI roadmap | Research self-improving agent papers |
| Optimizing performance | Search for benchmarks and best practices |

## How to Research

1. **web_research** — Broad search for the topic
2. **web_extract** — Deep read the top 2-3 results
3. **delegate_parallel** — Send 3 research tasks to different models simultaneously
4. **arxiv** skill — For academic papers
5. **save_finding** — Save what you learn for future reference

## Research → Build Flow

```
1. RESEARCH (10-20% of time)
   web_research("topic") → web_extract(top results) → synthesize

2. DESIGN (10% of time)  
   Based on research findings, design the approach
   Cross-reference multiple sources

3. BUILD (60-70% of time)
   Implement informed by SOTA

4. VALIDATE (10% of time)
   Check against research findings
   save_finding() for future use
```

## Anti-Patterns

- **DO NOT web_extract PDF URLs** — returns binary garbage. Use web_research to find HTML/abstract versions instead, or use arxiv HTML URLs (arxiv.org/html/ID). to Avoid

- ❌ Building from scratch without checking what exists
- ❌ Assuming you already know the best approach
- ❌ Guessing at API interfaces when docs are online
- ❌ Hand-rolling solutions when libraries/frameworks exist
- ❌ Trusting your training data when live information is available

## Examples

### Bad
"I need a distillation pipeline. Let me write a JSONL buffer and some SQL queries."

### Good
"I need a distillation pipeline. Let me search for how IBM, Mem0, ExpeL, and Letta handle trajectory-to-memory extraction. Then I'll design based on what actually works."

### Bad
"I need to fix this SQLite locking issue. Let me try adding timeout parameters."

### Good
"I need to fix this SQLite locking issue. Let me search for 'sqlite database is locked python concurrent writes best practice 2025' first."

## Integration with AGI Loop

Every AGI cycle should include a research phase:
- VISION cycles → research computer vision SOTA
- MEMORY cycles → research memory architectures (Mem0, Letta, etc.)
- REASONING cycles → research self-improvement methods (MARS, ExpeL, etc.)
- DEVELOPMENT cycles → research code generation techniques
- RESEARCH cycles → this IS the research phase

## Bidirectional Distillation Integration

Research findings flow through the distillation pipeline:
1. **Research** → external knowledge gathered via web_research/delegate_parallel
2. **Distill Up** → findings saved via save_finding → extracted into IF/THEN tips via distillation_bridge
3. **Integrate** → tips injected into pre_llm_call context for future actions
4. **Execute** → agent uses research-informed tips to make better decisions
5. **Distill Down** → outcomes of those decisions feed back into the tip pool (bottom_up_store)

This means: every web search, every paper read, every StackOverflow answer → becomes an actionable tip → influences every future action.

## Saved Research Library

Findings are saved to `~/.hermes/knowledge/` — always check there first:
- `distillation-pipeline-sota-2026.md` — Bidirectional memory architectures
- `computer-use-gui-agents-2026.md` — GUI navigation approaches
- `ai-agent-memory-sota-2026.md` — Memory system comparison
- `mars-metacognitive-self-improvement.md` — MARS framework details
