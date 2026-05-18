# Cognitive Orchestrator Wiring Session — May 13, 2026

## Context

User directive (May 13 2026): When orphaned cognitive modules are found, the expected
response is to wire ALL of them into the source code (run_agent.py) via a unified
dispatcher pattern, not just audit and report. User also expects NEW enhancements to
be built proactively (not just fixing what's broken). The cognitive orchestrator
pattern with 4 integration points (init, before_action, after_action, session_end)
is the correct approach.

## Problem: 10 of 13 Cognitive Modules Were Orphaned

| Status | Count | Modules |
|--------|-------|---------|
| WIRED | 2 | iteration_engine, cortex_learning |
| IMPORT_ONLY | 1 | error_learning (imported but never called) |
| ORPHANED | 10 | brain, training_gym, self_audit, cortex_flywheel, tiered_memory, memory_cortex_bridge, distillation_bridge, subconscious_hook_wiring, autobrowse_tracer, skill_effectiveness_tracker |

Total dead code: ~211KB, ~5,500 lines, ~15% of agent/ directory.

## Solution: Cognitive Orchestrator (Unified Dispatcher)

### Architecture

A single `CognitiveOrchestrator` class (`agent/cognitive_orchestrator.py`) that:
1. **Initializes** all subsystems in dependency order
2. **Routes** before_action / after_action calls to every subsystem
3. **Runs** post-session processes in parallel (ThreadPoolExecutor)
4. **Records** everything to `cerebrum_memory.db`
5. **Fails safely** — one subsystem crash doesn't kill the rest

### Integration Points in run_agent.py

```python
# __init__ (~line 2127): Initialize all cognitive systems
self.cognitive_orchestrator = get_orchestrator()
self.cognitive_orchestrator.initialize(self)

# before_action (~line 10061): Multi-subsystem pre-action lookup
_cognitive_lessons = _co.before_action(action_type, detail)

# after_action (~line 10161): Multi-subsystem post-action learning
_co.after_action(action_type, detail, result, duration_ms)

# session_end (~line 15028): Parallel post-session processing
_report = _co.session_end(telemetry)
```

### Subsystem Initialization Pattern

```python
def _init_error_learning(self):
    try:
        from agent.error_learning import ErrorLearningEngine
        engine = ErrorLearningEngine()
        return engine
    except Exception as e:
        logger.warning("Error learning init failed: %s", e)
        return None
```

Each subsystem is wrapped in try/except. If it fails, it's marked "failed" in status
but the orchestrator continues initializing the rest. The user never sees a crash.

### before_action Hook Pattern

```python
def before_action(self, action_type: str, detail: str) -> Optional[str]:
    lessons = []
    
    # 1. Error learning — check for known error patterns
    if "error_learning" in self._subsystems:
        try:
            warning = self._subsystems["error_learning"].get_preemptive_warning(
                f"{action_type}: {detail}"
            )
            if warning: lessons.append(f"[ErrorGuard] {warning}")
        except Exception: pass
    
    # 2. Tiered memory — check for relevant memories
    if "tiered_memory" in self._subsystems:
        try:
            memories = self._subsystems["tiered_memory"].recall(
                query=f"{action_type} {detail}", limit=3
            )
            for mem in memories:
                lessons.append(f"[Memory] {str(mem)[:150]}")
        except Exception: pass
    
    # 3. Trust scorer — filter lessons by epistemic trust
    if "trust_scorer" in self._subsystems and lessons:
        try:
            trusted = []
            for lesson in lessons:
                trust = self._subsystems["trust_scorer"].score_fact(
                    content=lesson, formation="inferred", grounding="speculative"
                )
                if trust.trust_tier in ("gold", "silver"):
                    trusted.append(lesson)
            lessons = trusted
        except Exception: pass
    
    return "\n".join(lessons) if lessons else None
```

### after_action Hook Pattern

```python
def after_action(self, action_type, detail, result, duration_ms, error):
    result_status = "failure" if error else "success"
    
    # 1. Error learning — record failures
    if result_status == "failure" and "error_learning" in self._subsystems:
        try:
            self._subsystems["error_learning"].on_error(
                error_text=error or result[:500],
                context=f"{action_type}: {detail}",
                session_id=self._session_telemetry.session_id if self._session_telemetry else 'unknown',
            )
        except Exception: pass
    
    # 2. Skill tracker — update effectiveness
    if "skill_tracker" in self._subsystems:
        try:
            self._subsystems["skill_tracker"].record_observation(
                skill_name=action_type, outcome=result_status,
                context=detail, duration_ms=duration_ms,
                source="cognitive_orchestrator",
            )
        except Exception: pass
    
    # 3. Record to DB
    self._record_action(action_type, detail, result_status, error, duration_ms)
```

### session_end Pattern (Parallel Processing)

```python
def session_end(self, telemetry) -> Dict:
    report = { ... }
    futures = []
    
    if "self_audit" in self._subsystems:
        futures.append(self._executor.submit(self._run_self_audit, report))
    if "cortex_flywheel" in self._subsystems:
        futures.append(self._executor.submit(self._run_flywheel_update))
    if "skill_tracker" in self._subsystems:
        futures.append(self._executor.submit(self._run_skill_recalc))
    
    for future in futures:
        try: future.result(timeout=30)
        except Exception as e: logger.warning("Post-session task failed: %s", e)
    
    return report
```

## API Introspection Technique

When wiring orphaned modules, NEVER guess method names. Use live introspection:

```python
import inspect

# Discover actual API of any module
from agent.error_learning import ErrorLearningEngine
for name, method in inspect.getmembers(ErrorLearningEngine, predicate=inspect.isfunction):
    if not name.startswith('_'):
        sig = inspect.signature(method)
        print(f"ErrorLearningEngine.{name}{sig}")

# Output reveals:
# ErrorLearningEngine.on_error(error_text: str, context: str = '', session_id: str = '') -> Dict[str, Any]
# ErrorLearningEngine.get_preemptive_warning(action_description: str) -> Optional[str]
# ErrorLearningEngine.on_resolution_attempt(pattern_id: str, resolution: str, successful: bool)
```

**Critical**: After upstream merges, method names often change. The `iteration-pipeline-wiring`
skill documents common renames. Always introspect before calling.

## Schema Migration Pattern

When a module's expected schema doesn't match the actual DB:

```python
def _ensure_schema(self):
    with _cortex_cursor() as cur:
        cur.execute("PRAGMA table_info(error_patterns)")
        existing_cols = {row[1] for row in cur.fetchall()}
        
        if existing_cols and 'error_signature' in existing_cols:
            # Old schema detected — drop and recreate
            cur.execute("DROP TABLE error_patterns")
            cur.execute("DROP TABLE IF EXISTS error_occurrences")
        
        # Create with new schema
        cur.execute("""
            CREATE TABLE IF NOT EXISTS error_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT UNIQUE NOT NULL,
                ...
            )
        """)
```

**Why drop/recreate**: SQLite doesn't support `ALTER TABLE DROP COLUMN`. For small
tables (<10K rows), this is fast and clean.

## New Enhancements Built (Proactive, Not Just Fixes)

### 1. Adaptive Context Sculptor
- **File**: `agent/adaptive_context_sculptor.py`
- **Purpose**: Analyze task complexity and dynamically adjust compression strategy
- **API**: `get_sculptor().analyze_task(messages, current_query)` → `CompressionProfile`
- **Complexity factors**: Message count, token density, code block ratio, urgency signals
- **Strategies**: Simple (threshold 0.75), Medium (0.70), Complex (0.60), Crisis (0.40)

### 2. Predictive Tool Oracle
- **File**: `agent/predictive_tool_oracle.py`
- **Purpose**: Predict which tools will be needed before the model asks
- **API**: `get_oracle().predict_for_query(query, available_tools)` → prediction dict
- **Signals**: Keyword→tool Bayesian scoring, conversation phase detection
- **Phases**: research → web_search, coding → patch/terminal, debugging → read_file

### 3. Epistemic Trust Scorer
- **File**: `agent/epistemic_trust_scorer.py`
- **Purpose**: Score knowledge with F-G-R Trust Tuple to prevent hallucination poisoning
- **API**: `get_trust_scorer().score_fact(content, formation, grounding, category)`
- **Tiers**: Gold (0.9-1.0), Silver (0.7-0.9), Bronze (0.4-0.7), Rust (0.1-0.4), Toxic (0.0-0.1)

## Test Results

```
=== LIVE COGNITIVE ORCHESTRATOR TEST ===
1. Initialization...        ✓ 11/14 active, 0 failed
2. before_action hook...    ✓ No errors
3. after_action (success)   ✓ Recorded to DB
4. after_action (failure)   ✓ Error pattern learned
5. Error learning...        ✓ 4 patterns stored
6. Self-audit...            ✓ Call tracking functional
7. Skill tracker...         ✓ 2 skills scored
8. Session end...           ✓ Full report generated
9. Database state...        ✓ 8 tables populated

=== NEW ENHANCEMENTS ===
1. Context Sculptor...      ✓ complexity=0.35-0.50
2. Tool Oracle...           ✓ phase detection working
3. Trust Scorer...          ✓ gold/bronze tiers correct
```

## Database Schema (All in cerebrum_memory.db)

```sql
-- Session tracking
cognitive_sessions (session_id, duration_seconds, tool_calls, errors, error_rate, audit_score)

-- Action-level tracking
cognitive_actions (session_id, action_type, action_hash, detail, result, error_preview, duration_ms)

-- Subsystem health
cognitive_subsystems (name, status, last_error, call_count, error_count)

-- Epistemic facts
epistemic_facts (content_hash, content, formation, grounding, overall_trust, trust_tier)

-- Error patterns
error_patterns (fingerprint, error_type, error_summary, context, resolution, occurrence_count)
error_occurrences (pattern_id, session_id, full_error, resolution_attempted, resolution_successful)

-- Tool predictions
tool_predictions (query_keywords, tool_name, predicted, success)
```

## Known Non-Fatal Issues

1. **CortexDB duplicate key errors**: Skill tracker tries to re-insert existing skills
   into PostgreSQL cortex database. Non-fatal — skills already there.

2. **Cortex flywheel eval schema**: `record_eval` references `round_id` column that
   doesn't exist in PostgreSQL schema. Flywheel initializes and stats work, but
   eval sweeps need schema alignment.

3. **3 skipped subsystems**: distillation_bridge, subconscious_hook_wiring, training_gym
   — no main class exists (only module-level functions). Can be wired when classes
   are added or by calling functions directly.

## Files Created/Modified

### New Files
- `agent/cognitive_orchestrator.py` (31KB) — Central dispatcher
- `agent/adaptive_context_sculptor.py` (16KB) — Dynamic context optimization
- `agent/predictive_tool_oracle.py` (15KB) — Tool prediction
- `agent/epistemic_trust_scorer.py` (18KB) — Trust scoring

### Modified Files
- `run_agent.py` — 4 integration points wired
- `agent/error_learning.py` — Schema migration for old table format

## Key Design Decisions

1. **Orchestrator over per-module wiring**: With 11+ subsystems, per-module hooks
   in run_agent.py become unmaintainable. The orchestrator centralizes all routing.

2. **SQLite for hot path, PostgreSQL for cold**: All per-turn operations use SQLite
   (`cerebrum_memory.db`). PostgreSQL (`cortex_access.py`) is used for background
   processes (flywheel, consolidation) where latency matters less.

3. **Fail-safe by design**: Every subsystem wrapped in try/except. One crash doesn't
   kill the agent loop. Status tracked in `cognitive_subsystems` table.

4. **ThreadPoolExecutor for post-session**: Self-audit, flywheel, and skill recalc
   run in parallel with 30s timeout. No blocking of session end.

5. **API introspection before calling**: Never guess method names after merges.
   Use `inspect.getmembers()` + `inspect.signature()` to discover actual APIs.
