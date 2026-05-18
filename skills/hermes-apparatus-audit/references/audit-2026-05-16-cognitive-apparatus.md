# Cognitive Apparatus Audit — 2026-05-16

Session audit of Hermes Agent learning apparatus. Run after user asked "audit your learning apparatus and ensure its all wired in properly."

## Overall Score: 62.8/100

| Layer | Score | Status |
|-------|-------|--------|
| Cerebrum Knowledge Base | 95 | ✅ 1,282 tips, canonical schema |
| Cognitive Orchestrator | 90 | ✅ Wired in run_agent.py |
| Hook Wiring | 85 | ⚠️ Missing post_tool_call |
| DGX Infrastructure | 75 | ⚠️ vLLM down, daemon running |
| Skills Ecosystem | 70 | ⚠️ 5 key meta skills missing |
| Cron Infrastructure | 60 | ⚠️ All jobs stale since April 22 |
| Plugin Activation | 50 | ⚠️ Most plugins dormant |
| Memory Persistence | 40 | ❌ MEMORY.md + memory/ missing |
| vLLM Inference | 0 | ❌ Server not responding |

## Key Findings

### Cerebrum (HEALTHY)
- `distilled_tips`: 1,282 tips, 0.86 avg confidence
- Schema: canonical 15 columns verified
- Backup present: `cerebrum_memory.db.corrupt_backup` (9.3MB)
- 22 tables, 2,950 total rows

### Hook Wiring (PARTIAL)
- `invoke_hook`: 21 occurrences
- `pre_llm_call`: 5, `post_llm_call`: 3
- `pre_tool_call`: 9, `post_tool_call`: **0 (MISSING)**
- `before_action`: 3, `after_action`: 3
- `cognitive_orchestrator`: 25 occurrences — wired

**Impact:** Tool outcomes are intercepted (pre_tool_call) but never learned from (no post_tool_call). This is an asymmetric hook pair that breaks the learning loop for tool execution.

### Databases (MIXED)
- 73 total databases
- 48 healthy (rows > 0)
- 17 empty (0 rows, schema only)
- 1 corrupted: `state.db` ("file is not a database")
- Largest: `lcm.db` 252MB, 419K rows
- Notable: `code_intelligence.db` 133MB, 119K rows

### Skills (INCOMPLETE)
- 88 skills installed
- **Missing critical meta skills:**
  - `training-gym-continuous` — continuous self-improvement gym
  - `cerebrum-memory` — 4-tier biomimetic memory system
  - `agent-self-audit` — self-audit methodology
  - `hermes-dojo` — performance review + skill patching
  - `adaptive-cortex-v2` — real-time personalized learning

### Cron (STALE)
- 3 active jobs, all last ran April 22, 2026 (3+ weeks stale)
- `daily-intelligence-scan`: 7am daily, delivery local
- `X AI News Scanner`: 9am/3pm/9pm, delivery local
- `Cortex Dojo`: 3am daily, delivery telegram (fails — not configured)

### Memory Files (MISSING)
- `~/.hermes/memory/` — directory did not exist (created during audit)
- `~/.hermes/MEMORY.md` — file does not exist
- No daily logs, no long-term curated memory

### External Directories
- `~/subconscious/` — still exists with 2 DB files (skill_rewards.db, tool_capability.db)
- `~/atropos/`, `~/training_gym/`, `~/cortex/`, `~/hindsight/` — removed ✅

### DGX Status
- Hermes gateway: running (PID 98690)
- Distillation daemon: running (PID 2152)
- Hermes fixed runner: running (PID 206580)
- vLLM: **NOT RUNNING** — GPU idle (0% util, 46°C)
- Port 8000: no response

## Actions Taken During Session
1. Created `~/.hermes/memory/` directory

## Recommended Actions (Priority)
- **P0:** Create `~/.hermes/MEMORY.md`
- **P1:** Restart vLLM on DGX
- **P1:** Fix cron scheduler (stale since April 22)
- **P1:** Enable dormant plugins (disk-cleanup, observability, kanban)
- **P2:** Install missing meta skills
- **P2:** Add `post_tool_call` hook to `run_agent.py`
- **P2:** Clean 17 empty databases
- **P2:** Remove corrupted `state.db`
- **P2:** Integrate/remove `~/subconscious/`
- **P3:** Fix Cortex Dojo delivery (telegram → local)
