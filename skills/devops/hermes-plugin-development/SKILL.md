---
name: hermes-plugin-development
description: Build, debug, and wire Hermes Agent plugins that register hooks, tools, or context engines. Covers plugin structure, hook registration, Python version compatibility, and config activation.
version: 1.0.0
author: Hermes Agent
trigger: When building a new Hermes plugin, registering hooks, or wiring self-improvement systems into the agent runtime.
---

# Hermes Plugin Development

## Plugin Structure

Every directory plugin needs three files:

```
plugins/<name>/
  plugin.yaml      # Manifest
  __init__.py      # register(ctx) entry point
  plugin.py        # Optional: additional module code
```

### plugin.yaml

```yaml
name: my-plugin
version: 1.0.0
description: What this plugin does
author: You
kind: standalone          # or backend, exclusive, platform
provides_hooks:
  - pre_tool_call
  - post_tool_call
  - on_session_start
  - on_session_end
```

### __init__.py

```python
def register(ctx):
    """Register hooks, tools, or skills."""
    ctx.register_hook("pre_tool_call", my_pre_hook)
    ctx.register_hook("post_tool_call", my_post_hook)
    ctx.register_hook("on_session_start", my_start_hook)
    print(f"[{ctx.manifest.name}] Plugin loaded")
```

## Available Hooks

| Hook | Fires When | Can Block? | Kwargs |
|------|-----------|------------|--------|
| `pre_tool_call` | Before every tool dispatch | Yes (return string = block msg) | tool_name, args, task_id, session_id, tool_call_id |
| `post_tool_call` | After every tool completes | No (observational) | tool_name, args, result, duration_ms, task_id, session_id |
| `on_session_start` | New conversation begins | No | session_id, user_message |
| `on_session_end` | Conversation ends | No | session_id, final_response |
| `transform_tool_result` | After post_tool_call | Yes (return string replaces result) | tool_name, args, result, ... |
| `pre_llm_call` | Before API request | No | messages, model, ... |
| `post_llm_call` | After API response | No | response, duration_ms, ... |

## Hook Return Semantics

- **pre_tool_call**: Return `None` to allow. To block, return a dict:
  ```python
  {"action": "block", "message": "Reason the tool was blocked"}
  ```
  Returning a plain string will NOT block — the caller (`get_pre_tool_call_block_message`) specifically checks for `result.get("action") == "block"`.
- **post_tool_call**: Return value ignored (observational only)
- **transform_tool_result**: Return `str` to replace the result

## Wiring Self-Improvement Systems

To wire a learning brain into the agent runtime:

```python
# In __init__.py
import sys
from pathlib import Path

HERMES_ROOT = Path(__file__).resolve().parent.parent.parent
if str(HERMES_ROOT / "hermes_cli") not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT / "hermes_cli"))

from hermes_brain import HermesBrain

_brain = None

def _get_brain():
    global _brain
    if _brain is None:
        _brain = HermesBrain()
    return _brain

def pre_tool_call_hook(**kwargs):
    brain = _get_brain()
    check = brain.before_tool_call(
        kwargs.get("tool_name"),
        kwargs.get("args", {}),
        kwargs.get("session_id", "")
    )
    if check.get("action") == "BLOCK":
        # MUST return dict with action="block" — plain string won't block
        return {
            "action": "block",
            "message": f"[BLOCKED] {check.get('reason')}"
        }
    return None

def post_tool_call_hook(**kwargs):
    brain = _get_brain()
    brain.after_tool_call(
        kwargs.get("tool_name"),
        kwargs.get("args", {}),
        kwargs.get("result"),
        error=extract_error(kwargs.get("result"))
    )

def register(ctx):
    ctx.register_hook("pre_tool_call", pre_tool_call_hook)
    ctx.register_hook("post_tool_call", post_tool_call_hook)
```

## Enabling the Plugin

Add to `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - existing-plugin-1
    - my-new-plugin
```

### CRITICAL: Config File Location

Hermes reads `config.yaml` from **`~/.hermes/config.yaml`**, NOT from the repo directory (`~/hermes-agent/config.yaml`).

**Symptom:** Plugins exist in `~/.hermes/plugins/` but `discover_plugins()` shows "0 enabled" or skips them with "not in plugins.enabled".

**Root cause:** You edited `~/hermes-agent/config.yaml` but Hermes loads from `~/.hermes/config.yaml`.

**Fix:**
```bash
# Check which config Hermes actually loads
python3 -c "from hermes_cli.config import get_config_path; print(get_config_path())"
# → /home/user/.hermes/config.yaml  (NOT the repo path)

# Edit the HOME config, not the repo config
nano ~/.hermes/config.yaml
```

### Plugin Enablement Format

Two formats exist. The modern format uses `plugins.enabled` and `plugins.disabled` lists:

```yaml
plugins:
  disabled:
    - plugin-i-dont-want
  enabled:
    - my-plugin-1
    - my-plugin-2
```

The old format used flat module paths (`hermes_cli.plugins.memory`) and is deprecated for user plugins.

### Cross-Machine Plugin Sync

When deploying Hermes to a new machine, plugins in `~/.hermes/plugins/` do NOT sync automatically. To achieve tool parity:

```bash
# On source machine (e.g., MacBook)
ls ~/.hermes/plugins/ | wc -l  # e.g., 43 plugins

# Sync to target machine (e.g., DGX)
rsync -avz --exclude='__pycache__' ~/.hermes/plugins/ user@target:/home/user/.hermes/plugins/

# Copy the plugins.enabled config section too
# Edit target's ~/.hermes/config.yaml to match source's plugins.enabled list
```

**Tool count check before/after:**
```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
from model_tools import get_tool_definitions
tools = get_tool_definitions(quiet_mode=True)
print(f'Total tools: {len(tools)}')
"
# Before sync: ~21 tools (core only)
# After sync + enable: ~84+ tools (core + plugins)
```

## Python Version Compatibility (CRITICAL)

**The system Python may be 3.8 but Hermes needs 3.10+.**

### Symptom
```
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

### Root Cause
Code uses Python 3.10+ union syntax: `def foo() -> Path | None:`

### Fix

**Always use the venv Python:**
```bash
cd ~/hermes-agent && source venv/bin/activate && python3 --version
# Should show 3.11.14, not 3.8.8
```

**If you must patch core files for 3.8 compatibility:**
```python
# Replace: def foo() -> Path | None:
# With:    def foo() -> Optional[Path]:
# And add: from typing import Optional
```

**Bulk fix script for union syntax:**
```python
import re

with open('file.py', 'r') as f:
    content = f.read()

# Fix return types: ) -> X | None:
content = re.sub(r'\) -> ([A-Za-z_][A-Za-z0-9_\[\]]*) \| None:', r') -> Optional[\1]:', content)

# Fix param types: param: X | None =
content = re.sub(r': ([A-Za-z_][A-Za-z0-9_\[\]]*) \| None =', r': Optional[\1] =', content)

with open('file.py', 'w') as f:
    f.write(content)
```

## Testing Plugin Loading

```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
from hermes_cli.plugins import PluginManager
pm = PluginManager()
pm.discover_and_load()
for name, plugin in pm._plugins.items():
    print(f'{name}: enabled={plugin.enabled}, hooks={plugin.hooks_registered}')
"
```

## Verifying Plugin Tools and Hooks Are Operational

**Critical:** `hermes tools list` does **NOT** show plugin-registered tools. It only lists built-in core toolsets. Use `PluginManager` introspection instead.

### Quick verification
```python
from hermes_cli.plugins import PluginManager
pm = PluginManager()
pm.discover_and_load()

plugin = pm._plugins.get('my-plugin')
print(f"Tools: {plugin.tools_registered}")   # ['screen_capture', 'gui_click', ...]
print(f"Hooks: {plugin.hooks_registered}")   # ['pre_llm_call', 'post_tool_call', ...]
print(f"Enabled: {plugin.enabled}")
print(f"Error: {plugin.error}")
```

### Confirm hooks are wired into the agent loop
```bash
grep -n 'invoke_hook.*"pre_llm_call"'   ~/hermes-agent/run_agent.py
grep -n 'invoke_hook.*"post_llm_call"'  ~/hermes-agent/run_agent.py
grep -n 'get_pre_tool_call_block_message' ~/hermes-agent/run_agent.py
grep -n 'invoke_hook.*"post_tool_call"'  ~/hermes-agent/model_tools.py
grep -n 'invoke_hook.*"on_session_start"\|invoke_hook.*"on_session_end"' ~/hermes-agent/run_agent.py
```

See `references/plugin-tool-verification.md` for full audit script and CLI command reference.

## Pitfalls

- **BUILDING WITHOUT WIRING IS WASTE**: The user will call out dead code. Every cognitive system, module, or script in `~/subconscious/` must have a live hook calling it, or it's useless. Before building anything new, verify the previous build is wired and producing data. Check `skill_rewards`, `tool_routing_decisions`, `tip_injection_attempts` — if they're empty, the wiring failed.
- **Wrong directory**: Plugins go in `plugins/<name>/` or `~/.hermes/plugins/<name>/`, NOT `hermes_cli/plugins/`
- **Missing `__init__.py`**: The file must exist with a `register(ctx)` function
- **Python 3.8 syntax**: Any `X | None` type annotation will crash on system Python. Use `Optional[X]`
- **Import path**: `hermes_cli/` must be on `sys.path` for brain imports
- **Singleton pattern**: Brain instances should be module-level singletons, not created per-hook
- **Config activation**: Plugin must be in `plugins.enabled` list or it won't load
- **Hook signature**: Hooks receive `**kwargs`, not positional args. Extract with `.get()`
- **Block semantics**: `pre_tool_call` must return `{"action": "block", "message": "..."}` dict to block. Plain string return will NOT block — `get_pre_tool_call_block_message()` checks `result.get("action") == "block"`.
- **Hook kwargs**: `pre_tool_call` receives `tool_name, args, task_id, session_id, tool_call_id`. Other hooks may receive different kwargs — always use `.get()` with defaults.
- **Process isolation**: `execute_code` runs each call in a fresh process. Plugin manager singleton state does NOT persist across `execute_code` calls. Use `discover_plugins(force=True)` + `get_plugin_manager()` in a single script for testing.
- **SQLite type safety**: `COUNT(*)` can return strings in some SQLite configs. Always wrap with `int()`: `count = int(c.fetchone()[0])`.
- **Import path**: `hermes_cli/` must be on `sys.path` for brain imports. Use `Path(__file__).resolve().parent.parent.parent` to find HERMES_ROOT.
- **Singleton pattern**: Brain instances should be module-level singletons (`_brain = None` + `_get_brain()`), not created per-hook.
- **Config activation**: Plugin must be in `plugins.enabled` list or it won't load.
- **No daemon required**: Plugins load automatically when the agent starts. No separate daemon needed.
- **Error extraction**: Tool results are JSON strings. Parse with `json.loads()` to detect `"error"` keys.
- **HOOK SIGNATURE MISMATCH — SILENT FAILURES**: The most dangerous plugin bug. When `invoke_hook` passes kwargs that don't match your hook's signature, Python raises `TypeError` which is swallowed by the try/except in `invoke_hook`. The hook appears to register but NEVER FIRES. **Always add `**kwargs` to hook signatures** to absorb extra parameters the core may pass:
  ```python
  # WRONG — will silently fail when invoke_hook passes extra kwargs
  def _on_post_tool_call(tool_name: str, args: dict, result: Any, status: str) -> None:
      ...

  # RIGHT — accepts all kwargs the core passes, plus future extras
  def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                          status: str = "", error: str = "", **kwargs) -> None:
      ...
  ```
  Verify by checking `invoke_hook` in `model_tools.py` — it passes `tool_name, args, result, task_id, session_id, tool_call_id, duration_ms` for `post_tool_call`, but the plugin may expect `status, error`. The mismatch is invisible because `invoke_hook` wraps each callback in try/except and logs at debug level only.
- **HOOK REGISTRATION ≠ INVOCATION**: Just because `ctx.register_hook("pre_tool_call", handler)` succeeds does NOT mean run_agent.py will call it. Only `pre_llm_call`, `post_llm_call`, `on_session_start`, `on_session_end`, `pre_api_request`, `post_api_request`, and `transform_llm_output` are actually invoked by the main loop. `pre_tool_call` and `post_tool_call` are registered by the plugin system but NOT called by run_agent.py. Verify with grep: `grep '_invoke_hook("pre_tool_call"' run_agent.py`.
- **DEAD CODE WITH SILENT FAILURES**: Code inside `try/except Exception: pass` blocks that imports modules with wrong paths will fail forever without anyone noticing. Remove dead code rather than leaving it wrapped in catch-all exceptions.
- **SELF-IMPORT ANTI-PATTERN**: `from my_module import MyClass` inside a function in `agent/my_module.py` works by accident (module already in sys.modules) but breaks refactoring. Always use the full path: `from agent.my_module import MyClass`.
- **Derive missing kwargs**: When the core doesn't pass a parameter your logic needs (e.g. `status`), derive it from available data:
  ```python
  if not status and result:
      result_str = str(result).lower()
      if '"error"' in result_str or 'error:' in result_str:
          status = "error"
      else:
          status = "success"
  ```
- **MODULE SHADOWING — `hermes_cli.plugins` vs `plugins/` package (CRITICAL)**: When `run_agent.py` imports `hermes_cli.plugins` before the `plugins/` directory package is loaded, Python registers `plugins` in `sys.modules` pointing to `hermes_cli/plugins.py` (a file, not a package). This breaks ALL `plugins.X` imports including `plugins.memory`, `plugins.spotify`, etc.

  **Symptom:**
  ```
  Memory provider plugin init failed: No module named 'plugins.memory'; 'plugins' is not a package
  Failed to load plugin 'spotify': No module named 'plugins.spotify'; 'plugins' is not a package
  ```

  **Root cause:**
  ```python
  import sys
  # Before importing run_agent.py:
  'plugins' not in sys.modules  # True
  
  # After importing run_agent.py:
  import run_agent
  sys.modules['plugins']  # <module 'plugins' from 'hermes_cli/plugins.py'>
  sys.modules['plugins'].__file__  # .../hermes_cli/plugins.py
  hasattr(sys.modules['plugins'], '__path__')  # False — NOT a package
  ```

  **Fix — Pre-import the plugins package in `run_agent.py`:**
  ```python
  import sys
  import importlib.util

  # Force plugins package to load BEFORE hermes_cli.plugins can shadow it
  _plugins_spec = importlib.util.spec_from_file_location(
      "plugins",
      "/data/SpecForge/hermes-agent/plugins/__init__.py",
      submodule_search_locations=["/data/SpecForge/hermes-agent/plugins"]
  )
  _plugins_mod = importlib.util.module_from_spec(_plugins_spec)
  sys.modules["plugins"] = _plugins_mod
  _plugins_spec.loader.exec_module(_plugins_mod)
  ```

  **Alternative fix (simpler, same effect):**
  ```python
  import sys
  sys.path.insert(0, "/data/SpecForge/hermes-agent")  # Ensure repo root is first
  import plugins  # Loads plugins/__init__.py as the package
  ```

  **Verification:**
  ```python
  import sys
  print(sys.modules['plugins'].__file__)  # Should end in plugins/__init__.py
  print(hasattr(sys.modules['plugins'], '__path__'))  # Should be True
  ```

  **Key rule:** The `plugins` package MUST be in `sys.modules` as a package (with `__path__`) before ANY code imports `hermes_cli.plugins`. Add the pre-import at the very top of `run_agent.py`, before other imports.

- **HOOK VARIABLE ORDERING — Logging Before Data Exists**: When adding logging/metrics code to a hook that assembles data incrementally (e.g., `injection_lines` in `pre_llm_call`), placing the logger BEFORE the data is populated causes empty or incorrect logs. The logger must run AFTER the final data structure is assembled but BEFORE the hook returns.

  **Wrong — logs empty injection_lines:**
  ```python
  def _on_pre_llm_call(user_message, **kwargs):
      injection_lines = []
      
      # WRONG: log_attempt called here — injection_lines is empty!
      gov.log_attempt(candidate_tips=injection_lines, ...)  # Always empty
      
      # ... populate injection_lines ...
      injection_lines.append((tip_text, priority))  # Too late
      
      return "\n".join(injection_lines)
  ```

  **Right — log after assembly, before return:**
  ```python
  def _on_pre_llm_call(user_message, **kwargs):
      injection_lines = []
      
      # ... populate injection_lines ...
      injection_lines.append((tip_text, priority))
      
      # Assemble final output
      final_lines = trim_to_budget(injection_lines)
      
      # CORRECT: log after final_lines exists, before returning
      if final_lines:
          gov = get_governor_v2()
          gov.turn_number += 1
          for line, priority in injection_lines:
              injected = line in final_lines
              gov.log_attempt(
                  tip_id=0, condition=line[:200], priority=priority,
                  injected=injected, drop_reason="" if injected else "budget",
                  chars_used=len(line), lines_used=len(final_lines)
              )
      
      return "\n".join(final_lines) if final_lines else None
  ```

  **Key rule:** In hooks that build data incrementally, the logging/metrics call must be the LAST thing before the return statement, NEVER before the data is ready.
- **`plugins` package shadowing by `hermes_cli.plugins`**: When `run_agent.py` imports `hermes_cli.plugins`, Python registers `plugins` in `sys.modules` pointing to `hermes_cli/plugins.py` (a file, not a package). This breaks all `plugins.X` imports including `plugins.memory`. Fix: pre-import the `plugins` package via `importlib.util` before `hermes_cli.plugins` loads. See `references/hook-debugging-patterns.md` for full details.

## Sub-Topic: Perception Plugin Pattern

See `hermes-perception-plugin` skill (absorbed). Full lifecycle pattern for building Hermes plugins that add tools, hooks, brain integration, and squad propagation.

**Architecture:**
```
~/.hermes/plugins/evey-<name>/
├── __init__.py          # Main plugin: register(), handler, hooks, core logic
├── scripts/             # External .py scripts (NO inline f-string code)
│   ├── process_A.py
│   └── process_B.py
```

**Study existing plugins:**
```bash
grep -n 'def register\|register_tool\|register_hook' ~/.hermes/plugins/evey-moltbook/__init__.py
```

## Sub-Topic: Wiring External Cognitive Systems Into Live Plugins

When you've built cognitive infrastructure in `~/subconscious/` (or any external module) and need to activate it in the agent loop, **patch the existing plugin's hook functions** rather than building new cron jobs or standalone scripts.

**Pattern:**
```python
# At top of existing plugin __init__.py (after imports)
_COGNITIVE_INFRA = False
try:
    import sys
    _subconscious = os.path.expanduser("~/subconscious")
    if _subconscious not in sys.path:
        sys.path.insert(0, _subconscious)
    from my_cognitive_module import get_component
    _COGNITIVE_INFRA = True
except Exception:
    pass  # Silently fail — don't break existing hooks

# In _on_pre_llm_call:
if _COGNITIVE_INFRA:
    try:
        comp = get_component()
        comp.record_injection(tool_name, tip_id)
    except Exception:
        pass

# In _on_post_tool_call:
if _COGNITIVE_INFRA:
    try:
        comp = get_component()
        comp.record_outcome(tool_name, is_success, error)
    except Exception:
        pass
```

**Critical rules:**
- Always wrap in `try/except` — if your external module crashes, the original plugin must keep working
- Use `**kwargs` in all hook signatures to absorb extra parameters from `invoke_hook`
- Import at module level with `_FLAG = False` default — plugin loads even if your module is broken
- Bridge state through the plugin's existing globals (e.g. `_injected_tips_this_turn`) rather than inventing new state channels
- Verify with `python3 -c "import py_compile; py_compile.compile('plugin.py', doraise=True)"` after every patch
- Test the full flow: simulate pre_llm_call → simulate tool execution → simulate post_tool_call → verify DB writes

**Anti-pattern (what NOT to do):**
- Don't build cron jobs that call your module — cronjob tool has 17% success rate
- Don't build new plugins that duplicate existing hook infrastructure
- Don't leave modules in `~/subconscious/` unwired — they're dead code until a hook calls them

## Sub-Topic: Subprocess Script Pattern

See `hermes-plugin-subprocess-scripts` skill (absorbed). When plugins need venv-only dependencies (matplotlib, librosa, trimesh, PIL, openpyxl), use external script files in a `scripts/` directory instead of inline f-string code blocks.

**Why:** Python 3.8 (system Python on macOS) chokes on dict literals `{}`, set literals, and braces inside f-strings. Even Python 3.11 f-strings with complex inline code are fragile.

**Core pattern in `__init__.py`:**
```python
import subprocess, os

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), 'scripts')

result = subprocess.run(
    [sys.executable, os.path.join(SCRIPT_DIR, 'analyze_audio.py'), input_path],
    capture_output=True, text=True, timeout=30
)
return json.loads(result.stdout)
```

## References

- `references/plugin-tool-parity-audit.md` — **Cross-machine plugin sync**: diagnose missing tools, config file location gotchas, expected tool counts, and step-by-step parity checklist
- `references/learning-brain-plugin-example.md` — Complete working example of self-improvement plugin with loop guard
  - `references/hook-debugging-patterns.md` — Process isolation gotchas, block format requirements, SQLite type safety, verification scripts
  - `references/autobrowse-hook-signature-debug-transcript.md` — Full debug transcript of silent hook signature mismatch that broke autobrowse pipeline
  - `references/hook-invocation-gaps-2026-05.md` — Which plugin hooks are registered vs actually invoked by run_agent.py, dead code patterns (from cognitive systems integration)
  - `references/plugin-tool-verification.md` — **Tool verification pattern**: `hermes tools list` does NOT show plugin tools; use `PluginManager._plugins[name].tools_registered` instead. Full audit script + CLI command reference.
- `references/python38-compatibility-fixes.md` — Bulk fix patterns for union syntax
- `references/perception-plugin-full-example.md` — Complete perception plugin with tool registration + hook wiring
- `references/subprocess-script-template.md` — Template for external script-based plugins
- `references/cognitive-infra-v2-wiring-pattern.md` — Step-by-step pattern for wiring `~/subconscious/` cognitive systems into live plugin hooks with `_COGNITIVE_INFRA_V2` flag and graceful degradation
