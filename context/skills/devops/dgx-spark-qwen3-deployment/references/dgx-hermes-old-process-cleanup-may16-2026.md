# DGX Hermes Old Process Cleanup (May 16, 2026)

## Problem

After deploying the module shadowing fix (run_hermes_fixed.py wrapper), old Hermes processes started via `venv/bin/hermes --resume` continue running. These old processes:
- Use broken imports (plugins/gateway shadowed by hermes_cli files)
- Cause confusing error logs
- Consume memory and CPU
- May interfere with the new fixed process

## Symptoms

```bash
ps aux | grep hermes | grep -v grep
```

Shows MULTIPLE Hermes processes:
```
djg6228   242054  ...  venv/bin/hermes --resume           # OLD — broken imports
djg6228   247019  ...  python3 run_hermes_fixed.py        # NEW — fixed
djg6228    70056  ...  venv/bin/python gateway/run        # Gateway service
djg6228    2161   ...  python3 dgx_distillation_daemon.py # Distillation daemon
```

The old process (242054) continues logging errors like:
```
WARNING:run_agent:Memory provider plugin init failed: No module named 'plugins.memory'
```

## Fix

Kill old processes, keep new ones:

```bash
# Identify old processes (hermes binary, NOT run_hermes_fixed.py)
ps aux | grep "venv/bin/hermes" | grep -v "run_hermes_fixed" | grep -v grep

# Kill them
for pid in $(ps aux | grep "venv/bin/hermes" | grep -v "run_hermes_fixed" | grep -v grep | awk '{print $2}'); do
    kill -9 $pid
done

# Verify only fixed process remains
ps aux | grep hermes | grep -v grep
# Should show: run_hermes_fixed.py, gateway/run, distillation_daemon
```

## Prevention

When deploying a new Hermes wrapper:
1. Check for old processes BEFORE starting new one
2. Kill old processes
3. Start new wrapper
4. Verify only expected processes are running

## Systemd Service Update

Ensure the service file uses the wrapper, not the old binary:

```ini
# CORRECT
ExecStart=/data/SpecForge/hermes-agent/venv/bin/python3 /data/SpecForge/hermes-agent/run_hermes_fixed.py

# INCORRECT (old pattern)
ExecStart=/data/SpecForge/hermes-agent/venv/bin/hermes --resume
```

## Verification

```bash
# Check process tree
pstree -p | grep hermes

# Check systemd status
systemctl --user status hermes-agent

# Check logs for module shadowing errors
journalctl --user -u hermes-agent -n 50 | grep -i "module\|shadow\|not a package"
# Should show NO errors after fix
```

## Related

- `references/gateway-module-shadowing-may16-2026.md` — Module shadowing fix
- `references/dgx-hermes-complete-deployment-may14-2026.md` — Full deployment guide
