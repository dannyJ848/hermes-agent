---
name: v0.13-integration-playbook
description: Surgical integration of upstream Hermes v0.13.0 with heavy custom code. Preserves all custom modules while getting latest upstream features.
version: 1.0
---

# v0.13 Integration Playbook

## When to Use
You have a heavily customized Hermes branch (900+ local commits) and want to integrate upstream v0.13.0 without breaking custom code.

## Prerequisites
- Custom code is in separate files (not modifying upstream files)
- Git remote `upstream` points to NousResearch/hermes-agent
- Training or other long-running processes are active

## Procedure

### Step 1: Create Integration Branch
```bash
cd ~/hermes-agent
git fetch upstream main
git checkout -b v0.13-integration upstream/main
```

### Step 2: Cherry-Pick Custom Files
```bash
# Port all custom files from your branch
git checkout <your-branch> -- hermes_cli/subconscious/
git checkout <your-branch> -- plugins/learning-brain/
git checkout <your-branch> -- hermes_cli/instant_context.py hermes_cli/context_updater.py
git checkout <your-branch> -- custom_dflash/
git checkout <your-branch> -- agent/cortex_access.py agent/error_learning.py agent/memory_learning.py
# ... etc
```

### Step 3: Fix Import Guards
Custom plugins often import from `hermes_cli/` which may not be on path in v0.13. Add guards:
```python
try:
    from hermes_brain import HermesBrain
except ImportError:
    HermesBrain = None

try:
    from context_updater import ContextUpdater
except ImportError:
    ContextUpdater = None
```

Also guard singleton creation:
```python
def _get_brain():
    global _brain
    if _brain is None and HermesBrain is not None:
        _brain = HermesBrain()
    return _brain
```

### Step 4: Test Everything
```bash
hermes --version  # Should show v0.13.0
python3 hermes_cli/instant_context.py  # Should load without errors
python3 -c "from hermes_cli.subconscious.autobrowse_tracer import AutobrowseTracer; print('OK')"
python3 -c "
import sys
sys.path.insert(0, 'plugins/learning-brain')
import __init__
print('learning-brain: OK')
"
```

### Step 5: Commit and Push
```bash
git add -A
git commit -m "v0.13 integration: port all custom code"
git push origin v0.13-integration
```

### Step 6: Merge to Main Branch
```bash
git checkout <your-main-branch>
git merge v0.13-integration --no-edit
# Resolve any conflicts (usually just plugins/learning-brain/__init__.py)
git push origin <your-main-branch>
```

## Conflict Resolution

### plugins/learning-brain/__init__.py
This file often conflicts because both branches modified it. Resolution:
1. Keep the v0.13 version (with import guards)
2. Remove all `<<<<<<< HEAD` / `=======` / `>>>>>>> v0.13-integration` markers
3. Ensure all `if _brain is None and HermesBrain is not None:` patterns are intact
4. Syntax check: `python3 -c "import py_compile; py_compile.compile('plugins/learning-brain/__init__.py', doraise=True)"`

### Other Files
For files you don't care about (website/, tests/, scripts/, optional-skills/):
```bash
git checkout --ours website/  # Keep upstream v0.13 versions
```

For core files you didn't modify (agent/, gateway/, tools/):
```bash
git checkout --ours agent/auxiliary_client.py  # Keep upstream
```

## Key v0.13 Features Now Active
- Secret redaction ON by default
- Post-write delta lint (syntax check on write_file/patch)
- `no_agent` cron watchdog mode
- SearXNG search backend
- Brave Search + DDGS providers
- MCP SSE transport + OAuth
- Gateway auto-resume after restart
- 7 i18n locales
- ProviderProfile ABC (pluggable providers)

## Verification Post-Merge
```bash
hermes --version  # v0.13.0
python3 hermes_cli/instant_context.py  # loads
python3 -c "from hermes_cli.subconscious.autobrowse_injector import record_tool_call; print('OK')"
git log --oneline HEAD..upstream/main | wc -l  # Should be 0
```
