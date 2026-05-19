# Cognitive Plugin Handler Signatures — July 2026

**Session:** July 10, 2026 — fixing class name mismatches and handler signature drift in cognitive-systems plugin

## The Problem

The `cognitive-systems` plugin at `~/.hermes/plugins/cognitive-systems/__init__.py` had broken handler code that called methods that didn't exist on the actual cognitive modules. Because each handler wraps calls in `except Exception: pass`, these failures were completely silent — the plugin appeared to load but did nothing.

## Class Name Mappings

| Plugin Expected | Actual Export | Module | Fix |
|----------------|-------------|--------|-----|
| `AgentScorecard` (class) | Functions only | `agent_scorecard.py` | `from agent import agent_scorecard` |
| `ToolHealthMonitor` (class) | Functions only | `tool_misuse_prevention.py` | `from agent import tool_misuse_prevention` |
| `ErrorMiner` (class) | Functions only | `red_team_hippocampus.py` | `from agent import red_team_hippocampus` |
| `MemoryBridge` (class) | `MemoryCortexBridge` | `memory_cortex_bridge.py` | `from agent.memory_cortex_bridge import MemoryCortexBridge` |
| `EnhancementTracker` (class) | `HermesEnhancementSuite` | `hermes_enhancement_suite.py` | `from agent.hermes_enhancement_suite import HermesEnhancementSuite` |

## Handler Signature Mappings

### post_tool_call handler

| What Plugin Called | Actual Method | Module | Correct Call |
|-------------------|-------------|--------|-------------|
| `scorecard.record_tool_call(tool_name, result, error, duration_ms)` | `compute_scorecard(db=None)` | `agent_scorecard` | `stats = scorecard.compute_scorecard()` |
| `red_team.mine_error(tool_name, error, result)` | `learn(outcome, url='', technique='', success=False)` | `red_team_hippocampus` | `red_team.learn(outcome=f"Tool {tool_name} failed: {error}", technique=tool_name, success=False)` |

### post_llm_call handler

| What Plugin Called | Actual Method | Module | Correct Call |
|-------------------|-------------|--------|-------------|
| `cortex.record_turn(response, history_length)` | `get_stats()` | `cortex_flywheel` | `stats = cortex.get_stats()` |
| `bridge.consolidate_turn(history, response)` | `is_pressure()`, `offload_if_needed()` | `memory_cortex_bridge` | `if bridge.is_pressure(): bridge.offload_if_needed()` |
| `enhancement.track_turn(response)` | `get_status()`, `install_hooks()` | `hermes_enhancement_suite` | `status = enhancement.get_status()` |

## Detection Script

Run this to check for drift:

```python
import inspect, sys, os
sys.path.insert(0, os.path.expanduser("~/hermes-agent"))

# Check all cognitive systems
systems = [
    ("agent_scorecard", None, ["compute_scorecard"]),
    ("tool_misuse_prevention", None, ["validate_tool_call"]),
    ("red_team_hippocampus", None, ["learn"]),
    ("cortex_flywheel", "CortexDB", ["get_stats"]),
    ("memory_cortex_bridge", "MemoryCortexBridge", ["is_pressure", "offload_if_needed"]),
    ("hermes_enhancement_suite", "HermesEnhancementSuite", ["get_status"]),
]

for name, class_name, methods in systems:
    try:
        if class_name:
            cls = getattr(__import__(f"agent.{name}", fromlist=[class_name]), class_name)
            obj = cls()
            for method in methods:
                if hasattr(obj, method):
                    sig = inspect.signature(getattr(obj, method))
                    print(f"✅ {name}.{method}{sig}")
                else:
                    print(f"❌ {name}.{method}() MISSING")
        else:
            mod = __import__(f"agent.{name}")
            for method in methods:
                if hasattr(mod, method):
                    print(f"✅ {name}.{method}() exists")
                else:
                    print(f"❌ {name}.{method}() MISSING")
    except Exception as e:
        print(f"❌ {name}: {e}")
```

## Prevention

1. **Before writing handler code**, run `inspect.getmembers()` on the target module
2. **Never assume** the class name matches the file name
3. **Never assume** the method name matches your mental model
4. **Remove `except Exception: pass`** during verification — let failures surface
5. **Run the compatibility script** after any agent/ module change
