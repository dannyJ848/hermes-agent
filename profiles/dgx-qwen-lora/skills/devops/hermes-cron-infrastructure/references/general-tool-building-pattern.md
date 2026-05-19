# General Tool Building Pattern (2026-05-09)

## Trigger
User asks: "what tools don't you have that would help you be more effective?" or similar open-ended capability expansion request.

## User Preference
Tools must be **general-purpose** (enhance overall agent functionality), not project-specific. User explicitly corrected: "they should not be project specific, but enhance your overall functionality."

## Pattern

### 1. Identify Gaps
Look for missing capabilities that would improve ALL future sessions:
- Tool-use logging/analysis (meta-cognition about tools)
- Context window monitoring (survival-critical)
- Multi-step execution with retry (autonomy)
- Self-diagnostic (proactive reliability)
- Skill auto-generation (growth)

### 2. Build 3-5 Tools
Create tools in `~/subconscious/` with consistent naming: `hermes_<purpose>.py`

Each tool should:
- Be importable as a module
- Have a `if __name__ == "__main__"` test block
- Use existing DBs (`~/.hermes/cerebrum_memory.db`, `~/.hermes/tool_intelligence.db`)
- Have graceful error handling (try/except with ImportError fallback)

### 3. Wire Into Existing Apparatus
**Critical: user gets angry when systems are built but not wired in.**

Wire into:
- **Unified daemon** (`hermes_unified_daemon.py`): add periodic checks, tool logging
- **Manual triggers** (`hermes_manual_triggers.py`): add trigger functions for on-demand use
- **Session-end hooks** (`cognitive_infrastructure_hooks.py`): auto-trigger on session close
- **Distillation plugin** (`~/.hermes/plugins/distillation/__init__.py`): add hooks if relevant

### 4. Verify With Self-Diagnostic
Run `hermes_self_diagnostic.py` to confirm:
- All new files detected
- All DB tables accessible
- All processes running
- Overall status: GREEN

### 5. Update Skill Library
Add the pattern to `hermes-cron-infrastructure` skill (or relevant umbrella) as a reference file.

## Example Tools Built (2026-05-09)

| Tool | Purpose | Wired Into |
|------|---------|-----------|
| `hermes_tool_logger.py` | Log all tool calls with metadata | Unified daemon, manual triggers |
| `hermes_context_gauge.py` | Monitor context window pressure | Unified daemon, manual triggers |
| `hermes_plan_executor.py` | Multi-step execution with retry | Manual triggers |
| `hermes_self_diagnostic.py` | Full system health check | Unified daemon, manual triggers |
| `hermes_skill_generator.py` | Auto-generate skills from sessions | Manual triggers, session-end hook |

## Verification Command
```bash
cd ~/subconscious && python3 hermes_manual_triggers.py self-diagnostic
```

Expected: Overall GREEN, all new files detected, all DBs accessible.
