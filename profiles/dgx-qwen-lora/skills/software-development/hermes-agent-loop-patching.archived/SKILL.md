---
name: hermes-agent-loop-patching
description: How to find and patch the Hermes agent loop in run_agent.py to change core behavior (anti-stop, auto-continue, forced tool calls, etc.). File is ~9000 lines — requires surgical approach.
---

# Patching the Hermes Agent Loop (run_agent.py)

## Why This Is Hard
- `run_agent.py` is ~9000 lines with deeply nested control flow
- The main iteration loop is a `while` at line ~6688 (`while api_call_count < self.max_iterations`)
- Tool calls vs text-only responses branch at line ~8054 (`if assistant_message.tool_calls:`)
- The "no tool calls" / break path starts at line ~8299 (`else: # No tool calls - this is the final response`)
- Bash escaping will betray you on complex grep/read commands — use Python scripts instead

## Step-by-Step Approach

### 1. Find the Target Line
Use a Python script to search, NOT bash grep with complex patterns:
```python
#!/usr/bin/env python3
with open("run_agent.py") as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if "YOUR TARGET STRING" in line:
        print(f"Line {i}: {line.rstrip()}")
```

### 2. Read Context Around Target
Use `read_file` with precise line numbers. The key landmarks:
- **Line 6688**: `while api_call_count < self.max_iterations` — main loop start
- **Line 8054**: `if assistant_message.tool_calls:` — tool call branch
- **Line 8299**: `else:` — no-tool-calls branch (final response / break)
- **Line 8300**: `# No tool calls - this is the final response`
- **Line 8301**: `final_response = assistant_message.content or ""`
- **Line 8585**: `# Plugin hook: post_llm_call` — after loop completes

### 3. Write a Patch Script
Do NOT try inline bash Python. Write a complete `.py` file:
```python
#!/path/to/venv/bin/python3
import sys
TARGET = "/path/to/run_agent.py"
with open(TARGET) as f:
    lines = f.readlines()

# Find target
for i, line in enumerate(lines):
    if "TARGET COMMENT" in line:
        # Insert code AFTER this line
        inject = "YOUR CODE HERE\n"
        lines.insert(i + 1, inject)
        break

with open(TARGET, "w") as f:
    f.writelines(lines)
```

### 4. Verify with AST (Not Import)
```bash
/path/to/venv/bin/python3 -c "import ast; ast.parse(open('run_agent.py').read()); print('OK')"
```

### 5. Test Before Restarting Gateway
```bash
/path/to/venv/bin/python3 run_agent.py --gateway --config ~/.hermes/config.yaml --test
```

## Known Patches Applied

### aggressive_continue (Apr 2026)
- **Location**: Lines 8301-8340 (injected after "No tool calls" comment)
- **What**: When model produces text-only response AND `aggressive_continue: true` in config, injects a user message forcing continuation instead of breaking
- **Config**: `aggressive_continue: true` in `~/.hermes/config.yaml`
- **Files**: `~/subconscious/patch_aggressive_continue.py` (patcher), `~/subconscious/self_awareness.py` (stop detector)

## Common Patch Bugs (from Apr 2026 debugging)

### Bug: `NameError: 'x' is not defined` (scope leak)
Variables defined inside inner functions (like `_stream_response` at L3883) are NOT accessible in the main loop scope (L9000+). If you patch code in the main loop that references a variable from a streaming method, it will crash with `NameError`.
- **Example**: `has_tool_calls` was defined in `_stream_response()` but referenced at L9098 in the main loop. Crashed every turn.
- **Fix**: Either remove the reference entirely or compute the value locally (e.g., check `assistant_message.tool_calls` instead).

### Bug: `AttributeError: 'AIAgent' object has no attribute 'x'` (uninitialized attribute)
If you use `self._some_attribute` in the main loop but never initialize it in `__init__`, it crashes when the attribute hasn't been set yet.
- **Example**: `self._aggressive_continue_enabled` at L8950 was only set at L9056 (conditional path), so first access crashed.
- **Fix**: ALWAYS use `getattr(self, '_some_attribute', default)` instead of direct `self._some_attribute` access for attributes that may not be initialized. Safer pattern:
  ```python
  # BAD — crashes if not initialized
  if self._aggressive_continue_enabled:
  
  # GOOD — returns False if not set
  if getattr(self, '_aggressive_continue_enabled', False):
  ```

### Bug: Ghost injection sections survive code changes (stale bytecode)
Disabled code sections (commented out) can STILL inject if `__pycache__/` contains stale `.pyc` files. The gateway uses `importlib` which can load cached bytecode even after source changes.
- **Symptom**: [ACTIVE INFERENCE], [PERSPECTIVE DIVERSITY], [META-INSIGHTS] etc. appearing in agent output despite being commented out in source.
- **Fix**: Before restarting gateway, clear ALL pycache:
  ```bash
  rm -rf ~/.hermes/plugins/*/__pycache__/ ~/.hermes/plugins/__pycache__/
  rm -rf ~/hermes-agent/gateway/__pycache__/
  hermes gateway restart
  ```
  There are 38+ plugin directories — wildcard is essential. Restarting gateway alone is NOT enough if pycache is stale.

### Bug: Gateway restart doesn't reload patched run_agent.py
The gateway process persists across restarts if managed by launchd. After patching `run_agent.py`, verify the running process picked up changes:
  ```bash
  # Check when gateway started vs when file was modified
  ls -la ~/hermes-agent/gateway/run.py | awk '{print $6,$7,$8}'
  ps aux | grep 'gateway run' | grep -v grep
  # If gateway started BEFORE file modification, restart again
  ```

## Pitfalls
- **Bash escaping WILL fail on this file**: I tried grep, awk, inline python -c, heredocs — ALL produced garbled output or syntax errors on run_agent.py's 9000 lines. The ONLY reliable approach is writing a complete .py file with write_file and executing it.
- **Indentation is 20 spaces**: The main loop code is deeply nested — match exactly
- **PII redaction**: terminal output may redact variables like `api_key` — don't "fix" these
- **Gateway must restart**: Python caches modules. Kill process, restart, verify PID
- **Multiple run_agent processes**: After crash, old processes may linger. Check with `ps aux | grep run_agent`
- **The patch tool has phantom lint errors**: Reports ES5 errors (Set, Map, Promise) from stale checker — ignore them
- **read_file shows PII-redacted content**: Some lines show `***` instead of real values — this is normal
- **ALWAYS clear __pycache__ before restart**: Stale `.pyc` files override source changes. This caused ghost injection sections to persist for 3+ sessions despite being disabled in code. See "Ghost injection sections" bug above.
- **ALWAYS use getattr for conditional attributes**: Any `self._attr` that isn't set in `__init__` MUST use `getattr(self, '_attr', default)`. Missing this caused `_aggressive_continue_enabled` crash on every turn.

## Self-Awareness Lesson
Danny caught me stopping 4+ times while working on this patch. The irony of stopping while building an anti-stop system was not lost. The fix required BOTH:
1. **Structural**: Code-level enforcement in run_agent.py (aggressive_continue)
2. **Behavioral**: Identity/SOUL.md rules + self-awareness module (detect_stop logging)
