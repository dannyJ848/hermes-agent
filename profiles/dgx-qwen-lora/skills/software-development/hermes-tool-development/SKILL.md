---
name: hermes-tool-development
description: Build and debug new tools for Hermes Agent. Covers registration, testing, and common Python gotchas when writing tool modules.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [hermes, tools, development, debugging]

---

# Hermes Tool Development

Guide for building new tools that plug into Hermes Agent's tool registry.

## Quick Pattern

1. **Create `tools/<name>_tool.py`** with `registry.register()` at module level
2. **Test import:** `python -c "from tools.<name>_tool import handler; print('import OK')"`
3. **Test end-to-end:** `python -c "from tools.<name>_tool import handler; print(handler({'arg': 'test'}))"`
4. **Verify registration:** `python -c "from tools.registry import registry; print(registry._tools.get('<name>'))"`
5. **Restart Hermes** to pick up the new tool

## Minimal Template

```python
#!/usr/bin/env python3
from tools.registry import registry, tool_error

def my_tool(path: str) -> dict:
    try:
        data = open(path).read()
        return {"success": True, "content": data}
    except Exception as e:
        return tool_error(str(e))

MY_SCHEMA = {
    "name": "my_tool",
    "description": "Read a file and return its contents.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"}
        },
        "required": ["path"]
    }
}

def check_requirements() -> tuple[bool, str]:
    return True, ""

registry.register(
    name="my_tool",
    toolset="file",  # or custom
    schema=MY_SCHEMA,
    handler=lambda args, **kw: my_tool(path=args.get("path", "")),
    check_fn=check_requirements,
    emoji="🔧",
)
```

## Key Rules

- **Return dicts, not JSON strings.** Hermes handles serialization.
- **Use `tool_error(msg)`** from `tools.registry` for consistent error formatting.
- **Always provide `check_fn`** returning `(bool, str)` — even if it just returns `(True, "")`.
- **Lazy imports:** Do heavy imports inside handler functions, not at module top-level.
- **Auto-discovery:** Any `tools/*.py` with a top-level `registry.register()` call is auto-imported. No manual list needed.
- **INTEGRATE INTO HERMES SOURCE, not standalone scripts.** See Pitfall "Standalone script trap" below.

## Integrating Cognitive Systems INTO Hermes (Not On Top)

**The user's #1 frustration:** Building standalone scripts in `~/subconscious/` that are never wired into the agent loop. Every cognitive system must be integrated into Hermes source code, not left as external utilities.

### Where to Inject Different System Types

| System Type | Inject Into | Hook/Pattern |
|-------------|-------------|--------------|
| **Auto-resume / handoff** | `cli.py` `HermesCLI.__init__` | Check for pending handoff file before session ID assignment |
| **Context pressure actions** | `run_agent.py` `_compress_context` | Trigger after compression count threshold |
| **New tools** | `tools/<name>_tool.py` | `registry.register()` at module level |
| **Tool call tracking** | `hermes_cli/plugins.py` `dispatch_tool` | Log in `finally` block |
| **Session-end hooks** | `run_agent.py` session cleanup | Call before session DB close |
| **Startup checks** | `cli.py` `main()` before agent init | Run health checks, show warnings |

### Integration Pattern

```python
# In cli.py HermesCLI.__init__:
# BEFORE: self.session_id = ...
# ADD:
_auto_resume = self._check_pending_handoff(resume)
if _auto_resume:
    resume = _auto_resume
    # user will auto-resume from handoff

# In run_agent.py AIAgent._compress_context:
# AFTER: compression_count warning
# ADD:
if _cc >= 5:
    self._trigger_compression_handoff(_cc, messages, new_system_prompt)
```

### Anti-Pattern: The Standalone Script Trap

**Broken:**
```bash
~/subconscious/hermes_thing.py        # Never imported by Hermes
~/subconscious/hermes_other.py          # Orphan code
```

**Correct:**
```bash
~/hermes-agent/tools/my_tool.py        # Auto-discovered by registry
~/hermes-agent/cli.py                  # Modified to check handoff
~/hermes-agent/run_agent.py            # Modified to trigger actions
```

### Verification Steps After Integration

1. **Import test:** `venv/bin/python -c "import tools.my_tool"`
2. **Registration test:** `venv/bin/python -c "from tools.registry import discover_builtin_tools; print('my_tool' in [m for m in discover_builtin_tools()])"`
3. **Integration test:** Start Hermes, verify tool appears in `/tools` list
4. **Hook test:** Trigger the condition (e.g., compression) and verify action fires
5. **Restart required:** Always restart Hermes after modifying `cli.py` or `run_agent.py`

## Common Pitfalls

| Pitfall | Broken | Correct |
|---------|--------|---------|
| **List membership vs substring** | `"{" in lines[i:j+1]` | `any("{" in l for l in lines[i:j+1])` |
| **Returning strings** | `return json.dumps({"ok": True})` | `return {"ok": True}` |
| **Missing tool_error** | `return {"error": msg}` | `return tool_error(msg)` |
| **Schema enum drift** | `"enum": ["a","b"]` but code checks `"c"` | Keep enum and code in sync |
| **Module import failing silently** | Top-level `import heavy_lib` | `def handler(): import heavy_lib` |
| **Standalone script trap** | Building `~/subconscious/my_thing.py` that never gets called | Put it in `tools/`, `cli.py`, or `run_agent.py` where Hermes actually executes |
| **Schema mismatch in existing code** | Inserting `(tool_name, success, elapsed_ms)` when table has `(tool_name, status, speed_ms)` | Check actual table schema with `.schema table_name` before writing INSERTs |
| **Alias vs implementation gap** | Assuming 76 aliases = 76 working tools | Verify with `grep 'def .*task_id' tools/` — only 31 actually implemented. See `references/tool-alias-vs-implementation-audit-may18-2026.md` |

The **list membership gotcha** is especially common when parsing multi-line text blocks. `"x" in some_list` checks if `"x"` is an *element*, not if any element *contains* `"x"`. Always use `any()` for substring checks across lists.

### Tool Alias vs Implementation Audit

When a user reports a tool count discrepancy (e.g., "I expected 92 tools but see 27"), run this audit:

```python
# Count aliases in toolsets.py
aliases = !grep 'ToolAlias' toolsets.py | wc -l

# Count actual implementations
functions = !grep -r 'def .*task_id' tools/ | wc -l

# Count registered tools
registered = !python3 -c "from tools.registry import registry; print(len(registry._tools))"

print(f"Aliases: {aliases}, Functions: {functions}, Registered: {registered}")
```

**Key insight:** Aliases in `toolsets.py` are a configuration wishlist. Actual tool functions in `tools/*.py` are the reality. The gap (60 unimplemented aliases in this case) is not a bug — it's undeveloped features. Document the actual count clearly.

## Testing Without Restarting Hermes

Current Hermes instance won't auto-discover new tools. Test in Python directly:

```bash
cd ~/hermes-agent
source venv/bin/activate

# 1. Import test
python -c "from tools.my_tool import my_tool; print('import OK')"

# 2. Handler test
python -c "from tools.my_tool import my_tool; print(my_tool('/tmp/test.txt'))"

# 3. Registration test (force reimport)
python -c "
import importlib
import tools.my_tool
importlib.reload(tools.my_tool)
from tools.registry import registry
print('registered:', 'my_tool' in registry._tools)
"
```

## Tool Registration Verification — `get_tool_definitions()` Structure

**CRITICAL: `get_tool_definitions()` returns OpenAI function-calling format, not flat dicts.**

The structure is:
```python
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "...",
        "parameters": {...}
    }
}
```

**The `name` is nested under `function`, NOT at the top level.**

### Correct verification code

```python
import model_tools as mt
tools = mt.get_tool_definitions()

# CORRECT — access name via function sub-dict
tool_names = [t.get("function", {}).get("name", "") for t in tools]

# WRONG — name is not at top level
tool_names = [t.get("name", "") for t in tools]  # Returns empty strings!

print(f"Total tools: {len(tools)}")
print(f"My tool present: {'my_tool' in tool_names}")
```

### Common mistake — false negative on tool presence

If you use `t.get("name")` instead of `t.get("function", {}).get("name")`, ALL tools will appear missing even though they're registered. This causes unnecessary panic and duplicate registration attempts.

**Always verify with the correct key path before concluding tools are missing.**

## Debugging Registration Failures

If the tool doesn't appear in `hermes tools list` after restart:

1. Check `tools/*.py` file has `registry.register()` at module level (not inside a function)
2. Check import works standalone: `python -c "import tools.my_tool"`
3. Check `discover_builtin_tools()` picks it up:
   ```python
   from tools.registry import discover_builtin_tools
   print(discover_builtin_tools())
   ```
4. Check `get_tool_definitions()` with correct key path (see above)
5. Check for syntax errors in the file
6. Check `check_fn` returns `(True, "")` — returning just `True` breaks registration
