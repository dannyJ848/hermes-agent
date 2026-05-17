# External Systems Audit Checklist

**Session:** May 9, 2026 — subconscious integration verification
**Context:** User asked "there is absolutely nothing left externally?" after integration

## The Audit

After surgically integrating 97 modules from `~/subconscious/` into `~/hermes-agent/`, the user wanted absolute confirmation that nothing remained external. This checklist was developed to provide that verification.

## Checklist Items

### 1. Source Code Path Verification
Check that NO source file creates or references the old path:
```bash
grep -rn 'Path.home().*subconscious\|os.path.expanduser.*subconscious\|mkdir.*subconscious\|makedirs.*subconscious' --include="*.py" ~/hermes-agent/
```

### 2. Config/Shell Files
Check all non-Python files:
```bash
grep -rn 'subconscious' --include="*.sh" --include="*.yaml" --include="*.yml" --include="*.json" ~/hermes-agent/
```

### 3. Active Config Files in ~/.hermes/
- `~/.hermes/config.yaml`
- `~/.hermes/.env`
- `~/.hermes/cortex_watchdog.sh`

### 4. Scheduled Jobs
```bash
crontab -l | grep -i subconscious
launchctl list | grep -i subconscious
```

### 5. Environment Variables
```python
import os
for k, v in os.environ.items():
    if 'subconscious' in v.lower():
        print(f"{k}={v}")
```

### 6. Python Import Path
```python
import sys
for p in sys.path:
    if 'subconscious' in p.lower():
        print(p)
```

### 7. Subprocess Spawns
```bash
grep -rn 'subprocess.*subconscious\|Popen.*subconscious\|call.*subconscious' --include="*.py" ~/hermes-agent/
```

### 8. External Directories Scan
```python
import os
home = os.path.expanduser("~")
for item in os.listdir(home):
    full = os.path.join(home, item)
    if os.path.isdir(full) and not item.startswith('.') and item != 'hermes-agent':
        py_files = []
        for root, dirs, files in os.walk(full):
            for f in files:
                if f.endswith('.py'):
                    py_files.append(os.path.join(root, f))
        if py_files and len(py_files) < 50:
            print(f"~/{item}/: {len(py_files)} .py files")
```

### 9. Standalone Scripts in Home
```python
import os
home = os.path.expanduser("~")
for item in os.listdir(home):
    if item.endswith('.py') and os.path.isfile(os.path.join(home, item)):
        print(f"~/{item}")
```

### 10. Databases in Home
```python
import os
home = os.path.expanduser("~")
for item in os.listdir(home):
    if item.endswith(('.db', '.sqlite', '.jsonl')):
        size = os.path.getsize(os.path.join(home, item))
        print(f"~/{item} ({size} bytes)")
```

## What Was Found (May 9, 2026)

| Check | Result |
|-------|--------|
| Source code path references | 0 |
| Config/shell references | 0 |
| Active config files | Clean |
| Scheduled jobs | Clean |
| Environment variables | Clean |
| Python import path | Clean |
| Subprocess spawns | 0 (false positives from docstrings only) |
| External directories | Many projects (repos/, deer-flow/, medrag/, etc.) but these are separate repositories, not Hermes cognitive systems |
| Standalone scripts | 10 training scripts in home (qwen36_franken_fullft_deepspeed.py, train_deepspeed.py, etc.) — these are training scripts, not Hermes systems |
| Databases | 3 databases: scweet_state.db, call_log.db, cerebrum_memory.db — these are application databases, not Hermes cognitive systems |

## Official Hermes Extension Points

These directories are **intentional** Hermes extension points and should NOT be treated as external:

| Directory | Purpose | Integration Status |
|-----------|---------|-------------------|
| `~/.hermes/plugins/` | User plugins — auto-loaded by Hermes plugin system | ✅ 36 evey plugins + distillation, all with `register()` |
| `~/.hermes/tools/` | User tools — registered with tool registry | ✅ 55 tools, all with `registry.register()` |
| `~/.hermes/scripts/` | Cron scripts — referenced by cronjob_tools.py | ✅ Official |
| `~/.hermes/hooks/` | Gateway hooks — referenced by gateway/hooks.py | ✅ Official |
| `~/.hermes/twitter_bridge/` | Data files for x-cookie-api skill | ✅ Official |
| `~/.hermes/local_vision/` | Cache for screen captures | ✅ Official |

## Pragmatism Lesson

When `~/subconscious/tool_capability.db` kept recreating (empty, 0 rows), the user said:
> "uhhh is it having any effect? if not let's mark it and leave it alone and audit anything else that is external that needs to be wired internally to hermes."

**Correct response:** Acknowledge the ghost file, note it will clear on `hermes restart`, and redirect to auditing other external systems. Do NOT let a zero-impact ghost block the audit.
