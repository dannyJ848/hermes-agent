# Hermes Plugin Tool Parity Audit

## Quick Check: How Many Tools Do I Have?

```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
from model_tools import get_tool_definitions
tools = get_tool_definitions(quiet_mode=True)
print(f'Total tools: {len(tools)}')
for t in tools:
    print(' ', t.get('function',{}).get('name','unknown'))
"
```

## Expected Tool Counts

| Setup | Typical Count | What's Included |
|-------|--------------|-----------------|
| Fresh Hermes install | ~21 | Core tools only (no external deps) |
| With browser tools | ~31 | +10 browser tools (needs agent-browser) |
| With Evey plugins | ~84 | +63 personal plugins |
| With API tools | ~103 | +Discord, Feishu, web search, etc. |

## Diagnosing Missing Tools

### Step 1: Check plugin discovery

```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
from hermes_cli.plugins import discover_plugins
import logging
logging.basicConfig(level=logging.DEBUG)
discover_plugins()
" 2>&1 | grep -E '(Skipping|enabled|not in plugins.enabled)'
```

**If you see "Skipping 'my-plugin' (not in plugins.enabled)":**
- Plugin exists but isn't enabled in config
- Edit `~/.hermes/config.yaml` (NOT repo config) to add to `plugins.enabled`

**If you see "Plugin discovery complete: X found, 0 enabled":**
- `plugins.enabled` list is missing or empty
- Add the list to `~/.hermes/config.yaml`

### Step 2: Check which config file is loaded

```bash
python3 -c "from hermes_cli.config import get_config_path; print(get_config_path())"
# Should print: /home/YOU/.hermes/config.yaml
```

### Step 3: Verify plugins exist on disk

```bash
ls ~/.hermes/plugins/ | sort
# Should show your plugin directories
```

### Step 4: Check for plugin load errors

```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
from hermes_cli.plugins import discover_plugins
import logging
logging.basicConfig(level=logging.INFO)
discover_plugins()
" 2>&1 | grep -i 'failed\|error\|exception'
```

Common errors:
- `No module named 'honcho_bridge'` → Missing dependency, add to `disabled` list
- `No module named 'plugins.spotify'` → Plugin references missing module
- `Tool registration REJECTED: 'X' would shadow existing tool` → Name collision between plugins

## Cross-Machine Sync Checklist

When setting up Hermes on a new machine:

- [ ] Sync `~/.hermes/plugins/` from source machine
- [ ] Sync `~/.hermes/skills/` from source machine (optional)
- [ ] Copy `plugins.enabled` list from source `~/.hermes/config.yaml`
- [ ] Verify target config path: `get_config_path()`
- [ ] Run tool count check: should match source count
- [ ] Test a few plugin tools to confirm they work

## Plugin-Registered Tools vs Core Tools

**Important:** `hermes tools list` does NOT show plugin-registered tools. Use Python introspection:

```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "
from model_tools import get_tool_definitions
tools = get_tool_definitions(quiet_mode=True)
names = [t.get('function',{}).get('name','') for t in tools]
print(f'Total: {len(names)}')
print('Plugin tools:', [n for n in names if n.startswith(('evey_', 'claude_bridge', 'mesh_', 'verify_'))])
"
```
