---
name: epistemic-trust-scoring
version: 2.0
description: Score memory facts using F-G-R Trust Tuple (Formation, Grounding, Recency) with conservative Gödel t-norm aggregation and verification-count boost. Prevents cascading hallucination and detects stale knowledge.
trigger: When storing new facts, auditing memory quality, or checking if stored knowledge is trustworthy.
---

# Epistemic Trust Scoring

## Module Location
`~/subconscious/epistemic_trust.py`

## F-G-R Trust Tuple
Every fact is scored on three axes:
- **F (Formation)**: How was it created? (observation=0.95, web_research=0.80, delegation=0.60, inference=0.50)
- **G (Grounding)**: What evidence supports it? (primary_source=0.95, empirical_test=0.90, no_source=0.10)
- **R (Recency)**: When was it last verified? Decays with 30-day half-life.

## Aggregation: Gödel T-Norm (Min) + Verification Boost
**Trust = min(F_score, effective_G, decay_factor)**

Where `effective_G = min(G_score + 0.05 × verification_count, 0.95)`

Conservative by design — weak evidence CANNOT inflate overall trust. But facts independently verified multiple times get a grounding boost (capped at +0.30), reflecting that repeated confirmation from different sources increases reliability. This is based on Google DeepMind's March 2026 framework for trustworthy epistemic agents (arXiv:2603.02960).

## CLI Usage
```bash
# Check overall stats
python3 ~/subconscious/epistemic_trust.py stats

# Find stale facts needing re-verification
python3 ~/subconscious/epistemic_trust.py stale
python3 ~/subconscious/epistemic_trust.py stale 0.50  # custom threshold

# Add a new fact
python3 ~/subconscious/epistemic_trust.py add "content here" formation_type grounding_type
```

## Formation Types
| Type | Score | Use When |
|------|-------|----------|
| direct_observation | 0.95 | Terminal output, file read verified |
| web_research | 0.80 | Extracted from web with URL |
| user_stated | 0.90 | Danny explicitly said it |
| delegation | 0.60 | Sub-agent produced, not verified |
| inference | 0.50 | LLM reasoning, no source |

## Grounding Types
| Type | Score | Use When |
|------|-------|----------|
| primary_source | 0.95 | Official docs, peer-reviewed paper |
| empirical_test | 0.90 | Verified via execution |
| multiple_sources | 0.95 | 2+ independent confirmations |
| secondary_source | 0.75 | Blog, tutorial |
| tertiary_source | 0.50 | Reddit, forum |
| no_source | 0.10 | No evidence |

## Staleness Threshold
- Trust < 0.40 → needs re-verification
- Decay half-life: 30 days (configurable per fact)
- After 30 days unaccessed: trust drops by 50%
- After 60 days: trust drops by 75%

## Verification Count
- Each `reverify_fact()` call auto-increments `verification_count`
- Each verification adds +0.05 to effective grounding (max boost: +0.30)
- Facts confirmed by 2+ independent sources should start with `verification_count=2`
- This implements the "multi-source confirmation" principle from epistemic trust research

## DB Migration
The module auto-migrates: if `verification_count` column is missing from the table, `ensure_table()` adds it via ALTER TABLE. No manual migration needed.

## Advanced Features (from March 2026 epistemic trust research)

### Canonical Flag
High-confidence facts (trust > 0.85, verified 3+ times) can be marked `canonical=true`.
Canonical facts resist decay (half-life extended to 90 days instead of 30) and survive
epistemic-memory-cleanup purges. Use for: core project architecture decisions, verified
API behaviors, stable mathematical/scientific facts.

### Falsifiability Score (0-1)
Every fact should have a `falsifiable` field:
- `1.0` = Can be verified against a specific source or test right now
- `0.5` = Theoretically verifiable but would require significant effort
- `0.0` = Unfalsifiable (subjective opinion, aesthetic judgment)

Low falsifiability + high trust = red flag. Unfalsifiable "facts" should be tagged as
opinions or hypotheses, not knowledge.

### Provenance Chain
Track the origin of every fact:
- `source_agent`: Who/what produced it (evey, danny, delegation:model_name, web:url)
- `source_chain`: Array of intermediate sources if derived from other facts
- `revision_count`: How many times this fact has been corrected (0 = original)

High revision_count suggests the fact is in an active area of uncertainty — treat with
appropriate epistemic humility.

## Integration Points
- Store in `cerebrum_memory.db` → `epistemic_facts` table
- Wire into `pre_llm_call` hook to flag low-trust facts before injection
- Use in `epistemic-memory-cleanup` skill to prioritize purging
- When saving research findings via `save_finding`, also store as epistemic fact for trust tracking
- Use canonical flag for architecture decisions and stable scientific facts
- Cross-reference falsifiability before promoting facts to semantic memory
