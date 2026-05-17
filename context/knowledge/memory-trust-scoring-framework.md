# memory-trust-scoring-framework

*Researched: 2026-04-05 04:16 CDT*

# Memory Trust Scoring: Beyond Retrieval Accuracy

## Source
"What Memory Benchmarks Don't Test" — Andrew Estey-Ang (March 2026), pith.run

## Key Insight
Current memory benchmarks (LoCoMo, MemoryArena) only measure retrieval accuracy — whether the system surfaces the right memory. They don't measure **epistemic trustworthiness**: what happens when the system retrieves wrong, stale, or contradictory information.

## 3 Critical Failure Modes

### 1. Confident Retrieval of Stale Beliefs
- Memory retrieved in session 3 with same confidence in session 47, despite contradicting evidence
- No staleness decay — confidence doesn't track age or corroboration
- **Fix needed:** Confidence scores that decay without recency/corroboration updates

### 2. Simultaneous Contradictory Beliefs
- "Deadline is Q3" → later "Deadline moved to Q2" — both stored, both returned
- System returns by highest cosine similarity, not recency or supersession
- **Fix needed:** Contradiction detection + supersession chains (old belief demoted, linked to replacement)

### 3. No Confidence Signal for Consuming Agent
- Cosine similarity = retrieval signal, NOT epistemic trust signal
- High similarity ≠ high trustworthiness (could be unverified, conflicted, single-observation)
- **Fix needed:** Separate retrieval scores from epistemic confidence scores

## Proposed Evaluation Dimensions (Beyond LoCoMo)

| Dimension | What it tests | Current coverage |
|-----------|--------------|-----------------|
| Retrieval accuracy | Surface right memory | ✓ LoCoMo |
| Staleness decay | Confidence decreases without corroboration | ✗ |
| Contradiction detection | Flag conflicting beliefs | ✗ |
| Supersession chains | Old belief demoted, linked to replacement | ✗ |
| Confidence calibration | Scores correlate with factual accuracy | ~ MemGPT partial |
| Cold-start quality | New session context relevance | ~ MemoryArena partial |
| Irrelevant decay | Low-relevance memories fade | ✗ |

## Application to Cerebrum
- Cerebrum's semantic tier already has access frequency tracking
- Missing: **staleness decay** (time since last corroboration), **contradiction detection** (conflicting semantic facts), **supersession chains** (linking updated beliefs)
- Trust score should factor: recency × corroboration count × consistency with other beliefs / staleness
- This directly maps to the MEMORY domain focus on "grounding" and "trust scoring"


## Sources

- https://dev.to/esteyang/what-memory-benchmarks-dont-test-h9c
