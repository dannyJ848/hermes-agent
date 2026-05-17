# Cognitive Systems Plugin Pattern — Hermes Integration

**Session:** May 9, 2026 — wiring 11 cognitive modules into Hermes via official plugin system
**Context:** After moving modules from ~/subconscious/ to agent/, they were orphaned — present in source but no hooks registered. This pattern fixes that.

## The Problem

Moving cognitive modules into `agent/` is necessary but NOT sufficient. The Hermes agent loop must actually CALL them. There are two ways to wire:

1. **Direct monkey-patching in run_agent.py** — fragile, breaks on upstream updates
2. **Hermes Plugin System** — official, stable, survives updates

## The Plugin Pattern

### Step 1: Create plugin directory

```
~/.hermes/plugins/cognitive-systems/
├── __init__.py          # register(ctx) function
└── plugin.yaml          # manifest
```

### Step 2: Write __init__.py with hook handlers

```python
def register(ctx):
    """Called by Hermes plugin loader on discovery."""
    ctx.register_hook("pre_tool_call", _pre_tool_call_handler)
    ctx.register_hook("post_tool_call", _post_tool_call_handler)
    ctx.register_hook("pre_llm_call", _pre_llm_call_handler)
    ctx.register_hook("post_llm_call", _post_llm_call_handler)
    ctx.register_hook("on_session_start", _on_session_start_handler)
    ctx.register_hook("on_session_end", _on_session_end_handler)
    
    # Register tools
    ctx.register_tool(
        name="screen_capture",
        toolset="vision",
        schema=SCREEN_CAPTURE_SCHEMA,
        handler=screen_capture_tool,
        description="Capture screen and analyze visual content",
        emoji="👁️"
    )
```

### Step 3: Write plugin.yaml manifest

```yaml
name: cognitive-systems
version: "2.0.0"
description: "Integrated cognitive systems for Hermes Agent"
author: "Evey"
provides_hooks:
  - pre_tool_call
  - post_tool_call
  - pre_llm_call
  - post_llm_call
  - on_session_start
  - on_session_end
kind: standalone
```

### Step 4: Lazy-load cognitive modules

```python
_SYSTEMS: Dict[str, Any] = {}

def _load_system(name: str):
    if name in _SYSTEMS:
        return _SYSTEMS[name]
    try:
        if name == "iteration_engine":
            from agent.iteration_engine import get_engine
            _SYSTEMS[name] = get_engine()
        # ... etc
        return _SYSTEMS[name]
    except Exception as e:
        logger.warning(f"Failed to load {name}: {e}")
        return None
```

### Step 5: Hook handler pattern

```python
def _pre_tool_call_handler(tool_name: str, args: Dict, **kwargs) -> Optional[str]:
    """Return context string to inject into prompt, or None."""
    contexts = []
    
    engine = _load_system("iteration_engine")
    if engine:
        try:
            lesson_ctx = engine.before_action(tool_name, str(args)[:200])
            if lesson_ctx.get("has_history"):
                # Format lessons for prompt injection
                contexts.append(format_lessons(lesson_ctx))
        except Exception:
            pass  # Never fail the tool call
    
    return "\n\n".join(contexts) if contexts else None
```

## Critical Pitfall: Class Name Mismatch

When lazy-loading cognitive modules, **the class name in the plugin often does not match the actual export**. The `_load_system()` function must use the real class/function names.

**Example from July 2026:**
```python
# WRONG — causes ImportError silently swallowed by except:
from agent.agent_scorecard import AgentScorecard  # No such class!
_SYSTEMS[name] = AgentScorecard()

# CORRECT — module has functions, not classes:
from agent import agent_scorecard
_SYSTEMS[name] = agent_scorecard  # module with compute_scorecard(), etc.
```

**Always verify actual exports before writing imports:**
```python
import inspect
mod = __import__('agent.memory_cortex_bridge')
classes = [n for n, o in inspect.getmembers(mod) if inspect.isclass(o)]
functions = [n for n, o in inspect.getmembers(mod) if inspect.isfunction(o)]
print(f"Classes: {classes}")   # ['MemoryCortexBridge', 'MemoryParser']
print(f"Functions: {functions}")  # ['memory_add_hook', 'pre_tool_call_hook']
```

## Critical Pitfall: Handler Signature Drift

Even when modules load, the **methods expected by handlers often don't exist**. This causes silent failures on every hook fire.

**Example from July 2026:**
```python
# WRONG — method doesn't exist:
cortex.record_turn(response=assistant_response, history_length=len(history))
# AttributeError: 'CortexDB' object has no attribute 'record_turn'

# CORRECT — use actual method:
stats = cortex.get_stats()
logger.debug(f"Cortex stats: {stats}")
```

**Always verify method signatures before writing handler code:**
```python
import inspect
obj = MemoryCortexBridge()
for name, method in inspect.getmembers(obj, predicate=inspect.ismethod):
    if not name.startswith('_'):
        print(f"  {name}{inspect.signature(method)}")
# Output: is_pressure() -> bool, offload_if_needed(force=False) -> Dict, ...
```

## Key Principles

1. **Fail-safe**: Every hook handler wraps its work in try/except. A cognitive system failure must NEVER break the agent loop.
2. **Lazy loading**: Don't import all modules at startup — load on first use to avoid import errors blocking hermes startup.
3. **Context injection**: `pre_tool_call` and `pre_llm_call` return strings that get injected into the prompt. This is how the agent "learns" from past experiences.
4. **Silent recording**: `post_tool_call` and `post_llm_call` record experiences without returning anything. No prompt injection here.

## What Was Built (May 9, 2026)

| Module | Hook | Purpose |
|--------|------|---------|
| iteration_engine | pre_tool_call, post_tool_call, pre_llm_call | Retrieve lessons, record experiences |
| tool_misuse_prevention | pre_tool_call | Validate tool health before use |
| agent_scorecard | post_tool_call | Score tool call quality |
| red_team_hippocampus | post_tool_call | Mine errors for patterns |
| cortex_flywheel | post_llm_call | Record turn to cortex |
| memory_cortex_bridge | post_llm_call | Consolidate memory |
| hermes_enhancement_suite | post_llm_call | Track improvements |
| vision_loop | tool registration | Screen capture, GUI automation |
| self_evolution | on_session_end | Run evolution cycles |

## Files Created

- `~/.hermes/plugins/cognitive-systems/__init__.py` — plugin registration
- `~/.hermes/plugins/cognitive-systems/plugin.yaml` — manifest
- `~/hermes-agent/agent/vision_loop.py` — screen capture + GUI automation
- `~/hermes-agent/agent/vision_tools.py` — tool wrappers for vision
- `~/hermes-agent/agent/self_evolution.py` — Elo tournaments, tip evolution, hindsight
