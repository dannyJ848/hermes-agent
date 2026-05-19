---
title: Autobrowse Self-Improvement System
version: 1.0
category: meta
---

# Autobrowse Self-Improvement System

Proactive self-improvement by analyzing execution traces to detect inefficiency patterns and generate actionable tips.

## Architecture

4 modules in `~/subconscious/`:

| Module | File | Purpose |
|--------|------|---------|
| Tracer | `autobrowse_tracer.py` | Captures tool calls with metadata |
| Analyzer | `autobrowse_analyzer.py` | Detects waste patterns |
| Synthesizer | `autobrowse_synthesizer.py` | Generates tips + maintains strategy.md |
| Graduator | `autobrowse_graduator.py` | Promotes tips through lifecycle |

## Wiring

Integrated into `distillation` plugin as **R191**:

- **post_tool_call**: Records every tool execution → triggers analysis every 20 calls
- **pre_llm_call**: Injects hints from trace stats, patterns, strategy.md, and promotion status

## Pattern Detection

Analyzer detects 5 pattern types:

1. **redundant_loop** — Same tool called ≥3x with similar input
2. **suboptimal_model** — Expensive model used for simple tool
3. **token_waste** — Oversized outputs for small inputs
4. **failure_cluster** — Same error type repeating
5. **tool_mismatch** — Wrong tool chosen when better alternative exists

## Tip Lifecycle

| Stage | Threshold | Action |
|-------|-----------|--------|
| activate | 5 apps, Elo ≥1100 | Enable in CortexDB |
| module | 10 apps, Elo ≥1200 | Add to `autobrowse_generated.py` |
| skill | 20 apps, Elo ≥1300 | Graduate to `autobrowse_skills.md` |

## Files

- `~/subconscious/autobrowse_tracer.py` — Trace capture
- `~/subconscious/autobrowse_analyzer.py` — Pattern detection
- `~/subconscious/autobrowse_synthesizer.py` — Tip generation
- `~/subconscious/autobrowse_graduator.py` — Promotion tracking
- `~/subconscious/strategy.md` — Running scratchpad
- `~/subconscious/autobrowse_generated.py` — Promoted modules
- `~/subconscious/autobrowse_skills.md` — Graduated skills

## Usage

Modules auto-load on Hermes startup via distillation plugin. No manual action needed.

To check status:
```python
from autobrowse_tracer import get_instance as gt
from autobrowse_analyzer import get_instance as ga
from autobrowse_synthesizer import get_instance as gs
from autobrowse_graduator import get_instance as gg

print(gt().get_stats())
print(ga().get_top_patterns(3))
print(gg().get_lifecycle_report())
```
