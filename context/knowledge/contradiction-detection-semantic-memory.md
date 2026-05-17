# contradiction-detection-semantic-memory

*Researched: 2026-04-05 07:14 CDT*

# Contradiction Detection in Semantic Agent Memory

**Date:** 2026-04-05 | **Cycle:** 114 (MEMORY domain)

## Key Finding: Hermes Agent Issue #509 — Cognitive Memory Operations

An open feature request (teknium1, March 2026) on the Hermes Agent repo proposes LLM-driven memory operations inspired by CrewAI's Cognitive Memory:

**Current problem:** Flat text entries in MEMORY.md with manual add/replace/remove. No contradiction detection — "We use PostgreSQL" on Monday and "We switched to MySQL" on Friday coexist permanently.

**Proposed operations:**
1. **LLM-Driven Encoding** — Agent extracts structured facts from conversations using LLM calls, not regex
2. **Consolidation** — Merge related memories, resolve contradictions, update confidence scores
3. **Adaptive Recall** — Confidence-aware retrieval with relevance + recency + importance scoring
4. **Extraction** — Automatic fact extraction from conversations without manual triggers
5. **Forgetting mechanism** — Time-based decay + irrelevance pruning

## Practical Contradiction Detection Approaches

From the Oracle blog on agent memory:
- **Update phase:** Compare each new fact against most similar entries in vector DB using conflict detection
- **Conflict resolution strategies:** supersede (new replaces old), merge (combine), flag (mark for human review)
- **Temporal metadata:** Each memory needs timestamps to determine which is "current"

## Implications for Cerebrum

Our current implementation gaps vs. the proposed ideal:

1. **Contradiction detection is MISSING** — We store facts without checking if they conflict with existing entries. This is the #1 gap.
2. **Provenance chains exist partially** — Honcho stores source metadata but Cerebrum doesn't systematically track fact origins
3. **Decay exists** — memory_decay tool implements time-based scoring, which is good
4. **Consolidation is manual** — consolidate_daily_memory exists but requires explicit invocation

### Concrete improvement: Pre-storage contradiction check
Before honcho_store or memory add, run a semantic search for similar existing facts. If cosine similarity > 0.85, flag for review or auto-merge. This prevents the "PostgreSQL on Monday, MySQL on Friday" problem.

## Sources
- NousResearch/hermes-agent Issue #509 (March 2026)
- Oracle Developer Blog: "Agent Memory: Why Your AI Has Amnesia and How to Fix It"


## Sources

- https://github.com/NousResearch/hermes-agent/issues/509
- https://blogs.oracle.com/developers/agent-memory-why-your-ai-has-amnesia-and-how-to-fix-it
