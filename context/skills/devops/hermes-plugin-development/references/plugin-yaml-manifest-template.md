# Plugin YAML Manifest Template

Every Hermes plugin needs a `plugin.yaml` manifest file alongside `__init__.py` for the plugin loader to discover and activate it.

## Location

```
~/.hermes/plugins/<name>/
  plugin.yaml      # Manifest (required)
  __init__.py      # register(ctx) entry point (required)
  plugin.py        # Optional: additional module code
```

## Manifest Fields

```yaml
name: my-plugin                # Unique plugin identifier (required)
version: "1.0.0"             # Semver string (required)
description: "What this does" # Human-readable description (required)
author: "You"                  # Attribution (optional)
kind: standalone              # Plugin type: standalone | backend | exclusive | platform | memory
provides_hooks:                # List of hooks this plugin registers (optional)
  - pre_tool_call
  - post_tool_call
  - on_session_start
  - on_session_end
entry_point: "my_plugin"       # Python module path for dynamic loading (optional, for memory providers)
config:                        # Plugin-specific configuration (optional)
  db_path: "~/.hermes/my.db"
  some_param: 42
```

## Plugin Types (kind)

| Kind | Purpose |
|------|---------|
| `standalone` | General-purpose plugin with hooks and/or tools |
| `backend` | Provides a backend service (e.g., database, API client) |
| `exclusive` | Only one exclusive plugin of this type can be active |
| `platform` | Platform-specific integration (e.g., Telegram, Discord) |
| `memory` | Memory provider plugin — implements MemoryProvider ABC |

## Memory Provider Example

```yaml
name: yantrikdb
version: "0.2.4"
description: "YantrikDB cognitive memory engine — semantic vector search"
author: "Evey"
kind: memory
entry_point: "memory.yantrikdb"
provides_hooks:
  - pre_tool_call
  - post_tool_call
  - on_session_start
  - on_session_end
config:
  db_path: "~/.hermes/yantrikdb_copy.db"
  embedding_dim: 64
  default_namespace: "default"
```

The `kind: memory` tag tells Hermes this is a memory provider. The `entry_point: "memory.yantrikdb"` tells the plugin loader to import `plugins.memory.yantrikdb` and call `register_memory_provider()`.

## Standalone Plugin Example

```yaml
name: cognitive-systems
version: "2.0.0"
description: "Integrated cognitive systems for Hermes Agent"
author: "Evey"
kind: standalone
provides_hooks:
  - pre_tool_call
  - post_tool_call
  - pre_llm_call
  - on_session_start
```

## Verification

```bash
# Check if plugin is discovered
hermes plugins list | grep my-plugin

# Or via Python
python3 -c "
from hermes_cli.plugins import discover_plugins
for name, desc, available in discover_plugins():
    print(f'{name}: {desc[:50]}... available={available}')
"
```

## Common Mistakes

- **Missing `plugin.yaml`**: Plugin exists on disk but `discover_plugins()` skips it
- **Wrong `kind`**: Using `kind: standalone` for a memory provider — won't be loaded as memory provider
- **Missing `entry_point`**: Memory providers need `entry_point` so the loader knows which module to import
- **YAML syntax errors**: Unquoted strings with special characters, missing quotes on version numbers
- **Wrong directory**: Must be in `~/.hermes/plugins/<name>/`, NOT `~/hermes-agent/plugins/`
