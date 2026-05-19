# Audit Session: 2026-05-09 — Subconscious Integration Verification

## Context

After bulk-moving 97 cognitive modules from `~/subconscious/` to `~/hermes-agent/agent/` and `tools/`, user asked for complete audit to confirm everything is "wired and fully functional."

## Key Finding: Integration ≠ Wiring

**Files were in the right place but NOT connected to the agent loop.**

### What Was Integrated
- 97 modules moved to `agent/` (162 .py files) and `tools/` (84 .py files)
- All path references updated from `~/subconscious/` to `~/hermes-agent/`
- Old `hermes_cli/subconscious/` deleted
- Committed to git (be01b8d1c)

### What Was NOT Wired
- `subconscious_plugin_loader.py` looked in `~/hermes-agent/` (root) for `*.py` files, not in `agent/`
- It loaded wrong files (batch_runner.py, cli.py) or nothing
- Created empty `~/subconscious/tool_capability.db` as side effect
- No cognitive module registered with Hermes plugin hooks
- `iteration_engine.before_action()` / `after_action()` never called

## Detailed Findings by Layer

### 1. Iteration Engine — DISCONNECTED
- `agent/iteration_engine.py` exists (28,961 bytes)
- Instantiated in run_agent.py line 2128
- `before_action()` / `after_action()` NEVER called
- No experiential learning actually happening

### 2. Cognitive Systems — ALL ORPHANED
All 10 modules exist in `agent/` but NONE register hooks:
- `cognitive_infrastructure_hooks.py` — helper functions only
- `cortex_flywheel.py` — DB access only
- `brain_to_toolintel.py` — helper functions only
- `agent_scorecard.py` — DB access only
- `tool_misuse_prevention.py` — helper functions only
- `red_team_hippocampus.py` — helper functions only
- `memory_cortex_bridge.py` — helper functions only
- `hermes_enhancement_suite.py` — helper functions only

### 3. Autobrowse/Vision — NOT BUILT
- No `agent/autobrowse_engine.py`
- No `agent/vision_loop.py`
- No `agent/screen_capture.py`
- Playwright NOT installed
- cliclick and screencapture available but no custom pipeline

### 4. Databases — CORRUPTED/EMPTY
- `unified_context.db` — 94KB, 5 tables ✅ functional
- `cerebrum_memory.db` — 40KB, CORRUPTED (invalid SQLite)
- `tool_capability.db` — 49KB, 4 tables ✅ functional
- `skill_rewards.db` — 0 bytes, 0 tables ⚠️ empty
- `cortex.db` — 16KB, 1 table ✅ functional
- `distillation_buffer.db` — MISSING

### 5. Self-Evolution — MINIMAL
- `training_gym.py` exists but not wired
- No `elo_tournament.py`
- No `tip_evolution.py`
- No `auto_distillation.py`

## What WAS Working
- Skills: 83 ✅
- Tools: 84 built-in + 50 custom ✅
- Plugins: 40, all registered ✅
- Cron: 5 jobs ✅
- Knowledge: 1,154 files ✅
- Gateway/Telegram: via alternative paths ✅

## Root Cause

The integration focused on **file movement** (integration) without **hook wiring** (connection). The subconscious modules were designed as standalone scripts, not as Hermes plugins that register with the hook system. Moving them to `agent/` didn't automatically make them part of the agent loop.

## Fix Required

1. **Fix `subconscious_plugin_loader.py`** — change search path from root to `agent/`, remove auto-init
2. **Add hook registrations** to each cognitive module
3. **Wire `iteration_engine`** into run_agent.py's action lifecycle
4. **Rebuild corrupted databases**
5. **Build missing autobrowse/vision modules**

## Lesson Learned

**Always verify wiring after integration.** Use the maximal wiring checklist. Files present ≠ functional.
