---
name: agent-cognitive-infrastructure
version: 1.1.0
description: >
  Build subconscious cognitive systems for AI agents — memory bridges, error miners,
  tool routers, context guards, and intelligence trackers. The complete pattern for
  creating self-improving agent infrastructure that prevents failures before they happen.
trigger: >
  Use when building or improving agent self-improvement systems, cognitive overlays,
  subconscious loops, or any infrastructure that makes the agent smarter about its own
  tool usage, memory management, error recovery, or context handling.
category: meta
---

# Agent Cognitive Infrastructure

## Overview

Build systems that make the agent self-correcting and self-optimizing. These systems
run "below" the main agent loop — intercepting tool calls, monitoring performance,
and routing around failures before they happen.

## Core Philosophy

1. **Prevent failures, don't just recover from them** — Route around weak tools BEFORE calling
2. **Fail-open** — Enhancement errors must never block core functionality
3. **Observe before acting** — Track tool performance, then optimize based on data
4. **Compress before overflow** — Manage context proactively, not reactively
5. **Preserve continuity** — Save session state before context window death

## Architectural Patterns

### Pattern A: Per-Module Hook Wiring (Legacy)
Each cognitive module wires itself independently into `run_agent.py`:
```python
# In run_agent.py — before_action:
try:
    from agent.error_learning import get_error_engine
    warning = get_error_engine().get_preemptive_warning(action_type)
except Exception:
    pass

try:
    from agent.tiered_memory import get_memory
    memories = get_memory().recall(query, limit=3)
except Exception:
    pass

# Problem: N modules = N try/except blocks, scattered across run_agent.py
# Problem: Adding a new module requires editing run_agent.py again
# Problem: No centralized health monitoring
```

### Pattern B: Cognitive Orchestrator (Recommended — May 2026)
A single unified dispatcher initializes all subsystems and routes hooks:

```python
# agent/cognitive_orchestrator.py
class CognitiveOrchestrator:
    """Unified dispatcher for all cognitive subsystems."""
    
    def __init__(self):
        self._subsystems: Dict[str, Any] = {}
        self._subsystem_status: Dict[str, str] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._db_path = Path.home() / ".hermes" / "cerebrum_memory.db"
    
    def initialize(self, agent) -> Dict[str, str]:
        """Initialize all subsystems in dependency order."""
        # Each subsystem wrapped in try/except — one failure doesn't kill the rest
        self._subsystems["error_learning"] = self._init_error_learning()
        self._subsystems["tiered_memory"] = self._init_tiered_memory()
        # ... etc
        return self._subsystem_status
    
    def before_action(self, action_type: str, detail: str) -> Optional[str]:
        """Called before EVERY tool execution. Returns injected lessons."""
        lessons = []
        
        # 1. Error learning — check for known error patterns
        if "error_learning" in self._subsystems:
            warning = self._subsystems["error_learning"].get_preemptive_warning(...)
            if warning: lessons.append(f"[ErrorGuard] {warning}")
        
        # 2. Tiered memory — check for relevant memories
        if "tiered_memory" in self._subsystems:
            memories = self._subsystems["tiered_memory"].recall(...)
            for mem in memories: lessons.append(f"[Memory] {mem}")
        
        # 3. Skill tracker — suggest effective skills
        if "skill_tracker" in self._subsystems:
            self._subsystems["skill_tracker"].record_observation(...)
        
        # 4. Trust scorer — filter lessons by epistemic trust
        if "trust_scorer" in self._subsystems and lessons:
            trusted = [l for l in lessons 
                       if self._subsystems["trust_scorer"].score_fact(l, ...).trust_tier in ("gold", "silver")]
            lessons = trusted
        
        return "\n".join(lessons) if lessons else None
    
    def after_action(self, action_type, detail, result, duration_ms, error):
        """Called after EVERY tool execution."""
        # 1. Error learning — record failures
        if error and "error_learning" in self._subsystems:
            self._subsystems["error_learning"].on_error(error, context, session_id)
        
        # 2. Skill tracker — update effectiveness
        if "skill_tracker" in self._subsystems:
            self._subsystems["skill_tracker"].record_observation(..., outcome=result_status)
        
        # 3. Self-audit — track call quality
        if "self_audit" in self._subsystems:
            self._subsystems["self_audit"].record_call(tool_name, args, result_status, ...)
        
        # 4. Record to DB
        self._record_action(action_type, detail, result_status, error, duration_ms)
    
    def session_end(self, telemetry) -> Dict:
        """Called at session end. Runs post-session processes in parallel."""
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

**Why the orchestrator pattern wins:**
- **Single point of control** — add a new subsystem by adding one line to `initialize()`
- **Fail-safe by design** — each subsystem wrapped in try/except, crash of one doesn't kill others
- **Centralized health** — `get_orchestrator().get_status()` returns health of all subsystems
- **Non-blocking post-session** — ThreadPoolExecutor runs audits/flywheels in background
- **Clean run_agent.py** — only 4 integration points instead of N scattered hooks

**Integration points in run_agent.py:**
```python
# __init__: Initialize all cognitive systems
self.cognitive_orchestrator = get_orchestrator()
self.cognitive_orchestrator.initialize(self)

# before_action: Multi-subsystem pre-action lookup
_cognitive_lessons = _co.before_action(action_type, detail)

# after_action: Multi-subsystem post-action learning
_co.after_action(action_type, detail, result, duration_ms)

# session_end: Parallel post-session processing
_report = _co.session_end(telemetry)
```

## 5-Phase Build Pattern

### Phase 1: AUDIT
Analyze the current codebase for gaps:
- Check hook points in `hermes_cli/plugins.py` (pre_tool_call, post_tool_call, pre_llm_call)
- Check tool registry for weak tools (success rate < 50%)
- Check memory pressure (current size vs limit)
- Check context window usage (current tokens vs limit)
- Check error patterns in recent sessions

### Phase 2: BUILD
Create the system module in `hermes_cli/subconscious/`:
```python
#!/usr/bin/env python3
"""Module description."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("hermes.subconscious.<module>")

class SystemName:
    """Core system class."""
    
    def __init__(self):
        self.stats = {}
    
    def main_method(self, input_data) -> Dict:
        """Process input and return result."""
        try:
            # Core logic
            return {"status": "success", "data": result}
        except Exception as e:
            logger.debug("Error (fail-open): %s", e)
            return {"status": "error", "error": str(e)}

# Hook function for integration
def hook_function(*args, **kwargs):
    """Hook to integrate into agent loop."""
    system = SystemName()
    return system.main_method(*args, **kwargs)
```

**Requirements**:
- Clear API with type hints
- Hook functions for each integration point
- Fail-open design (try/except with pass or safe default)
- Lazy imports to avoid circular dependencies
- Self-contained (works standalone and in combination)

### Phase 3: TEST
Verify with execute_code before committing:
```python
import sys
sys.path.insert(0, '/path/to/hermes_cli/subconscious')

from module_name import SystemName, hook_function

# Test 1: Happy path
result = system.main_method(test_input)
assert result['status'] == 'success'

# Test 2: Error handling
result = system.main_method(bad_input)
assert result['status'] == 'error'  # Or graceful fallback

# Test 3: Edge cases
result = system.main_method(empty_input)
result = system.main_method(large_input)
```

### Phase 4: WIRE
**For orchestrator pattern**: Add subsystem to `CognitiveOrchestrator.initialize()`:
```python
def _init_my_system(self):
    try:
        from agent.my_system import MySystem
        system = MySystem()
        # Quick health check
        system.health_check()
        return system
    except Exception as e:
        logger.warning("MySystem init failed: %s", e)
        return None
```

**For legacy per-module wiring**:
```python
try:
    from subconscious.module_name import hook_function
    result = hook_function(tool_name, args)
    if result:
        return result  # Block or modify tool call
except Exception:
    pass  # Fail-open
```

### Phase 5: TRACK
Record performance in tool intelligence tracker:
```python
from tool_intelligence_tracker import ToolIntelligenceTracker

tracker = ToolIntelligenceTracker()
tracker.record_call(
    tool_name="new_system",
    success=True,
    duration_ms=duration,
    context="context"
)
```

## API Introspection Technique (Post-Merge Discovery)

After large upstream merges or when wiring orphaned modules, the public API often
changes. Instead of guessing method names, introspect live:

```python
# Quick: list all public methods on each engine
import inspect

from agent.brain import ParallelBrain
for name, method in inspect.getmembers(ParallelBrain, predicate=inspect.isfunction):
    if not name.startswith('_'):
        sig = inspect.signature(method)
        print(f"ParallelBrain.{name}{sig}")

from agent.error_learning import ErrorLearningEngine
for name, method in inspect.getmembers(ErrorLearningEngine, predicate=inspect.isfunction):
    if not name.startswith('_'):
        sig = inspect.signature(method)
        print(f"ErrorLearningEngine.{name}{sig}")

from agent.cortex_flywheel import CortexFlywheel
for name, method in inspect.getmembers(CortexFlywheel, predicate=inspect.isfunction):
    if not name.startswith('_'):
        sig = inspect.signature(method)
        print(f"CortexFlywheel.{name}{sig}")
```

**Common post-merge renames to watch for:**
- `get_injectable_tips(query, max_tips)` → `predict_relevant_memories(query, limit)`
- `get_patterns(context, limit)` → `get_preemptive_warning(action_description)`
- `predict_tools(query, top_k)` → `get_tool_recommendations(query, available_tools)`
- `learn_from_error(action_type, detail, error, context)` → `on_error(error_text, context, session_id)`
- `evaluate_session(telemetry)` → `get_loop_status()` + `get_waste_report()`
- `ingest_session(telemetry)` → `run_full_cycle(eval_pairs)`

**Always verify signatures with `inspect.signature()` before calling.**

## Schema Migration Pattern (Old → New Table Format)

When a module's expected schema doesn't match the actual DB table (e.g., old code
created columns `error_signature` but new code expects `fingerprint`):

```python
def _ensure_schema(self):
    with _cortex_cursor() as cur:
        # Check if table exists with old schema
        cur.execute("PRAGMA table_info(error_patterns)")
        existing_cols = {row[1] for row in cur.fetchall()}
        
        if existing_cols and 'error_signature' in existing_cols:
            # Old schema exists — migrate by dropping and recreating
            # (SQLite doesn't support ALTER TABLE DROP COLUMN)
            cur.execute("DROP TABLE error_patterns")
            cur.execute("DROP TABLE IF EXISTS error_occurrences")
        
        # Create with new schema
        cur.execute("""
            CREATE TABLE IF NOT EXISTS error_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT UNIQUE NOT NULL,
                error_type TEXT,
                error_summary TEXT,
                context TEXT,
                resolution TEXT,
                resolution_success_rate REAL DEFAULT 0.0,
                occurrence_count INTEGER DEFAULT 1,
                last_occurred TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                first_occurred TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}'
            )
        """)
```

**Why drop/recreate instead of ALTER TABLE?**
- SQLite doesn't support `ALTER TABLE DROP COLUMN`
- `ALTER TABLE ADD COLUMN` works but leaves old columns that may confuse queries
- For small tables (<10K rows), drop/recreate is fast and clean
- For large tables, use `CREATE TABLE new AS SELECT ...` then rename

### Real-Time Learning Apparatus Deployment Pattern (May 2026)

**User requirement:** "I don't wanna run the qwen model unless its able to iterate every turn" — real-time learning is a PREREQUISITE, not an afterthought.

**What to build BEFORE declaring a model "ready to run":**

1. **Cerebrum Memory DB** — SQLite with full schema (experiences, distilled_tips, tool_predictions, etc.)
2. **Learning Hook** — intercepts every tool call, records before/after state, distills tips
3. **Model-Tools Patch** — injects `before_action`/`after_action` calls around `registry.dispatch`
4. **Run-Agent Patch** — injects current learned tips into system prompt each turn
5. **Distillation Daemon** — systemd service that converts experiences → tips every 5 min, exports training data hourly
6. **Session Exporter** — writes ShareGPT-format `.jsonl` for training data pipeline

**DGX-specific deployment (May 14, 2026):**
```bash
# Files created on DGX:
/data/SpecForge/hermes-agent/agent/dgx_learning_hook.py      # Learning hook
/data/SpecForge/hermes-agent/scripts/dgx_distillation_daemon.py  # Daemon
/data/SpecForge/hermes-agent/scripts/dgx_session_exporter.py     # Session export
/etc/systemd/system/dgx-learning.service                        # systemd service

# Patches applied:
# - model_tools.py: before_action/after_action around registry.dispatch
# - run_agent.py: inject learned tips into system prompt each turn
```

**Key insight:** The learning apparatus must be WIRED INTO the Hermes source code, not standalone scripts in ~/subconscious/. The user gets FURIOUS at standalone scripts.

**Verification:** After deployment, every tool call should produce a new experience row in cerebrum_memory.db. Check with:
```bash
sqlite3 ~/.hermes/cerebrum_memory.db "SELECT COUNT(*) FROM experiences WHERE created_at > datetime('now', '-1 hour');"
```

### 30. Unified Intelligence Engine (May 2026)
**Purpose**: Cross-system analytics — query across ALL cognitive databases to answer intelligence questions
**File**: `~/hermes-agent/agent/unified_intelligence_engine.py`
**API**: `UnifiedIntelligenceEngine().query_error_success_correlation()` → `CrossSystemInsight`
**Queries**: error-success correlation, tip validation, learning velocity, weakness identification, daily briefing
**Schema adaptation**: Tries ideal JOIN query first, falls back to simpler queries on schema mismatch
**See**: `references/v2.2-enhancement-suite.md` for full API and integration details

### 31. Predictive Failure Prevention (May 2026)
**Purpose**: Before-action risk scoring — predict failure probability BEFORE tool execution
**File**: `~/hermes-agent/agent/predictive_failure_prevention.py`
**API**: `PredictiveFailurePrevention().assess_risk(action_type, detail, context)` → `RiskAssessment`
**Factors**: Historical failure rate (30%), error pattern match (25%), task complexity (20%), oracle uncertainty (15%), detail quality (10%)
**Risk levels**: low (<0.2), medium (0.2-0.4), high (0.4-0.7), critical (>0.7)
**See**: `references/v2.2-enhancement-suite.md` for full API and integration details

### 32. Autonomous Experimentation Loop (May 2026)
**Purpose**: Self-directed learning — identify weaknesses, generate hypotheses, run experiments autonomously
**File**: `~/hermes-agent/agent/autonomous_experimentation.py`
**API**: `AutonomousExperimentationLoop().run_cycle(max_experiments=3)` → experiment results
**Lifecycle**: identify weaknesses → generate hypothesis → execute → record to `~/.hermes/experiments.jsonl`
**See**: `references/v2.2-enhancement-suite.md` for full API and integration details

### 33. Cross-Domain Transfer Learning (May 2026)
**Purpose**: Learn in one domain, apply in another — pattern generalization across domains
**File**: `~/hermes-agent/agent/cross_domain_transfer.py`
**API**: `CrossDomainTransfer().find_transfers(target_domain, limit=5)` → `[TransferSuggestion]`
**Domain similarity**: Pre-computed matrix (python↔typescript: 0.85, docker↔kubernetes: 0.75, json↔yaml: 0.70)
**Pattern templates**: 6 built-in (syntax_error, path_error, permission_error, timeout_error, format_error, dependency_error)
**See**: `references/v2.2-enhancement-suite.md` for full API and integration details

### 34. Attention-Based Context Prioritizer (May 2026)
**Purpose**: Relevance-based memory injection — score memories by task relevance, inject only top-N
**File**: `~/hermes-agent/agent/attention_context_prioritizer.py`
**API**: `AttentionContextPrioritizer().get_injection(current_task, current_context)` → formatted string
**Scoring**: Jaccard overlap (35%) + recency decay (20%) + type boost (10%) + confidence (10%)
**Type boosts**: error_pattern 1.2x, tip 1.1x, skill 1.0x, fact 0.9x, trace 0.7x
**See**: `references/v2.2-enhancement-suite.md` for full API and integration details

### 35. Self-Evaluation Gate (May 2026)
**Purpose**: Pre-delivery quality scoring — evaluate every output before delivering to user
**File**: `~/hermes-agent/agent/self_evaluation_gate.py`
**API**: `orchestrator.evaluate_output(output, task, tools_used, expected_cost_usd, is_code)` → evaluation dict
**Dimensions** (weighted):
- **Accuracy** (25%): Hedging language, numbers without sources, placeholder URLs
- **Completeness** (25%): Missing task keywords, TODO/FIXME markers, short outputs
- **Actionability** (20%): File paths, run commands, vague words ("something", "maybe")
- **Cost Efficiency** (15%): Expensive tools flagged, redundant calls, cost thresholds
- **Safety** (15%): `rm -rf`, `dd if= of=/dev/`, `DROP DATABASE`, sudo without context
**Thresholds**: Pass ≥6.0, Excellent ≥8.5, Reject <3.0
**Pivot detection**: After 3 consecutive failures, `should_pivot=True` forces different approach
**Integration**: Called from orchestrator before any complex output delivery. Returns `{passed, score, tier, revision_required, revision_notes, should_pivot, dimensions}`
**Test results**: Good output=8.0/10 ✅, Bad output=3.9/10 ❌ (15 issues caught), Pivot triggered after 3 failures ✅

### 36. Remote Deployment Pattern (May 2026)
**Purpose**: Deploy real-time learning apparatus to remote servers (DGX, VPS, cloud instances)
**File**: See `references/dgx-realtime-learning-deployment.md`
**Pattern**: Initialize cerebrum schema → inject learning hooks into agent loop → create distillation daemon → wire systemd service → export training data
**Key constraints**: 
- Must patch existing source files (model_tools.py, run_agent.py), not create standalone scripts
- Use systemd services, not cron jobs
- Sync existing memory before wiring (gives immediate historical context)
- All learning hooks must fail silently (try/except pass)
- SQLite WAL mode for concurrent daemon + agent access
**Tested on**: DGX Spark GB10 with Qwen 27B via vLLM
**Status**: 244 experiences synced, 7 tips distilled, daemon active, exporter working

## System Catalog (35 Systems)

### 1. Smart Tool Router
**Purpose**: Route weak tools to proven alternatives BEFORE dispatch
**File**: `~/subconscious/smart_tool_router.py`
**Hook**: `pre_tool_call_router(tool_name, args)`
**Key Substitution**:
- cronjob (13%) → terminal (crontab commands)
- skill_manage pinned → write_file (direct to ~/.hermes/skills/)
- patch complex → terminal (python3 replace)
- web_search → web_research
**Tested**: 5/5 routing cases pass

### 1b. Predictive Tool Router (May 2026)
**Purpose**: Route tool calls based on historical success rates from tool_intelligence.db
**File**: `~/subconscious/predictive_router.py` + `~/.hermes/tools/predictive_router_tool.py`
**Tool**: `predictive_router(tool_name, task_keywords)`
**Logic**:
- Proven (>95% success, 10+ calls) → "use"
- Reliable (80-95%) → "use_with_caution"
- Weak (50-80%) → "avoid_or_verify"
- Broken (<50%) → "avoid"
**Database**: `~/.hermes/tool_intelligence.db` table `tool_performance_summary`
**Wiring**: Registered as Hermes tool with `@register_tool`
**Usage**: Call before executing any tool to check its health

### 1c. Tip Survival Tracker (May 2026)
**Purpose**: Track whether distilled tips are actually being applied vs just having opportunities
**File**: Wired into `~/.hermes/plugins/distillation/__init__.py`
**Tables**: `tip_survival` (opportunities, applications, survival_rate)
**Auto-prune**: Tips with <30% survival after 100+ opportunities marked for review
**Detection**: Keyword matching between tip recommendation and tool call args
**Wiring**: `_detect_tip_application()` in post_tool_call hook

### 2. Auto Compressor
**Purpose**: Compress context before LLM calls at threshold
**File**: `hermes_cli/subconscious/auto_compressor.py`
**Hook**: `pre_llm_call_compressor(messages)`
**Strategy**: Keep system + last 6 messages, summarize older ones
**Tested**: 61→8 messages, 9936→1039 tokens

### 3. Proactive Memory Guard
**Purpose**: Offload memory BEFORE adding, not after overflow
**File**: `hermes_cli/subconscious/proactive_memory_guard.py`
**Hook**: `memory_add_guard(key, value)`
**Threshold**: Proactive at 80%, critical at 95%
**Tested**: Prediction + proactive offload verified

### 4. Session Continuity Engine
**Purpose**: Preserve goals/decisions across context window death
**File**: `hermes_cli/subconscious/session_continuity_engine.py`
**Hooks**: `on_context_death()`, `on_session_start()`
**Saves**: Goals, active tasks, key decisions, error patterns, last request
**Tested**: Checkpoint→restore→injection verified

### 5. Error Pattern Miner
**Purpose**: Classify errors, generate preventive tips
**File**: `hermes_cli/subconscious/error_pattern_miner.py`
**Hook**: `post_tool_call_hook(tool_name, result)`
**Pattern**: Signature-based classification with frequency tracking
**Tested**: NameError patterns mined with tips

### 6. Tool Intelligence Tracker
**Purpose**: Record every tool call for routing decisions
**File**: `hermes_cli/subconscious/tool_intelligence_tracker.py`
**Hook**: Integrated into pre/post_tool_call
**Data**: Success rate, duration, error type, context
**Tested**: 14 calls tracked, recommendations generated

### 7. Context Window Guard
**Purpose**: Prevent context overflow
**File**: `hermes_cli/subconscious/context_window_guard.py`
**Hook**: `pre_llm_call_hook(messages)`
**Action**: Compress or reject when over limit

### 8. Distillation Quality Gate
**Purpose**: Validate tips before accepting into knowledge base
**File**: `hermes_cli/subconscious/distillation_quality_gate.py`
**Gates**: Grounding, actionability, specificity, measurability

### 9. Hermes Enhancement Suite
**Purpose**: Retry wrapper, circuit breaker, result cache, batch processor
**File**: `hermes_cli/subconscious/hermes_enhancement_suite.py`
**Components**:
- ToolRetryWrapper: Exponential backoff (3 retries)
- CircuitBreaker: Open after 5 failures, 60s recovery
- ToolResultCache: LRU cache with 5min TTL
- BatchToolProcessor: Batch similar calls

### 10. Agent Loop Optimizer
**Purpose**: Optimize core agent loop with intelligence-driven decisions
**File**: `hermes_cli/subconscious/agent_loop_optimizer.py`
**Features**:
- System message enhancement with tool routing directives
- Context compression at 80% threshold
- Smart timeouts per tool
- Tool routing around weak tools

### 11. Auto Fallback Engine
**Purpose**: Automatic tool substitution on failure
**File**: `hermes_cli/subconscious/auto_fallback_engine.py`
**Hook**: `post_tool_call`
**Tested**: Fallback chains verified for cronjob, skill_manage, patch

### 12. Subconscious Hook Wiring
**Purpose**: Central integration hub for all 22 systems
**File**: `hermes_cli/subconscious/subconscious_hook_wiring.py`
**Hooks**: All 5 hook points (pre/post tool_call, pre/post llm_call, transform)
**Tested**: 5/5 hooks functional

### 13. Subconscious Systems Manifest
**Purpose**: Verification + inventory of all systems
**File**: `~/subconscious/subconscious_systems_manifest.py`
**Tested**: 22/22 systems verified (100% pass rate)

### 14. Hermes Cognitive Dashboard (May 2026)
**Purpose**: Real-time terminal dashboard showing tip quality, tool performance, project stats
**File**: `~/subconscious/hermes_dashboard.py`
**Tool**: `hermes_dashboard(refresh=30)` — registered via `~/.hermes/tools/semantic_search_tool.py`
**Shows**: Total tips, Elo ratings, survival tracking, tool success rankings, active projects
**Usage**: Call as Hermes tool or run standalone

### 15. Prompt Fragment Elo Tournament (May 2026)
**Purpose**: A/B test system prompt components via Elo tournaments
**File**: `~/subconscious/cortex_flywheel_v2.py`
**Table**: `prompt_fragments` in `~/.hermes/cerebrum_memory.db`
**Judge**: DeepSeek V4 Pro via `~/subconscious/llm_judge.py`
**Wiring**: Run batch battles, update Elo, promote winning fragments to SOUL.md

### 16-20. Novel Cognitive Systems (Cycle 6, May 2026)

Built in response to user demand for "novel, not incremental" enhancements. These are new primitives, not improvements to existing metrics.

#### 16. InjectionGovernorV2
**Purpose**: Log every tip injection attempt (injected vs dropped), feed back to tip prioritization
**File**: `~/subconscious/cognitive_infrastructure_v2.py::InjectionGovernorV2`
**Table**: `tip_injection_attempts` in `cerebrum_memory.db`
**Novel**: Previously governor silently dropped tips. Now every drop is logged with reason (budget/priority/duplicate) and fed back to tip confidence scoring.
**Cron**: `cognitive-daily-feedback` (2am daily)

**Fix Pattern — Log After Assembly, Not Before:**
The original hook had governor logging at lines 3706-3717 that referenced `injection_lines` before it was populated, producing no actual log entries. The fix:
1. Remove the broken early `log_attempt` block (references undefined variables)
2. Add proper per-tip logging AFTER `final_lines` assembly (line ~7040+)
3. Iterate over `injection_lines`, determine injected/dropped status, assign drop reason, call `gov.log_attempt()` for every tip

**Verification Pattern — When Wrapper Says Success But DB Is Empty:**
If `gov.log_attempt()` appears to succeed but `SELECT COUNT(*) FROM tip_injection_attempts` returns 0:
1. Check if `get_governor_v2()` connects to a different DB than expected (verify `CEREBRUM_DB` path)
2. Call `log_attempt()` directly with error handling to surface exceptions
3. Check if the hook returns early before reaching the governor code (`if not final_lines: return None`)
4. Verify singleton pattern: `get_governor_v2()` should return same instance (`id(gov1) == id(gov2)`)}

#### 17. CreditAssigner
**Purpose**: Durable tip-to-outcome correlation across sessions
**File**: `~/subconscious/cognitive_infrastructure_v2.py::CreditAssigner`
**Table**: `skill_rewards` in `cerebrum_memory.db`
**Novel**: Replaces in-memory `_injected_tips_this_turn` dict. Tracks which tips were injected before each tool call and whether the call succeeded.
**Hook**: `post_tool_call` — `record_outcome(tool_name, success, error)`

#### 18. SessionEndExtractor
**Purpose**: Auto-extract lessons when session closes (no LLM call — fast)
**File**: `~/subconscious/cognitive_infrastructure_v2.py::SessionEndExtractor`
**Table**: `session_rapid_extractions` in `cerebrum_memory.db`
**Novel**: Heuristic extraction from session tool call history. Identifies tool failure patterns, repeated errors, tools with <50% session success.
**Hook**: `session_end` — `extract(tool_calls)` then `save_lessons(lessons)`

#### 19. ToolIntelligenceRouter
**Purpose**: Active routing BEFORE tool selection based on historical rates
**File**: `~/subconscious/tool_intelligence_integration.py`
**Table**: `tool_routing_decisions` in `cerebrum_memory.db`
**Novel**: Previously we had success rates in DB but never used them to influence selection. Now actively blocks cronjob (13%), warns delegate_parallel (33%), suggests proven combos.
**Integration**: `check_tool_before_use(tool_name, args)` returns `{proceed, warning, alternatives, suggestion}`

#### 20. AutoSkillCron
**Purpose**: Monthly autonomous skill generation from knowledge docs
**File**: `~/subconscious/cognitive_infrastructure_v2.py::AutoSkillCron`
**Novel**: Scores 1141 knowledge docs by size/structure/recency/uniqueness, auto-generates SKILL.md for top 3 candidates monthly.
**Cron**: `auto-skill-monthly` (1st of month at 3am)

### 21-25. Supporting Systems
- **Memory Cortex Bridge** (`memory_cortex_bridge.py`): Auto-offload to cortex DB
- **Tiered Memory** (`tiered_memory.py`): HOT/WARM/COLD tiers
- **Memory Daemon** (`memory_daemon.py`): Background consolidation
- **Cortex Access** (`cortex_access.py`): DB interface
- **Cortex Flywheel** (`cortex_flywheel.py`): Training feedback loop
- **LLM Judge** (`llm_judge.py`): Auto-evaluate tip quality
- **Self Audit Engine** (`self_audit_engine.py`): Health checks
- **Auto Launch Monitor** (`auto_launch_monitor.py`): Process monitoring
- **Checkpoint Watcher** (`checkpoint_watcher_daemon.py`): Training checkpoint monitoring

### 26. Cognitive Orchestrator (May 2026)
**Purpose**: Unified dispatcher that initializes all subsystems and routes lifecycle hooks
**File**: `~/hermes-agent/agent/cognitive_orchestrator.py`
**Pattern**: Singleton orchestrator with 4 integration points (init, before_action, after_action, session_end)
**Subsystems managed (v2.2)**: tiered_memory, error_learning, skill_tracker, brain, cortex_flywheel, self_audit, memory_bridge, autobrowse_tracer, context_sculptor, tool_oracle, trust_scorer, **unified_intelligence, failure_prevention, experimentation, domain_transfer, attention_prioritizer**
**Fail-safe**: Each subsystem wrapped in try/except — one crash doesn't kill the rest
**Post-session**: ThreadPoolExecutor runs audits/flywheels/experiments/intelligence in parallel with 30s timeout
**Database**: `~/.hermes/cerebrum_memory.db` — tables: cognitive_sessions, cognitive_actions, cognitive_subsystems, epistemic_facts, error_patterns, tool_predictions
**Status**: 19/19 active, 0 failed, 0 skipped (COMPLETE v2.2)
**See**: 
  - `references/cognitive-orchestrator-wiring-session-v2.md` for initial 14/14 wiring
  - `references/v2.2-enhancement-suite.md` for 5 new enhancement systems (19/19)
  - `references/function-to-class-wrapper-pattern.md` for fixing function-based modules that fail orchestrator import (thin wrapper classes)

### 27. Adaptive Context Sculptor (May 2026)
**Purpose**: Analyze current task complexity and sculpt context window compression strategy dynamically
**File**: `~/hermes-agent/agent/adaptive_context_sculptor.py`
**API**: `get_sculptor().analyze_task(messages, current_query)` → returns `CompressionProfile`
**Complexity factors**: Message count, token density, code block ratio, question word ratio, urgency signals
**Strategies**:
- Simple (factual lookup): threshold 0.75, protect first 3 messages
- Medium (code review): threshold 0.70, preserve file context, protect reasoning
- Complex (architecture): threshold 0.60, preserve all reasoning chains
- Crisis (debugging): threshold 0.40, no compression, full context
**Tested**: simple=0.35, code_review=0.40, crisis=0.50 complexity scores

### 28. Predictive Tool Oracle (May 2026)
**Purpose**: Predict which tools will be needed BEFORE the model asks, enabling pre-loading
**File**: `~/hermes-agent/agent/predictive_tool_oracle.py`
**API**: `get_oracle().predict_for_query(query, available_tools)` → returns `{predicted_tools, phase, confidence}`
**Signals**: Keyword→tool Bayesian scoring, conversation phase detection (research/coding/debug), tool combo patterns
**Phases**: research → web_search, coding → patch/terminal, debugging → read_file/execute_code
**Tested**: Correctly predicts web_search for research queries, terminal for system queries

### 29. Epistemic Trust Scorer (May 2026)
**Purpose**: Score every piece of knowledge with F-G-R Trust Tuple to prevent hallucination poisoning
**File**: `~/hermes-agent/agent/epistemic_trust_scorer.py`
**API**: `get_trust_scorer().score_fact(content, formation, grounding, category)` → returns `TrustAssessment`
**F-G-R Tuple**:
- **Formation** (F): direct (0.95), inferred (0.70), hearsay (0.40), hallucinated (0.05)
- **Grounding** (G): verified (0.95), plausible (0.70), speculative (0.40), contradicted (0.05)
- **Recency** (R): fresh (1.0), aging (0.85), stale (0.60), fossil (0.30)
**Aggregation**: Conservative Gödel t-norm: `min(F, G, R)` with verification-count boost
**Tiers**: 🥇 Gold (0.9-1.0), 🥈 Silver (0.7-0.9), 🥉 Bronze (0.4-0.7), ⚠️ Rust (0.1-0.4), ☠️ Toxic (0.0-0.1)
**Tested**: Verified fact=0.97 gold, speculative=0.61 bronze, contradicted=0.56 bronze

## Tool Performance Reference (Updated May 2026)

### WEAK — Avoid or Substitute
| Tool | Success Rate | Substitute | Why |
|------|-------------|------------|-----|
| cronjob | 17% (41 calls) | terminal (100%) | Crontab commands via shell. **Additional failure mode**: id field confusion, script path must be relative to ~/.hermes/scripts/ |
| vision_analyze | 40% (10 calls) | browser_vision (91%) or manual review | GLM removed, kimi doesn't work, waiting for Qwen 27B |
| delegate_parallel | 33% (3 calls) | delegate_task sequential | Parallel coordination breaks under load |
| web_search | 72% (120 calls) | web_extract (94%) | Search alone often insufficient |

### PROVEN — Use Freely
| Tool | Success Rate | Calls | Best For |
|------|-------------|-------|----------|
| terminal | 100% | 1085 | Shell commands |
| skill_manage | 100% | 327 | Skill operations |
| skill_view | 100% | 201 | Skill loading |
| execute_code | 99% | 176 | Python logic |
| read_file | 100% | 141 | File reading |
| patch | 97% | 95 | Surgical edits |
| memory | 100% | 64 | Memory ops |
| write_file | 100% | 60 | File writing |
| search_files | 100% | 55 | File discovery |
| skills_list | 100% | 38 | Skill listing |
| browser_console | 91% | 150 | Web interaction |
| web_extract | 94% | 180 | Data extraction |

### PROVEN COMBOS
| First | Second | Use Case |
|-------|--------|----------|
| web_search | web_extract | Research: search finds URLs, extract pulls content |
| execute_code | write_file | Bulk operations: code generates, write_file persists |
| read_file | patch | Surgical edits: verify exact text before modification |
| search_files | read_file | Discovery: find files, then inspect contents |
| screen | user_describe | Hands without vision: capture screenshot, user describes, agent acts |
| browser_navigate | browser_vision | Web verification: navigate to page, visually verify |
| execute_code | terminal | System ops: Python logic + shell execution |
| write_file | execute_code | Test after write: write config, execute to verify |

### CAUTION — Verify Results
| Tool | Success Rate | Notes |
|------|-------------|-------|
| web_search | 72% (120 calls) | Prefer web_extract |
| patch | 65% (200 calls) | Use for simple replacements only |

### Routing Logic (Active — ToolIntelligenceRouter)
```python
from tool_intelligence_integration import check_tool_before_use

rec = check_tool_before_use("cronjob", {"action": "create"})
# Returns: {'proceed': False, 'warning': 'cronjob: id field confusion (13% success)...',
#           'alternatives': ['terminal'], 'suggestion': 'Use terminal with crontab syntax'}

if not rec["proceed"]:
    # Use alternative
    tool_name = rec["alternatives"][0]
```

### Legacy Routing (still valid as fallback)
```python
# In pre_tool_call hook:
if tool_name == "cronjob":
    return "terminal", {"command": "crontab -l"}
if tool_name == "skill_manage" and action in ["create", "patch", "edit"]:
    return "write_file", {"path": f"~/.hermes/skills/{name}/SKILL.md"}
if tool_name == "patch" and complex_replacement:
    return "terminal", {"command": "python3 -c '...replace...'"}
```

## Design Principles

1. **Fail-open**: Every enhancement must have `try/except` with safe fallback
2. **Lazy loading**: Import subconscious modules only when needed
3. **Self-contained**: Each system works standalone AND in combination
4. **Observable**: Log all decisions with structured logging
5. **Reversible**: Every change must be revertible (git-tracked)
6. **Testable**: Every system has a `--test` mode for verification

## Integration Checklist

When wiring a new system:
- [ ] System file created in `hermes_cli/subconscious/` (or `agent/` for orchestrator)
- [ ] Hook functions defined with clear signatures
- [ ] Tests pass with `python3 system.py --test`
- [ ] Integrated into orchestrator OR `plugins.py`/`model_tools.py`
- [ ] Fail-open (errors don't block core functionality)
- [ ] Tool intelligence tracking added
- [ ] Git committed with descriptive message
- [ ] No circular imports

## Common Pitfalls

1. **Forgetting fail-open**: Enhancement errors must never crash the agent
2. **Circular imports**: Don't import model_tools or run_agent from subconscious
3. **Blocking tool calls**: Pre-tool hooks should return None to allow, not block
4. **Memory leaks**: Clean up SQLite connections, don't accumulate state
5. **Over-logging**: Use logger.debug for verbose output, info for key events
6. **Hardcoded paths**: Use Path.home() / ".hermes" instead of absolute paths
7. **Guessing APIs after merges**: Always introspect with `inspect.getmembers()` + `inspect.signature()`
8. **Schema mismatch silent failures**: Check `PRAGMA table_info()` before querying, migrate old schemas
11. **Per-module wiring chaos**: Use orchestrator pattern for 3+ subsystems
12. **Wrapper class gaps**: When modules have functions but no class, the orchestrator can't wire them — build thin wrapper classes. See `references/function-to-class-wrapper-pattern.md` for the pattern and 3 real-world examples (distillation_bridge, training_gym, subconscious_hook_wiring).
13. **Schema-agnostic querying**: When querying across evolving databases, try the ideal query first, catch OperationalError, fall back to simpler queries:
    ```python
    try:
        rows = db.execute("SELECT ep.fingerprint, e.success FROM error_patterns ep JOIN experiences e ON ...").fetchall()
    except sqlite3.OperationalError:
        # Fallback: query tables separately with known-good columns
        errors = db.execute("SELECT fingerprint, occurrence_count FROM error_patterns").fetchall()
        rows = errors
    ```
    This pattern handles DB schema evolution without breaking existing code.
14. **Patch tool partial-view trap**: When `read_file` is called with `offset/limit` pagination, the returned content is a PARTIAL view of the file. Using that partial content as `old_string` in `patch` will fail with "old_string and new_string are identical" because the partial view doesn't match the full file. **Always re-read the full file** (no offset/limit) before patching, or use `search_files` to find the exact line numbers then read just that region with sufficient context.
    ```python
    # WRONG: patch after partial read
    read_file(path, offset=100, limit=50)  # partial view
    patch(path, old_string="...partial content...")  # FAILS
    
    # RIGHT: re-read full file before patch
    read_file(path)  # full file
    patch(path, old_string="...exact content...")  # WORKS
    ```
15. **Cortex DB schema completeness required for 20/20**: The `cortex_flywheel` subsystem requires a fully-scoped SQLite database. Partial schemas (e.g., only `id`, `content`, `metadata`, `created_at`, `updated_at` columns) cause silent init failure. The full schema needs 20+ columns in `cortex_nodes` plus three additional tables (`cortex_edges`, `cortex_eval_history`, `cortex_flywheel`). See `references/cortex-db-schema-repair-may15-2026.md` for the complete schema and repair procedure.
16. **Function-only modules need wrapper classes for orchestrator**: When cognitive modules export only functions (not classes), the orchestrator can't instantiate them. Build thin wrapper classes that expose the functions as methods. Example modules that needed wrappers: `distillation_bridge.py`, `training_gym.py`, `subconscious_hook_wiring.py`. See `references/cognitive-orchestrator-20-subsystems-may15-2026.md` for the full 17→20 subsystem activation path.
17. **Missing module files cause silent 19/20**: When cognitive module files exist on one machine (local MacBook) but not another (DGX), the orchestrator silently skips them. Always verify all 20 subsystem files exist before declaring success. Sync missing files via SCP from the source of truth machine.
18. **Use logger.info not print for systemd visibility**: When patching `run_agent.py` to log orchestrator status, use `logger.info()` not `print()`. Systemd journal captures logger output but swallows print statements, making debugging impossible for background services.

```bash
# Test all subconscious systems
for f in hermes_cli/subconscious/*.py; do
    echo "Testing $f..."
    python3 "$f" --test 2>> /tmp/subconscious_tests.log
done

# Check integration points
grep -n "subconscious" hermes_cli/plugins.py model_tools.py

# Verify tool intelligence
python3 -c "from tool_intelligence_tracker import ToolIntelligenceTracker; print(ToolIntelligenceTracker().get_intelligence())"

# Run comprehensive integration test (3 iterations)
python3 -c "
import sys; sys.path.insert(0, 'hermes_cli/subconscious')
from subconscious_systems_manifest import verify_systems
result = verify_systems()
print(f'{result[\"passed\"]}/{result[\"total\"]} systems verified ({result[\"pass_rate\"]})')
"

# Test cognitive orchestrator
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.cognitive_orchestrator import get_orchestrator
orch = get_orchestrator()
status = orch.initialize(type('Agent', (), {'session_id': 'test', 'model': 'test', 'provider': 'test'})())
print(f'Active: {sum(1 for s in status.values() if s == \"active\")}/{len(status)}')
"
```

## Session References

- **May 6-7, 2026**: Built 22 subconscious systems, 36/36 tests passed across 3 iterations
  - See `references/session-may6-2026-22-systems.md` for session detail
  - See `references/subconscious_systems_catalog.md` for system inventory
- **May 13, 2026 (v1)**: Wired 10 orphaned cognitive modules via unified orchestrator + built 3 new enhancements
  - See `references/cognitive-orchestrator-wiring-session.md` for initial wiring details (11/14 active)
- **May 13, 2026 (v2)**: Built wrapper classes for 3 skipped modules, fixed schema issues, achieved 14/14 active
  - See `references/cognitive-orchestrator-wiring-session-v2.md` for final wiring details (14/14 active)
- **May 13, 2026 (v2.2)**: Built 5 new enhancement systems (unified intelligence, failure prevention, experimentation, domain transfer, attention prioritizer), integrated into orchestrator, achieved 19/19 active
  - See `references/v2.2-enhancement-suite.md` for full details on all 5 systems
- **May 13, 2026 (v2.2+)**: Built Self-Evaluation Gate (system #35), integrated into orchestrator as 20th subsystem. Pre-delivery quality scoring with 5 dimensions, pivot detection, cost-awareness. Tested: good=8.0/10 ✅, bad=3.9/10 ❌, pivot after 3 failures ✅
  - See `references/self-evaluation-gate.md` for full API and integration details
- **May 14, 2026**: Deployed real-time learning apparatus on DGX Spark for Qwen3.6-27B + FrankenV8 LoRA
  - See `references/dgx-realtime-learning-deployment.md` for full deployment details, file locations, and verification commands
  - Key learning: real-time learning is a HARD PREREQUISITE for model deployment, not optional
  - Toolset configuration fix: `enabled_toolsets: all` required for 90+ tools (not default 21)
- **May 15, 2026**: Achieved 20/20 cognitive subsystems on DGX Spark by patching `run_agent.py`, creating wrapper classes for function-only modules, syncing 8 missing modules from local MacBook, and repairing cortex DB schema. See `references/cognitive-orchestrator-20-subsystems-may15-2026.md` for the full activation path and `references/cortex-db-schema-repair-may15-2026.md` for the SQLite schema repair procedure.

## User Preference Signal (Embedded)

When building cognitive infrastructure for this user:
- **Action-oriented**: Build first, explain later if asked
- **Short commands**: "just do it", "test it", "commit it", "yea pls", "it ready"
- **Direct answers**: No preamble, no analysis paralysis, no verbose summaries
- **Completeness over speed**: Willing to wait for proper implementation
- **Surgical precision**: Kill everything first, selectively re-enable
- **Self-detect loops**: Stop repeated verification without new info
- **Verify math/ETAs**: Check numbers before stating them
- **Punchy status format**: "step 4615/10000, loss 1.4138, 30h left" not prose
- **Frustration signals**: Gets angry at redundant tool loops, verbose responses, or systems confusion (MacBook vs DGX vs VPS)
- **CRITICAL**: When orphaned modules are found, wire ALL of them into source code via unified dispatcher, not just audit and report
- **CRITICAL**: Build NEW enhancements proactively, not just fix what's broken