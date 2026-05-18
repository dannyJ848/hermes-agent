# Live Cognitive Systems Verification — July 2026

**Session:** July 2026 — verifying the cognitive-systems plugin is fully operational after integration

## The Problem

After moving cognitive modules from `~/subconscious/` to `agent/`, they can appear integrated when they're actually orphaned. The user gets furious when systems are "built" but not "wired." This verification pattern uses the live Hermes PluginManager to prove actual operational status.

## Verification Commands

### Step 1: Load the plugin via PluginManager

```python
from hermes_cli.plugins import PluginManager
pm = PluginManager()
pm.discover_and_load()
```

This discovers and loads ALL plugins, including `cognitive-systems`. It also shows load errors for any broken plugins.

### Step 2: Check cognitive-systems plugin status

```python
plugin = pm._plugins.get('cognitive-systems')
print(f"Loaded: {plugin.module is not None if plugin else False}")
print(f"Enabled: {plugin.enabled if plugin else False}")
print(f"Error: {plugin.error if plugin else 'N/A'}")
print(f"Hooks registered: {plugin.hooks_registered if plugin else []}")
print(f"Tools registered: {plugin.tools_registered if plugin else []}")
```

**Expected for operational state:**
```
Loaded: True
Enabled: True
Error: None
Hooks registered: ['pre_llm_call', 'post_llm_call', 'on_session_start', 'on_session_end']
Tools registered: ['screen_capture', 'gui_click', 'gui_type']
```

**Note:** `hooks_registered` only shows hooks that were **newly** registered by this plugin. If another plugin (e.g., `learning-brain`) already registered `pre_tool_call`, it won't appear in `cognitive-systems`'s list. Always check `pm._hooks` for the complete callback picture.

### Step 3: Verify all hooks have cognitive-systems callbacks

```python
for hook_name, callbacks in pm._hooks.items():
    if callbacks:
        cs_callbacks = [c for c in callbacks 
                       if hasattr(c, '__name__') and '_handler' in c.__name__]
        if cs_callbacks:
            print(f"{hook_name}: {len(cs_callbacks)} cognitive-systems callback(s)")
```

**Expected:**
```
pre_tool_call: 1 cognitive-systems callback(s)
post_tool_call: 1 cognitive-systems callback(s)
pre_llm_call: 1 cognitive-systems callback(s)
post_llm_call: 1 cognitive-systems callback(s)
on_session_start: 1 cognitive-systems callback(s)
on_session_end: 1 cognitive-systems callback(s)
```

### Step 4: Verify all 7 cognitive systems load

```python
from hermes_cli.plugins import PluginManager, PluginManifest
pm = PluginManager()
manifest = PluginManifest(
    name='cognitive-systems',
    version='2.0.0',
    description='test',
    source='user',
    path='/Users/dannygomez/.hermes/plugins/cognitive-systems',
)
module = pm._load_directory_module(manifest)

systems = [
    'iteration_engine', 'cortex_flywheel', 'agent_scorecard',
    'tool_misuse_prevention', 'red_team_hippocampus',
    'memory_cortex_bridge', 'hermes_enhancement_suite',
]

for name in systems:
    try:
        system = module._load_system(name)
        print(f"{'✓' if system else '✗'} {name}: {type(system).__name__ if system else 'FAILED'}")
    except Exception as e:
        print(f"✗ {name}: {e}")
```

**Expected:**
```
✓ iteration_engine: IterationEngine
✓ cortex_flywheel: CortexDB
✓ agent_scorecard: module
✓ tool_misuse_prevention: module
✓ red_team_hippocampus: module
✓ memory_cortex_bridge: MemoryCortexBridge
✓ hermes_enhancement_suite: HermesEnhancementSuite
```

### Step 5: Verify iteration engine DB health

```python
from agent.iteration_engine import get_engine
import os, sqlite3

engine = get_engine()
print(f"DB path: {engine.db_path}")
print(f"DB exists: {os.path.exists(engine.db_path)}")

conn = sqlite3.connect(engine.db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tables: {tables}")

if 'experiences' in tables:
    cursor.execute('SELECT COUNT(*) FROM experiences')
    count = cursor.fetchone()[0]
    print(f"Experiences recorded: {count}")
conn.close()
```

**Expected:**
```
DB path: /Users/dannygomez/.hermes/cerebrum_memory.db
DB exists: True
Tables: ['experiences', 'sqlite_sequence', 'skills', ...]
Experiences recorded: 113
```

## Critical Pitfall: Testing the Wrong Module

There are TWO files that look like the cognitive systems plugin:

1. `~/hermes-agent/agent/cognitive_systems_plugin.py` — **WRONG class names**, broken imports
2. `~/.hermes/plugins/cognitive-systems/__init__.py` — **CORRECT class names**, working

**The Hermes plugin loader uses #2**, but developers often test #1 by mistake.

**Wrong test (returns false negatives):**
```python
from agent.cognitive_systems_plugin import _load_system  # WRONG MODULE
_load_system("agent_scorecard")  # Returns None — uses wrong class name
```

**Correct test (returns true state):**
```python
from hermes_cli.plugins import PluginManager, PluginManifest
pm = PluginManager()
manifest = PluginManifest(name='cognitive-systems', ...)
module = pm._load_directory_module(manifest)  # Loads actual plugin
module._load_system("agent_scorecard")  # Returns module — correct
```

## Plugin Coexistence

Multiple plugins can register the same hooks. Both `learning-brain` and `cognitive-systems` register `pre_tool_call`, `post_tool_call`, `on_session_start`, `on_session_end`. Both fire independently.

**The `hooks_registered` list on a plugin only shows hooks that were NEWLY added by that plugin.** If another plugin already registered a hook, it won't appear in the list. Always check `pm._hooks` for the complete callback picture.

## Complete Verification Script

```python
#!/usr/bin/env python3
"""Verify cognitive-systems plugin is fully operational."""
import os, sys
sys.path.insert(0, os.path.expanduser("~/hermes-agent"))

from hermes_cli.plugins import PluginManager, PluginManifest

pm = PluginManager()
pm.discover_and_load()

print("=" * 60)
print("COGNITIVE SYSTEMS PLUGIN VERIFICATION")
print("=" * 60)

# 1. Plugin loaded?
plugin = pm._plugins.get('cognitive-systems')
assert plugin and plugin.enabled, "Plugin not loaded or not enabled"
print("✓ Plugin loaded and enabled")

# 2. All hooks registered?
expected_hooks = ['pre_tool_call', 'post_tool_call', 'pre_llm_call', 'post_llm_call', 'on_session_start', 'on_session_end']
for hook in expected_hooks:
    callbacks = pm._hooks.get(hook, [])
    cs_callbacks = [c for c in callbacks if hasattr(c, '__name__') and '_handler' in c.__name__]
    assert len(cs_callbacks) > 0, f"No cognitive-systems callback for {hook}"
    print(f"✓ {hook}: {len(cs_callbacks)} cognitive-systems callback(s)")

# 3. Tools registered?
expected_tools = ['screen_capture', 'gui_click', 'gui_type']
for tool in expected_tools:
    assert tool in plugin.tools_registered, f"Tool {tool} not registered"
    print(f"✓ Tool {tool} registered")

# 4. All systems load?
manifest = PluginManifest(
    name='cognitive-systems', version='2.0.0', description='test',
    source='user', path=os.path.expanduser('~/.hermes/plugins/cognitive-systems'),
)
module = pm._load_directory_module(manifest)

systems = [
    'iteration_engine', 'cortex_flywheel', 'agent_scorecard',
    'tool_misuse_prevention', 'red_team_hippocampus',
    'memory_cortex_bridge', 'hermes_enhancement_suite',
]
for name in systems:
    system = module._load_system(name)
    assert system is not None, f"System {name} failed to load"
    print(f"✓ {name}: loaded ({type(system).__name__})")

# 5. Iteration engine DB healthy?
from agent.iteration_engine import get_engine
engine = get_engine()
assert os.path.exists(engine.db_path), "DB does not exist"
import sqlite3
conn = sqlite3.connect(engine.db_path)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM experiences")
count = c.fetchone()[0]
conn.close()
print(f"✓ Iteration engine DB: {count} experiences recorded")

print("=" * 60)
print("ALL CHECKS PASSED — Cognitive systems are operational")
print("=" * 60)
```
