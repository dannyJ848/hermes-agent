# Function-to-Class Wrapper Pattern for Cognitive Orchestrator

## Problem

The `CognitiveOrchestrator` expects class-based subsystems with `__init__()` methods it can instantiate:

```python
def _init_distillation_bridge(self):
    from agent.distillation_bridge import DistillationBridge
    return DistillationBridge()  # expects a class
```

But some modules export only functions (no classes):

```python
# distillation_bridge.py — only functions, no class
def bottom_up_store(tool_name, args, status, ...): ...
def top_down_recall(task_context, max_items=None): ...
```

This causes `ImportError: cannot import name 'DistillationBridge'` and the subsystem is marked "failed".

## Solution: Thin Wrapper Class

Add a wrapper class at the bottom of the module that delegates to the existing functions:

```python
# At the bottom of distillation_bridge.py

class DistillationBridge:
    """Wrapper class for cognitive orchestrator compatibility."""
    
    def __init__(self):
        self._ensure_tips_table()
    
    def _ensure_tips_table(self):
        _ensure_tips_table()
    
    def bottom_up_store(self, tool_name, args, status, speed_ms, error="", lesson="", failure_stage=""):
        return bottom_up_store(tool_name, args, status, speed_ms, error, lesson, failure_stage)
    
    def top_down_recall(self, task_context, max_items=None):
        return top_down_recall(task_context, max_items)
```

## Real-World Examples (May 15, 2026)

### distillation_bridge.py
```python
class DistillationBridge:
    def __init__(self):
        self._ensure_tips_table()
    
    def _ensure_tips_table(self):
        _ensure_tips_table()
    
    def bottom_up_store(self, tool_name, args, status, speed_ms, error="", lesson="", failure_stage=""):
        return bottom_up_store(tool_name, args, status, speed_ms, error, lesson, failure_stage)
    
    def top_down_recall(self, task_context, max_items=None):
        return top_down_recall(task_context, max_items)
```

### training_gym.py
```python
class TrainingGym:
    def __init__(self):
        init_db()
        seed_exercises()
    
    def get_next_exercise(self, category=None, tier=None):
        return get_next_exercise(category, tier)
    
    def record_attempt(self, exercise_id, score, max_score, tools_used=None, errors=None):
        return record_attempt(exercise_id, score, max_score, tools_used, errors)
    
    def get_stats(self):
        return get_stats()
```

### subconscious_hook_wiring.py
```python
class SubconsciousHookWiring:
    def __init__(self):
        pass
    
    def install_hooks(self):
        # Hooks are installed at module level via function calls
        # This is a no-op for compatibility
        pass
    
    def pre_tool_call(self, tool_name, args, task_id=""):
        return pre_tool_call_full(tool_name, args, task_id)
    
    def post_tool_call(self, tool_name, args, result, task_id=""):
        return post_tool_call_full(tool_name, args, result, task_id)
    
    def pre_llm_call(self, messages, context_limit=128000):
        return pre_llm_call_full(messages, context_limit)
```

## Result

Before wrappers:
```
✗ distillation_bridge init failed: cannot import name 'DistillationBridge'
✗ training_gym init failed: cannot import name 'TrainingGym'
✗ subconscious init failed: cannot import name 'SubconsciousHookWiring'
Cognitive Orchestrator: 17/20 subsystems active
```

After wrappers:
```
✓ distillation_bridge initialized (0ms)
✓ training_gym initialized (8ms)
✓ subconscious initialized (0ms)
Cognitive Orchestrator: 19/20 subsystems active
```

## When to Use This Pattern

1. **Module has functions but no classes** — and the orchestrator expects classes
2. **Module-level initialization** — functions that run on import (e.g., `seed_exercises()`)
3. **Legacy code** — modules built before the orchestrator pattern existed
4. **Third-party integrations** — external libraries that export functions

## When NOT to Use

1. **Module already has classes** — just ensure the class name matches what the orchestrator imports
2. **New modules** — build with classes from the start
3. **Simple stateless functions** — if the orchestrator doesn't need to instantiate, use a simpler adapter

## Detection

To find modules that need wrappers:

```bash
cd /data/SpecForge/hermes-agent/agent
for mod in distillation_bridge training_gym subconscious_hook_wiring; do
  if ! grep -q "^class " $mod.py; then
    echo "NEEDS WRAPPER: $mod.py (no classes found)"
  fi
done
```

## Integration Checklist

- [ ] Wrapper class name matches what `cognitive_orchestrator.py` imports
- [ ] `__init__()` calls any module-level initialization (DB setup, seeding, etc.)
- [ ] Methods delegate to existing functions (don't reimplement logic)
- [ ] No circular imports (wrapper stays in same module)
- [ ] Test: `python3 -c "from agent.module import ClassName; c = ClassName()"`
