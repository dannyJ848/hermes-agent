# Subconscious Integration — Complete (July 2026)

## Overview
All 97 cognitive modules from `~/subconscious/` have been fully migrated into `~/hermes-agent/agent/` (177 files) and `tools/` (106 files). The integration is surgically wired into Hermes source code — not standalone scripts.

## Architecture

### Filesystem Layout
```
~/hermes-agent/
├── agent/
│   ├── iteration_engine.py          # Core experiential learning loop
│   ├── cortex_flywheel.py            # Continuous learning flywheel
│   ├── agent_scorecard.py            # Self-evaluation scoring
│   ├── tool_misuse_prevention.py     # Tool guardrails
│   ├── red_team_hippocampus.py       # Adversarial testing
│   ├── memory_cortex_bridge.py       # Memory offloading
│   ├── hermes_enhancement_suite.py   # Agent enhancement
│   ├── auto_fallback_engine.py       # Fallback strategies
│   ├── proactive_memory_guard.py     # Memory pressure management
│   ├── tool_intelligence_tracker.py  # Tool usage analytics
│   ├── subconscious_hook_wiring.py   # Hook registration (legacy compat)
│   ├── subconscious_systems_manifest.py  # System manifest
│   ├── cognitive_systems_plugin.py   # Plugin registration helper
│   ├── cortex_compat.py            # Cortex compatibility
│   ├── cortex_unified.py             # Unified cortex DB
│   ├── distillation_bridge.py        # Research-to-tips pipeline
│   ├── distillation_quality_gate.py  # Quality validation
│   ├── error_pattern_miner.py        # Error pattern extraction
│   ├── episodic_memory.py            # Session memory
│   ├── self_critic.py               # Self-criticism engine
│   ├── testing_gym.py               # Tip evaluation gym
│   ├── vision_loop.py               # Screen capture + GUI automation
│   ├── vision_tools.py              # Vision tool wrappers
│   ├── self_evolution.py            # Elo tournaments + tip evolution
│   └── subconscious_plugin_loader.py # DEPRECATED — no-op
├── tools/
│   └── [106 cognitive tool files]
└── run_agent.py
    └── Lines 10053-10154: Iteration engine before_action/after_action hooks
```

### Hermes Plugin
```
~/.hermes/plugins/cognitive-systems/
├── __init__.py       # Plugin registration + hook handlers
└── plugin.yaml       # Manifest (name, version, hooks, tools)
```

**Hooks registered:**
- `pre_tool_call` — Context injection before tool execution
- `post_tool_call` — Logging after tool execution
- `pre_llm_call` — Context injection into user message (line 11601 run_agent.py)
- `post_llm_call` — Logging after LLM response (line 14870 run_agent.py)
- `on_session_start` — Session initialization (line 11459 run_agent.py)
- `on_session_end` — Session cleanup (line 14985 run_agent.py)

**Tools registered:**
- `screen_capture` — macOS screencapture + vision analysis
- `gui_click` — cliclick-based GUI clicking
- `gui_type` — cliclick-based text typing

### Databases
```
~/.hermes/
├── cerebrum_memory.db        # 10 tables — episodic/semantic memory
├── skill_rewards.db          # 3 tables — tool success tracking
└── distillation_buffer.db    # 4 tables — tip evolution + Elo scores
```

## Wiring Details

### Iteration Engine (run_agent.py)
```python
# Line 10053 — Before every tool call
if hasattr(self, "iteration_engine") and self.iteration_engine:
    _iteration_context = self.iteration_engine.before_action(
        action_type=function_name,
        detail=json.dumps(function_args, ensure_ascii=False)[:200],
    )

# Line 10143 — After every tool call
if hasattr(self, "iteration_engine") and self.iteration_engine:
    self.iteration_engine.after_action(
        action_type=function_name,
        detail=...,
        result="failure" if _is_error else "success",
        error=...,
        speed_ms=int((_tool_end - _tool_start_time) * 1000),
    )
```

### Plugin Context Injection (run_agent.py)
```python
# Line 11601 — Before every LLM call
_pre_results = _invoke_hook(
    "pre_llm_call",
    session_id=self.session_id,
    user_message=original_user_message,
    ...
)
# Results injected into user message at line 11874
```

## Self-Evolution Pipeline

### Components
1. **Distillation** — Extract tips from session experiences
2. **Elo Tournament** — Pairwise tip comparison with rating updates
3. **Tip Evolution** — Mutate/combine top tips to generate variants
4. **Reflection** — Post-session analysis with lesson extraction
5. **Hindsight** — Record task outcomes for future retrieval

### API
```python
from agent.self_evolution import SelfEvolutionPipeline
pipeline = SelfEvolutionPipeline()

# Full cycle
result = pipeline.run_cycle()  # {distilled, tournament_matches, evolved, top_tip}

# Individual operations
pipeline.distill_from_experiences(limit=50)
pipeline.run_elo_tournament(num_matches=20)
pipeline.evolve_tips(num_mutations=5)

# Hindsight
pipeline.record_hindsight(task_id, description, approach, result, ...)
pipeline.get_hindsight_for_task("task description")
```

## Known Gaps

| Hook | Registered | Invoked by run_agent.py | Coverage |
|------|-----------|------------------------|----------|
| pre_llm_call | ✅ | ✅ Line 11601 | Full |
| post_llm_call | ✅ | ✅ Line 14870 | Full |
| on_session_start | ✅ | ✅ Line 11459 | Full |
| on_session_end | ✅ | ✅ Line 14985 | Full |
| pre_tool_call | ✅ | ❌ | Iteration engine covers |
| post_tool_call | ✅ | ❌ | Iteration engine covers |

## Cleanup Status

| Item | Status |
|------|--------|
| Source files cleaned | ✅ |
| hermes_cli/plugins.py dead code removed | ✅ |
| run_agent.py old init removed | ✅ |
| Self-imports fixed (agent. prefix) | ✅ |
| ~/subconscious/ directory | ⏳ Clears on restart |
| Git commit | 0390d936d (132 files) |

## Restart Instructions

```bash
# 1. Restart hermes to load cognitive-systems plugin
hermes restart

# 2. Verify plugin loaded
hermes plugins list
# Expected: cognitive-systems v2.0.0 enabled

# 3. Verify hooks active
hermes hooks list

# 4. Verify databases
ls -la ~/.hermes/*.db

# 5. Verify ~/subconscious/ gone
ls ~/subconscious  # Should be "No such file or directory"
```

## Key Files for New CLI

| Purpose | Path |
|---------|------|
| Checkpoint | `~/.hermes/workspace/checkpoints/subconscious-integration-complete-july2026.json` |
| Knowledge (this file) | `~/.hermes/knowledge/subconscious-integration-complete.md` |
| Plugin | `~/.hermes/plugins/cognitive-systems/__init__.py` |
| Iteration Engine | `~/hermes-agent/agent/iteration_engine.py` |
| Self-Evolution | `~/hermes-agent/agent/self_evolution.py` |
| Vision System | `~/hermes-agent/agent/vision_loop.py` |
| run_agent.py hooks | Lines 10053-10154, 11601, 14870 |

## Date
Completed: July 2026 (originally May 9, 2026, refined through July)
