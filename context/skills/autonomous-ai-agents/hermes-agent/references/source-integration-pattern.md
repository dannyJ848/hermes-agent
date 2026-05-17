# Source Integration Pattern — Session Reference

Reference from session where standalone scripts were moved INTO Hermes source code.

## The Problem

User built cognitive systems in `~/subconscious/` as standalone scripts:
- `hermes_self_manager.py` — never called by Hermes
- `hermes_cli_resume.py` — never called by Hermes
- `hermes_context_gauge.py` — redundant with existing tool
- `hermes_tool_logger.py` — redundant with existing tracking

**User's frustration:** "Everything you built didn't actually help the hermes harness bc you never touched the fucking source code"

## The Solution

### Step 1: Find Entry Points

```bash
cd ~/hermes-agent
# Main entry points:
# - cli.py — CLI startup, session initialization
# - run_agent.py — Agent loop, compression, tool dispatch
# - hermes_cli/plugins.py — Plugin tool dispatch
# - tools/registry.py — Tool auto-discovery
```

### Step 2: Identify Injection Points

| Feature | File | Function | Line Area |
|---------|------|----------|-----------|
| Auto-resume | `cli.py` | `HermesCLI.__init__` | ~2397 (before session ID) |
| Compression handoff | `run_agent.py` | `AIAgent._compress_context` | ~9810 (after count warning) |
| Tool tracking fix | `hermes_cli/plugins.py` | `Plugin.dispatch_tool` | ~402 (finally block) |
| New tools | `tools/<name>_tool.py` | module level | `registry.register()` |

### Step 3: Inject Code

**Auto-resume in cli.py:**
```python
# Before: self.session_id = ...
_auto_resume = self._check_pending_handoff(resume)
if _auto_resume:
    resume = _auto_resume
    self._vprint(f"{self.log_prefix}🔄 Auto-resuming from handoff: {resume}", force=True)

# Add method:
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

**Compression handoff in run_agent.py:**
```python
# After: _cc warning
if _cc >= 5:
    self._trigger_compression_handoff(_cc, messages, new_system_prompt)

# Add method to AIAgent:
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
    
    # Emit instruction to user
    self._emit_warning(
        f"📋 HANDOFF COMPLETE. Start new Hermes CLI and say: "
        f"'resume from checkpoint {_handoff_label}'\n"
        f"   Or run: hermes --resume {_handoff_label}"
    )
```

### Step 4: Register New Tools

Create `tools/self_diagnostic.py`:
```python
from tools.registry import registry

SELF_DIAGNOSTIC_SCHEMA = {
    "type": "object",
    "properties": {
        "component": {"type": "string", "enum": ["", "cerebrum_db", "knowledge_dir", "workspace", "pending_handoff", "all"]},
        "format": {"type": "string", "enum": ["human", "json"], "default": "human"}
    },
    "required": [],
}

def run_self_diagnostic(component="all", format="human"):
    # ... implementation ...
    return report

registry.register(
    name="self_diagnostic",
    toolset="health",
    schema=SELF_DIAGNOSTIC_SCHEMA,
    handler=lambda args, **kw: run_self_diagnostic(
        component=args.get("component", "all"),
        format=args.get("format", "human")
    ),
    check_fn=lambda: True,
    emoji="🏥",
)
```

Same pattern for `tools/skill_generator.py` and `tools/plan_executor.py`.

### Step 5: Verify Integration

```bash
cd ~/hermes-agent

# Test tool discovery
venv/bin/python -c "
from tools.registry import discover_builtin_tools
mods = discover_builtin_tools()
print('self_diagnostic:', 'tools.self_diagnostic' in mods)
print('skill_generator:', 'tools.skill_generator' in mods)
print('plan_executor:', 'tools.plan_executor' in mods)
"

# Test specific tool
venv/bin/python -c "
from tools.self_diagnostic import run_self_diagnostic
print(run_self_diagnostic())
"

# Restart Hermes to pick up cli.py/run_agent.py changes
# (Must restart - these files loaded once at startup)
```

## Files Modified in This Session

| File | Change |
|------|--------|
| `run_agent.py` | Added `_trigger_compression_handoff`, injection at `_cc >= 5` |
| `cli.py` | Added `_check_pending_handoff`, auto-resume injection |
| `tools/context_pressure_gauge.py` | Enhanced with compression tracking |
| `tools/self_diagnostic.py` | New tool (registered) |
| `tools/skill_generator.py` | New tool (registered) |
| `tools/plan_executor.py` | New tool (registered) |
| `hermes_cli/plugins.py` | Fixed tool tracking schema mismatch |

## Key Lesson

**Standalone scripts in `~/subconscious/` are worthless unless integrated.** The integration points are:
1. `tools/*.py` with `registry.register()` — for new tools
2. `cli.py` `HermesCLI.__init__` — for startup behavior
3. `run_agent.py` `AIAgent` methods — for runtime behavior
4. `hermes_cli/plugins.py` — for tool dispatch hooks

Always verify: `discover_builtin_tools()` should include your tool, or your hook should fire in a test session.
