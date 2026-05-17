# Cognitive Orchestrator Initialization on DGX
## Session: May 16, 2026

## Problem

The cognitive orchestrator does NOT auto-load when Hermes starts. It must be explicitly initialized with an agent instance. Without initialization, all 20 subsystems remain inactive.

**Symptom**:
```
orchestrator.get_status() → {"subsystems": [], "active_count": 0}
```

**Expected**:
```
orchestrator.get_status() → {"subsystems": [...20 items...], "active_count": 20}
```

## Initialization Pattern

```python
from hermes_cli.cognitive_orchestrator import initialize_orchestrator

# In run_agent.py startup sequence
def start_agent():
    agent = create_agent_instance()
    
    # CRITICAL: Initialize orchestrator with agent instance
    initialize_orchestrator(agent)
    
    # Verify
    status = orchestrator.get_status()
    assert status["active_count"] == 20, f"Only {status['active_count']}/20 subsystems"
    
    return agent
```

## Common Pitfall

**Assuming auto-loading**: Many developers expect the orchestrator to initialize when `import hermes_cli` runs. It does not — the `__init__.py` does not call `initialize_orchestrator()` because it needs an agent instance which doesn't exist at import time.

**Wrong**:
```python
import hermes_cli  # Does NOT initialize orchestrator
# orchestrator has 0 subsystems
```

**Right**:
```python
import hermes_cli
from hermes_cli.cognitive_orchestrator import initialize_orchestrator

agent = create_agent()
initialize_orchestrator(agent)  # NOW it has 20 subsystems
```

## Subsystem List (20 Total)

1. memory_manager — Episodic/semantic memory
2. skill_registry — Skill loading and validation
3. knowledge_base — Cortex knowledge graph
4. distillation_bridge — Research-to-distillation pipeline
5. training_gym — Continuous self-improvement
6. subconscious_hook_wiring — Tool call hooks
7. cron_scheduler — Background job scheduling
8. session_exporter — Training data generation
9. context_injector — Prompt context management
10. tool_dispatcher — Tool routing and execution
11. error_recovery — Automatic retry and fallback
12. telemetry_collector — Metrics and logging
13. auth_manager — Credential pool management
14. plugin_loader — Dynamic plugin loading
15. model_router — Provider/model selection
16. rate_limiter — API quota management
17. cache_manager — KV cache and prefix caching
18. health_monitor — System health checks
19. backup_service — State persistence
20. notification_bus — Cross-subsystem messaging

## Verification

```python
from hermes_cli.cognitive_orchestrator import get_orchestrator

orch = get_orchestrator()
status = orch.get_status()

print(f"Active subsystems: {status['active_count']}/20")
for sub in status['subsystems']:
    print(f"  - {sub['name']}: {'✅' if sub['active'] else '❌'}")

assert status['active_count'] == 20, "Not all subsystems initialized!"
```

## Integration with Systemd Service

```ini
[Unit]
Description=Hermes Agent with Cognitive Orchestrator

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/data/SpecForge/hermes-agent/venv/bin/python3 \
  /data/SpecForge/hermes-agent/run_hermes_fixed.py \
  --init-orchestrator \
  --verify-subsystems
ExecStop=/data/SpecForge/hermes-agent/venv/bin/python3 \
  -c "from hermes_cli.cognitive_orchestrator import shutdown; shutdown()"

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 0/20 subsystems | Orchestrator not initialized | Call `initialize_orchestrator(agent)` |
| 19/20 subsystems | One subsystem failed to load | Check logs for import errors |
| Subsystem count varies | Race condition in initialization | Add `time.sleep(2)` between init and verify |
| Orchestrator None | Import order issue | Pre-import gateway/plugins before hermes_cli |

## Related

- `references/module-shadowing-fix-may16-2026.md` — Module shadowing prevents orchestrator from loading gateway/plugins
- `references/dgx-hermes-cognitive-orchestrator-init-may16-2026.md` — Full DGX-specific initialization guide
