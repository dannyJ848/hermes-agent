# Cognitive Orchestrator Module Sync (Cross-System)

## Problem

The cognitive orchestrator (`agent/cognitive_orchestrator.py`) initializes 20 subsystems. When deploying Hermes Agent across multiple systems (e.g., MacBook → DGX), the target system may be missing some cognitive subsystem files, causing initialization failures.

## Detection

Run the cognitive orchestrator initialization test:

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
for name, status in sorted(result.items()):
    icon = "✓" if status == "active" else ("⚠" if status == "skipped" else "✗")
    print(f"   {icon} {name}: {status}")
```

**Expected:** 19/20 active (cortex_flywheel skipped due to missing DB table is normal)
**Problem:** <19 active means missing module files

## Root Cause

The cognitive orchestrator imports modules by file name:

```python
# From cognitive_orchestrator.py _init_context_sculptor()
from agent.adaptive_context_sculptor import get_sculptor
```

If `adaptive_context_sculptor.py` doesn't exist on the target system, this init method fails.

## Solution: Cross-System Module Sync

### Step 1: Identify missing files

Compare `agent/*.py` between source and target systems:

```bash
# On source system
ls ~/hermes-agent/agent/*.py | sort > /tmp/source_modules.txt

# On target system
ls ~/hermes-agent/agent/*.py | sort > /tmp/target_modules.txt

# Compare
diff /tmp/source_modules.txt /tmp/target_modules.txt
```

### Step 2: Create tar archive

```bash
cd ~/hermes-agent/agent

# Tar the missing modules
tar czf /tmp/cognitive_modules.tar.gz \
  adaptive_context_sculptor.py \
  epistemic_trust_scorer.py \
  unified_intelligence_engine.py \
  predictive_failure_prevention.py \
  autonomous_experimentation.py \
  cross_domain_transfer.py \
  attention_context_prioritizer.py \
  self_evaluation_gate.py
```

### Step 3: Transfer to target

```bash
scp /tmp/cognitive_modules.tar.gz user@target:/tmp/
```

### Step 4: Extract on target

```bash
cd ~/hermes-agent/agent
tar xzf /tmp/cognitive_modules.tar.gz
```

### Step 5: Verify imports

```bash
cd ~/hermes-agent
source venv/bin/activate

python3 -c "from agent.adaptive_context_sculptor import get_sculptor; print('OK')"
python3 -c "from agent.epistemic_trust_scorer import get_trust_scorer; print('OK')"
python3 -c "from agent.unified_intelligence_engine import UnifiedIntelligenceEngine; print('OK')"
python3 -c "from agent.predictive_failure_prevention import PredictiveFailurePrevention; print('OK')"
python3 -c "from agent.autonomous_experimentation import AutonomousExperimentationLoop; print('OK')"
python3 -c "from agent.cross_domain_transfer import CrossDomainTransfer; print('OK')"
python3 -c "from agent.attention_context_prioritizer import AttentionContextPrioritizer; print('OK')"
python3 -c "from agent.self_evaluation_gate import SelfEvaluationGate; print('OK')"
```

### Step 6: Restart gateway

```bash
sudo systemctl restart hermes-gateway.service
```

### Step 7: Verify

```bash
hermes -z "test"
```

Check logs for:
```
Cognitive Orchestrator: 19/20 subsystems active
```

## Naming Mismatches

The orchestrator's import paths may not match the actual file names. The orchestrator uses these imports:

| Init Method | Import Statement | Actual File |
|-------------|------------------|-------------|
| `_init_context_sculptor` | `from agent.adaptive_context_sculptor import get_sculptor` | `adaptive_context_sculptor.py` |
| `_init_trust_scorer` | `from agent.epistemic_trust_scorer import get_trust_scorer` | `epistemic_trust_scorer.py` |
| `_init_unified_intelligence` | `from agent.unified_intelligence_engine import UnifiedIntelligenceEngine` | `unified_intelligence_engine.py` |
| `_init_failure_prevention` | `from agent.predictive_failure_prevention import PredictiveFailurePrevention` | `predictive_failure_prevention.py` |
| `_init_experimentation` | `from agent.autonomous_experimentation import AutonomousExperimentationLoop` | `autonomous_experimentation.py` |
| `_init_domain_transfer` | `from agent.cross_domain_transfer import CrossDomainTransfer` | `cross_domain_transfer.py` |
| `_init_attention_prioritizer` | `from agent.attention_context_prioritizer import AttentionContextPrioritizer` | `attention_context_prioritizer.py` |
| `_init_evaluation_gate` | `from agent.self_evaluation_gate import SelfEvaluationGate` | `self_evaluation_gate.py` |

**Key insight:** The file name doesn't need to match the subsystem name — only the import path matters. The orchestrator knows the actual file names.

## Wrapper Classes for Function-Based Modules

Some modules export functions, not classes. The orchestrator expects classes. Add wrapper classes:

### Example: distillation_bridge.py

```python
# At bottom of file, after all function definitions

class DistillationBridge:
    def __init__(self):
        self._ensure_tips_table()
    
    def _ensure_tips_table(self):
        _ensure_tips_table()
    
    def bottom_up_store(self, tool_name, args, status, speed_ms, error="", lesson="", failure_stage=""):
        return bottom_up_store(tool_name, args, status, speed_ms, error, lesson, failure_stage)
    
    def top_down_recall(self, task_context, max_items=None):
        return top_down_recall(task_context, max_items)
```

### Example: training_gym.py

```python
class TrainingGym:
    def __init__(self):
        init_db()
        seed_exercises()
    
    def get_next_exercise(self, category=None, tier=None):
        return get_next_exercise(category, tier)
    
    def record_attempt(self, exercise_id, score, max_score, tools_used=None, errors=None):
        return record_attempt(exercise_id, score, max_score, tools_used, errors)
    
    def get_stats(self):
        return get_stats()
```

## Common Issues

### Issue: Module imports but class not found
**Symptom:** `ImportError: cannot import name 'ClassName'`
**Fix:** Check if the module exports functions only. If so, add a wrapper class.

### Issue: Module file missing
**Symptom:** `ModuleNotFoundError: No module named 'agent.module_name'`
**Fix:** The file doesn't exist. Sync it from source system.

### Issue: DB table missing
**Symptom:** `cortex_flywheel: skipped` with "no such table: cortex_nodes"
**Fix:** This is expected if the cortex DB hasn't been initialized. Create the table:
```bash
sqlite3 ~/.hermes/cortex.db "CREATE TABLE IF NOT EXISTS cortex_nodes (id INTEGER PRIMARY KEY, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
```

### Issue: Gateway not picking up changes
**Symptom:** Still shows old subsystem count after sync
**Fix:** Restart the gateway: `sudo systemctl restart hermes-gateway.service`

## Verification Script

Save this as `verify_cognitive_subsystems.py`:

```python
#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, ".")

from agent.cognitive_orchestrator import get_orchestrator

co = get_orchestrator()

class MockAgent:
    pass

agent = MockAgent()
result = co.initialize(agent)

active = sum(1 for v in result.values() if v == "active")
skipped = sum(1 for v in result.values() if v == "skipped")
failed = sum(1 for v in result.values() if v == "failed")
total = len(result)

print(f"Cognitive Orchestrator: {active}/{total} subsystems active")
print(f"  Skipped: {skipped}, Failed: {failed}")
print()
for name, status in sorted(result.items()):
    icon = "✓" if status == "active" else ("⚠" if status == "skipped" else "✗")
    print(f"   {icon} {name}: {status}")

if active >= 19:
    print("\n✓ Healthy — 19+ subsystems active")
else:
    print(f"\n✗ Unhealthy — only {active}/{total} active")
    print("  Missing modules need to be synced from source system")
```

Run with:
```bash
cd ~/hermes-agent
source venv/bin/activate
python3 verify_cognitive_subsystems.py
```
