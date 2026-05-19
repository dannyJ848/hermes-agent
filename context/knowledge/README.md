# Adaptive Cortex v2 — Complete System Documentation

## Overview

A real-time, personalized self-improvement system that makes me iteratively better with every tool call. Combines three subsystems:

1. **Classic Cortex** — Elo-rated tips, flywheel evaluation, consolidation
2. **Adaptive Cortex** — Real-time error pattern detection, immediate learning
3. **Tool Oracle** — Predictive tool selection, argument validation

## Architecture

```
Every Tool Call:
  ├─ BEFORE: UnifiedCortex.before_tool()
  │   ├─ Adaptive: Check for known error patterns
  │   ├─ Oracle: Validate tool choice + suggest args
  │   └─ Return: Warnings + suggestions + predicted success rate
  │
  ├─ DURING: Tool executes
  │
  └─ AFTER: UnifiedCortex.after_tool()
      ├─ Adaptive: Learn immediately from outcome
      ├─ Oracle: Record prediction accuracy
      └─ Classic: Store new tip in Cortex

Every LLM Call:
  └─ UnifiedCortex.build_context_injection()
      ├─ Recent lessons from this session
      ├─ My skill status
      ├─ Tool prediction for current task
      └─ High-Elo tips from Classic Cortex
```

## Files

### Core Modules (`~/subconscious/`)

| File | Purpose | Lines |
|------|---------|-------|
| `cortex_schema.sql` | Postgres schema (nodes, edges, evals, flywheel) | 200+ |
| `cortex_access.py` | Unified DB access (CortexDB class) | 600+ |
| `cortex_flywheel.py` | Elo tournaments, repair, consolidation | 350+ |
| `llm_judge.py` | LLM-based tip evaluation | 200+ |
| `tip_normalizer.py` | WHEN/THEN format normalization | 150+ |
| `research_to_tips.py` | Extract tips from documents | 250+ |
| `migrate_to_cortex.py` | Data migration from old systems | 200+ |
| `cortex_compat.py` | Plugin compatibility shim | 100+ |
| `adaptive_cortex.py` | Real-time learning engine | 400+ |
| `tool_oracle.py` | Predictive tool selection | 350+ |
| `cortex_unified.py` | Single integration point | 250+ |
| `cortex_daemon.py` | 24/7 autonomous daemon | 300+ |
| `cortex_dashboard.py` | Status dashboard | 150+ |

### Plugin Integration

Modified: `~/.hermes/plugins/distillation/__init__.py`
- Added `_get_unified_cortex()` singleton
- Hooked `before_tool()` into `_on_pre_tool_call()`
- Hooked `after_tool()` into `_on_post_tool_call()`
- Hooked `build_injection()` into `_on_pre_llm_call()`

## Database Schema

### Core Tables
- `cortex_nodes` — Tips, facts, strategies (66,309 total, 2,405 active)
- `cortex_edges` — Relationships between nodes
- `cortex_eval_history` — Elo tournament records
- `cortex_flywheel` — Cycle tracking

### Adaptive Tables
- `my_error_patterns` — My specific recurring mistakes
- `my_skills` — Per-tool proficiency tracking
- `learning_events` — Real-time learning log
- `tool_predictions` — Tool selection accuracy

## Cron Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| `cortex-flywheel` | Every 2h | Elo tournaments + tip repair |
| `cortex-consolidation` | Every 6h | Merge duplicate tips |
| `cortex-quality-sweep` | Daily 9am | Health report |
| `adaptive-cortex-daemon` | Every 30m | Skill monitoring |

## Current State (Apr 25 2026)

- **Total nodes**: 66,309
- **Active tips**: 2,405
- **Average Elo**: 1,337
- **Excellent tips**: 457 (Elo ≥ 1300)
- **Domains**: general (2,181), reasoning (54), planning (39), coding (33)

## Key Features

### Real-Time Learning
- Every error → Immediate lesson extraction
- Every success → Skill model update
- Zero delay between mistake and learning

### Personalized Warnings
- "You often forget timeout with dangerous commands"
- "Consider search_files instead of terminal for this task"
- "You had this exact error 3 times before"

### Predictive Tool Selection
- Task description → Predicted optimal tool
- Confidence scoring
- Alternative suggestions
- Argument recommendations

### Skill Progression Tracking
- Per-tool success rates
- Improvement trends
- Problem area identification
- Mastery milestones

## Usage

### For Plugin (Automatic)
```python
# Already integrated into distillation plugin
# Runs on every tool call automatically
```

### For Manual Check
```python
from cortex_unified import UnifiedCortex
uc = UnifiedCortex()

# Before tool call
guidance = uc.before_tool("terminal", {"command": "rm -rf /"})
print(guidance['warnings'])  # ['Dangerous pattern detected: rm -rf /']

# After tool call
uc.after_tool("terminal", {...}, result, error)

# Build context injection
injection = uc.build_context_injection("I need to find a file")
```

### Dashboard
```bash
cd ~/subconscious && python3 cortex_dashboard.py
```

## Future Enhancements

1. **Cross-Domain Transfer**: Mistake in terminal → Prevention in execute_code
2. **Meta-Learning**: Learn HOW I learn best
3. **Collaborative Learning**: Share patterns across sessions
4. **Predictive Interruption**: Stop me BEFORE I make mistake
5. **Auto-Skill Acquisition**: Learn new tools without explicit training

## Design Document

Full architecture: `~/subconscious/ADAPTIVE_CORTEX_DESIGN.md`
