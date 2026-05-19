# agent-semantic-memory-research-2026

*Researched: 2026-04-14 14:17 CDT*

# Agent Semantic Memory (AgentSM) — State of Research (Jan 2026)

**Source:** Emergent Mind research summary + multiple papers
**URL:** https://www.emergentmind.com/topics/agent-semantic-memory-agentsm

## Definition
AgentSM is the explicit, persistent, generalizable knowledge component in agent architectures. Unlike episodic memory (temporal, granular events), semantic memory stores **distilled, conceptual, reusable** knowledge — critiques, facts, procedural demonstrations.

## Key Implementations
- Textual summaries
- Dense vector stores
- Structured program traces
- Graph-based facts
- Hybrid knowledge graphs

## Core Functions
1. **Store** — Capture insights beyond instance-level experiences
2. **Distill** — Abstract episodic events into reusable knowledge
3. **Retrieve** — Efficient cross-situational access for new tasks
4. **Update** — Dynamic revision as agent encounters new contexts

## Relevance to Hermes Architecture
Hermes already implements a form of this:
- `distilled_tips` table = semantic memory (distilled procedural knowledge)
- `kg_nodes`/`kg_edges` = graph-based semantic memory
- `memory` tool = persistent factual memory
- `skills` = procedural semantic memory

## Improvement Opportunities
- Trustcall-style schema-driven extraction for structured memory
- Better distillation from episodic → semantic (our `research_to_distillation.py`)
- Cross-session retrieval optimization using dense embeddings
- Memory merging/conflict resolution when facts contradict

## Sources

- https://www.emergentmind.com/topics/agent-semantic-memory-agentsm
- https://aipractitioner.substack.com/p/long-term-memory-unlocking-smarter-38d
