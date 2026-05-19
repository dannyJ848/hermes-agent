# epistemic-trust-scoring-fpf-framework

*Researched: 2026-04-05 04:28 CDT*

# First Principles Framework (FPF) for Epistemic Trust Scoring in AI Agents

**Source:** "AI-Assisted Engineering Should Track the Epistemic Status and Temporal Validity of Architectural Decisions" (arXiv 2601.21116, Gilda & Gilda 2026)

## Key Concepts for Cerebrum Integration

### 1. The F-G-R Trust Tuple
Every memory/claim gets scored on three axes:
- **F (Formation)**: How was this knowledge formed? (direct observation=high, inferred=medium, hallucinated/assumed=low)
- **G (Grounding)**: Is it grounded in verifiable evidence? (empirical=high, theoretical=medium, none=low)
- **R (Reliability)**: How often has this claim been validated in practice? (tested=high, untested=low)

### 2. Evidence Decay and Temporal Validity
- Evidence has a half-life — it becomes stale over time
- 20-25% of architectural decisions had stale evidence within 2 months (retrospective audit)
- Automated decay tracking surfaces stale assumptions before failures
- **Key for Cerebrum:** Every semantic fact should have a `last_verified` timestamp and a decay function

### 3. Conservative Assurance Aggregation (Gödel t-norm)
- When combining multiple evidence sources, use **minimum** trust score (not average)
- Prevents weak evidence from inflating confidence
- More conservative than averaging — "a chain is only as strong as its weakest link"

### 4. Epistemic Layers
Separate knowledge into layers:
- **Layer 0**: Unverified hypotheses (LLM suggestions without testing)
- **Layer 1**: Anecdotal evidence (worked once, in one context)
- **Layer 2**: Corroborated evidence (worked in multiple contexts)
- **Layer 3**: Empirically validated (tested with benchmarks/tests)

### 5. Application to Cerebrum Memory
- Each semantic fact in `cerebrum_memory.db` should have F, G, R scores (0.0-1.0)
- Aggregate trust = min(F, G, R) — conservative Gödel t-norm
- Facts decay over time: trust *= decay_factor^(days_since_verification)
- Periodic epistemic audit: surface facts below trust threshold for re-verification
- When a fact is used and confirmed, boost its R (reliability) score

### 6. The ADI Reasoning Cycle
- **A**ssert: Make a claim or store a fact
- **D**iscriminate: Classify its epistemic status (which layer?)
- **I**ntegrate: Aggregate with existing knowledge using conservative operator

## NeurIPS 2025 Complement: Knowledge Scaffolds for Agentic AI
Sebastián Ferrada's NeurIPS 2025 talk argues that structured knowledge (knowledge graphs) provide the scaffolding agents need for grounding, memory, and evolving understanding. GraphRAG + knowledge engineering complement LLMs rather than compete with them. Key challenges: scalable graph+vector systems, evaluation of grounded agents, multimodal schema design.

## Action Items for Cerebrum
1. Add F/G/R columns to `semantic_memory` table
2. Implement decay function in `self_awareness.py`
3. Wire epistemic audit into controller cron (weekly)
4. Use min-aggregation when multiple sources contribute to a fact


## Sources

- https://arxiv.org/html/2601.21116v1
- https://neurips.cc/virtual/2025/136264
