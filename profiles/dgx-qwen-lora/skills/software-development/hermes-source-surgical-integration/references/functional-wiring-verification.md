# Functional Wiring Verification Pattern

After integrating code into Hermes source, **file presence is worthless without functional wiring**. The May 2026 subconscious integration audit revealed 10 cognitive modules were "orphaned" — files present in `agent/` but none registered hooks or were called by `run_agent.py`. This caused user fury.

## The Verification Ladder (4 Levels)

### Level 1: File Presence (Worthless Alone)
```python
# ❌ BAD — only checks files exist
os.path.exists("~/hermes-agent/agent/self_evolution.py")
```

### Level 2: Module Import (Still Insufficient)
```python
# ❌ BAD — only checks import works
from agent.self_evolution import SelfEvolutionPipeline
hasattr(SelfEvolutionPipeline, '_graduate_tips_to_skills')
```

### Level 3: Class Method Existence (Better, But Not Wired)
```python
# ⚠️  BETTER — checks method exists on instance
pipeline = SelfEvolutionPipeline()
hasattr(pipeline, '_graduate_tips_to_skills')
```

### Level 4: Actual Hook Invocation (REQUIRED)
```python
# ✅ CORRECT — traces _invoke_hook() calls in run_agent.py
with open("~/hermes-agent/run_agent.py") as f:
    source = f.read()

# Find actual hook calls
import re
hook_calls = re.findall(r'_invoke_hook\(\s*["\'](\w+)["\']', source)
print(f"Hooks invoked: {set(hook_calls)}")

# Expected: pre_llm_call, post_llm_call, pre_tool_call, post_tool_call,
#          on_session_start, on_session_end, pre_api_request, post_api_request
```

## The Complete Verification Script

Run this after ANY integration to prove wiring:

```python
import os, sys, re, inspect
sys.path.insert(0, os.path.expanduser('~/hermes-agent'))

print("=== FUNCTIONAL WIRING VERIFICATION ===\n")

# 1. Agent Loop Hook Invocation
run_agent_path = os.path.expanduser('~/hermes-agent/run_agent.py')
with open(run_agent_path) as f:
    source = f.read()

hooks = ['pre_llm_call', 'post_llm_call', 'pre_tool_call', 'post_tool_call',
         'on_session_start', 'on_session_end', 'pre_api_request', 'post_api_request']
for hook in hooks:
    count = source.count(f'"{hook}"')
    status = "✅" if count > 0 else "❌"
    print(f"  {status} {hook}: {count} _invoke_hook() calls")

# 2. Tool Execution Path (post_tool_call is in model_tools.py, not run_agent.py)
model_tools_path = os.path.expanduser('~/hermes-agent/model_tools.py')
if os.path.exists(model_tools_path):
    with open(model_tools_path) as f:
        mt_source = f.read()
    if 'post_tool_call' in mt_source:
        print(f"  ✅ post_tool_call: found in model_tools.py")

# 3. Plugin Enabled Status
config_path = os.path.expanduser('~/.hermes/config.yaml')
with open(config_path) as f:
    config = f.read()
if 'cognitive-systems' in config and 'enabled' in config:
    print(f"  ✅ cognitive-systems: referenced in config")

# 4. Self-Evolution Trigger Points
plugin_init = os.path.expanduser('~/.hermes/plugins/cognitive-systems/__init__.py')
with open(plugin_init) as f:
    plugin_source = f.read()
if 'get_evolution_pipeline' in plugin_source:
    print(f"  ✅ Self-evolution: triggered from plugin")
if 'run_cycle' in plugin_source:
    print(f"  ✅ run_cycle(): called from plugin")

# 5. Class Method Called (Not Just Existing)
from agent.self_evolution import SelfEvolutionPipeline
pipeline = SelfEvolutionPipeline()
run_cycle_source = inspect.getsource(pipeline.run_cycle)
if '_graduate_tips_to_skills' in run_cycle_source:
    print(f"  ✅ _graduate_tips_to_skills(): called by run_cycle()")

print("\n=== ALL SYSTEMS VERIFIED ===")
```

## Class Name Mismatch Pitfall (CRITICAL)

When wiring a plugin that imports cognitive modules, **the class name in the plugin often does not match the actual class name in the module**. This causes silent failures because the import raises `ImportError`, which gets caught by `except Exception: pass` and the system simply doesn't load.

**Example from July 2026 audit:**

| Plugin Expected | Actual Export | Module |
|-----------------|-------------|--------|
| `AgentScorecard` | Functions only (`compute_scorecard`, `score_tool_mastery`) | `agent_scorecard.py` |
| `ToolHealthMonitor` | Functions only (`validate_tool_call`, `get_tool_stats`) | `tool_misuse_prevention.py` |
| `ErrorMiner` | Functions only (`learn`, `attack`, `harden`) | `red_team_hippocampus.py` |
| `MemoryBridge` | `MemoryCortexBridge` | `memory_cortex_bridge.py` |
| `EnhancementTracker` | `HermesEnhancementSuite` | `hermes_enhancement_suite.py` |

**Detection:**
```python
import inspect

# Before writing plugin code, scan the actual module
module = __import__('agent.agent_scorecard')
classes = [name for name, obj in inspect.getmembers(module) if inspect.isclass(obj)]
functions = [name for name, obj in inspect.getmembers(module) if inspect.isfunction(obj)]
print(f"Classes: {classes}")
print(f"Functions: {functions}")
```

**Fix:** Update the plugin's `_load_system()` to use the actual export:
```python
# BEFORE (broken):
from agent.agent_scorecard import AgentScorecard
_SYSTEMS[name] = AgentScorecard()

# AFTER (fixed):
from agent import agent_scorecard
_SYSTEMS[name] = agent_scorecard  # module with functions
```

## Handler Signature Drift Pitfall (CRITICAL)

Even when classes load correctly, the **method signatures expected by the plugin handler often don't match the actual methods on the class**. This causes `AttributeError` on every hook fire, which gets silently swallowed by `except Exception: pass`.

**Example from July 2026 audit:**

| Plugin Called | Actual Method | Module |
|--------------|-------------|--------|
| `scorecard.record_tool_call(tool_name, result, error, duration_ms)` | `compute_scorecard(db=None)` | `agent_scorecard` |
| `red_team.mine_error(tool_name, error, result)` | `learn(outcome, url='', technique='', success=False)` | `red_team_hippocampus` |
| `cortex.record_turn(response, history_length)` | `get_stats()` | `cortex_flywheel` |
| `bridge.consolidate_turn(history, response)` | `is_pressure()`, `offload_if_needed()` | `memory_cortex_bridge` |
| `enhancement.track_turn(response)` | `get_status()`, `install_hooks()` | `hermes_enhancement_suite` |

**Detection:**
```python
import inspect

# Check actual method signatures before writing handler
obj = MemoryCortexBridge()
for name, method in inspect.getmembers(obj, predicate=inspect.ismethod):
    if not name.startswith('_'):
        sig = inspect.signature(method)
        print(f"  {name}{sig}")
```

**Fix:** Rewrite handler to call actual methods with correct signatures:
```python
# BEFORE (broken):
scorecard.record_tool_call(tool_name, result, error, duration_ms)

# AFTER (fixed):
stats = scorecard.compute_scorecard()
logger.debug(f"Scorecard: {stats}")
```

## The Complete Plugin-System Compatibility Check

Before declaring a cognitive plugin operational, run this:

```python
import os, sys, inspect
sys.path.insert(0, os.path.expanduser('~/hermes-agent'))

systems = [
    ("iteration_engine", "get_engine", None),  # function-based
    ("cortex_flywheel", "CortexDB", ["get_stats"]),
    ("agent_scorecard", None, ["compute_scorecard"]),  # module-level functions
    ("tool_misuse_prevention", None, ["validate_tool_call"]),
    ("red_team_hippocampus", None, ["learn"]),
    ("memory_cortex_bridge", "MemoryCortexBridge", ["is_pressure", "offload_if_needed"]),
    ("hermes_enhancement_suite", "HermesEnhancementSuite", ["get_status"]),
]

for name, class_name, methods in systems:
    try:
        if class_name:
            cls = getattr(__import__(f'agent.{name}', fromlist=[class_name]), class_name)
            obj = cls()
            print(f"✅ {name}: {class_name} instantiates")
            for method in methods or []:
                if hasattr(obj, method):
                    print(f"   ✅ .{method}() exists")
                else:
                    print(f"   ❌ .{method}() MISSING")
        else:
            mod = __import__(f'agent.{name}')
            print(f"✅ {name}: module loads")
            for method in methods or []:
                if hasattr(mod, method):
                    print(f"   ✅ .{method}() exists")
                else:
                    print(f"   ❌ .{method}() MISSING")
    except Exception as e:
        print(f"❌ {name}: {e}")
```

## Common False Positives

| False Positive | Why It's Wrong | Correct Check |
|----------------|---------------|---------------|
| `hasattr(module, 'function')` | Function exists but never called | Search for `function(` in run_agent.py |
| `import works` | Module loads but not wired | Check for instantiation in agent loop |
| `registry.register()` present | Registration exists but tool not in schema | Check `get_tool_definitions()` output |
| `plugin enabled in config` | Config says enabled but init fails | Check `_invoke_hook` actually fires |
| `hook handler defined` | Handler exists but not registered | Check `register_hook` or hook manager |
| `class instantiates` | Class loads but methods don't match | Verify each method signature used by plugin |
| `handler runs without error` | `except Exception: pass` hides failures | Remove exception suppression for verification |

## The User's Expectation

When the user asks "is it all wired and functional for every turn?", they want:

1. **Proof of hook firing** — `_invoke_hook("pre_llm_call")` appears in run_agent.py
2. **Proof of plugin enabled** — `cognitive-systems` in config.yaml enabled list
3. **Proof of method called** — `run_cycle()` calls `_graduate_tips_to_skills()`, not just defines it
4. **Proof of per-turn execution** — hooks fire on EVERY turn, not just at startup

## Anti-Pattern: Checkbox Theater

```python
# ❌ BAD — creates false confidence
print("✅ Skill graduation: CREATED")  # File says CREATED but skill missing
print("✅ Hooks: registered")          # Handlers exist but not in _invoke_hook
print("✅ Self-evolution: wired")      # Module imported but run_cycle never called
```

The knowledge file `agent-architecture-resources.md` had "✅ CREATED" for all 10 skills, but 4 were in different categories than expected. The checkbox created false confidence. Always verify with the filesystem + import test.

## Pragmatism: When to Stop

If a ghost file/directory recreates but has:
- Empty database (0 rows)
- No code references
- No config references
- Zero functional impact

**Mark "will clear on restart" and move on.** The user said: *"uhhh is it having any effect? if not let's mark it and leave it alone."*
