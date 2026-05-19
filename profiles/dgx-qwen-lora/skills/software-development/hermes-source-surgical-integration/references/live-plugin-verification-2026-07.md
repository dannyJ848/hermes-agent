# Live Plugin Verification — July 2026

**Session:** July 2026 — verifying cognitive-systems plugin is actually operational in a running Hermes session

## The Problem

After integration, cognitive modules can appear "operational" when they're actually orphaned:
- Files exist in `agent/` ✅
- Module imports work ✅
- Plugin is "enabled" in config ✅
- But hooks are NOT firing because the plugin module has wrong class names

The existing verification approaches (file presence, config checks) give false confidence. This pattern uses the **live PluginManager** to verify actual hook registration.

## The Verification Commands

### Step 1: Discover and load all plugins

```python
from hermes_cli.plugins import PluginManager
pm = PluginManager()
pm.discover_and_load()
```

This loads ALL plugins including `cognitive-systems` and shows any load errors.

### Step 2: Check specific plugin status

```python
plugin = pm._plugins.get('cognitive-systems')
print(f"Loaded: {plugin.module is not None if plugin else False}")
print(f"Enabled: {plugin.enabled if plugin else False}")
print(f"Error: {plugin.error if plugin else 'N/A'}")
print(f"Hooks registered: {plugin.hooks_registered if plugin else []}")
print(f"Tools registered: {plugin.tools_registered if plugin else []}")
```

**Expected output for operational state:**
```
Loaded: True
Enabled: True
Error: None
Hooks registered: ['pre_llm_call', 'post_llm_call', 'on_session_start', 'on_session_end']
Tools registered: ['screen_capture', 'gui_click', 'gui_type']
```

**Note:** `hooks_registered` only shows hooks that were **newly** registered by this plugin. If another plugin (e.g., `learning-brain`) already registered `pre_tool_call`, it won't appear in `cognitive-systems`'s list. Check `_hooks` directly for the full picture.

### Step 3: Check all hooks with callbacks

```python
for hook_name, callbacks in pm._hooks.items():
    if callbacks:
        print(f"{hook_name}: {len(callbacks)} callback(s)")
        for cb in callbacks:
            name = cb.__qualname__ if hasattr(cb, '__qualname__') else str(cb)[:50]
            print(f"  - {name}")
```

**Expected output:**
```
on_session_start: 2 callback(s)
  - on_session_start_hook          # from learning-brain
  - _on_session_start_handler     # from cognitive-systems
pre_tool_call: 4 callback(s)
  - pre_tool_call_hook            # from learning-brain
  - _pre_tool_call_handler        # from cognitive-systems
  - _on_pre_tool_call             # from evey-tool-intelligence
  - on_pre_tool_call              # from evey-validate
post_tool_call: 4 callback(s)
  - post_tool_call_hook           # from learning-brain
  - _post_tool_call_handler       # from cognitive-systems
  - _on_post_tool_call            # from evey-tool-intelligence
  - on_post_tool_call             # from evey-validate
pre_llm_call: 3 callback(s)
  - _pre_llm_call_handler         # from cognitive-systems
  - _on_pre_llm_call              # from evey-validate
  - on_pre_llm_call               # from evey-reflect
post_llm_call: 1 callback(s)
  - _post_llm_call_handler        # from cognitive-systems
```

### Step 4: Verify cognitive systems actually load

```python
# Import the actual plugin module that Hermes loads
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

# Test all 7 cognitive systems
systems = [
    'iteration_engine',
    'cortex_flywheel',
    'agent_scorecard',
    'tool_misuse_prevention',
    'red_team_hippocampus',
    'memory_cortex_bridge',
    'hermes_enhancement_suite',
]

for name in systems:
    try:
        system = module._load_system(name)
        if system:
            print(f"✓ {name}: {type(system).__name__}")
        else:
            print(f"✗ {name}: returned None")
    except Exception as e:
        print(f"✗ {name}: {e}")
```

**Expected output:**
```
✓ iteration_engine: IterationEngine
✓ cortex_flywheel: CortexDB
✓ agent_scorecard: module
✓ tool_misuse_prevention: module
✓ red_team_hippocampus: module
✓ memory_cortex_bridge: MemoryCortexBridge
✓ hermes_enhancement_suite: HermesEnhancementSuite
```

### Step 5: Verify iteration engine database health

```python
from agent.iteration_engine import get_engine
engine = get_engine()
print(f"DB path: {engine.db_path}")
print(f"DB exists: {os.path.exists(engine.db_path)}")

# Check tables
import sqlite3
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

**Expected output:**
```
DB path: /Users/dannygomez/.hermes/cerebrum_memory.db
DB exists: True
Tables: ['experiences', 'sqlite_sequence', 'skills', 'memory_echo', ...]
Experiences recorded: 113
```

## Critical Pitfall: Testing the Wrong Module

There are TWO `cognitive_systems_plugin.py` files:

1. `~/hermes-agent/agent/cognitive_systems_plugin.py` — **WRONG class names**, broken
2. `~/.hermes/plugins/cognitive-systems/__init__.py` — **CORRECT class names**, working

**The Hermes plugin loader uses #2**, but developers often test #1 by mistake.

**Wrong test:**
```python
from agent.cognitive_systems_plugin import _load_system  # WRONG MODULE
_load_system("agent_scorecard")  # Returns None — uses wrong class name
```

**Correct test:**
```python
from hermes_cli.plugins import PluginManager, PluginManifest
pm = PluginManager()
manifest = PluginManifest(name='cognitive-systems', ...)
module = pm._load_directory_module(manifest)  # Loads ~/.hermes/plugins/cognitive-systems/__init__.py
module._load_system("agent_scorecard")  # Returns module — correct
```

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
print(f"✓ Plugin loaded and enabled")

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

## Key Insight

**Plugin coexistence is normal.** Multiple plugins can register the same hooks. The `learning-brain` plugin registers `pre_tool_call`, `post_tool_call`, `on_session_start`, `on_session_end`. The `cognitive-systems` plugin also registers these hooks. Both fire independently.

**The `hooks_registered` list on a plugin only shows hooks that were NEWLY added by that plugin.** If another plugin already registered a hook, it won't appear in the list. Always check `pm._hooks` for the complete callback picture.
