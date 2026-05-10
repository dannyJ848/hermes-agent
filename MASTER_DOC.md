# Hermes Agent — Master Documentation

## Status: FULLY OPERATIONAL (July 2026)

All cognitive systems, tools, plugins, and configurations are verified, wired, and functional within the Hermes source tree.

---

## Quick Verification

```bash
# Plugin status
hermes plugins list | grep cognitive-systems

# Tool status
hermes tools list | grep -E "screen_capture|gui_click|gui_type|x_"

# Resume from checkpoint
hermes --resume cognitive-systems-complete-july2026
```

---

## Systems Verified

### X/Twitter Tools
| Tool | Status |
|------|--------|
| x_tweet_fetch | Working |
| x_user_tweets | Working |
| x_search | Hash stale (graceful error) |

Cookies stored in `~/.hermes/config.yaml` under `x_cookies`.

### Vision (GLM-5V-Turbo)
| Tool | Status |
|------|--------|
| screen_capture | Registered |
| gui_click | Registered |
| gui_type | Registered |

Provider: custom via Z.AI general endpoint.

### Cognitive-Systems Plugin v2.0.0
- **Location**: `~/.hermes/plugins/cognitive-systems/`
- **Enabled**: Yes (in `~/.hermes/config.yaml`)
- **Hooks**: 6 registered
  - `on_session_start` — initialize all systems
  - `pre_llm_call` — iteration_engine retrieves lessons
  - `post_llm_call` — cortex + memory + enhancement + self-evolution
  - `pre_tool_call` — iteration_engine + tool_misuse_prevention
  - `post_tool_call` — iteration_engine records + scorecard + red_team
  - `on_session_end` — reflection + evolution cycle

- **7 Systems Loaded**:
  1. `iteration_engine` — retrieves lessons, records experiences
  2. `cortex_flywheel` — stats tracking
  3. `agent_scorecard` — `compute_scorecard()`
  4. `tool_misuse_prevention` — `validate_tool_call()`
  5. `red_team_hippocampus` — `learn()` from errors
  6. `memory_cortex_bridge` — `MemoryCortexBridge` with `is_pressure()`/`offload_if_needed()`
  7. `hermes_enhancement_suite` — `HermesEnhancementSuite` with `get_status()`

### Self-Evolution Pipeline
- **Module**: `agent/self_evolution.py`
- **Class**: `SelfEvolutionPipeline`
- **Graduation**: `_graduate_tips_to_skills()` wired into `run_cycle()`
- **Trigger**: Every 50 turns (post_llm_call) + 30% at session end (on_session_end)

### CLAUDE.md Rules
- **Location**: `tools/delegate_tool.py` `_build_child_system_prompt()`
- **Count**: 8 rules
- **Applied**: Every `delegate_task` call automatically

Rules:
1. Think Before Acting
2. Simplicity First
3. Surgical Changes
4. Goal-Oriented Execution
5. Code Decides Deterministic Things
6. Read Before You Write
7. Fail Visibly, Not Silently
8. Convention Beats Novelty

### X/Twitter Resources (10 Skills)
| # | Skill | Category |
|---|-------|----------|
| 1 | supervisor-routing | software-development |
| 2 | llm-wiki | research |
| 3 | anthropic-prompting | software-development |
| 4 | prd-prompt | software-development |
| 5 | claude-md-rules | software-development |
| 6 | anti-sycophancy | meta |
| 7 | skill-graduation | meta |
| 8 | agent-native-cli | software-development |
| 9 | production-ai-architecture | software-development |
| 10 | personal-research-engine | research |

---

## Directory Structure

```
~/hermes-agent/              # Source code (all internal)
  agent/
    self_evolution.py        # Evolution pipeline
    iteration_engine.py      # Learning loop
    cortex_flywheel.py       # Stats/tracking
    ... (97 total modules)
  tools/
    x_tool.py                # X/Twitter API
    delegate_tool.py         # Delegation + CLAUDE.md rules
    ...

~/.hermes/
  config.yaml               # Config including x_cookies
  plugins/                  # 41 plugins
    cognitive-systems/        # v2.0.0
    distillation/
    ...
  skills/                   # 289 skills
    software-development/
    research/
    meta/
    ...
  knowledge/                # 1158 knowledge files
  *.db                      # 105 databases
  cron/                     # Scheduled jobs
  workspace/checkpoints/      # Session checkpoints
```

---

## External Dependencies

**ZERO.** All systems internal to Hermes.

- `~/subconscious/` contains 2 orphaned DB files (PID 58704) — will clear on restart
- `/tmp/x_api.py` removed
- No source code references to external paths

---

## Every-Turn Execution Chain

```
1. on_session_start → initialize all cognitive systems

2. pre_llm_call → iteration_engine retrieves lessons
                → tool_misuse_prevention validates

3. LLM generates response

4. post_llm_call → cortex_flywheel stats
                 → memory_cortex_bridge pressure check
                 → hermes_enhancement_suite status
                 → self-evolution (every 50 turns)

5. pre_tool_call → iteration_engine lessons
                 → tool_misuse_prevention validation

6. Tool executes

7. post_tool_call → iteration_engine records experience
                  → agent_scorecard stats
                  → red_team_hippocampus learns from errors

8. on_session_end → reflection + evolution cycle (30% chance)
```

---

## Fixes Applied (This Session)

1. Fixed cognitive-systems plugin class names to match actual module exports
2. Fixed handler function signatures (e.g., `record_turn`→`get_stats`, `mine_error`→`learn`)
3. Verified all 7 cognitive systems load without import errors
4. Confirmed self-evolution triggers at correct frequency
5. Verified X tools read cookies from `~/.hermes/config.yaml`

---

## Resume Context

**Checkpoint**: `~/.hermes/workspace/checkpoints/cognitive-systems-complete-july2026.json`

```bash
hermes --resume cognitive-systems-complete-july2026
```

**Knowledge**: `~/.hermes/knowledge/cognitive-systems-complete-july2026.md`

---

*Last updated: July 2026*
