# Subconscious Directory Recreation Debug — May 9-10, 2026

## Problem

After integrating all 97 modules from `~/subconscious/` into `~/hermes-agent/`, the old directory kept being recreated within 1-2 seconds after deletion with a `tool_capability.db` file.

## Root Cause Analysis (COMPLETE)

The recreation had **THREE contributing causes**, all of which must be fixed:

1. **Running hermes processes with open file handles** — `lsof -p 98882 | grep subconscious` showed `tool_capability.db` open. The process had been running for 9+ hours and had old module-level path constants cached in memory.
2. **Cached bytecode** in `__pycache__` directories — 549 directories found and cleared.
3. **Source code path constants** in some modules still used old naming/comments — fixed in `agent/cortex_flywheel.py`, `agent/cortex_compat.py`, `agent/cognitive_infrastructure_hooks.py`.

## Detection Commands

```bash
# Check which processes have files open in old directory
lsof +D ~/subconscious/ 2>/dev/null

# Or check specific hermes PIDs
ps aux | grep hermes | grep python
lsof -p <PID> | grep subconscious

# Monitor recreation with timing
cd ~ && rm -rf subconscious/ && for i in {1..10}; do sleep 1; if [ -d subconscious ]; then echo "Recreated at ${i}s"; ls -la subconscious/; break; fi; done
```

## Resolution (VERIFIED)

**Step 1: Identify running processes**
```bash
ps aux | grep hermes | grep python
# Note all PIDs — there may be multiple hermes sessions running
```

**Step 2: Check which processes have open handles**
```bash
lsof -p <PID> | grep subconscious
```

**Step 3: Kill old/stale processes** (NOT the current session)
```bash
kill <OLD_PID>  # e.g., kill 98882
```

**Step 4: Clear ALL __pycache__ directories**
Use Python script via execute_code (not terminal loops — hits same_tool_failure_halt):
```python
import shutil, os
base = os.path.expanduser("~/hermes-agent")
count = 0
for root, dirs, _ in os.walk(base):
    for d in dirs:
        if d == "__pycache__":
            shutil.rmtree(os.path.join(root, d))
            count += 1
print(f"Cleared {count} __pycache__ directories")
```

**Step 5: Fix source code path constants**
Search and replace any remaining `sys.path.insert` with "subconscious" references:
```bash
grep -r "sys.path.insert.*subconscious" ~/hermes-agent --include="*.py"
```

**Step 6: Restart hermes**
The current session's Python interpreter also has cached module state. Full restart required.

**Step 7: Verify eradication**
```bash
cd ~ && rm -rf subconscious/ && sleep 5 && ls subconscious/ 2>/dev/null || echo "SUCCESS: gone"
```

## Key Lesson

**Directory recreation after source cleanup is almost always a RUNNING PROCESS, not just cached bytecode.** Check `lsof` FIRST before assuming it's a bytecode issue. Multiple hermes processes can run simultaneously (old sessions, gateway, cron jobs) — any of them can hold open file handles that recreate deleted directories.

## Files Modified During Fix

- `agent/cortex_flywheel.py` — updated comment, path constant
- `agent/cortex_compat.py` — renamed `_SUBCONSCIOUS_DIR` → `_HERMES_DIR`
- `agent/cognitive_infrastructure_hooks.py` — updated comment
- `agent/tool_misuse_prevention.py` — already used correct path
- `agent/brain_to_toolintel.py` — already used correct path
