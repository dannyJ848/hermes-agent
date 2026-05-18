# Hermes Core Integration Surgery — Session Record

Date: 2026-05-09
Trigger: User discovered all tools were built in ~/subconscious/ as standalone scripts, not integrated into Hermes source code.
User reaction: "you didn't build it INTO the hermes source code like I thought you were doing... holy fuck this is disappointing."

## Files Integrated

### 1. Auto-handoff at compression threshold
- **Target**: `~/hermes-agent/run_agent.py`
- **Method**: `_compress_context()` method, after compression_count warning
- **Patch**: Added `if _cc >= 5: self._trigger_compression_handoff(...)`
- **New method**: `_trigger_compression_handoff()` added to AIAgent class
- **Lines**: ~2670-2750 (method), ~9813 (trigger point)

### 2. Auto-resume on CLI startup
- **Target**: `~/hermes-agent/cli.py`
- **Method**: `HermesCLI.__init__()` before session ID assignment
- **Patch**: Added `_auto_resume = self._check_pending_handoff(resume)`
- **New method**: `_check_pending_handoff()` added to HermesCLI class
- **Lines**: ~2400 (injection), ~4045 (method)

### 3. Context pressure gauge enhancement
- **Target**: `~/hermes-agent/tools/context_pressure_gauge.py`
- **Added**: `log_compression()`, `get_compression_count()`, `check_handoff_threshold()`
- **Purpose**: Track compressions and detect when handoff threshold reached

### 4. Self-diagnostic tool
- **Target**: `~/hermes-agent/tools/self_diagnostic.py`
- **Registration**: `registry.register(name="self_diagnostic", toolset="health", ...)`
- **Schema**: SELF_DIAGNOSTIC_SCHEMA with component and format params
- **Discovery**: Verified via `discover_builtin_tools()` — shows as `tools.self_diagnostic`

### 5. Skill generator tool
- **Target**: `~/hermes-agent/tools/skill_generator.py`
- **Registration**: `registry.register(name="skill_generator", toolset="meta", ...)`
- **Modes**: "session" (from rapid_learnings) or "topic" (from description)
- **Discovery**: Verified via `discover_builtin_tools()` — shows as `tools.skill_generator`

### 6. Plan executor tool
- **Target**: `~/hermes-agent/tools/plan_executor.py`
- **Registration**: `registry.register(name="plan_executor", toolset="meta", ...)`
- **Schema**: PLAN_EXECUTOR_SCHEMA with plan array and mode param
- **Discovery**: Verified via `discover_builtin_tools()` — shows as `tools.plan_executor`

### 7. Tool tracking fix
- **Target**: `~/hermes-agent/hermes_cli/plugins.py`
- **Bug**: `dispatch_tool()` had schema mismatch — inserted into wrong columns
- **Fix**: Updated INSERT to match actual table schema (status, speed_ms, args, created_at)
- **Table**: `tool_call_log` in cerebrum_memory.db

## Hermes Source Structure (MacBook dev install)

```
~/hermes-agent/
├── cli.py                    # Main entry, HermesCLI class
├── run_agent.py              # AIAgent class, agent loop
├── agent/
│   ├── cortex_access.py      # DB connection helpers
│   ├── cortex_learning.py    # Learning engine
│   ├── context_compressor.py # Compression logic
│   └── ...
├── tools/
│   ├── registry.py           # Tool discovery (discover_builtin_tools)
│   ├── context_pressure_gauge.py
│   ├── self_diagnostic.py    # NEW
│   ├── skill_generator.py    # NEW
│   ├── plan_executor.py      # NEW
│   └── ...
└── hermes_cli/
    └── plugins.py            # dispatch_tool with tracking
```

## Verification Commands

```bash
# Discover all tool modules
cd ~/hermes-agent && venv/bin/python -c "
from tools.registry import discover_builtin_tools
mods = discover_builtin_tools()
print(f'Total: {len(mods)}')
"

# Test a specific tool
cd ~/hermes-agent && venv/bin/python -c "
from tools.self_diagnostic import run_self_diagnostic
print(run_self_diagnostic('all', 'human'))
"

# Check tool tracking
cd ~/hermes-agent && venv/bin/python -c "
from hermes_cli.plugins import dispatch_tool
# This now logs correctly to tool_call_log
"
```

## Redundant Standalone Scripts (to clean up)

These were built in ~/subconscious/ but are now superseded by Hermes core:
- `hermes_tool_logger.py` — REDUNDANT (hermes has tracking in plugins.py)
- `hermes_context_gauge.py` — REDUNDANT (enhanced tools/context_pressure_gauge.py)
- `hermes_self_diagnostic.py` — MOVED to tools/self_diagnostic.py
- `hermes_skill_generator.py` — MOVED to tools/skill_generator.py
- `hermes_plan_executor.py` — MOVED to tools/plan_executor.py
- `hermes_cli_resume.py` — PARTIALLY MOVED (logic in cli.py)
- `hermes_self_manager.py` — PARTIALLY MOVED (logic in run_agent.py)

## Key Lesson

**Standalone scripts in ~/subconscious/ are prototypes only. The user considers them unfinished work until they are surgically integrated into Hermes source code and the user is asked to restart.**
