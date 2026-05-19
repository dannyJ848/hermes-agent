# Cognitive Orchestrator 20-Subsystem Initialization

## Overview
The cognitive orchestrator in `agent/cognitive_orchestrator.py` initializes 20 subsystems. This reference documents the exact initialization sequence and common failure modes.

## Subsystem List

| # | Name | Init Method | Module | Class/Function | Common Failure |
|---|------|-------------|--------|----------------|----------------|
| 1 | tiered_memory | `_init_tiered_memory` | `agent.tiered_memory` | `get_memory()` | DB lock |
| 2 | error_learning | `_init_error_learning` | `agent.error_learning` | `get_error_miner()` | Missing table |
| 3 | skill_tracker | `_init_skill_tracker` | `agent.skill_tracker` | `get_tracker()` | Import error |
| 4 | brain | `_init_brain` | `agent.brain` | `get_brain()` | Already active |
| 5 | cortex_flywheel | `_init_cortex_flywheel` | `agent.cortex_flywheel` | `CortexFlywheel()` | **DB schema: cortex_nodes table missing** |
| 6 | distillation_bridge | `_init_distillation_bridge` | `agent.distillation_bridge` | `DistillationBridge()` | **Class not found (needs wrapper)** |
| 7 | self_audit | `_init_self_audit` | `agent.self_audit_engine` | `SelfAuditEngine()` | None |
| 8 | training_gym | `_init_training_gym` | `agent.training_gym` | `TrainingGym()` | **Class not found (needs wrapper)** |
| 9 | memory_bridge | `_init_memory_bridge` | `agent.memory_cortex_bridge` | `MemoryCortexBridge()` | None |
| 10 | subconscious | `_init_subconscious` | `agent.subconscious_hook_wiring` | `SubconsciousHookWiring()` | **Class not found (needs wrapper)** |
| 11 | autobrowse_tracer | `_init_autobrowse_tracer` | `agent.autobrowse_tracer` | `AutobrowseTracer()` | None |
| 12 | context_sculptor | `_init_context_sculptor` | `agent.adaptive_context_sculptor` | `get_sculptor()` | Missing file |
| 13 | tool_oracle | `_init_tool_oracle` | `agent.tool_oracle` | `get_oracle()` | None |
| 14 | trust_scorer | `_init_trust_scorer` | `agent.epistemic_trust_scorer` | `get_trust_scorer()` | Missing file |
| 15 | unified_intelligence | `_init_unified_intelligence` | `agent.unified_intelligence_engine` | `UnifiedIntelligenceEngine()` | Missing file |
| 16 | failure_prevention | `_init_failure_prevention` | `agent.predictive_failure_prevention` | `PredictiveFailurePrevention()` | Missing file |
| 17 | experimentation | `_init_experimentation` | `agent.autonomous_experimentation` | `AutonomousExperimentationLoop()` | Missing file |
| 18 | domain_transfer | `_init_domain_transfer` | `agent.cross_domain_transfer` | `CrossDomainTransfer()` | Missing file |
| 19 | attention_prioritizer | `_init_attention_prioritizer` | `agent.attention_context_prioritizer` | `AttentionContextPrioritizer()` | Missing file |
| 20 | evaluation_gate | `_init_evaluation_gate` | `agent.self_evaluation_gate` | `SelfEvaluationGate()` | Missing file |

## Verification Script

```python
import sys
sys.path.insert(0, ".")
from agent.cognitive_orchestrator import get_orchestrator

co = get_orchestrator()

class MockAgent:
    pass

agent = MockAgent()
result = co.initialize(agent)

active = sum(1 for v in result.values() if v == "active")
total = len(result)
print(f"Cognitive Orchestrator: {active}/{total} subsystems active")
for name, status in result.items():
    icon = "✓" if status == "active" else "⚠" if status == "skipped" else "✗"
    print(f"  {icon} {name}: {status}")
```

## Expected Output (Healthy System)

```
Cognitive Orchestrator: 19/20 subsystems active
  ✓ tiered_memory: active
  ✓ error_learning: active
  ✓ skill_tracker: active
  ✓ brain: active
  ⚠ cortex_flywheel: skipped          (DB schema: cortex_nodes table missing)
  ✓ distillation_bridge: active
  ✓ self_audit: active
  ✓ training_gym: active
  ✓ memory_bridge: active
  ✓ subconscious: active
  ✓ autobrowse_tracer: active
  ✓ context_sculptor: active
  ✓ tool_oracle: active
  ✓ trust_scorer: active
  ✓ unified_intelligence: active
  ✓ failure_prevention: active
  ✓ experimentation: active
  ✓ domain_transfer: active
  ✓ attention_prioritizer: active
  ✓ evaluation_gate: active
```

## Fixing Missing Subsystems

### Missing Module Files (8 modules)
If modules 12-20 show "failed", the `.py` files are missing from `agent/`. Sync them from a working system:

```bash
# On source system
cd ~/hermes-agent/agent
tar czf /tmp/cognitive_modules.tar.gz \
  adaptive_context_sculptor.py \
  epistemic_trust_scorer.py \
  unified_intelligence_engine.py \
  predictive_failure_prevention.py \
  autonomous_experimentation.py \
  cross_domain_transfer.py \
  attention_context_prioritizer.py \
  self_evaluation_gate.py

scp /tmp/cognitive_modules.tar.gz user@target:/tmp/

# On target system
cd ~/hermes-agent/agent && tar xzf /tmp/cognitive_modules.tar.gz
```

### Missing Wrapper Classes (3 modules)
If modules 6, 8, 10 show "failed", add wrapper classes to the module files (see Wrapper Class Pattern in SKILL.md).

### Missing DB Table (1 module)
If module 5 shows "skipped", create the `cortex_nodes` table:
```bash
sqlite3 ~/.hermes/cortex.db "CREATE TABLE IF NOT EXISTS cortex_nodes (id INTEGER PRIMARY KEY, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
```

## Logging

The cognitive orchestrator logs at INFO level. To see initialization details:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Or check gateway logs:
```bash
journalctl -u hermes-gateway.service -f | grep cognitive_orchestrator
```
