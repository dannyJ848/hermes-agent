---
name: hermes-context-engine-install
description: Install and wire in third-party context engine plugins for Hermes Agent. Covers slot verification, cloning, testing, and config activation.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
---

# Hermes Context Engine Plugin Installation

Hermes Agent has a pluggable context engine slot (PR #7464+). Third-party engines replace the built-in `ContextCompressor`. Only ONE engine can be active at a time, selected via `context.engine` in config.yaml.

## Install Steps

### 1. Verify the slot exists

```python
# Check for the ABC
from agent.context_engine import ContextEngine
# Check for the plugin loader
from plugins.context_engine import discover_context_engines, load_context_engine
```

If these import, the slot is available.

### 2. Clone into the correct directory

Context engines MUST go under `plugins/context_engine/<name>/`, NOT `~/.hermes/plugins/`:

```bash
git clone https://github.com/USER/hermes-engine ~/hermes-agent/plugins/context_engine/engine_name
```

Per-profile alternative:
```bash
git clone https://github.com/USER/hermes-engine ~/.hermes/profiles/myprofile/hermes-agent/plugins/context_engine/engine_name
```

### 3. Verify the engine loads

```python
import sys; sys.path.insert(0, ".")
from plugins.context_engine import discover_context_engines, load_context_engine

# List all available engines
engines = discover_context_engines()
for name, desc, available in engines:
    print(f"  {name}: available={available} | {desc}")

# Load the specific engine
engine = load_context_engine("engine_name")
print(f"name={engine.name}, type={type(engine).__name__}")
print(f"Is ContextEngine: {isinstance(engine, ContextEngine)}")
```

Key attributes to verify:
- `engine.name` — short identifier
- `engine.threshold_percent` — default 0.75
- `engine.protect_first_n` — default 3
- `engine.protect_last_n` — varies (LCM uses 64)
- `engine.compression_count` — starts at 0

### 4. Run the plugin's own tests

```bash
cd ~/hermes-agent/plugins/context_engine/engine_name
source ~/hermes-agent/venv/bin/activate
python3 -m pytest tests/ -v --tb=short
```

**Known issue:** Tests written for standalone import (e.g. `hermes_lcm.tools`) may fail when run from the plugin directory because the module path differs (`plugins.context_engine.lcm.tools`). This is a test isolation issue, not a functional bug. Check if failures are only monkeypatch path mismatches.

### 5. Activate in config.yaml

```yaml
context:
  engine: lcm  # was: compressor
```

File: `~/.hermes/config.yaml`

### 6. Verify end-to-end after restart

Check that the engine loaded by looking for its tools in the agent's available tools, or run:

```python
from plugins.context_engine import load_context_engine
engine = load_context_engine("engine_name")
from agent.context_engine import ContextEngine
schemas = ContextEngine.get_tool_schemas(engine)
# Note: schemas may be empty until register() is called at runtime
```

## Available Engines

- `compressor` — built-in default (ContextCompressor)
- `hindsight` — knowledge-graph-backed compression using Hindsight API + cerebrum tips
- `lcm` — Lossless Context Management, DAG-based, zero deps, every message persisted

## Pitfalls

- **Wrong directory:** Context engines go in `plugins/context_engine/<name>/`, not `plugins/<name>/`. The general plugins directory is for tools/hooks — context engines are discovered separately.
- **Only one active:** Setting `context.engine: lcm` replaces the compressor entirely. The old compressor is still installed, just not selected.
- **Test path mismatches:** Plugin tests may assume standalone import paths. Run them but don't block on monkeypatch failures.
- **Storage paths:** Each engine manages its own storage. LCM uses `~/.hermes/lcm.db` (SQLite). Hindsight uses the cortex PostgreSQL DB.
- **Config via env vars:** LCM uses `LCM_*` env vars for tuning (fresh_tail_count, leaf_chunk_tokens, etc.). Defaults are sensible — no env vars needed unless customizing.
