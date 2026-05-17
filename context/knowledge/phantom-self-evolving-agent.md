# phantom-self-evolving-agent

*Researched: 2026-04-01 22:51 CDT*

# Phantom — Self-Evolving AI Co-Worker Architecture

**Source:** [ghostwright/phantom](https://github.com/ghostwright/phantom) (★906, Apache 2.0, v0.18.2)

## Overview
Phantom gives an AI its own computer. It's a co-worker that runs on Slack, has its own email, creates its own tools, and builds infrastructure autonomously. Most importantly, it has a built-in **Evolution Engine** — the agent literally rewrites its own config files based on session observations.

## Architecture: Two Core Systems

### 1. Evolution Engine (`src/evolution/`)

**12 files, fully self-contained evolution pipeline:**

| File | Purpose |
|------|---------|
| `engine.ts` | Main orchestrator. Runs the full evolve cycle: observe → reflect → generate deltas → validate → apply |
| `config.ts` | YAML config with cadence intervals, gate thresholds, reflection model, judge settings |
| `reflection.ts` | Extracts observations from sessions using LLM judge (Sonnet) with regex fallback. Generates `ConfigDelta` proposals |
| `consolidation.ts` | Periodic grouping of observations, principle extraction, file compression. Runs every N sessions |
| `constitution.ts` | Immutable principles file. Pattern-matches proposed deltas against safety rules (no self-preservation, no hiding changes, etc.) |
| `validation.ts` | 5 validation gates: constitution, regression (golden suite), size, drift, safety |
| `application.ts` | Applies approved deltas (append/replace/remove) to config files atomically |
| `versioning.ts` | Git-like version tracking with parent chains and rollback support |
| `metrics.ts` | Tracks success_rate, correction_rate, session_count. Triggers auto-rollback if score drops below threshold |
| `golden-suite.ts` | Growing test suite of past successful interactions. Used as regression check |
| `judges/` | LLM-as-judge modules: quality-judge, observation-judge, constitution-judge, regression-judge, safety-judge, consolidation-judge |

**Evolution Cadence:**
- **Every session**: Extract observations (corrections, preferences, errors, successes)
- **Every 10 sessions**: Consolidation (group observations, extract principles, compress)
- **Every 50 sessions**: Full review (comprehensive re-evaluation)
- **Every 20 sessions**: Drift check (detect if agent behavior has drifted from constitution)

**Config Tiers:**
- `immutable`: Constitution file, meta/ — never auto-modified
- `constrained`: Role descriptions, behavior rules — modified with extra validation
- `free`: Working memory, preferences — freely modifiable

**Safety Gates (all must pass):**
1. Constitution gate — no safety/honesty/privacy/transparency violations
2. Regression gate — doesn't contradict golden suite lessons
3. Size gate — no file exceeds 200 lines
4. Drift gate — behavior stays within 0.7 similarity to baseline
5. Safety gate — LLM judge confirms no harmful changes

**Auto-Rollback:** If success rate drops below 0.1 over last 5 sessions, automatically reverts to previous version.

### 2. Memory System (`src/memory/`)

**11 files, Qdrant + Ollama embeddings architecture:**

| Store | Purpose | Vector Schema |
|-------|---------|---------------|
| **EpisodicStore** | Session memories with outcome tracking | Dual vectors (summary + detail) + BM25 sparse |
| **SemanticStore** | Subject-predicate-object facts with contradiction resolution | Single vector + BM25 |
| **ProceduralStore** | Learned procedures with trigger conditions, steps, success/failure counts | Single vector + BM25 |

**Ranking System (`ranking.ts`):**
- 4 recall strategies: similarity, temporal, metadata, recency (default)
- Recency half-life: 14 days (memories decay over time)
- Access saturation: logarithmic scaling based on access count
- Context threshold: 0.25 minimum score to include in prompt

**Context Builder (`context-builder.ts`):**
- Token budget management (facts → episodes → procedures priority)
- Facts get highest priority (accumulated knowledge)
- Episodes provide narrative context
- Procedures provide actionable patterns

**Embedding:** Local Ollama, 768-dim vectors, BM25 sparse vectors for hybrid search.

## Key Patterns for SOMA

1. **Constitution-Based Safety**: Phantom's immutable constitution prevents self-modification from going off-rails. SOMA needs this for medical safety — no hallucination-prone modifications.

2. **Observation Types**: `correction | preference | error | success | tool_pattern | domain_fact` — exactly the categories a medical agent needs. "Patient reported chest pain" = domain_fact, "Wrong drug interaction" = correction.

3. **Procedural Memory**: Stores learned procedures with success/failure counts. When SOMA learns a new medical workflow, it should track how often it succeeds.

4. **Contradiction Resolution**: SemanticStore detects when new facts contradict existing ones and resolves them. Critical for medical knowledge that evolves.

5. **Golden Test Suite**: Successful interactions get promoted to test cases. SOMA should promote correct medical interactions to regression tests.

6. **Auto-Rollback**: If the agent's success rate drops, revert to last known-good state. Essential for a medical agent.


## Sources

- https://github.com/ghostwright/phantom
