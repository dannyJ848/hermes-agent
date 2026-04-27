# KIMI HARNESS ENHANCEMENT MANIFEST v2.0
## Self-Improving Adaptive Context Injection

**Date:** 2026-04-26
**Status:** DEPLOYED

---

## WHAT CHANGED FROM v1.0

v1.0 was static — it scored relevance once and never learned.
v2.0 is **self-improving** — it tracks what was useful and learns from it.

---

## ARCHITECTURE

### Layer 1: Adaptive Injection (v1.0 — unchanged)
- Relevance scoring via TF-IDF
- Budget enforcement
- Pressure-aware reduction

### Layer 2: Cortex Learning (NEW)
- PostgreSQL-backed learning store
- `usefulness_score` column on `memory_units`
- `memory_usage_log` table for event tracking
- Bayesian score updates after each session

### Layer 3: Feedback Loop (NEW)
- Tracks which memories/skills were injected per turn
- At session end, analyzes which were actually useful
- Updates Cortex scores for next time
- Scores compound over time — the system gets smarter

---

## SCHEMA CHANGES

Added to `memory_units`:
- `usefulness_score FLOAT DEFAULT 0.5`
- `success_count INTEGER DEFAULT 0`
- `failure_count INTEGER DEFAULT 0`
- `last_accessed TIMESTAMP`
- `usage_contexts JSONB DEFAULT '[]'`

New table `memory_usage_log`:
- `id UUID PRIMARY KEY`
- `memory_id UUID REFERENCES memory_units`
- `session_id TEXT`
- `action TEXT` (injected, referenced, loaded, followed, evaluated)
- `was_useful BOOLEAN`
- `query_context TEXT`
- `timestamp TIMESTAMP`
- `metadata JSONB`

---

## FILES

### New
- `agent/cortex_learning.py` — Learning engine with Cortex integration

### Modified
- `agent/adaptive_injection.py` — Added Cortex learned score boost to filtering
- `run_agent.py` — Added injection tracking + session-end feedback loop
- `agent/context_compressor.py` — Added pressure detection (from v1.0)

---

## HOW IT LEARNS

1. **During conversation**: Every turn, the system tracks which memories and skills were injected into the system prompt

2. **At session end** (`commit_memory_session` or compression):
   - Collects all injected items from the session
   - Analyzes assistant output to infer which were referenced
   - Calls `CortexLearningEngine.process_session_feedback()`
   - Updates `success_count`, `failure_count`, `usefulness_score` in PostgreSQL

3. **Next session**: When filtering memories/skills, the system queries Cortex for learned scores and boosts items that were historically useful

4. **Compounding**: Over many sessions, frequently-useful items get higher scores and are injected more often; useless items get filtered out

---

## EXPECTED EVOLUTION

| Session # | Behavior |
|-----------|----------|
| 1-5 | Mostly TF-IDF scoring, little learned data |
| 6-20 | Learned scores start influencing selection |
| 21-50 | Strong preferences emerge — "DGX Spark" queries always get deployment memory |
| 50+ | Near-optimal injection — only the most relevant 2-3 memories per query |

---

## FUTURE ENHANCEMENTS

1. **Semantic embeddings** — Replace TF-IDF with sentence-transformers for better relevance
2. **User feedback** — Add explicit thumbs up/down on injected items
3. **Cross-session context** — Remember what the user was working on last session
4. **Predictive pre-fetch** — Load likely-needed memories before the user asks
5. **Skill auto-discovery** — Detect when a new skill would have been useful and suggest installing it

---

## TESTING

```python
from agent.cortex_learning import get_learning_engine
engine = get_learning_engine()

# Check what the system has learned
report = engine.get_learning_report()
print(f"Success rate: {report['success_rate']}")

# Predict what's relevant to a query
memories = engine.predict_relevant_memories("DGX Spark training", limit=5)
for m in memories:
    print(f"{m['combined_score']:.4f} | {m['text'][:60]}...")
```

---

## ROLLBACK

To disable learning, set `use_cortex_learning=False` in `filter_memory_entries()` and `filter_skills()` in `agent/adaptive_injection.py`.
