# DGX Cognitive Orchestrator Deployment — May 16 2026

## What Was Done

Deployed the full cognitive orchestrator on DGX Spark with all 20 subsystems active.

## Initialization Code

Added to `run_agent.py` in `AIAgent.__init__`:

```python
# After memory setup, before main loop:
from agent.cognitive_orchestrator import CognitiveOrchestrator
self.cognitive_orchestrator = CognitiveOrchestrator(self)
self.cognitive_orchestrator.initialize_cognitive_systems()
```

## Module Shadowing Fix

Used wrapper script `run_hermes_fixed.py` that pre-imports both `plugins` and `gateway` packages before importing `run_agent`:

```python
import sys, os, importlib.util
project_root = "/data/SpecForge/hermes-agent"
sys.path.insert(0, project_root)

for pkg_name in ["plugins", "gateway"]:
    init_path = os.path.join(project_root, pkg_name, "__init__.py")
    if os.path.exists(init_path) and pkg_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            pkg_name, init_path,
            submodule_search_locations=[os.path.join(project_root, pkg_name)]
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[pkg_name] = mod
        spec.loader.exec_module(mod)

from run_agent import main
import asyncio
asyncio.run(main())
```

## Verification

```python
from agent.cognitive_orchestrator import get_orchestrator
orch = get_orchestrator()
status = orch.get_status()
print(status['active_count'])  # 20
print(status['initialized'])   # True
```

## Goals Seeded

5 active goals using `hermes_cli.goals.save_goal()`:
1. `dgx_optimize_vllm` — Optimize vLLM performance and reliability
2. `dgx_learn_patterns` — Learn from user interactions and improve responses
3. `dgx_maintain_uptime` — Keep all services running 24/7
4. `dgx_distill_knowledge` — Distill insights into skills and memory
5. `dgx_monitor_health` — Monitor system health and proactively fix issues

## Environment Variables

In systemd service:
```
Environment="PYTHONPATH=/data/SpecForge/hermes-agent"
Environment="TERMINAL_ENV=ssh"
Environment="TERMINAL_SSH_HOST=macbook"
Environment="TERMINAL_SSH_USER=dannygomez"
Environment="HERMES_HOME=/home/djg6228/.hermes"
```

## Key Files

- `/data/SpecForge/hermes-agent/run_hermes_fixed.py` — Wrapper script
- `~/.config/systemd/user/hermes-agent.service` — Systemd unit
- `/data/SpecForge/hermes-agent/config.yaml` — Config with goals, terminal, web sections

## Lessons

1. Cognitive orchestrator does NOT auto-load — must explicitly initialize
2. Module shadowing fix must happen BEFORE any hermes_cli imports
3. Goals are stored in SessionDB, not in config.yaml directly
4. 20 subsystems initialize but many are "orphaned" (hooks never called in main loop)
5. The orchestrator's `get_status()` is the best way to verify initialization
