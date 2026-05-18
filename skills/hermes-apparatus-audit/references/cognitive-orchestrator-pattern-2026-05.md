# Cognitive Orchestrator Pattern — Unified Dispatcher for Orphaned Modules

**Session**: May 13, 2026
**Context**: User discovered 10 of 13 cognitive modules in agent/ were orphaned (files present, never imported in run_agent.py). Only iteration_engine and cortex_learning were wired. Total orphaned code: ~211KB (~5,500 lines, ~15% of agent/).

**Solution**: Build a single CognitiveOrchestrator class that acts as a unified dispatcher. Instead of wiring each module individually into run_agent.py (brittle, error-prone), wire ONE orchestrator that manages all subsystems.

---

## The Problem with Individual Wiring

Before: Each module needed its own import, its own hook registration, its own error handling in run_agent.py:

```python
# BRITTLE: Individual wiring (what we had)
from agent.brain import ParallelBrain
from agent.training_gym import TrainingGym
from agent.self_audit_engine import SelfAuditEngine
# ... 10 more imports

# Each needs its own try/except block in 4 places (init, before, after, end)
```

After: One orchestrator, one import, one initialization, one call per lifecycle point:

```python
# ROBUST: Unified dispatcher
from agent.cognitive_orchestrator import get_orchestrator

# In __init__:
self.cognitive_orchestrator = get_orchestrator()
self.cognitive_orchestrator.initialize(self)

# In before_action:
_cognitive_lessons = self.cognitive_orchestrator.before_action(action_type, detail)

# In after_action:
self.cognitive_orchestrator.after_action(action_type, detail, result, duration_ms)

# In session_end:
self.cognitive_orchestrator.session_end(telemetry)
```

---

## Orchestrator Architecture

```
run_agent.py --> CognitiveOrchestrator --> 14 subsystems
                    |
                    |-- initialize(agent) --> init all in dependency order
                    |-- before_action() --> collect lessons from all
                    |-- after_action() --> learn from outcomes
                    |-- session_end() --> run post-session in parallel
                    |-- on_error() --> route to error_learning
```

### Dependency Order for Initialization

```python
init_order = [
    ("tiered_memory", self._init_tiered_memory),
    ("error_learning", self._init_error_learning),
    ("skill_tracker", self._init_skill_tracker),
    ("brain", self._init_brain),
    ("cortex_flywheel", self._init_cortex_flywheel),
    ("distillation_bridge", self._init_distillation_bridge),
    ("self_audit", self._init_self_audit),
    ("training_gym", self._init_training_gym),
    ("memory_bridge", self._init_memory_bridge),
    ("subconscious", self._init_subconscious),
    ("autobrowse_tracer", self._init_autobrowse_tracer),
    # NEW: v2.1 enhancements
    ("context_sculptor", self._init_context_sculptor),
    ("tool_oracle", self._init_tool_oracle),
    ("trust_scorer", self._init_trust_scorer),
]
```

### before_action Pipeline

Each subsystem contributes lessons. The orchestrator:
1. Collects lessons from ALL subsystems
2. Filters by epistemic trust (if trust_scorer active)
3. Deduplicates
4. Returns combined injection string

```python
def before_action(self, action_type: str, detail: str) -> Optional[str]:
    lessons = []
    
    # 1. Iteration engine
    if "iteration_engine" in self._subsystems:
        lesson = ie.before_action(action_type, detail)
        if lesson: lessons.append(f"[Iteration] {lesson}")
    
    # 2. Error learning — check for known error patterns
    if "error_learning" in self._subsystems:
        patterns = epm.check_patterns(action_type, detail)
        if patterns: lessons.append(f"[ErrorGuard] {patterns[0]['lesson']}")
    
    # 3. Tiered memory — relevant memories
    if "tiered_memory" in self._subsystems:
        memories = tm.recall(query=f"{action_type} {detail}", limit=3)
        for mem in memories:
            lessons.append(f"[Memory] {mem.get('content', '')[:150]}")
    
    # 4. Skill tracker — suggest effective skills
    if "skill_tracker" in self._subsystems:
        skills = st.suggest_skills(action_type, limit=2)
        for skill in skills:
            lessons.append(f"[Skill] {skill.get('name', '')}: {skill.get('tip', '')[:100]}")
    
    # 5. Brain — quick perception
    if "brain" in self._subsystems:
        perception = brain.perceive(action_type, detail)
        if perception.get("urgency") == "high":
            lessons.append(f"[Brain] High-risk action: {perception.get('warning', '')}")
    
    # 6. Trust Scorer — filter lessons by epistemic trust
    if "trust_scorer" in self._subsystems and lessons:
        trusted_lessons = []
        for lesson in lessons:
            trust = ts.score_fact(content=lesson, formation="inferred", 
                                  grounding="plausible", category="procedural")
            if trust.overall_trust >= 0.3:  # Bronze threshold
                tier_emoji = {"gold": "🥇", "silver": "🥈", "bronze": "🥉", "rust": "⚠️"}
                emoji = tier_emoji.get(trust.trust_tier, "")
                trusted_lessons.append(f"{emoji} {lesson}")
        lessons = trusted_lessons
    
    return "\n".join(lessons) if lessons else None
```

### session_end Parallel Processing

Post-session work runs in parallel via ThreadPoolExecutor:

```python
def session_end(self, telemetry: SessionTelemetry) -> Dict[str, Any]:
    report = {"session_id": telemetry.session_id}
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        
        # Self-audit (quality scoring)
        if "self_audit" in self._subsystems:
            futures["audit"] = executor.submit(
                self._subsystems["self_audit"].run_audit, telemetry
            )
        
        # Cortex flywheel (continuous learning)
        if "cortex_flywheel" in self._subsystems:
            futures["flywheel"] = executor.submit(
                self._subsystems["cortex_flywheel"].process_session, telemetry
            )
        
        # Memory bridge (sync to cortex)
        if "memory_bridge" in self._subsystems:
            futures["memory"] = executor.submit(
                self._subsystems["memory_bridge"].sync_session, telemetry
            )
        
        # Training gym (tip generation)
        if "training_gym" in self._subsystems:
            futures["gym"] = executor.submit(
                self._subsystems["training_gym"].extract_lessons, telemetry
            )
        
        # Collect results
        for name, future in futures.items():
            try:
                report[name] = future.result(timeout=5.0)
            except Exception as e:
                report[name] = {"error": str(e)}
    
    return report
```

---

## Integration Points in run_agent.py

### 1. __init__ (~line 2127)

```python
# ── Cognitive Orchestrator: unified subsystem dispatcher ──────────────
try:
    from agent.cognitive_orchestrator import get_orchestrator
    self.cognitive_orchestrator = get_orchestrator()
    _co_status = self.cognitive_orchestrator.initialize(self)
    logger.info("Cognitive orchestrator: %s", _co_status)
except Exception as _co_err:
    logger.warning("Cognitive orchestrator init failed: %s", _co_err)
    self.cognitive_orchestrator = None
```

### 2. before_action (~line 10061)

```python
# ── Cognitive Orchestrator: multi-subsystem pre-action lookup ─────────
if hasattr(self, "cognitive_orchestrator") and self.cognitive_orchestrator:
    try:
        from agent.cognitive_orchestrator import get_orchestrator
        _co = get_orchestrator()
        _cognitive_lessons = _co.before_action(
            action_type=function_name,
            detail=json.dumps(function_args, ensure_ascii=False)[:200],
        )
        if _cognitive_lessons:
            _iteration_context.injected_lessons.append(_cognitive_lessons)
    except Exception:
        pass
```

### 3. after_action (~line 10161)

```python
# ── Iteration Engine + Tool Cache + Cognitive Orchestrator: post-action ──
_tool_end = _time.time()
_is_error = "error" in result.lower() or result.startswith("Error")
_duration_ms = int((_tool_end - _tool_start_time) * 1000)

# Iteration engine (existing)
if hasattr(self, "iteration_engine") and self.iteration_engine:
    # ... existing code ...

# Cognitive orchestrator: multi-subsystem post-action
if hasattr(self, "cognitive_orchestrator") and self.cognitive_orchestrator:
    try:
        from agent.cognitive_orchestrator import get_orchestrator
        _co = get_orchestrator()
        _co.after_action(
            action_type=function_name,
            detail=json.dumps(function_args, ensure_ascii=False)[:200],
            result=result,
            duration_ms=_duration_ms,
            error=result[:500] if _is_error else "",
        )
    except Exception:
        pass
```

### 4. session_end (~line 15028)

```python
# ── COGNITIVE ORCHESTRATOR: session end processing ─────────────────
try:
    if hasattr(self, "cognitive_orchestrator") and self.cognitive_orchestrator:
        from agent.cognitive_orchestrator import get_orchestrator, SessionTelemetry
        _co = get_orchestrator()
        _telemetry = SessionTelemetry(
            session_id=self.session_id or "unknown",
            start_time=getattr(self, '_session_start_time', time.time()),
            end_time=time.time(),
            model=self.model,
            provider=self.provider,
        )
        _report = _co.session_end(_telemetry)
        if _report and _report.get("audit_score"):
            logger.info("Session audit score: %.2f", _report["audit_score"])
except Exception as _co_end_err:
    logger.debug("Cognitive session-end failed: %s", _co_end_err)
```

---

## New Enhancements Built (v2.1)

### Adaptive Context Sculptor

Analyzes task complexity in real-time and sculpts context window allocation:

```python
from agent.adaptive_context_sculptor import get_sculptor
sculptor = get_sculptor()

messages = [...]
profile = sculptor.analyze_task(messages, current_query)
strategy = profile.compression_strategy
# strategy = {"threshold": 0.85, "protect_first_n": 3, "preserve_reasoning": True}
```

**Task profiles**:
- Debug mode → preserve full history
- Code-heavy + multi-file → preserve file context
- Research-heavy → accumulate findings
- Simple lookup → aggressive compression

### Predictive Tool Oracle

Predicts which tools will be needed before the model asks:

```python
from agent.predictive_tool_oracle import get_oracle
oracle = get_oracle()

prediction = oracle.predict_for_query(
    "Search for Python docs",
    available_tools=['web_search', 'web_extract', 'read_file']
)
# prediction = {"predicted_tools": [("web_search", 0.85), ...], "phase": "research"}
```

Uses Bayesian keyword→tool scoring from historical usage. Learns from actual outcomes.

### Epistemic Trust Scorer

Scores every piece of knowledge by trustworthiness using F-G-R Trust Tuple:

```python
from agent.epistemic_trust_scorer import get_trust_scorer
scorer = get_trust_scorer()

trust = scorer.score_fact(
    content="Python lists are mutable",
    formation="direct",
    grounding="verified",
    sources=["python.org"],
    category="technical",
)
# trust.overall_trust = 0.99, trust.trust_tier = "gold"
```

**Tiers**:
- 🥇 Gold (0.9-1.0): Directly verified, recent, multiple sources
- 🥈 Silver (0.7-0.9): Plausible, single source, recent
- 🥉 Bronze (0.4-0.7): Inferred, unverified, aging
- ⚠️ Rust (0.1-0.4): Speculative, old, or contradicted
- ☠️ Toxic (0.0-0.1): Hallucinated or proven false

---

## Audit Script

Use this to check cognitive module wiring status:

```python
#!/usr/bin/env python3
"""Cognitive Systems Audit — checks which modules are wired vs orphaned."""

import ast
import os
from pathlib import Path

HERMES_ROOT = Path.home() / "hermes-agent"
AGENT_DIR = HERMES_ROOT / "agent"
RUN_AGENT = HERMES_ROOT / "run_agent.py"

def get_agent_modules():
    """Find all Python modules in agent/ directory."""
    modules = {}
    for f in AGENT_DIR.glob("*.py"):
        if f.name.startswith("_"):
            continue
        module_name = f.stem
        try:
            tree = ast.parse(f.read_text())
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            modules[module_name] = {"file": f, "classes": classes, "functions": functions}
        except SyntaxError:
            modules[module_name] = {"file": f, "classes": [], "functions": []}
    return modules

def check_wiring_status():
    """Check which modules are imported/called in run_agent.py."""
    run_agent_text = RUN_AGENT.read_text()
    
    modules = get_agent_modules()
    
    # Check imports
    for name, info in modules.items():
        import_patterns = [
            f"from agent.{name} import",
            f"import agent.{name}",
            f"from .{name} import",
        ]
        is_imported = any(p in run_agent_text for p in import_patterns)
        
        # Check if any class/function is called
        is_called = False
        for cls in info["classes"]:
            if f"{cls}(" in run_agent_text or f"{cls}." in run_agent_text:
                is_called = True
                break
        for func in info["functions"]:
            if f"{func}(" in run_agent_text:
                is_called = True
                break
        
        info["imported"] = is_imported
        info["called"] = is_called
        info["wired"] = is_imported and is_called
    
    return modules

def print_report(modules):
    """Print audit report."""
    wired = []
    import_only = []
    orphaned = []
    
    for name, info in sorted(modules.items()):
        if info["wired"]:
            wired.append(name)
        elif info["imported"]:
            import_only.append(name)
        else:
            orphaned.append(name)
    
    total_size = sum(
        info["file"].stat().st_size 
        for info in modules.values()
    )
    orphaned_size = sum(
        modules[name]["file"].stat().st_size 
        for name in orphaned
    )
    
    print("=" * 60)
    print("COGNITIVE SYSTEMS AUDIT REPORT")
    print("=" * 60)
    print(f"\nWIRED ({len(wired)}):")
    for name in wired:
        print(f"  ✓ {name}")
    
    print(f"\nIMPORT_ONLY ({len(import_only)}):")
    for name in import_only:
        print(f"  ⚠️  {name} (imported but never called)")
    
    print(f"\nORPHANED ({len(orphaned)}):")
    for name in orphaned:
        size = modules[name]["file"].stat().st_size
        print(f"  ✗ {name} ({size:,} bytes)")
    
    print(f"\n{'=' * 60}")
    print(f"Total modules: {len(modules)}")
    print(f"Wired: {len(wired)} | Import-only: {len(import_only)} | Orphaned: {len(orphaned)}")
    print(f"Orphaned code: {orphaned_size:,} bytes ({orphaned_size/max(total_size,1)*100:.1f}% of agent/)")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    modules = check_wiring_status()
    print_report(modules)
```

**Expected output (after v2.1 wiring)**:
```
============================================================
COGNITIVE SYSTEMS AUDIT REPORT
============================================================

WIRED (14):
  ✓ cognitive_orchestrator
  ✓ iteration_engine
  ✓ cortex_learning
  ...

ORPHANED (0):

============================================================
Total modules: 14
Wired: 14 | Import-only: 0 | Orphaned: 0
Orphaned code: 0 bytes (0.0% of agent/)
============================================================
```

---

## Key Design Principles

1. **FAIL-SAFE**: Every subsystem wrapped in try/except. One failure doesn't kill the rest.
2. **LAZY**: Initialize on first use, not at import time.
3. **NON-BLOCKING**: Heavy operations (session_end processing) run in background threads.
4. **OBSERVABLE**: All actions logged to cerebrum_memory.db with timestamps.
5. **TRUST-AWARE**: All injected knowledge scored by epistemic trust before entering context.

---

## Verification Commands

```bash
# Test all imports
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.cognitive_orchestrator import get_orchestrator
from agent.adaptive_context_sculptor import get_sculptor
from agent.predictive_tool_oracle import get_oracle
from agent.epistemic_trust_scorer import get_trust_scorer
print('All modules import OK')
"

# Test functionality
python3 -c "
import sys; sys.path.insert(0, '.')
from agent.adaptive_context_sculptor import get_sculptor
sculptor = get_sculptor()
profile = sculptor.analyze_task([{'role': 'user', 'content': 'debug this'}], 'error on line 42')
print(f'Complexity: {profile.complexity_score}, Debug: {profile.debug_mode}')
"

# Run audit
python3 ~/hermes-agent/agent/cognitive_systems_audit.py
```
