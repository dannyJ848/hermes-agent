---
name: agent-self-management-tooling
version: 1.0.0
description: Build general-purpose self-management tools for AI agents — tool logging, context pressure monitoring, plan execution with retry, self-diagnostic, skill auto-generation, and full handoff orchestration for context window survival.
created: 2026-05-09
category: meta
trigger: When building tools to enhance agent autonomy, monitoring agent health, managing context windows, or creating self-improvement infrastructure. Also when the user says "build tools that make you more effective" or "what tools don't you have".
---

# Agent Self-Management Tooling

## Overview

Build general-purpose tools that enhance the agent's own effectiveness — not project-specific tools, but infrastructure that improves ALL future work. These tools form the agent's "nervous system": sensing, logging, planning, diagnosing, and self-healing.

## The Five Core Tools

### 1. Tool-Use Logger (`hermes_tool_logger.py`)

**Purpose**: Log every tool call with full metadata for pattern analysis.

**Key functions**:
- `log_tool_call(tool_name, args, result, success, error, duration_ms, context)` — universal logging
- `analyze_tool_patterns(query, tool_name, time_window_hours)` — find what works
- `get_tool_recommendation(task_description)` — suggest tools based on history

**Wiring**: Import in unified daemon to log daemon cycles. Import in manual triggers for on-demand analysis.

**Table**: `tool_calls_v2` in `tool_intelligence.db` with indexes on tool_name, timestamp, success.

### 2. Context Window Gauge (`hermes_context_gauge.py`)

**Purpose**: Monitor context usage, predict compression timing, trigger handoffs.

**Key functions**:
- `check_context_pressure()` — returns GREEN/YELLOW/RED status with action recommendation
- `suggest_handoff(reason)` — auto-saves handoff file when pressure >80%
- `predict_compression_time()` — estimates hours until context full
- `log_context_event(event, details)` — compression tracking

**Wiring**: Called by unified daemon every hour. Called by manual trigger `context-pressure`. Integrates with `hermes_cli_resume.py` for handoff save.

**Critical pitfall**: `HERMES_CONTEXT_CHARS` env var may not be set — falls back to 0%. Use heuristics or manual tracking.

### 3. Plan Executor (`hermes_plan_executor.py`)

**Purpose**: Multi-step plan execution with retry, fallback, and adaptation.

**Key classes**:
- `Step(tool, args, retries, fallback_tool, condition, timeout_seconds)` — plan step
- `StepResult(step, success, result, error, duration_ms, attempt, adapted)` — execution result
- `PlanResult(success, steps_completed, total_steps, step_results, context, adaptations)` — full result

**Key function**:
- `execute_plan(steps, context, continue_on_error)` — runs plan with full retry logic
- Template resolution: `{step0.result.url}` references previous step results
- Fallback tool execution when primary fails

**Wiring**: Add to manual triggers for complex on-demand workflows. Integrate with tool logger for execution tracking.

### 4. Self-Diagnostic (`hermes_self_diagnostic.py`)

**Purpose**: Comprehensive system health check — test all tools, providers, DBs, files.

**Key functions**:
- `quick_health_check()` — 5-second critical component check
- `run_full_diagnostic()` — 30-second full system scan
- `format_report(results)` — human-readable report
- `save_report(results, path)` — JSON + text output

**Checks**:
- Databases: cerebrum_memory, tool_intelligence, cortex
- Files: all hermes_*.py tools, distillation plugin
- Processes: unified daemon running
- Directories: knowledge, skills, workspace
- Stats: tip counts, learning counts

**Wiring**: Called by unified daemon every 30 minutes. Called by manual trigger `self-diagnostic`.

### 5. Skill Auto-Generator (`hermes_skill_generator.py`)

**Purpose**: Generate SKILL.md drafts from session learnings or topics.

**Key functions**:
- `generate_skill_from_session(hours_back, min_confidence)` — analyze recent learnings
- `generate_skill_from_topic(topic, source_files, description)` — topic-based generation
- `list_auto_skills()` — list all auto-generated skills

**Wiring**: Called by manual trigger `skill-generate`. Auto-triggered at session end.

## The Self-Manager (`hermes_self_manager.py`)

**Purpose**: Full orchestration of context window death and seamless resume.

**The loop**:
1. `detect_compression_count()` — count compressions in session
2. `full_checkpoint(label)` — comprehensive checkpoint with all state
3. `distill_all_context(checkpoint_file)` — save to knowledge, rapid learnings, handoff
4. `generate_resume_script(checkpoint_label)` — shell script for new CLI
5. `trigger_new_cli()` — instructions for terminal/gateway restart

**Usage**:
```bash
# Background watchdog (detects 5th compression, auto-handoffs):
python3 ~/subconscious/hermes_self_manager.py --watchdog

# Immediate handoff:
python3 ~/subconscious/hermes_self_manager.py --handoff

# Check status:
python3 ~/subconscious/hermes_self_manager.py --status
```

**Integration with CLI Resume** (`hermes_cli_resume.py`):
- Self-manager saves handoff via `save_handoff()`
- New CLI runs `auto_resume()` on startup
- Detects pending handoff, prints summary
- User says "resume from checkpoint <label>"

## Wiring Rules (Critical)

Every new tool MUST be wired into existing apparatus within 3 tool calls. But wiring into standalone scripts in `~/subconscious/` is NOT enough. The user gets angry when systems are built but not integrated into the agent loop: "What's the point of building anything if you're not wiring it in?"

### The Two Levels of Integration

**Level 1 — Standalone Scripts (Insufficient alone)**
- Build in `~/subconscious/` as prototype
- Wire into unified daemon, manual triggers, session hooks
- This is the testing ground ONLY — not the destination

**Level 2 — Hermes Core Integration (Required)**
- Find the Hermes source code: `~/hermes-agent/` (development) or the pip install location
- Patch the actual Hermes Python modules directly
- Add imports, hook calls, or middleware in the core agent loop
- Register tools via `registry.register()` in `tools/<name>.py`
- Ask user to restart Hermes to activate
- **This is what the user expects. Standalone scripts alone are considered unfinished work.**

**The user's exact words: "you didn't build it INTO the hermes source code like I thought you were doing... holy fuck this is disappointing."**

**The rule: After building standalone scripts, the NEXT step is ALWAYS surgical integration into Hermes source. Never declare done until core integration is complete.**

### How to Patch Hermes Core — Surgical Integration Steps

**Step 1: Find Hermes source**
```bash
# Development install (most common):
ls ~/hermes-agent/

# Or pip install location:
pip3 show hermes-agent | grep Location
```

**Step 2: Identify integration points**
- `cli.py` — startup, session init, resume handling
- `run_agent.py` — agent loop, compression, tool dispatch
- `tools/registry.py` — tool discovery and registration
- `tools/*.py` — existing tools to enhance or replace
- `agent/*.py` — core agent modules (context compressor, learning, etc.)

**Step 3: Surgical patches (examples from this session)**

*Auto-handoff at compression:*
```python
# In run_agent.py, _compress_context() after compression_count warning:
if _cc >= 5:
    self._trigger_compression_handoff(_cc, messages, new_system_prompt)
```

*Auto-resume on startup:*
```python
# In cli.py, HermesCLI.__init__ before session ID assignment:
_auto_resume = self._check_pending_handoff(resume)
if _auto_resume:
    resume = _auto_resume
```

*Tool registration:*
```python
# In tools/<your_tool>.py, at module level:
from tools.registry import registry
registry.register(
    name="your_tool",
    toolset="meta",
    schema=YOUR_SCHEMA,
    handler=lambda args, **kw: your_handler(args),
    check_fn=check_requirements,
    emoji="🔧",
)
```

*Enhance existing tool:*
```python
# In tools/context_pressure_gauge.py — add methods to existing class:
def log_compression(self):
    self.compression_count += 1
    # ... log to file

def check_handoff_threshold(self, threshold=5):
    return self.get_compression_count() >= threshold
```

**Step 4: Verify discovery**
```bash
cd ~/hermes-agent && venv/bin/python -c "
from tools.registry import discover_builtin_tools
mods = discover_builtin_tools()
print(f'Discovered: {len(mods)} modules')
for m in sorted(mods):
    print(f'  {m}')
"
```

**Step 5: Test the tool**
```bash
cd ~/hermes-agent && venv/bin/python -c "
from tools.your_tool import your_function
result = your_function()
print(result)
"
```

**Step 6: Ask for restart**
"I've patched Hermes core at `<paths>`. Please restart Hermes to activate."

### Critical Integration Checklist

- [ ] Patched `run_agent.py` for loop-level hooks (compression, handoff)
- [ ] Patched `cli.py` for startup behavior (auto-resume, handoff detection)
- [ ] Patched `tools/*.py` for new or enhanced tools
- [ ] Patched `agent/*.py` for core module enhancements
- [ ] Fixed any schema mismatches in existing code (e.g., tool tracking)
- [ ] Verified tool discovery shows new modules
- [ ] Verified tools execute without errors
- [ ] Asked user to restart Hermes
- [ ] **Deleted or archived redundant standalone scripts from `~/subconscious/` after integration**

### Wiring Checklist

1. **Unified daemon**: Add health check / monitor function
2. **Manual triggers**: Add trigger function to `TRIGGERS` dict
3. **Session-end hook**: Auto-trigger if relevant
4. **Hermes core patch**: Add to actual agent source code
5. **Restart request**: Ask user to restart

**Verification**: After restart, run `self-diagnostic` and confirm new tool appears in FILES section AND is called from core.

## Pitfalls

- **Orphan tools**: Building in `~/subconscious/` without integrating into Hermes core makes the user angry. "What's the point of building anything if you're not wiring it in?" and "you didn't build it INTO the hermes source code like I thought you were doing... holy fuck this is disappointing."
- **Standalone-only trap**: Building in `~/subconscious/` and declaring done. The user expects core integration. ALWAYS follow standalone build with surgical Hermes source patches.
- **WAL mode silent failure**: SQLite WAL causes inserts to appear successful but `SELECT` returns 0. Use `PRAGMA wal_checkpoint(TRUNCATE)` to verify.
- **Import errors in daemon**: Daemon runs in isolated context. Wrap all imports in `try/except ImportError`.
- **Context gauge 0%**: If `HERMES_CONTEXT_CHARS` env var missing, gauge shows 0%. This is expected — add manual tracking or use heuristics.
- **Self-manager can't spawn terminal**: macOS security prevents Python from opening new Terminal windows. Generate script + instructions instead.
- **Duplicate daemon instances**: Always `pgrep -f` before starting. Kill old instances.
- **Schema mismatch in existing code**: The hermes tool tracking had a broken INSERT (wrong column names). Always verify table schema with `.schema <table>` before writing INSERTs.

## Verification

- [ ] All 5 tools exist in `~/subconscious/`
- [ ] Self-diagnostic shows all tools in FILES section
- [ ] Manual triggers include all 5 tools
- [ ] Unified daemon calls tool logger, self-diagnostic, context gauge
- [ ] Session-end hook triggers skill generation
- [ ] Self-manager can execute `--handoff` successfully
- [ ] CLI resume detects handoff and prints summary

## References

- `references/hermes-core-integration-surgery-2026-05-09.md` — **COMPLETE SESSION RECORD**: Actual file paths, patches, and verification commands from integrating 7 components into Hermes source code. Use this as the canonical reference for surgical integration.
- `references/tool-logger-schema.md` — Database schema and query patterns
- `references/context-gauge-handoff-flow.md` — Compression detection to resume flow
- `references/plan-executor-template-syntax.md` — Step template resolution syntax
- `references/self-diagnostic-checks.md` — Full list of diagnostic checks
- `references/skill-generator-prompt-patterns.md` — SKILL.md generation patterns
- `scripts/test-all-tools.py` — Verification script for all 5 tools
