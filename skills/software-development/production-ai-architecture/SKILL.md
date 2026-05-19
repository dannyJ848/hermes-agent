---
name: production-ai-architecture
description: 9-layer production AI architecture for building production-grade AI systems. Based on techNmak's honest breakdown and real-world patterns.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  commands: [python3]
---

# Production AI Architecture

Based on techNmak's "most honest AI architecture breakdown on the internet" and real-world production patterns.

## The 9 Layers

```
┌─────────────────────────────────────────┐
│  Layer 9: Monitoring & Observability     │
│  Layer 8: Safety & Guardrails            │
│  Layer 7: Evaluation & Testing           │
│  Layer 6: Deployment & Scaling           │
│  Layer 5: Memory & State                 │
│  Layer 4: Tools & Actions                │
│  Layer 3: Routing & Planning             │
│  Layer 2: Retrieval & Context            │
│  Layer 1: Input Processing               │
└─────────────────────────────────────────┘
```

## Layer Details

### Layer 1: Input Processing
- **Sanitization** — Strip injection attempts, validate length
- **Classification** — Route to appropriate handler (simple vs complex)
- **Extraction** — Pull structured data from unstructured input

### Layer 2: Retrieval & Context
- **RAG Pipeline** — Vector search + reranking + context assembly
- **Semantic Cache** — Cache similar queries to avoid redundant LLM calls
- **Query Rewriting** — Expand/rewrite user queries for better retrieval

### Layer 3: Routing & Planning
- **Intent Router** — Classify intent, route to specialist agent
- **Task Planner** — Break complex tasks into subtasks
- **Adaptive Router** — Learn from failures, adjust routing rules

### Layer 4: Tools & Actions
- **Tool Registry** — Catalog of available tools with schemas
- **Tool Selection** — LLM picks tools based on task
- **Tool Execution** — Run tools, handle errors, retry logic
- **Result Validation** — Validate tool output against schema

### Layer 5: Memory & State
- **Short-term** — Session context, conversation history
- **Long-term** — User preferences, learned patterns
- **Episodic** — Specific past interactions
- **Semantic** — General knowledge distilled from experiences

### Layer 6: Deployment & Scaling
- **Model Serving** — vLLM, TGI, or API endpoints
- **Load Balancing** — Distribute requests across instances
- **Caching** — Redis for hot data, CDN for static assets
- **Queueing** — Celery, RabbitMQ for async tasks

### Layer 7: Evaluation & Testing
- **Unit Tests** — Test individual components
- **Integration Tests** — Test layer interactions
- **A/B Tests** — Compare model versions
- **Human Evaluation** — Review outputs for quality

### Layer 8: Safety & Guardrails
- **Input Filtering** — Block harmful requests
- **Output Filtering** — Block harmful responses
- **Rate Limiting** — Prevent abuse
- **Audit Logging** — Track all decisions

### Layer 9: Monitoring & Observability
- **Metrics** — Latency, throughput, error rates
- **Tracing** — Follow requests across layers
- **Alerting** — Notify on anomalies
- **Dashboards** — Visualize system health

## Key Insight: Not One File, Five

```
services/
  ├── rag_pipeline.py      # Layer 2
  ├── semantic_cache.py    # Layer 2
  ├── memory.py            # Layer 5
  ├── query_rewriter.py    # Layer 2
  └── router.py            # Layer 3

agents/
  ├── document_grader.py   # Layer 2 quality check
  ├── decomposer.py        # Layer 3 task planning
  └── adaptive_router.py   # Layer 3 learning
```

## Production Checklist

- [ ] Input sanitized before reaching LLM
- [ ] RAG pipeline has reranking (not just vector search)
- [ ] Semantic cache reduces redundant calls
- [ ] Router handles unknown intents gracefully
- [ ] Tools have schemas and validation
- [ ] Memory persists across sessions
- [ ] Evaluation runs before every deployment
- [ ] Safety filters on both input and output
- [ ] Monitoring tracks latency and errors
- [ ] Fallbacks for every LLM call (timeout, error, rate limit)

## Anti-Patterns

- ❌ **Monolithic agent** — One file does everything
- ❌ **No caching** — Every call hits the LLM
- ❌ **No validation** — Trust LLM output blindly
- ❌ **No fallback** — Single point of failure
- ❌ **No evaluation** — Ship without testing

## Hermes Alignment

Hermes already implements many of these layers:
- **Layer 2** — `knowledge_search`, `web_search`, `web_extract`
- **Layer 3** — `delegate_task` with model routing
- **Layer 4** — 40+ tools in registry
- **Layer 5** — `memory`, `skill_view`, `session_search`
- **Layer 7** — `validate_output`, `autonomous_reflect`
- **Layer 8** — `email_screen`, input sanitization
- **Layer 9** — `telemetry_query`, `cost_analytics`

## When to Use This Architecture

- Building production AI systems (not prototypes)
- Multi-user deployments
- High-stakes applications (health, finance, legal)
- Systems requiring audit trails

## When to Simplify

- Personal projects
- Internal tools
- Low-stakes automation
- Rapid prototyping (add layers later)
