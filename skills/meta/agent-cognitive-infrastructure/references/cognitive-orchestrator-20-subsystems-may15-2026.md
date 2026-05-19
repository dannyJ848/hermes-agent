# Cognitive Orchestrator 20/20 Subsystems — May 15, 2026

## Problem

DGX Spark Hermes Agent only showed iteration engine (7 subsystems) instead of full cognitive orchestrator (20 subsystems). Root cause: `run_agent.py` only initialized iteration engine; no call to `CognitiveOrchestrator`.

## Fix Path: 17 → 19 → 20 Subsystems

### Stage 1: Patch run_agent.py (17 → 17+orchestrator)

Added cognitive orchestrator initialization in `run_agent.py` lines 2136-2149:

```python
from agent.cognitive_orchestrator import CognitiveOrchestrator

try:
    self.cognitive_orchestrator = CognitiveOrchestrator()
    status = self.cognitive_orchestrator.get_status()
    active = sum(1 for s in status.values() if s.get('active', False))
    total = len(status)
    logger.info(f"Cognitive orchestrator ready: {active}/{total} subsystems active")
    for name, st in status.items():
        if st.get('active'):
            logger.info(f"   ✓ {name}")
        else:
            logger.info(f"   ✗ {name}")
except Exception as e:
    logger.warning(f"Cognitive orchestrator init failed: {e}")
    self.cognitive_orchestrator = None
```

**Critical**: Use `logger.info` not `print` — systemd swallows print output but preserves logs.

### Stage 2: Wrapper Classes for Function-Only Modules (17 → 19)

Several cognitive modules exported only functions, not classes. The orchestrator expects class instances. Created wrapper classes:

**distillation_bridge.py:**
```python
class DistillationBridge:
    def __init__(self):
        from agent.distillation_bridge import run_distillation_cycle
        self.run_cycle = run_distillation_cycle
```

**training_gym.py:**
```python
class TrainingGym:
    def __init__(self):
        from agent.training_gym import run_training_gym_cycle
        self.run_cycle = run_training_gym_cycle
```

**subconscious_hook_wiring.py:**
```python
class SubconsciousHookWiring:
    def __init__(self):
        from agent.subconscious_hook_wiring import wire_hooks
        self.wire = wire_hooks
```

This brought 17 → 19 subsystems active.

### Stage 3: Sync Missing Modules from Local MacBook (19 → 20)

8 cognitive modules existed on local MacBook but not on DGX. Synced via SCP:

```bash
# From MacBook to DGX
scp /Users/dannygomez/hermes-agent/agent/adaptive_context_sculptor.py \
    /Users/dannygomez/hermes-agent/agent/epistemic_trust_scorer.py \
    /Users/dannygomez/hermes-agent/agent/unified_intelligence_engine.py \
    /Users/dannygomez/hermes-agent/agent/predictive_failure_prevention.py \
    /Users/dannygomez/hermes-agent/agent/autonomous_experimentation.py \
    /Users/dannygomez/hermes-agent/agent/cross_domain_transfer.py \
    /Users/dannygomez/hermes-agent/agent/attention_context_prioritizer.py \
    /Users/dannygomez/hermes-agent/agent/self_evaluation_gate.py \
    djg6228@spark-85e8.local:/data/SpecForge/hermes-agent/agent/
```

Result: 19 → 20 subsystems active.

### Stage 4: Fix Cortex DB Schema (Final Blocker)

Last subsystem `cortex_flywheel` failed with "no such table: cortex_edges". Required creating full SQLite schema. See `references/cortex-db-schema-repair-may15-2026.md` for complete procedure.

## Final Status

```
🧠 Cognitive orchestrator ready: 20/20 subsystems active
   ✓ tiered_memory
   ✓ error_learning
   ✓ skill_tracker
   ✓ brain
   ✓ cortex_flywheel
   ✓ distillation_bridge
   ✓ self_audit
   ✓ training_gym
   ✓ memory_bridge
   ✓ subconscious
   ✓ autobrowse_tracer
   ✓ context_sculptor
   ✓ tool_oracle
   ✓ trust_scorer
   ✓ unified_intelligence
   ✓ failure_prevention
   ✓ experimentation
   ✓ domain_transfer
   ✓ attention_prioritizer
   ✓ evaluation_gate
```

## Key Lessons

1. **Cognitive orchestrator does NOT auto-load** — Must be explicitly imported and initialized in `run_agent.py`
2. **Function-only modules need wrapper classes** — The orchestrator expects `__init__()` callable objects
3. **Missing files are silent failures** — `ImportError` is caught and logged as warning, not error
4. **DB schema must match exactly** — Partial schemas cause silent subsystem deactivation
5. **Use logger not print for systemd** — Print output is lost; logger.info appears in journalctl
6. **Always verify with get_status()** — Don't assume initialization succeeded

## Verification Commands

```bash
# Check subsystem status
cd /data/SpecForge/hermes-agent && source venv/bin/activate
python3 -c "
from run_agent import AIAgent
agent = AIAgent()
" 2>&1 | grep -E "orchestrator|subsystem|active|failed"

# Check individual subsystem
python3 -c "
from agent.cortex_flywheel import CortexFlywheel
cf = CortexFlywheel()
print(cf.get_stats())
"
```
