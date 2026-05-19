# Hermes Source Integration Points

Reference from session where standalone scripts were moved into Hermes source.

## Entry Points

| File | Purpose | Key Functions |
|------|---------|---------------|
| `cli.py` | CLI startup, session init | `HermesCLI.__init__`, `main()` |
| `run_agent.py` | Agent loop, compression, tool dispatch | `AIAgent._compress_context`, `AIAgent.chat()` |
| `hermes_cli/plugins.py` | Plugin tool dispatch | `Plugin.dispatch_tool()` |
| `tools/registry.py` | Tool auto-discovery | `discover_builtin_tools()` |

## Auto-Resume Integration (cli.py)

Inject before session ID assignment in `HermesCLI.__init__`:

```python
# Line ~2397
# ── SELF-MANAGER: Auto-detect pending handoff ──
_auto_resume = self._check_pending_handoff(resume)
if _auto_resume:
    resume = _auto_resume
    self._vprint(f"{self.log_prefix}🔄 Auto-resuming from handoff: {resume}", force=True)

# Then add method:
def _check_pending_handoff(self, explicit_resume: str = None) -> str:
    if explicit_resume:
        return None
    import json
    from pathlib import Path
    _handoff_file = Path.home() / ".hermes" / "workspace" / "handoff_pending.json"
    if not _handoff_file.exists():
        return None
    try:
        _handoff = json.loads(_handoff_file.read_text())
        if time.time() - _handoff.get("timestamp", 0) > 86400:
            _archive = _handoff_file.with_suffix(".archived.json")
            _handoff_file.rename(_archive)
            return None
        _checkpoint_label = _handoff.get("checkpoint_label")
        if _checkpoint_label:
            try: _handoff_file.unlink()
            except: pass
            return _checkpoint_label
    except:
        pass
    return None
```

## Compression Handoff Integration (run_agent.py)

Inject after compression count warning in `_compress_context`:

```python
# Line ~9810
# ── SELF-MANAGER: Auto-handoff at 5th compression ──
if _cc >= 5:
    self._trigger_compression_handoff(_cc, messages, new_system_prompt)

# Then add method to AIAgent class:
def _trigger_compression_handoff(self, compression_count, messages, system_prompt):
    import time, json
    from pathlib import Path
    _handoff_label = f"auto-handoff-{int(time.time())}"
    _workspace = Path.home() / ".hermes" / "workspace"
    _workspace.mkdir(parents=True, exist_ok=True)
    
    # Save checkpoint
    _checkpoint_file = _workspace / "checkpoints" / f"{_handoff_label}.json"
    _checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    _checkpoint_data = {
        "label": _handoff_label,
        "timestamp": time.time(),
        "context": {
            "session_id": self.session_id,
            "compression_count": compression_count,
            "message_count": len(messages),
            "model": self.model,
        },
        "session_id": self.session_id,
    }
    _checkpoint_file.write_text(json.dumps(_checkpoint_data, indent=2, default=str))
    
    # Save handoff
    _handoff_file = _workspace / "handoff_pending.json"
    _handoff = {
        "timestamp": time.time(),
        "reason": "compression_threshold",
        "checkpoint_label": _handoff_label,
        "session_id": self.session_id,
        "compression_count": compression_count,
        "next_steps": f"Resume from checkpoint {_handoff_label}",
    }
    _handoff_file.write_text(json.dumps(_handoff, indent=2, default=str))
    
    # Log to rapid learnings
    if self._memory_manager:
        try:
            self._memory_manager.add_rapid_learning(
                lesson=f"Session handoff at {compression_count} compressions. Resume with '{_handoff_label}'.",
                category="meta", confidence=0.99, source="self_manager",
            )
        except: pass
    
    # Emit instruction
    self._emit_warning(
        f"📋 HANDOFF COMPLETE. Start new Hermes CLI and say: "
        f"'resume from checkpoint {_handoff_label}'\n"
        f"   Or run: hermes --resume {_handoff_label}"
    )
```

## Tool Registration Pattern

```python
# In tools/my_tool.py:
from tools.registry import registry

MY_SCHEMA = {
    "type": "object",
    "properties": {
        "arg": {"type": "string", "description": "Argument"}
    },
    "required": ["arg"]
}

def handler(args, **kw):
    return {"result": args.get("arg")}

def check_fn():
    return True  # or (True, "") for older versions

registry.register(
    name="my_tool",
    toolset="my_toolset",  # or "meta", "health", etc.
    schema=MY_SCHEMA,
    handler=handler,
    check_fn=check_fn,
    emoji="🔧",
)
```

## Tool Tracking Fix (hermes_cli/plugins.py)

The existing tool tracking had schema mismatch. Fixed INSERT:

```python
# In dispatch_tool() finally block:
c.execute('''
    INSERT INTO tool_call_log (tool_name, status, speed_ms, args, created_at)
    VALUES (?, ?, ?, ?, ?)
''', (
    tool_name,
    'error' if error else 'success',
    int(elapsed * 1000),
    json.dumps(args) if args else '{}',
    time.time()
))
```

Table schema:
```sql
CREATE TABLE tool_call_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT,
    status TEXT,
    speed_ms REAL,
    args TEXT,
    created_at REAL
);
```

## Testing Integration

```bash
cd ~/hermes-agent

# 1. Verify tool discovery
venv/bin/python -c "
from tools.registry import discover_builtin_tools
mods = discover_builtin_tools()
for m in sorted(mods):
    print(m)
"

# 2. Verify specific tool
venv/bin/python -c "
from tools.self_diagnostic import run_self_diagnostic
print(run_self_diagnostic())
"

# 3. Restart Hermes to pick up cli.py/run_agent.py changes
# (Must restart - these files are loaded once at startup)
```

## Files Modified in This Session

- `~/hermes-agent/run_agent.py` - Added `_trigger_compression_handoff`, injection at `_cc >= 5`
- `~/hermes-agent/cli.py` - Added `_check_pending_handoff`, auto-resume injection
- `~/hermes-agent/tools/context_pressure_gauge.py` - Enhanced with compression tracking
- `~/hermes-agent/tools/self_diagnostic.py` - New tool (registered)
- `~/hermes-agent/tools/skill_generator.py` - New tool (registered)
- `~/hermes-agent/tools/plan_executor.py` - New tool (registered)
- `~/hermes-agent/hermes_cli/plugins.py` - Fixed tool tracking schema mismatch
