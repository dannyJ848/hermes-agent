# Screen-Based Autonomous Runner (No Daemon) — May 17 2026

## User Preference

User explicitly rejected systemd daemon dependency for Hermes autonomous mode. Wants screen/tmux-based persistence instead.

## Why Screen/Tmux Over Systemd

- **No daemon complexity** — No systemd service files, no `systemctl`, no journald logs
- **Interactive attach/detach** — Can `screen -r` to watch the agent work in real-time
- **Survives SSH disconnect** — Screen session persists after SSH logout
- **Simple process management** — `kill` the screen session to stop, no daemon reload needed
- **User preference** — "eliminate any daemon, I don't want it depending on any daemon"

## Implementation

### 1. Create Autonomous Runner Script

Save as `/data/SpecForge/hermes-agent/run_autonomous_hermes.py`:

```python
#!/usr/bin/env python3
import sys, os, importlib.util, time, json, re
from datetime import datetime

project_root = '/data/SpecForge/hermes-agent'
sys.path.insert(0, project_root)

# Pre-load gateway and plugins (module shadowing fix)
gateway_init = os.path.join(project_root, 'gateway', '__init__.py')
if os.path.exists(gateway_init) and 'gateway' not in sys.modules:
    spec = importlib.util.spec_from_file_location('gateway', gateway_init,
        submodule_search_locations=[os.path.join(project_root, 'gateway')])
    gateway_pkg = importlib.util.module_from_spec(spec)
    sys.modules['gateway'] = gateway_pkg
    spec.loader.exec_module(gateway_pkg)

plugins_init = os.path.join(project_root, 'plugins', '__init__.py')
if os.path.exists(plugins_init) and 'plugins' not in sys.modules:
    spec = importlib.util.spec_from_file_location('plugins', plugins_init,
        submodule_search_locations=[os.path.join(project_root, 'plugins')])
    plugins_pkg = importlib.util.module_from_spec(spec)
    sys.modules['plugins'] = plugins_pkg
    spec.loader.exec_module(plugins_pkg)

from run_agent import main

AUTONOMOUS_TASKS = [
    'Check system status and report any issues',
    'Review recent logs for errors or warnings',
    'Update knowledge base with new findings',
    'Run self-diagnostic on all subsystems',
    'Check for updates or improvements needed',
    'Monitor DGX GPU utilization and temperature',
    'Verify vLLM service health and performance',
    'Check disk space and cleanup if needed',
    'Review and optimize configuration files',
    'Run security audit on exposed services',
]

def get_next_task():
    task_file = '/tmp/hermes_autonomous_state.json'
    if os.path.exists(task_file):
        with open(task_file, 'r') as f:
            state = json.load(f)
        idx = state.get('task_index', 0) % len(AUTONOMOUS_TASKS)
    else:
        idx = 0
    task = AUTONOMOUS_TASKS[idx]
    with open(task_file, 'w') as f:
        json.dump({'task_index': (idx + 1) % len(AUTONOMOUS_TASKS)}, f)
    return task

print(f'[{datetime.now()}] AUTONOMOUS HERMES STARTED')
print(f'[{datetime.now()}] Model: /data/models/Qwen3.6-27B-Uncensored')
print(f'[{datetime.now()}] Provider: local-dgx')
print(f'[{datetime.now()}] Mode: Fully autonomous with tool calling')
print('='*60)

iteration = 0
while True:
    iteration += 1
    try:
        task = get_next_task()
        print(f'\n[{datetime.now()}] TASK {iteration}: {task}')
        
        result = main(
            query=task,
            model='/data/models/Qwen3.6-27B-Uncensored',
            api_key='not-needed',
            base_url='http://localhost:8000/v1',
            max_turns=10,
            verbose=True
        )
        
        print(f'[{datetime.now()}] Task completed')
        print(f'[{datetime.now()}] Waiting 30s before next task...')
        time.sleep(30)
        
    except KeyboardInterrupt:
        print(f'\n[{datetime.now()}] Stopped by user')
        break
    except Exception as e:
        print(f'[{datetime.now()}] Error: {e}')
        import traceback
        traceback.print_exc()
        time.sleep(60)
```

### 2. Start in Screen Session

```bash
# Kill any existing session
screen -S hermes_auto -X quit 2>/dev/null
sleep 2

# Start new session
cd /data/SpecForge/hermes-agent
screen -dmS hermes_auto bash -c '
    export PYTHONPATH=/data/SpecForge/hermes-agent
    /data/SpecForge/hermes-agent/venv/bin/python3 \
        /data/SpecForge/hermes-agent/run_autonomous_hermes.py \
        > /tmp/hermes_auto_out.txt 2>&1
'

# Verify
screen -ls
```

### 3. Monitor and Control

```bash
# Attach to watch live
screen -r hermes_auto

# Detach (leave running)
Ctrl+A then D

# Check logs without attaching
tail -f /tmp/hermes_auto_out.txt

# Check if running
ps aux | grep run_autonomous | grep -v grep

# Stop gracefully
screen -S hermes_auto -X quit

# Kill forcefully
kill -9 $(pgrep -f run_autonomous)
```

### 4. Send Custom Tasks

```bash
# Write task to queue file
echo '{"id": "custom-001", "query": "Your custom task here"}' \
    >> /tmp/hermes_dgx_requests.jsonl
```

The runner can be modified to check this queue file and prioritize user tasks over autonomous tasks.

## Comparison: Daemon vs Screen

| Aspect | Systemd Daemon | Screen Session |
|--------|---------------|----------------|
| Startup | `systemctl start` | `screen -dmS` |
| Logs | `journalctl` | `tail -f /tmp/...` |
| Attach | Not possible | `screen -r` |
| Auto-restart | Built-in | Manual |
| Boot start | `systemctl enable` | Cron or manual |
| Complexity | High (service files) | Low (one command) |
| User preference | Rejected | Preferred |

## Pitfalls

1. **Screen session name collisions** — Always kill existing session before starting new one: `screen -S hermes_auto -X quit 2>/dev/null`

2. **PYTHONPATH must be set** — The screen session needs `PYTHONPATH=/data/SpecForge/hermes-agent` or imports will fail

3. **Log rotation** — Long-running sessions produce large log files. Add log rotation or truncate periodically

4. **GPU memory leaks** — If the agent crashes, vLLM may hold GPU memory. Monitor with `nvidia-smi`

5. **SSH disconnect kills foreground** — Always use `screen -dmS` (detached) not `screen` (attached) when starting remotely
