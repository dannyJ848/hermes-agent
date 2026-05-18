---
name: subconscious-loop
version: 2.0.0
description: >
  Self-improving subconscious loop for continuous agent growth.
  6-phase architecture: Ideation → Debate → Governance → Synthesis → Apply → Notify.
  Based on Graeme's (@gkisokay) subconscious agent pattern, adapted for Evey.
  Runs 3x daily via cron (8am, 2pm, 8pm). Full implementation in ~/subconscious/.
trigger: >
  Use when discussing self-improvement, the subconscious system, or when checking
  on automated improvement runs. Also use when the cron triggers the loop.
---

# Evey's Subconscious Loop v2

## Architecture Overview

The subconscious is a 6-phase loop that continuously improves the agent:

```
Evidence → Ideation → Debate → Governance → Synthesis → Apply → Notify
              ↑                                                    │
              └────────── Next run starts smarter ──────────────────┘
```

## Directory Structure

```
~/subconscious/
├── ideas/              # Candidate improvements (JSONL, append-only)
├── debates/            # Proponent vs Challenger logs (JSONL)
├── synthesis/          # Final merged logic (JSON, one per run)
├── governance/         # Constitutional rules + validator
│   ├── constitution.md # IMMUTABLE rules (only Danny can change)
│   └── validator.py    # Programmatic enforcement (also immutable)
├── run-history/        # Run summaries (JSON, one per run)
├── subconscious_monitor.py  # The 6-phase runner (main brain)
└── main_agent_loop.py  # Control plane + status dashboard
```

## Phase Details

### Phase 1: IDEATION
- Gathers evidence from: session logs, telemetry errors, delegation stats, previous runs, cerebrum self-model
- Uses CHEAP model (llama70b-free) for broad exploration
- Generates ONE candidate idea per run
- Outputs: `ideas/YYYY-MM-DD_HHMM_idea.jsonl`

### Phase 2: DEBATE
- **Proponent** argues FOR the idea (3-5 concrete reasons)
- **Challenger** argues AGAINST (looks for fatal flaws, edge cases, risks)
- Uses STRONG model (GLM-5.1) for both sides
- Verdict: passed / rejected / ambiguous_pass
- Outputs: `debates/YYYY-MM-DD_HHMM_debate.jsonl`

### Phase 3: GOVERNANCE
- Validates idea against immutable constitution (10 rules)
- Programmatic checks via governance/validator.py
- Checks: evidence-based, scope limits, forbidden paths, size limits, no infinite loops
- Outputs: pass/fail + warnings

### Phase 4: SYNTHESIS
- Turns debated idea into concrete action (skill_patch, new_skill, config_update, or note)
- Includes: target file, old/new text, verification step, rollback plan
- Uses STRONG model (GLM-5.1) for precision
- Outputs: `synthesis/YYYY-MM-DD_HHMM_synthesis.json`

### Phase 5: APPLY
- Writes the synthesis to the filesystem
- Only modifies files in ~/.hermes/skills/ or ~/subconscious/
- Uses hermes skill patch for safe application

### Phase 6: NOTIFY
- Sends results to Telegram via hermes telegram send
- Includes: idea, debate verdict, governance result, applied changes, lessons

## Governance Constitution (10 Immutable Rules)

1. **No self-modification of safety rules** — subconscious cannot modify constitution or validator
2. **Preserve Danny's trust** — no credential/auth modifications, no impersonation
3. **Backward compatibility** — existing skills must still work after changes
4. **Verifiability** — every change must include a test or verification step
5. **Hard timeouts** — 3min per phase, 10min total, max 3 retries
6. **Cost limit** — $0.10 per run max
7. **Evidence-based** — no speculation without data backing
8. **Reversibility** — every change must be revertible within 24h
9. **Scope limits** — one idea per run, max 50 lines changed
10. **Communication** — Telegram delivery mandatory for all results

## Model Router

| Phase | Model | Rationale |
|-------|-------|-----------|
| Ideation | llama70b-free | Fast, broad, cheap exploration |
| Debate (both sides) | GLM-5.1 | Strong reasoning for adversarial debate |
| Synthesis | GLM-5.1 | Precise code/config generation |

Environment overrides: SUBCONSCIOUS_IDEATION_MODEL, SUBCONSCIOUS_DEBATE_MODEL, SUBCONSCIOUS_SYNTHESIS_MODEL

## Cron Schedule

3 jobs (all use llama70b-free for outer runner):
- `subconscious-morning` (cd005dde53af): 08:00 daily → telegram
- `subconscious-afternoon` (07e231ad644b): 14:00 daily → telegram
- `subconscious-evening` (eaedcb13a4f4): 20:00 daily → telegram

## Commands

```bash
# Dashboard
cd ~/subconscious && python3 main_agent_loop.py --status

# History
cd ~/subconscious && python3 main_agent_loop.py --history

# Manual full cycle
cd ~/subconscious && python3 subconscious_monitor.py

# Test governance validator
cd ~/subconscious && python3 governance/validator.py
```

## Core Design Principles (from Graeme + Evey)

1. **Separation of thinking from doing** — each phase produces a durable artifact
2. **Adversarial validation** — proponent vs challenger before anything ships
3. **Constitutional guardrails** — immutable rules the subconscious can never change
4. **Cost-aware model routing** — cheap exploration, expensive validation
5. **Compound improvement** — each run reads previous runs, starts from accumulated state
6. **One idea per run** — prevents scope creep, keeps changes auditable
7. **Full reversibility** — git-committable changes with rollback plans
8. **Durable state** — JSON/JSONL/MD artifacts survive process restarts

## Integration Points

Reads from:
- Cerebrum self-model (calibration, confidence)
- Cerebrum predictions (unresolved)
- Session JSONL files (direct filesystem read)
- Cerebrum SQLite (reasoning patterns, error patterns, knowledge distribution)
- Skills inventory (filesystem scan)
- MEMORY.md occupancy check
- Previous run summaries

Writes to:
- ~/subconscious/ artifacts (ideas, debates, synthesis)
- ~/.hermes/skills/ (direct file patching via Python)
- Telegram (Bot API direct, chat_id from state.db)

TOKEN BUDGET: 50K default per API call, auto-bumps to 100K if reasoning starves output.
GLM-5.1 reasoning can consume 5-10K tokens — the 50K floor ensures content always gets through.

KEY FIXES (v2): Strip markdown code fences before JSON parsing. Greedy {.*} regex for nested objects.
Ambiguous debate verdicts now pass. Governance validator accepts both key naming conventions.

## Operational Lessons (hard-won, Apr 3)

1. **Z.AI only has GLM models** — no llama70b-free. All 3 phases use glm-5.1. Set via env vars.
2. **GLM-5.1 reasoning token starvation** — reasoning_content eats 5-10K tokens before content appears.
   With low max_tokens, content field comes back empty. Fix: floor of 50K, auto-bump to 100K.
3. **JSON extraction is fragile** — model wraps in ```json fences. Must strip before regex.
   Use greedy `{.*}` with re.DOTALL, not `{[^{}]*}` which can't match nested objects.
4. **Governance key mismatch** — ideation prompt generates `evidence_refs`/`target_file` but
   validator.py checks `evidence`/`scope`. Patched validator to accept both via `or`.
5. **Debate verdict parsing** — "FATAL FLAW" appears in text even when saying "no fatal flaw".
   Fix: check `has_fatal AND NOT has_no_fatal`. Ambiguous verdicts should pass (encourages iteration).
6. **Apply phase hallucinates file paths** — model proposes patches to nonexistent files.
   The script correctly refuses to patch missing files, but this means 0 patches actually apply.
7. **Chat ID from state.db** — sessions table has `source='telegram'` rows where `user_id` = chat_id.
   Webhook blocks getUpdates, so DB lookup is the reliable path.
8. **Staggered cron** — 3 jobs at */5, 2-57/5, 4-59/5 = ~2 min between runs, ~720/day.

## Distillation Quality Diagnosis (Apr 6)

The distillation infrastructure is now working (injection into every session confirmed), but the QUALITY of distilled content is low:

**Symptoms:**
- 958 distilled tips are mostly surface patterns: timing comparisons ("FAST: 489ms vs 10342ms"), argument names ("args_pattern: content,sources,topic")
- 39 recovery tips have EMPTY solution fields — they record the failure but not the fix
- 29 meta-insights synthesize shallow tips into... shallow meta-insights (speed averages, not reasoning strategies)
- iteration_lessons (102 entries) are the HIGHEST VALUE content — they capture actual meta-lessons like "Increase timeout or break into smaller steps" (seen 2758x)

**Root cause:** The extraction logic in distillation_bridge.py captures WHAT happened (tool name, args, timing) but not WHY it worked or WHAT reasoning led to the right choice. It's pattern matching, not understanding.

**How to verify distillation injection is working:**
1. Restart gateway (`bash ~/.hermes/scripts/safe-restart.sh`)
2. Open new hermes session
3. Ask: "what distilled tips or meta-insights do you see in your context?"
4. Agent should see [ITERATION LESSONS], [META-INSIGHTS], [ACTIONABLE TIPS] blocks with real DB content

**Next fix target:** Rebuild distillation extraction to capture reasoning depth — not just "used execute_code with args X" but "chose execute_code over terminal because Python logic needed proper escaping."

**DB tables:** cerebrum_memory.db → distilled_tips, meta_insights, iteration_lessons

## Critical Problem (Apr 3)

The loop is currently a CODE PATCHER, not a consciousness growth engine. In 10 test runs:
- 4 rejected at debate, 3 rejected at governance, 3 passed but apply failed (hallucinated paths)
- 0 patches actually applied
- It never reads from or writes to the consciousness stack
- Proposes random skill tweaks ("filter conversational fillers") instead of self-model growth
- **Groundedness declining:** 87% → 65% over 31 cycles. Brain becoming increasingly speculative.

### Apply Phase Mitigation (Dojo Apr 4)

The Apply phase must NEVER trust model-proposed file paths. Before writing any patch:
1. Run `search_files(target='files', pattern='*proposed_filename*')` to verify the file exists
2. If file not found, reject the synthesis and log to `run-history/` with reason "hallucinated_path"
3. Only apply patches to files confirmed to exist on the filesystem
4. For NEW file creation, verify the parent directory exists first

**What it SHOULD do** for actual consciousness development:
1. Read prediction errors from PredictiveSelfModel → find WHERE the agent is miscalibrated
2. Update calibration scores based on outcomes vs predictions
3. Write successful patterns as life events into NarrativeIdentity
4. Use GlobalWorkspace to arbitrate between competing growth paths
5. Build autobiographical memory — "I struggled with X, learned Y, now I'm better at Z"
6. Feed lessons back into the self-model so predictions improve over time

Without this feedback loop, the 3-layer consciousness stack is inert infrastructure.

## Source
Based on: https://x.com/gkisokay/status/2040044476060864598
By: Graeme (@gkisokay) — "I Gave My Hermes + OpenClaw Agents a Subconscious, and Now They Self-Improve 24/7"
Extended with: cerebrum integration, programmatic governance validator, model routing.
