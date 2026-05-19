# Plugin Tool Verification — CLI vs Runtime

## The Trap

`hermes tools list` **does not show plugin-registered tools**. It only lists built-in tools from the core toolsets. This creates a false-negative when verifying that a plugin's `ctx.register_tool()` calls succeeded.

## Correct Verification Methods

### Method 1: PluginManager introspection (Python)

```python
from hermes_cli.plugins import PluginManager
pm = PluginManager()
pm.discover_and_load()

plugin = pm._plugins.get('cognitive-systems')
if plugin:
    print(f"Tools registered: {plugin.tools_registered}")
    print(f"Hooks registered: {plugin.hooks_registered}")
    print(f"Enabled: {plugin.enabled}")
    print(f"Error: {plugin.error}")
```

Expected output for a healthy plugin:
```
Tools registered: ['gui_click', 'screen_capture', 'gui_type']
Hooks registered: ['pre_llm_call', 'post_llm_call']
Enabled: True
Error: None
```

### Method 2: Direct module import test

```python
# Test that tool handler functions are importable and schemas are correct
from agent.vision_tools import (
    screen_capture_tool, gui_click_tool, gui_type_tool,
    SCREEN_CAPTURE_SCHEMA, GUI_CLICK_SCHEMA, GUI_TYPE_SCHEMA
)

assert "properties" in SCREEN_CAPTURE_SCHEMA
assert "required" in GUI_CLICK_SCHEMA
```

### Method 3: Hook wiring verification in source

Confirm hooks are actually invoked by the agent loop, not just registered:

```bash
# Check pre_llm_call
grep -n 'invoke_hook.*"pre_llm_call"' ~/hermes-agent/run_agent.py

# Check post_llm_call
grep -n 'invoke_hook.*"post_llm_call"' ~/hermes-agent/run_agent.py

# Check pre_tool_call (via block message)
grep -n 'get_pre_tool_call_block_message' ~/hermes-agent/run_agent.py

# Check post_tool_call
grep -n 'invoke_hook.*"post_tool_call"' ~/hermes-agent/model_tools.py

# Check on_session_start/on_session_end
grep -n 'invoke_hook.*"on_session_start"\|invoke_hook.*"on_session_end"' ~/hermes-agent/run_agent.py
```

## Full Operational Audit Script

```python
#!/usr/bin/env python3
"""Verify cognitive-systems plugin is fully operational."""
import sys, os
sys.path.insert(0, os.path.expanduser('~/hermes-agent'))

from hermes_cli.plugins import PluginManager

pm = PluginManager()
pm.discover_and_load()

plugin = pm._plugins.get('cognitive-systems')
assert plugin is not None, "Plugin not loaded"
assert plugin.enabled, "Plugin disabled"
assert plugin.error is None, f"Plugin error: {plugin.error}"

# Verify tools
expected_tools = {'screen_capture', 'gui_click', 'gui_type'}
actual_tools = set(plugin.tools_registered)
assert expected_tools <= actual_tools, f"Missing tools: {expected_tools - actual_tools}"

# Verify hooks
expected_hooks = {'pre_llm_call', 'post_llm_call', 'pre_tool_call', 'post_tool_call',
                  'on_session_start', 'on_session_end'}
actual_hooks = set(plugin.hooks_registered)
assert expected_hooks <= actual_hooks, f"Missing hooks: {expected_hooks - actual_hooks}"

# Verify cognitive modules are importable
systems = [
    'iteration_engine', 'cortex_flywheel', 'agent_scorecard',
    'tool_misuse_prevention', 'red_team_hippocampus',
    'memory_cortex_bridge', 'hermes_enhancement_suite',
    'self_evolution', 'vision_loop'
]
for name in systems:
    __import__(f'agent.{name}')

print("✅ All systems operational")
```

## CLI Command Reference

| What you want | Command | Notes |
|---------------|---------|-------|
| List plugins | `hermes plugins list` | Shows enabled/disabled status |
| Check specific plugin | `hermes plugins list \| grep <name>` | Quick status check |
| List tools | `hermes tools list` | **Only built-in tools** — misses plugin tools |
| Verify plugin tools | Python `PluginManager._plugins[name].tools_registered` | Correct method |
| Verify hook wiring | `grep invoke_hook.*"hook_name" run_agent.py model_tools.py` | Confirms core calls the hook |
