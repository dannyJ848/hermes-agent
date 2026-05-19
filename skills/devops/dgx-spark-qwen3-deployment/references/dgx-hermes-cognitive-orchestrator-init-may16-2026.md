# DGX Hermes Cognitive Orchestrator Initialization (May 16, 2026)

## Overview

The cognitive orchestrator provides 20 subsystems for self-improvement but does NOT auto-initialize. It must be explicitly initialized with an agent instance.

## Problem

After deploying Hermes with cognitive orchestrator code, the orchestrator shows 0 active subsystems:

```python
from agent.cognitive_orchestrator import get_orchestrator
orch = get_orchestrator()
status = orch.get_status()
print(status)
# {'subsystems': {}, 'active_count': 0, 'failed_count': 0, 'session_active': False}
```

## Solution

Initialize with a mock agent (or real agent instance):

```python
from agent.cognitive_orchestrator import get_orchestrator, initialize_cognitive_systems

orch = get_orchestrator()

class MockAgent:
    def __init__(self):
        self.session_id = "dgx_session"
        self.cognitive_orchestrator = orch

mock = MockAgent()
result = initialize_cognitive_systems(mock)

status = orch.get_status()
print(f"Active: {status['active_count']}/20")  # Active: 20/20
print(f"Failed: {status['failed_count']}")     # Failed: 0
```

## Integration in run_agent.py

Add to `AIAgent.__init__` after memory setup:

```python
# Initialize cognitive orchestrator
try:
    from agent.cognitive_orchestrator import get_orchestrator, initialize_cognitive_systems
    self.cognitive_orchestrator = get_orchestrator()
    initialize_cognitive_systems(self)
    logger.info(f"Cognitive orchestrator: {self.cognitive_orchestrator.get_status()['active_count']}/20 subsystems active")
except Exception as e:
    logger.warning(f"Cognitive orchestrator init failed: {e}")
```

## Subsystems List

After initialization, all 20 subsystems are active:

1. tiered_memory
2. error_learning
3. skill_tracker
4. brain
5. cortex_flywheel
6. distillation_bridge
7. self_audit
8. training_gym
9. memory_bridge
10. subconscious
11. autobrowse_tracer
12. context_sculptor
13. tool_oracle
14. trust_scorer
15. unified_intelligence
16. failure_prevention
17. experimentation
18. domain_transfer
19. attention_prioritizer
20. evaluation_gate

## Verification

```bash
# On DGX
cd /data/SpecForge/hermes-agent
venv/bin/python -c "
import sys
sys.path.insert(0, '/data/SpecForge/hermes-agent')
from agent.cognitive_orchestrator import get_orchestrator, initialize_cognitive_systems

orch = get_orchestrator()
class MockAgent:
    def __init__(self):
        self.session_id = 'test'
        self.cognitive_orchestrator = orch

mock = MockAgent()
initialize_cognitive_systems(mock)
status = orch.get_status()
print(f'Active: {status[\"active_count\"]}/20')
print(f'Failed: {status[\"failed_count\"]}')
print(f'Subsystems: {list(status[\"subsystems\"].keys())}')
"
```

## Common Issues

**Module shadowing prevents initialization:**
If you see `No module named 'gateway.status'` errors, the gateway package is shadowed. Fix with the wrapper script pattern (see `references/gateway-module-shadowing-may16-2026.md`).

**Orphaned subsystems:**
Some subsystems exist in `agent/` but are not wired into the orchestrator. These are dead code (~211KB, ~5,500 lines). Only the 20 subsystems listed above are active.

## Key Files

- `agent/cognitive_orchestrator.py` — Orchestrator class
- `agent/cognitive_orchestrator_config.py` — Subsystem configuration
- `run_agent.py` — Integration point (AIAgent.__init__)

## Related

- `references/gateway-module-shadowing-may16-2026.md` — Module shadowing fix
- `references/dgx-hermes-complete-deployment-may14-2026.md` — Full deployment guide
- `hermes-agent:references/cognitive-orchestrator-20-subsystems-may15-2026.md` — 20/20 subsystems achievement
