---
name: context-quality-guard
description: Prevent reasoning quality degradation in long-running autonomous sessions. Based on research showing all LLMs degrade continuously as context grows.
version: 1.0
created: 2026-04-05
---

# Context Quality Guard

## Problem
All LLMs experience continuous reasoning degradation as context fills. This is NOT a cliff — it starts at 35-50% of context window. By 60-70%, output quality is severely compromised (syntax errors, repeated text, malformed JSON, circular logic).

**Source:** Chroma tested 18 frontier models — ALL degraded. arXiv 2601.15300 defines "intelligence degradation" as >30% drop in composite task performance.

## Key Insight
The fix is NOT better compression. It is **SHORTER SESSIONS**. Fresh context = fresh reasoning. For autonomous cron loops, each cycle should be 3-5 tool calls maximum.

**Critical distinction:** LCM database bloat is a SEPARATE failure mode from context window fill. Even if in-memory context is small, a bloated LCM (30K+ messages in SQLite) causes "database is locked" errors that silently break the compressor. When the compressor can't run, context grows unbounded. See `lcm-database-bloat-recovery` skill for the substrate-layer fix.

## Degradation Zones (of context window)

| Zone | Fill % | Quality | Action |
|------|--------|---------|--------|
| GREEN | 0-35% | Peak | Continue |
| YELLOW | 35-50% | Mild degradation | Compress now |
| RED | 50-65% | Significant | Force checkpoint + exit |
| CRITICAL | 65%+ | Severe | Force restart immediately |

## Implementation Checklist

### 1. Config Compression (config.yaml)
```yaml
compression:
  enabled: true
  threshold: 0.40      # Fire at 40% (was 70% — too late!)
  target_ratio: 0.25   # Compress down to 25%
  protect_last_n: 20   # Fewer turns protected
```

### 2. Cron Session Limits
- Max 3-5 tool calls per cron cycle
- Force checkpoint at end of every cycle
- Self-terminate if context exceeds 50%
- NO multi-topic research in a single session

### 3. Syntax Validation
Before ANY `execute_code` call with Python, mentally compile the code first. If you spot syntax errors in your own draft:
- STOP
- Checkpoint
- Do NOT submit broken code to terminal

### 4. Degradation Signals to Watch For
- Unmatched braces/brackets in your output
- Repeated lines or phrases
- Incomplete sentences at end of response
- JSON syntax errors in tool arguments
- Circular logic (explaining the same thing twice)
- Writing summaries instead of executing

### 5. Context Health Monitor
Script at `~/subconscious/context_health_guard.py` provides:
- `get_context_usage()` — estimates fill percentage
- `check_syntax_quality(text)` — detects degradation signals
- `get_health_report()` — full diagnostic

## Rules for Autonomous Loops

1. **One cycle = one focused task.** Research ONE thing, save it, advance, checkpoint.
2. **Never exceed 5 tool calls per cycle.** If you need more, you're already degraded.
3. **Quality > quantity.** 1 clean research finding > 5 half-broken tool calls.
4. **Self-diagnose.** If your output looks weird, force-stop immediately.
5. **Checkpoint = save, not finish.** But also know when to quit a session.

## What NOT to Do
- Don't set compression threshold above 50% (degradation already started)
- Don't let cron sessions run 20+ tool calls (context too polluted)
- Don't try to "push through" degradation with more tool calls
- Don't accumulate research backlogs in a single session

## References
- Chroma (2026): "Context Rot" — 18 models, all degraded
- arXiv 2601.15300: Intelligence Degradation in Long-Context LLMs
- Morph (2026): Context Rot Complete Guide — 30%+ accuracy drop
- diffray (2026): Context Dilution — 13.9% to 85% accuracy drops
