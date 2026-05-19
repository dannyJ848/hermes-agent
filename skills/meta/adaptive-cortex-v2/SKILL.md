---
name: adaptive-cortex-v2
title: Adaptive Cortex v2 — Real-Time Self-Improvement System
description: |
  Complete real-time personalized learning system that makes the agent iteratively
  better with every tool call. Combines Classic Cortex (Elo tips), Adaptive Cortex
  (error patterns), and Tool Oracle (predictive selection).
triggers:
  - When building self-improvement systems
  - When integrating learning into tool calls
  - When designing agent memory/evaluation systems
  - When the user wants the agent to get smarter over time
---

# Adaptive Cortex v2

## Quick Start

```python
from cortex_unified import UnifiedCortex
uc = UnifiedCortex()

# Before tool call — get warnings + suggestions
guidance = uc.before_tool("terminal", {"command": "rm -rf /"})
# Returns: {'warnings': [...], 'suggestions': {...}, 'predicted_success': 0.0}

# After tool call — immediate learning
uc.after_tool("terminal", {...}, result, error)

# Build context injection for LLM
injection = uc.build_context_injection("I need to find a file")
```

## Architecture

Three subsystems unified into one:

1. **Classic Cortex** — Elo-rated tips, flywheel evaluation
2. **Adaptive Cortex** — Real-time error pattern detection
3. **Tool Oracle** — Predictive tool selection

## Files

All in `~/subconscious/`:
- `cortex_access.py` — Database access
- `cortex_flywheel.py` — Elo tournaments
- `adaptive_cortex.py` — Real-time learning
- `tool_oracle.py` — Tool prediction
- `cortex_unified.py` — Single integration point
- `cortex_dashboard.py` — Status dashboard

## Database

Postgres at `postgresql://hindsight:***@localhost:5432/hindsight`

Key tables:
- `cortex_nodes` — Tips and facts
- `my_error_patterns` — Personal mistake patterns
- `my_skills` — Per-tool proficiency
- `learning_events` — Real-time learning log

## Cron Jobs

| Job | Schedule |
|-----|----------|
| cortex-flywheel | Every 2h |
| cortex-consolidation | Every 6h |
| adaptive-cortex-daemon | Every 30m |

## Plugin Integration

Already wired into `~/.hermes/plugins/distillation/__init__.py`:
- `_on_pre_tool_call()` → `uc.before_tool()`
- `_on_post_tool_call()` → `uc.after_tool()`
- `_on_pre_llm_call()` → `uc.build_injection()`

## Key Features

- **Real-time learning**: Every error → immediate lesson
- **Personalized warnings**: "You often forget X"
- **Tool prediction**: Task → optimal tool suggestion
- **Skill tracking**: Per-tool success rates + trends
- **Context injection**: Recent lessons injected into LLM context

## Dashboard

```bash
cd ~/subconscious && python3 cortex_dashboard.py
```

## Tips

- The system learns from EVERY tool call, success or failure
- Warnings appear before I repeat known mistakes
- The more I use a tool, the better the predictions get
- Cron jobs keep the system healthy automatically
- The database already has 66K+ nodes from previous usage