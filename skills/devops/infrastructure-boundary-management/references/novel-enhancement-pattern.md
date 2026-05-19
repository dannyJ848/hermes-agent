# Novel Enhancement Pattern on MacBook

## Session: Enhancement Cycle 6, 2026-05-09

## Context

When running enhancement cycles on MacBook (Hermes self-improvement ONLY), user said: "all of them. I want you to make novel enhancements, not incremental ones."

This triggered a shift from incremental polish to building new cognitive primitives.

## The Pattern

Build **integrated cognitive infrastructure** — 5+ systems that compose together, not isolated improvements.

## Example: Cognitive Infrastructure V2

Built in Cycle 6:

| System | Table | What It Does |
|--------|-------|-------------|
| InjectionGovernorV2 | `tip_injection_attempts` | Logs every drop, feeds back to tip priority |
| CreditAssigner | `skill_rewards` | Durable tip→outcome correlation |
| SessionEndExtractor | `session_rapid_extractions` | Auto-extracts lessons on session close |
| ToolIntelligenceRouter | `tool_routing_decisions` | Blocks cronjob (13%), warns delegate_parallel (33%) |
| AutoSkillCron | (cron job) | Monthly auto-generates skills from knowledge docs |

All share:
- Same DB: `cerebrum_memory.db`
- Same session_id tracking
- Hook-based activation
- Daily/monthly cron maintenance

## Key Files

- `~/subconscious/cognitive_infrastructure_v2.py` — 5 classes
- `~/subconscious/cognitive_infrastructure_hooks.py` — hook wiring
- `~/subconscious/tool_intelligence_integration.py` — active routing

## When to Apply

- User says "make it smarter", "novel", "not incremental"
- Diminishing returns on existing metrics
- New primitive would unlock multiple downstream improvements
