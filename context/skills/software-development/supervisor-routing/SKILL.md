---
name: supervisor-routing
description: Supervisor-agent routing pattern for multi-agent systems. Supervisor orchestrates, specialized subagents handle retrieval, structured data, analytics. Based on JP Morgan's AskDavid architecture.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [python3]
---

# Supervisor-Agent Routing Pattern

Based on JP Morgan's AskDavid multi-agent system architecture. The same pattern appears in Claude Code, OpenHands, and production AI systems.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│ Supervisor  │────▶│ Subagent 1  │
│  Request    │     │   Agent     │     │  Retrieval  │
└─────────────┘     └─────────────┘     └─────────────┘
                            │
                            ▼
                      ┌─────────────┐
                      │ Subagent 2  │
                      │ Structured  │
                      │   Data      │
                      └─────────────┘
                            │
                            ▼
                      ┌─────────────┐
                      │ Subagent 3  │
                      │  Analytics  │
                      └─────────────┘
```

## Core Pattern

1. **Supervisor Agent** — Receives request, plans decomposition, routes to subagents
2. **Specialized Subagents** — Each handles one domain:
   - Retrieval: RAG, search, document lookup
   - Structured Data: SQL, API queries, database operations
   - Analytics: Computation, aggregation, analysis
   - Code: Generation, review, debugging
   - Validation: Testing, verification, quality checks

## Implementation

### In Hermes

Use `delegate_task` with specialized context:

```python
# Supervisor decides routing
def route_task(task_description):
    if "database" in task_description or "SQL" in task_description:
        return delegate_task(
            goal=task_description,
            model="qwen-coder-free",
            context="You are a structured data specialist. Use SQL, pandas, or API queries. Return structured results only."
        )
    elif "search" in task_description or "find" in task_description:
        return delegate_task(
            goal=task_description,
            model="nemotron-free",
            context="You are a retrieval specialist. Use web_search, web_extract, knowledge_search. Return findings with sources."
        )
    elif "analyze" in task_description or "compute" in task_description:
        return delegate_task(
            goal=task_description,
            model="deepseek-r1-local",
            context="You are an analytics specialist. Use execute_code for computation. Return numerical results with methodology."
        )
    else:
        return delegate_task(
            goal=task_description,
            model="claude-sonnet-4",
            context="You are a general-purpose coding specialist. Follow CLAUDE.md rules."
        )
```

### Key Principles

1. **Single Responsibility** — Each subagent does one thing well
2. **Schema Contracts** — Subagents declare input/output schemas
3. **Error Propagation** — Subagent failures bubble to supervisor for retry routing
4. **Parallel Where Possible** — Independent subagents run simultaneously via `delegate_parallel`

## AskDavid Specifics

JP Morgan's system:
- Supervisor: Orchestrates research workflow
- Retrieval Agent: Fetches documents, filings, news
- Structured Data Agent: Queries databases, APIs
- Analytics Agent: Runs models, computes metrics
- Synthesis Agent: Combines outputs into final report

## When to Use

- Multi-step research tasks
- Tasks requiring different expertise domains
- High-stakes tasks needing validation layers
- Tasks with clear decomposition boundaries

## When NOT to Use

- Simple single-domain tasks (overhead not worth it)
- Tasks requiring tight iterative feedback
- Low-latency requirements (routing adds latency)
