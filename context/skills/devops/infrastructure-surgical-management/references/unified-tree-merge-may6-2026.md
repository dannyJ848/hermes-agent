# Unified Tree Merge Session

**Date:** May 6, 2026
**Trigger:** User said "merge everything into the central hermes tree so you can see everything at once"

## Problem

The training apparatus (judge, flywheel, cortex) lived in `~/subconscious/` (2653 files) — invisible to the central `hermes_cli/` tree. The agent couldn't find the DeepSeek v4 pro judge because it only searched `hermes_cli/` and `gateway/`.

## Solution

Created a unified tree with symlinks + registry:

```
hermes_cli/
├── subconscious/
│   ├── llm_judge.py → ~/subconscious/llm_judge.py
│   ├── cortex_flywheel.py → ~/subconscious/cortex_flywheel.py
│   └── cortex_access.py → ~/subconscious/cortex_access.py
├── systems_registry.json — unified config
├── unified_status.py — single command status view
└── persistence_health.py — database health checker
```

## Key Insight

When the user says "find it" and the initial search in `hermes_cli/` returns nothing, **immediately expand to `~/subconscious/`, `~/custom_dflash/`, and `~/.hermes/`** before concluding something doesn't exist.

The user had to say "find it" and "expand scope" repeatedly before the agent searched outside `hermes_cli/`. This is a first-class skill signal: the search scope was too narrow.

## Registry Structure

```json
{
  "hermes_core": {"path": "hermes_cli/", "status": "active"},
  "gateway": {"path": "gateway/", "status": "active"},
  "subconscious": {
    "path": "hermes_cli/subconscious/",
    "components": {
      "llm_judge.py": {"default_model": "deepseek-v4-pro", "status": "active"},
      "cortex_flywheel.py": {"heuristic_alignment": "85%", "status": "active"},
      "cortex_access.py": {"tables": 77, "tips": 1900, "status": "active"}
    }
  },
  "training": {"path": "custom_dflash/", "status": "running"},
  "monitoring": {"tools": {...}}
}
```

## Health Checker Pattern

```python
# Defensive: check table existence before querying
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cortex_nodes'")
if c.fetchone():
    c.execute("SELECT COUNT(*) FROM cortex_nodes")
    count = c.fetchone()[0]
else:
    count = 0  # Table doesn't exist yet
```

## Practice Run Results

All systems tested and passing:
- Loop Guard: blocked at call 3
- Self-Healing: patch → write_file fallback
- Post-Mortem: learned 3 error patterns
- Confidence: 0.40 for assumed, 0.95 for direct observation
- Brain: all subsystems respond through unified API
