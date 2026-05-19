---
name: adaptive-cortex-v2-complete
title: Adaptive Cortex v2 Complete — 6-Subsystem Self-Improvement
description: |
  Full real-time self-improvement system with 6 integrated subsystems:
  Classic Cortex, Adaptive Cortex, Tool Oracle, Reasoning Analyzer,
  Sequence Learner, and Anomaly Detector. All wired into the
  distillation plugin for automatic operation on every tool call.
triggers:
  - When building agent self-improvement systems
  - When designing real-time learning pipelines
  - When integrating cognitive architectures
  - When the user wants maximum agent capability
---

# Adaptive Cortex v2 Complete

## Architecture (6 Subsystems)

```
Every Tool Call:
  ├─ BEFORE: UnifiedCortex.before_tool()
  │   ├─ Adaptive Cortex    → Check known error patterns
  │   ├─ Tool Oracle        → Validate tool choice + suggest args
  │   ├─ Sequence Learner   → Suggest next tool in chain
  │   ├─ Anomaly Detector   → Detect unusual behavior
  │   └─ Risk Scorer        → Calculate overall risk
  │
  ├─ DURING: Tool executes
  │
  └─ AFTER: UnifiedCortex.after_tool()
      ├─ Adaptive Cortex    → Learn immediately from outcome
      ├─ Sequence Learner   → Record in chain
      ├─ Reasoning Analyzer → Score reasoning quality
      └─ Classic Cortex     → Store new tip

Every LLM Call:
  └─ UnifiedCortex.build_context_injection()
      ├─ Recent lessons
      ├─ Skill status
      ├─ Tool predictions
      ├─ Reasoning analysis
      └─ Session stats
```

## Files (`~/subconscious/`)

| File | Subsystem | Purpose |
|------|-----------|---------|
| `cortex_access.py` | Core | Database access |
| `cortex_flywheel.py` | Classic | Elo tournaments |
| `adaptive_cortex.py` | Adaptive | Real-time learning |
| `tool_oracle.py` | Oracle | Predictive selection |
| `reasoning_analyzer.py` | Reasoning | Quality scoring |
| `sequence_learner.py` | Sequence | Chain optimization |
| `anomaly_detector.py` | Anomaly | Risk prediction |
| `cortex_unified.py` | Integration | Single API |
| `cortex_dashboard_v2.py` | UI | Status dashboard |

## Database (Postgres)

Key tables:
- `cortex_nodes` — 66K tips, Elo-rated
- `my_skills` — 57 skills mined from history
- `my_error_patterns` — Personal mistake patterns
- `tool_sequences` — Chain optimization data
- `learning_events` — Real-time learning log

## Plugin Integration

Wired into `~/.hermes/plugins/distillation/__init__.py`:
- `_on_pre_tool_call()` → `uc.before_tool()`
- `_on_post_tool_call()` → `uc.after_tool()`
- `_on_pre_llm_call()` → `uc.build_injection()`

## Cron Jobs

| Job | Schedule |
|-----|----------|
| cortex-flywheel | Every 2h |
| cortex-consolidation | Every 6h |
| adaptive-cortex-daemon | Every 30m |
| cortex-quality-sweep | Daily 9am |

## Usage

```python
from cortex_unified import UnifiedCortex
uc = UnifiedCortex()

# Before tool call
guidance = uc.before_tool("terminal", {"command": "rm -rf /"})
print(guidance['risk_score'])      # 0.3
print(guidance['warnings'])        # ['Dangerous pattern...']
print(guidance['sequence_suggestion'])  # {'tool': 'search_files'}

# After tool call
uc.after_tool("terminal", {...}, result, error, reasoning)

# Build injection
injection = uc.build_context_injection("I need to find a file")
```

## Dashboard

```bash
cd ~/subconscious && python3 cortex_dashboard_v2.py
```

## Key Features

1. **Real-time learning** — Every error → immediate lesson
2. **Predictive warnings** — Before I repeat known mistakes
3. **Tool prediction** — Task → optimal tool + args
4. **Reasoning scoring** — Quality analysis of my thinking
5. **Chain optimization** — "After X, try Y" suggestions
6. **Anomaly detection** — "This is unusual for you" alerts
7. **Risk scoring** — 0-100% risk per action
8. **Session tracking** — Stats across all 6 dimensions

## Data Mined

- 57 tools with usage history
- Success rates per tool
- Common error patterns
- Transition probabilities
- 66K existing tips from previous usage