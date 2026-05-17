---
name: cortex-flywheel-operation
description: Operate the Cortex continuous learning flywheel — experience capture, tip distillation, Elo rating, tip injection, and regression guarding. The engine that makes Hermes get smarter every session.
version: 1.0.0
metadata:
  hermes:
    tags: [cortex, flywheel, learning, distillation, elo, self-improvement]
    related_skills: [hermes-agent-self-evolution, training-gym-continuous, research-to-distillation]
---

# Cortex Flywheel Operation

The continuous learning engine. Every tool call feeds the flywheel. Tips get extracted, rated, injected, and measured.

## When to Use

- User says "make me smarter", "continuous improvement", "learning loop"
- Setting up new distillation pipelines
- Debugging why tips aren't improving agent behavior
- Running Elo tournaments or tip quality audits

## The Flywheel Cycle

```
EXPERIENCE → DISTILL → RATE → INJECT → PERFORM → MEASURE → GUARD → REPEAT
```

## Phase 1: EXPERIENCE CAPTURE

**Trigger:** Every `post_tool_call` hook
**Where:** `distillation/__init__.py`

Captures:
- Tool name, status, duration, error type
- Tip extraction via 56 R-modules
- Self-critic (R25), uncertainty reward (R26), task frontier (R27)

## Phase 2: DISTILLATION

**Trigger:** Post-tool-call + daemon cycles
**Pipeline:**
1. `self_critic.py` — evaluate outcomes
2. `uncertainty_reward.py` — prediction accuracy rewards
3. `tip_normalizer.py` — domain normalization (13 canonical domains)
4. `tip_dedup.py` — 3-phase deduplication:
   - Phase 1: MD5 exact match
   - Phase 2: ILIKE fuzzy match on condition+domain
   - Phase 3: Vector similarity >0.92

**Critical:** Dedup-at-insertion prevents mass-duplicate problem.

## Phase 3: RATING (Elo System)

**Two concurrent loops:**

**flywheel_loop** (15-30s):
1. LLM judge eval sweep (every 3rd cycle)
2. Full audit sweep (every 5th cycle)
3. Experience eval (every 3rd cycle)
4. Repair: deactivate tips with elo <1100 after 8+ matches
5. Consolidation: merge similar tips
6. 3-DB sync (every 10th cycle)

**training_gym_loop** (20-60s):
1. Rate 30 tips/cycle via heuristic judge
2. Deactivate tips with elo <1050 after 8+ matches
3. Metacog cycle every 5th iteration

**Scoring signals:**
- `vote_score`: upvotes vs downvotes
- `text_quality`: specificity, actionability, conciseness
- `domain_score`: canonical domain alignment

## Phase 4: INJECTION (Top-Down)

**Trigger:** `_on_pre_llm_call()` — once per turn
**Cap:** 5 tips, 1500 chars max

**Priority pipeline:**
1. Task-relevant heuristics (max 3) — confidence >= 0.7
2. Self-improvement tips (max 2) — highest confidence
3. High-Elo experiences (max 1) — elo > 1150

**Credit assignment:**
- Track `_injected_tips_this_turn` per tool
- Success → credit tips (upvote + temporal bonus)
- Failure → no penalty (avoid negative loops)

**Injection Governor V2 (Cycle 6+):**
- Logs every injection attempt: candidate tips, injected tips, dropped tips, drop reasons
- Tracks budget usage: `_INJECTION_MAX_CHARS` (2500), `_INJECTION_MAX_LINES` (12), `_MAX_INJECT` (8)
- Provides feedback loop: penalize frequently-dropped tips, boost frequently-injected+successful tips

**CRITICAL FIX — Governor Log Placement:**
The governor `log_attempt()` must be called AFTER `injection_lines` is fully populated and AFTER `final_lines` is assembled by budget trimming. Calling it before `injection_lines` exists (early in `_on_pre_llm_call`) logs empty data. The correct placement is:

```python
# After final_lines assembled:
for line, priority in injection_lines:
    injected = line in final_lines
    drop_reason = "" if injected else "budget" if len(final_lines) >= _INJECTION_MAX_LINES else "chars"
    gov.log_attempt(tip_id=0, condition=line[:200], priority=priority,
                    injected=injected, drop_reason=drop_reason,
                    chars_used=len(line), lines_used=len(final_lines))
```

See `references/injection-governor-fix.md` for full details.

## Phase 5: REGRESSION GUARDS

**Checks:**
- Tip survival rate <30% after 100 opportunities → mark for review
- Tool performance degradation >50% in last hour → alert
- Database size >100MB → warn
- Error pattern frequency >10 occurrences → escalate

## Key Tables

| Table | Purpose |
|-------|---------|
| `distilled_tips` | 1900+ tips with confidence scores |
| `tip_survival` | Opportunities + applications tracking |
| `tip_adversarial` | Red-team validation results |
| `prompt_fragments` | Elo-rated SOUL.md components |
| `enhancement_effectiveness` | Cycle-by-cycle improvement metrics |

## Daemon Setup

```bash
# Flywheel daemon (continuous)
hermes cron create --name "cortex-flywheel" --schedule "*/5 * * * *" \
  --prompt "Run cortex flywheel: rate tips, audit, sync DBs"

# Training gym (tip evolution)
hermes cron create --name "training-gym" --schedule "*/10 * * * *" \
  --prompt "Run training gym: 30 tip Elo comparisons"
```

## Debugging

**Tips not improving behavior?**
1. Check `tip_survival` — are tips getting opportunities?
2. Check injection logs — are tips reaching the LLM context?
3. Check Elo scores — are high-Elo tips actually better?

**Duplicate tips flooding?**
1. Verify `tip_dedup.py` 3-phase dedup is running
2. Check MD5 unique constraint on `distilled_tips`
3. Review `cortex_compat._check_duplicate()` vector similarity threshold

**Elo scores stuck?**
1. Run manual tournament: `python ~/subconscious/cortex_flywheel_v2.py`
2. Check LLM judge availability (DeepSeek V4 Pro)
3. Verify `heuristic_judge` fallback is functional
