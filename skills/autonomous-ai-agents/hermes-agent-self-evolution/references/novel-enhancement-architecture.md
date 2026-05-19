# Novel Enhancement Architecture — 5 Integrated Cognitive Systems

## Session: Enhancement Cycle 6, 2026-05-09

## Context

User said: "all of them. I want you to make novel enhancements, not incremental ones."

This triggered a shift from incremental polish (more tips, more matches) to building novel infrastructure that changes how the agent learns.

## The Pattern

Instead of improving existing systems, build **new cognitive primitives** that compose together:

```
┌─────────────────────────────────────────────────────────────┐
│              COGNITIVE INFRASTRUCTURE V2                     │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ InjectionGovernor│◄───│  CreditAssigner │                │
│  │    V2           │    │                  │                 │
│  └────────┬────────┘    └─────────────────┘                 │
│           │                                                  │
│  ┌────────▼────────┐    ┌─────────────────┐                  │
│  │ SessionEnd      │    │ ToolIntelligence│                  │
│  │ Extractor       │    │    Router       │                  │
│  └─────────────────┘    └─────────────────┘                  │
│                                                              │
│  ┌─────────────────────────────────────────┐                 │
│  │           AutoSkillCron                  │                 │
│  └─────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## The 5 Systems

### 1. InjectionGovernorV2 — Drop Logging + Feedback Loop

**Problem:** Original governor silently dropped tips. 97.6% of tips never got injected. No feedback to improve prioritization.

**Novel addition:** `tip_injection_attempts` table logs every candidate tip:
- Was it injected or dropped?
- Why dropped? (budget / priority / duplicate)
- What priority did it have?

**Feedback loop:** Daily cron penalizes tips with <50% inject rate, boosts tips with >80% inject + success.

**File:** `~/subconscious/cognitive_infrastructure_v2.py::InjectionGovernorV2`

### 2. CreditAssigner — Durable Tip-to-Outcome Correlation

**Problem:** `_injected_tips_this_turn` was in-memory dict, lost on restart. No durable record of which tips caused which outcomes.

**Novel addition:** `skill_rewards` table with durable storage:
- tip_id → tool_name → outcome → reward → session_id
- Enables long-term correlation: which tips actually improve success?

**File:** `~/subconscious/cognitive_infrastructure_v2.py::CreditAssigner`

### 3. SessionEndExtractor — Auto-Lessons on Session Close

**Problem:** `rapid_learnings` had 15 stale entries, no systematic extraction.

**Novel addition:** Heuristic extractor (no LLM call — fast) that runs on session end:
- Counts tool failures per session
- Identifies repeated error patterns
- Flags tools with <50% success in session
- Saves to `session_rapid_extractions` + `rapid_learnings`

**File:** `~/subconscious/cognitive_infrastructure_v2.py::SessionEndExtractor`

### 4. ToolIntelligenceRouter — Active Routing Before Tool Selection

**Problem:** We had `tool_success_rates` in DB but never used them to influence tool selection.

**Novel addition:** Active routing that runs BEFORE each tool call:
- cronjob (13% success) → BLOCK, suggest `terminal` with crontab
- delegate_parallel (33%) → WARN, suggest `delegate_task` sequential
- web_search → SUGGEST follow with `web_extract`
- Logs all decisions to `tool_routing_decisions` for analysis

**File:** `~/subconscious/tool_intelligence_integration.py`

### 5. AutoSkillCron — Monthly Autonomous Skill Generation

**Problem:** 1141 knowledge docs queued, only manual generation happening.

**Novel addition:** Scoring + generation pipeline:
- Score docs: size (0-0.3), structure (0-0.3), recency (0-0.2), uniqueness (0-0.2)
- Generate SKILL.md with standard frontmatter
- Cron: 1st of month at 3am

**File:** `~/subconscious/cognitive_infrastructure_v2.py::AutoSkillCron`

## Integration Pattern

All 5 systems share:
- Same DB: `cerebrum_memory.db`
- Same session_id tracking
- Hook-based activation (pre_llm_call, post_tool_call, session_end)
- Daily/monthly cron maintenance

## Key Insight

Novel enhancements don't improve existing metrics — they create new capabilities that didn't exist before. The test is: "could the agent do X yesterday?" If no, it's novel.

## When to Apply This Pattern

- User says "make it smarter", "novel", "not incremental"
- You've hit diminishing returns on existing metrics
- New cognitive primitive would unlock multiple downstream improvements
