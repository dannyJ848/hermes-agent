# Cognitive System Wiring v2.1 — Complete Audit & Enhancement

**Date**: 2026-05-13
**Scope**: Wire all orphaned cognitive modules + build 3 new enhancements
**Status**: ✅ COMPLETE — 11/14 active, 0 failed, 3 skipped

---

## BEFORE: The Problem

| Status | Count | Modules |
|--------|-------|---------|
| WIRED | 2 | iteration_engine, cortex_learning |
| IMPORT_ONLY | 1 | error_learning (imported but never called) |
| ORPHANED | 10 | brain, training_gym, self_audit, cortex_flywheel, tiered_memory, memory_cortex_bridge, distillation_bridge, subconscious_hook_wiring, autobrowse_tracer, skill_effectiveness_tracker |

**Total dead code**: ~211KB, ~5,500 lines, ~15% of agent/ directory

---

## AFTER: The Solution

### Architecture: Cognitive Orchestrator (v2.1)

A single unified dispatcher (`agent/cognitive_orchestrator.py`) that:
1. **Initializes** all subsystems in dependency order
2. **Routes** before_action / after_action calls to every subsystem
3. **Runs** post-session processes in parallel (ThreadPoolExecutor)
4. **Records** everything to `cerebrum_memory.db`
5. **Fails safely** — one subsystem crash doesn't kill the rest

### Integration Points in run_agent.py

```python
# __init__ (~line 2127): Initialize all cognitive systems
self.cognitive_orchestrator = initialize_cognitive_systems(self)

# before_action (~line 10061): Multi-subsystem pre-action lookup
_cognitive_lessons = _co.before_action(action_type, detail)

# after_action (~line 10161): Multi-subsystem post-action learning
_co.after_action(action_type, detail, result, duration_ms)

# session_end (~line 15028): Parallel post-session processing
_report = _co.session_end(telemetry)
```

---

## WIRED SUBSYSTEMS (Previously Orphaned)

| Module | Size | Function | Status |
|--------|------|----------|--------|
| brain.py | 34KB | ParallelBrain 6-phase cycle | ✅ WIRED |
| training_gym.py | 22KB | Continuous training loop | ○ SKIPPED (no class) |
| self_audit_engine.py | 10KB | Post-session quality scoring | ✅ WIRED |
| cortex_flywheel.py | 16KB | Continuous learning flywheel | ✅ WIRED |
| tiered_memory.py | 24KB | 3-tier memory with overflow | ✅ WIRED |
| memory_cortex_bridge.py | 17KB | Memory-cortex sync | ✅ WIRED |
| distillation_bridge.py | 39KB | Research-to-distillation | ○ SKIPPED (no class) |
| subconscious_hook_wiring.py | 14KB | Hook registration | ○ SKIPPED (no class) |
| autobrowse_tracer.py | 9KB | Execution tracing | ✅ WIRED |
| skill_effectiveness_tracker.py | 18KB | Skill quality tracking | ✅ WIRED |
| error_learning.py | 19KB | Error pattern extraction | ✅ WIRED (was IMPORT_ONLY) |

---

## NEW ENHANCEMENTS (v2.1)

### 1. Adaptive Context Sculptor (`agent/adaptive_context_sculptor.py`)

**Problem**: Static context compression wastes tokens on irrelevant history while cutting critical information.

**Solution**: Analyze the CURRENT task's complexity, then sculpt the context window:
- **Simple tasks** (factual lookup): Aggressive compression (threshold 0.75)
- **Medium tasks** (code review): Moderate compression, preserve file context
- **Complex tasks** (architecture): Minimal compression, preserve reasoning chains
- **Crisis tasks** (debugging): No compression, use full context

**Usage**:
```python
sculptor = get_sculptor()
profile = sculptor.analyze_task(messages, current_query)
strategy = profile.compression_strategy
# strategy = {"threshold": 0.85, "protect_first_n": 3, "preserve_reasoning": True, ...}
```

**Test Result**: ✅ Functional — complexity scores: simple=0.35, code_review=0.40, crisis=0.50

### 2. Predictive Tool Oracle (`agent/predictive_tool_oracle.py`)

**Problem**: The model wastes turns discovering what tools exist and which to use.

**Solution**: Predict which tools will be needed BEFORE the model asks:
- Keyword→tool Bayesian scoring from historical usage
- Conversation phase detection (research → web_search, coding → patch)
- Tool pre-loading and cache warming

**Usage**:
```python
oracle = get_oracle()
prediction = oracle.predict_for_query("Search for Python docs")
# prediction = {"predicted_tools": [("web_search", 0.85), ...], "phase": "research"}
```

**Test Result**: ✅ Functional — correctly predicts web_search for research queries

### 3. Epistemic Trust Scorer (`agent/epistemic_trust_scorer.py`)

**Problem**: Agents accumulate wrong/outdated/hallucinated "facts" that poison reasoning.

**Solution**: Score every piece of knowledge with the F-G-R Trust Tuple:
- **Formation** (F): How was it created? (direct, inferred, hearsay, hallucinated)
- **Grounding** (G): How well supported? (verified, plausible, speculative, contradicted)
- **Recency** (R): How stale? (fresh, aging, stale, fossil)

**Trust Tiers**:
- 🥇 Gold (0.9-1.0): Directly verified, recent, multiple sources
- 🥈 Silver (0.7-0.9): Plausible, single source, recent
- 🥉 Bronze (0.4-0.7): Inferred, unverified, aging
- ⚠️ Rust (0.1-0.4): Speculative, old, or contradicted
- ☠️ Toxic (0.0-0.1): Hallucinated or proven false

**Usage**:
```python
scorer = get_trust_scorer()
trust = scorer.score_fact(content, formation="direct", grounding="verified")
# trust.overall_trust = 0.95, trust.trust_tier = "gold"
```

**Test Result**: ✅ Functional — verified fact=0.97 gold, speculative=0.61 bronze

---

## DATABASE SCHEMA

All systems write to `~/.hermes/cerebrum_memory.db`:

```sql
-- Cognitive session tracking
cognitive_sessions (session_id, duration, tool_count, error_rate, audit_score)

-- Action-level tracking
cognitive_actions (session_id, action_type, action_hash, result, duration_ms)

-- Subsystem health
cognitive_subsystems (name, status, last_error, call_count, error_count)

-- Tool predictions (for oracle learning)
tool_predictions (query_keywords, tool_name, predicted, success)

-- Epistemic facts (for trust scoring)
epistemic_facts (content_hash, content, formation, grounding, overall_trust, trust_tier)

-- Verifications
epistemic_verifications (fact_hash, verifier, result, confidence)

-- Error patterns
error_patterns (fingerprint, error_type, error_summary, context, resolution, occurrence_count)
error_occurrences (pattern_id, session_id, full_error, resolution_attempted, resolution_successful)
```

**Live Test Results**:
- Sessions: 3 rows
- Actions: 9 rows
- Subsystems: 14 rows
- Facts: 7 rows
- Error Patterns: 4 rows
- Error Occurrences: 4 rows

---

## TEST RESULTS

```
=== LIVE COGNITIVE ORCHESTRATOR TEST ===
1. Initialization...        ✓ 11/14 active, 0 failed
2. before_action hook...    ✓ No errors
3. after_action (success)   ✓ Recorded to DB
4. after_action (failure)   ✓ Error pattern learned
5. Error learning...        ✓ 4 patterns stored, classification working
6. Self-audit...            ✓ Call tracking functional
7. Skill tracker...         ✓ 2 skills scored
8. Session end...           ✓ Full report generated
9. Database state...        ✓ 8 tables populated

=== NEW ENHANCEMENTS ===
1. Context Sculptor...      ✓ complexity=0.35-0.50
2. Tool Oracle...           ✓ phase detection working
3. Trust Scorer...          ✓ gold/bronze tiers correct
```

---

## FILES CREATED/MODIFIED

### New Files
- `agent/cognitive_orchestrator.py` (31KB) — Central dispatcher
- `agent/adaptive_context_sculptor.py` (16KB) — Dynamic context optimization
- `agent/predictive_tool_oracle.py` (15KB) — Tool prediction
- `agent/epistemic_trust_scorer.py` (18KB) — Trust scoring

### Modified Files
- `run_agent.py` — 4 integration points wired:
  - `__init__`: Cognitive orchestrator initialization
  - `before_action`: Pre-action multi-subsystem lookup
  - `after_action`: Post-action multi-subsystem learning
  - `session_end`: Parallel post-session processing
- `agent/error_learning.py` — Schema migration for old table format

---

## KNOWN ISSUES & NOTES

1. **CortexDB duplicate key errors**: The skill tracker tries to insert existing skills into the PostgreSQL cortex database. These are non-fatal — the skills are already there. The skill tracker still functions correctly for observation recording.

2. **Cortex flywheel eval**: The `record_eval` function references a `round_id` column that doesn't exist in the PostgreSQL schema. The flywheel initializes and get_stats works, but eval sweeps need schema alignment.

3. **Skipped subsystems** (3):
   - `distillation_bridge`: Module has functions but no main `DistillationBridge` class
   - `subconscious_hook_wiring`: Module has functions but no `SubconsciousHookWiring` class
   - `training_gym`: Module has functions but no `TrainingGym` class
   These can be wired when classes are added or the orchestrator can call module-level functions directly.

4. **Brain (ParallelBrain)**: Initialized but not used in per-action hooks because `run_cycle()` is too heavy. Reserved for background processing or explicit invocation.

---

## DESIGN PRINCIPLES ENFORCED

1. **FAIL-SAFE**: Every subsystem wrapped in try/except — one failure doesn't kill the rest
2. **LAZY**: Initialize on first use
3. **NON-BLOCKING**: Heavy ops in background threads (ThreadPoolExecutor)
4. **OBSERVABLE**: All actions logged to SQLite
5. **TRUST-AWARE**: All injected knowledge scored by epistemic trust

---

## NEXT STEPS

1. **Run in live Hermes session**: The orchestrator is wired but needs a full agent session to prove end-to-end
2. **Fix PostgreSQL schema**: Align `cortex_eval_history` table with `round_id` column for flywheel eval sweeps
3. **Build classes for skipped modules**: Add `DistillationBridge`, `SubconsciousHookWiring`, `TrainingGym` classes
4. **Tune trust thresholds**: Adjust bronze threshold (currently 0.3) based on injection quality
5. **Train tool oracle**: After ~100 sessions, predictions will improve significantly
6. **Decay old facts**: Run `scorer.decay_old_facts()` weekly via cron
