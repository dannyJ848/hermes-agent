# Hermes Harness Adaptations — May 6, 2026

## Session Context

Comprehensive audit of the Hermes harness revealed gaps between upstream features and our fork. Adopted 4 upstream commits and created 3 workflow helper scripts to work around weak tools.

## Adopted Upstream Features

### 1. Per-Capability Backend Selection (bf4e50214)

**What:** `web_search` and `web_extract` now use different backends based on capability.

**Why:** Previously both used the same backend, causing failures when the backend was good at one but not the other.

**Files changed:**
- `hermes_cli/config.py` — backend selection logic
- `tools/web_tools.py` — capability routing
- `tools/web_providers/` — new provider architecture

**Status:** Cherry-picked cleanly. No conflicts.

### 2. Hook Context Spill to Disk (b6c53ef0b)

**What:** Large skill hooks (>8KB) spill to disk instead of flooding the context window.

**Why:** Skills like `infrastructure-surgical-management` with long reference files were consuming excessive tokens.

**Files changed:**
- `agent/shell_hooks.py` — spill detection
- `tools/hook_output_spill.py` — spill handler
- `run_agent.py` — hook loading

**Status:** Cherry-picked cleanly.

### 3. Kanban Task Runs Summary (3f9729741)

**What:** `kanban show` and dashboard cards display `task_runs.summary`.

**Why:** Better visibility into what actually happened during task execution.

**Files changed:**
- `hermes_cli/kanban.py` — summary collection
- `hermes_cli/kanban_db.py` — summary storage
- `plugins/kanban/dashboard/plugin_api.py` — dashboard display

**Status:** Cherry-picked cleanly.

### 4. Cron No-Agent Mode (3db6b9cc8)

**What:** Cron jobs can run as scripts without spawning a full agent.

**Why:** Training monitors and watchdogs don't need agent overhead — they're just polling scripts.

**Files changed:**
- `cron/scheduler.py` — no_agent scheduling
- `cron/jobs.py` — job execution mode
- `hermes_cli/cron.py` — CLI support
- `tools/cronjob_tools.py` — tool support

**Status:** Cherry-picked cleanly.

## Workflow Helper Scripts

Created to replace weak tools:

| Helper | Replaces | Weak Tool Success | Helper Method |
|--------|----------|-------------------|---------------|
| `cron_helper.py` | `cronjob` tool | 13% | `hermes cron` CLI |
| `patch_helper.py` | `patch` tool | 59% | Python file I/O with validation |
| `skill_helper.py` | `skill_manage` | 49% | Direct file writes + YAML validation |

### cron_helper.py

```python
# Usage:
python3 ~/.hermes/scripts/cron_helper.py list
python3 ~/.hermes/scripts/cron_helper.py remove <job_name>
python3 ~/.hermes/scripts/cron_helper.py create <name> <schedule> <script>
```

**Key insight:** The `cronjob` tool fails because it requires an `id` field that isn't documented. The `hermes cron` CLI works reliably.

### patch_helper.py

```python
# Usage:
python3 ~/.hermes/scripts/patch_helper.py <file> <old_string> <new_string>
```

**Key insight:** `patch` tool fails when:
1. File wasn't read first (stale view)
2. `old_string` contains invisible characters
3. File was modified by another tool between read and patch

This helper reads the file fresh, validates the old_string exists, then applies the change.

### skill_helper.py

```python
# Usage:
python3 ~/.hermes/scripts/skill_helper.py create <name> <category> <content>
python3 ~/.hermes/scripts/skill_helper.py patch <name> <old> <new>
```

**Key insight:** `skill_manage` fails because:
1. YAML frontmatter parsing is strict (numbered lists with colons break it)
2. `old_string` matching is fragile
3. No validation before write

This helper validates YAML before writing and uses exact string matching.

## Tool Intelligence Integration

The tool intelligence system reported these weaknesses:

```
WEAK TOOLS:
  - cronjob: 13% success (31 calls)
  - skill_manage: 49% success (365 calls)
  - patch: 59% success (397 calls)

PROVEN:
  - write_file: 87%
  - execute_code: 93%
  - web_extract: 94%
  - web_search: 96%
```

**Decision:** Route around weak tools. Use proven tools for critical operations.

## Verification

```bash
# Check adopted features are present
grep -q "per_capability" hermes_cli/config.py && echo "✓ per-capability backend"
grep -q "hook_spill" agent/shell_hooks.py && echo "✓ hook context spill"
grep -q "task_runs.summary" hermes_cli/kanban.py && echo "✓ kanban summary"
grep -q "no_agent" cron/scheduler.py && echo "✓ cron no_agent"

# Check helpers exist
ls ~/.hermes/scripts/cron_helper.py && echo "✓ cron helper"
ls ~/.hermes/scripts/patch_helper.py && echo "✓ patch helper"
ls ~/.hermes/scripts/skill_helper.py && echo "✓ skill helper"
```

## Skipped Features

| Feature | Commit | Reason |
|---------|--------|--------|
| Providers pluggable | 9022804d7 | Our branch deleted `providers/` directory — structural conflict |
| i18n locales | Multiple | Low value for our use case |

## Commit

All changes committed to `qwen27b-training-artifacts-may3-2026`:
- `46ee245e4` — Adopt upstream features
- `1d522fb74` — Workflow helpers + learning apparatus enhancements
