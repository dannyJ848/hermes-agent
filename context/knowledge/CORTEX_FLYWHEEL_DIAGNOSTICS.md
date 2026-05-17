# CORTEX FLYWHEEL — REAL DIAGNOSTICS
## What Actually Works vs What's Just Wired

---

## EXECUTIVE SUMMARY

The apparatus has 56 R-modules, 5904 lines of plugin code, 436 subconscious files, and a dual-loop daemon. But the **actual learning flywheel is running at ~2.4% efficiency**. Here's the real state:

| System | Wired? | Works? | Hit Rate | Root Cause |
|--------|--------|--------|----------|------------|
| Tip Injection (P1/P2/P3) | ✓ | PARTIAL | 2.4% | Only 9/374 tips ever accessed |
| World Model Sim | ✓ | BROKEN | 0.0% | simulate() fires but `should_simulate` gate too strict |
| Metacognitive Rounds | ✓ | BROKEN | 0 rounds | No cortex tables, SQLite has 198 stale predictions |
| Episodic Memory | ✓ | BROKEN | 0% retrieval | 19K experiences but only 882 rated, salience filter rejects all |
| Credit Assignment | ✓ | PARTIAL | Unknown | skill_rewards table missing, tracking works but no storage |
| Elo Rating | ✓ | WORKS | Good | 288/374 tips injectable, daemon rating active |
| Dedup-at-Insertion | ✓ | WORKS | Good | 3-phase catches dupes |
| Domain Normalization | ✓ | WORKS | 100% | 13 canonical domains |
| Daemon | ✓ | WORKS | Active | Rating experiences, 0 errors in last 50 log lines |
| World Model Record | ✓ | WORKS | Good | 12 record_outcome calls in code |
| Distillation Throughput | ✓ | WORKS | 795 tips/day | But most never get injected |

---

## 1. INJECTION EFFECTIVENESS — THE CORE BOTTLENECK

**97.6% of tips are dead knowledge.** Only 9 out of 374 tips have ever been accessed.

```
Access Distribution:
  Never accessed:  365 tips (97.6%)
  Low (1-5):         7 tips (1.9%)
  Mid (6-20):        0 tips (0.0%)
  High (20+):        2 tips (0.5%)
```

**Why?** The injection pipeline has 5 competing problems:

1. **Budget too tight**: 1500 chars / 12 lines / max 5 tips. With 150 build_injection calls from 56 modules fighting for that budget, ~138 injection calls are **silently dropped every turn**.

2. **Entity extraction is weak**: The P1 path queries by entity keywords, but most tips have abstract conditions that don't match user message entities. A tip about "psycopg2 abort cascade" won't match "fix database error".

3. **Confidence threshold too high**: P1 requires conf >= 0.7, P2 requires domain='self-improvement', P3 requires elo > 1150 AND conf >= 0.5 AND keyword match. With 287 injectable tips, only ~5 actually make it through per turn.

4. **No negative feedback signal**: When the injection governor drops lines, there's no record of what was dropped or why. The system can't learn to prioritize better.

5. **touch_node happens too late**: Tips get touch_node'd only after injection + successful tool call. But if injection is too restrictive, tips never get touched, never get access_count > 0, and the system can't tell which tips are useful.

### ELO Quality Distribution
```
<1000 (garbage):     0 tips
1000-1200 (bad):    26 tips ###  
1200-1400 (weak):   55 tips ######
1400-1600 (ok):      5 tips #
1600-1800 (good):  164 tips ##############################
1800+ (strong):    124 tips ##############################
```

### Domain Injection Readiness
287 of 374 tips meet injection criteria (elo>1500, conf>=0.7).
**But only 9 have ever been accessed. The gap isn't quality — it's delivery.**

---

## 2. WORLD MODEL — BROKEN AT THE GATE

`simulate()` is called in code (1 call in pre_tool_call), but `should_simulate` has a target rate of 10% and actual rate is 0%.

**Root cause**: The `SimulationGate.should_simulate()` method has conditions that never fire:
- Requires uncertainty above a threshold
- Requires error probability > 50%
- The transition model's uncertainties are too low because `record_outcome` mostly records successes

**Fix**: Either lower the simulation threshold, or change `should_simulate` to randomly sample at a fixed rate (10% of calls) rather than waiting for high uncertainty.

---

## 3. METACOGNITION — ZERO ROUNDS COMPLETED

Metacog has `analyze_gaps` + `start_round` + `generate_self_directed_task` methods but 0 rounds have ever completed. 

**Root cause**: 
- No cortex tables for metacog state (all in SQLite: `metacog_predictions` with 198 rows)
- `run_metacog_cycle()` is called every 5th daemon cycle, but it needs an active session context
- The daemon doesn't have a session, so metacog can't access conversation history to find gaps
- The injection path (`get_metacognitive_injection()`) returns stale data from SQLite, not live analysis

**Fix**: Metacog needs to either:
1. Store its state in cortex (not SQLite) so it persists across sessions
2. Get periodic conversation context snapshots from the plugin
3. Or run as a plugin hook (not daemon), where it has access to session data

---

## 4. EPISODIC MEMORY — ALWAYS EMPTY

The injection shows `sal=0.50: {} {}` every turn. 19,299 experience nodes exist, 7,897 are meaningful, but none are retrieved.

**Root cause**: The episodic memory retrieval path has a salience filter (`sal > threshold`) that rejects everything:
- Experiences have default elo=1200 and confidence=0.50
- Only 882 of 19,299 have elo > 1200
- The P3 injection path tries to inject 1 experience, but the keyword match often fails
- The entity-based query doesn't match experience text well

---

## 5. CREDIT ASSIGNMENT — TRACKING WITHOUT STORAGE

`_injected_tips_this_turn` tracks which tips were injected per tool. When tools succeed, tips get upvoted. But:
- `skill_rewards` SQLite table is referenced in code but **doesn't exist**
- No durable record of which injections led to which outcomes
- Can't do long-term correlation analysis

---

## 6. DEAD CODE / ZOMBIE MODULES

56 R-modules registered. 150 build_injection calls. But:
- 43 modules produce 0 directly attributable tips
- ~138 injection calls are **silently dropped** each turn by the governor
- Many R-modules (R150-R157, etc.) are dead code without any active tips
- The plugin has accumulated R-modules like barnacles — each one adds import time, injection computation, and code complexity

**Zombie audit needed**: Which R-modules actually produce useful injections? Which should be unwired?

---

## 7. REDUNDANCY ANALYSIS

| Component Fails | Impact | Fallback | Recovery |
|-----------------|--------|----------|----------|
| Postgres down | All injection returns '' | Agent runs blind | Restart Postgres, daemon reconnects |
| Daemon down | Elo stops, no pruning | Tips exist but ossify | Restart daemon (PID auto-tracked) |
| Plugin crash | No injection, no distillation | Agent becomes static | Plugin reload needed |
| cortex_access down | No semantic_search | Falls back to search_text | Import error, injection returns '' |
| Embedding model fails | No vector search | Falls back to text search | Disabled until model reloads |
| Single tip corrupted | Doesn't affect others | Dedup catches duplicates | Deactivate via Elo |

**No redundancy for**: Postgres (SPOF), Plugin (SPOF). If either dies completely, the flywheel stops entirely.

---

## 8. STRENGTHS

1. **Elo rating works**: 288/374 tips are injectable quality, daemon actively rating
2. **Dedup-at-insertion works**: 3-phase prevents duplicate tips from re-entering
3. **Domain normalization works**: 13 canonical domains, 100% coverage
4. **Distillation throughput works**: 795 new tips/day (Apr 15)
5. **Daemon is stable**: 0 errors in last 50 log lines, dual-loop running
6. **Cost-aware governor works**: Budget enforcement prevents token bloat
7. **Touch_node works**: After fix, tips get access tracking

---

## 9. WEAKNESSES (Priority Order)

1. **Delivery bottleneck** (CRITICAL): 97.6% of tips never injected. Quality isn't the problem — 287 tips are ready. The injection pipeline is the bottleneck.
2. **World model gate too strict** (HIGH): 0% sim rate. Need to lower threshold or switch to sampling.
3. **Metacog disconnected** (HIGH): 0 rounds completed. Daemon can't access session context.
4. **Episodic memory empty** (HIGH): Salience filter rejects all 19K experiences.
5. **Zombie modules** (MEDIUM): 43 R-modules with 0 attributable output, 138 injection calls wasted per turn.
6. **No credit storage** (MEDIUM): skill_rewards table missing, can't analyze injection → outcome correlation.
7. **No negative signal** (LOW): When governor drops lines, no record for learning.
8. **Postgres SPOF** (LOW): No fallback, but Postgres is stable.

---

## 10. CRITICAL FIXES NEEDED

### Fix 1: Injection Delivery (97.6% → target 50%+)
- **Lower confidence threshold**: P1 from 0.7 → 0.6
- **Expand max inject**: 5 → 8 tips (trade 200 tokens for 2x coverage)
- **Add topic clustering**: inject diverse tips, not just top-by-confidence
- **Track what's dropped**: log which injection calls were rejected for tuning

### Fix 2: World Model Sim Rate (0% → 10%)
- **Switch to sampling**: `should_simulate()` → random 10% chance, not conditional
- **Or lower uncertainty threshold**: from 50% → 30% error probability

### Fix 3: Metacog Integration (0 → active)
- **Move state to cortex**: Create `metacog_state` table in Postgres
- **Hook-based execution**: Run metacog in post_tool_call (has session context), not daemon
- **Or inject conversation snapshots**: Plugin writes last-N messages to cortex for daemon

### Fix 4: Episodic Memory Retrieval
- **Lower salience threshold**: from current default → 0.3
- **Rate more experiences**: Currently 882/19K rated. Need daemon to rate ALL meaningful ones
- **Remove keyword match for P3**: Use semantic_search instead of text keyword matching

### Fix 5: Zombie Module Pruning
- **Audit which R-modules produce tips**: Track module→tip attribution
- **Unwire modules with 0 output after 30 days**: Same as phase 4 audit
- **Compress injection calls**: Batch build_injection, filter empty returns early

---

## 11. ENHANCEMENTS (Beyond Fixing)

1. **Injection A/B testing**: Randomly inject different tip sets, measure tool success rates
2. **Trajectory-aware injection**: Use conversation history to predict what tip will be needed next
3. **Tip aging**: Recently useful tips get boosted, stale tips get decayed
4. **Cross-session learning**: Aggregate injection outcomes across sessions for long-term trends
5. **Testing gym integration**: Close the loop — benchmark before/after each distillation round
6. **Adaptive budget**: Increase injection budget for hard tasks, decrease for easy ones

---

## 12. LAYER MAP

```
LAYER 0: Postgres (cortex DB) — all persistent state
LAYER 1: cortex_access.py — DB API (insert_node, search_text, semantic_search, update_elo)
LAYER 2: cortex_compat.py — tip sync + dedup bridge  
LAYER 3: cortex_flywheel.py — Elo rating, judge, sweeps
LAYER 4: cortex_daemon.py — mechanical maintenance (2 loops)
LAYER 5: world_model_r27.py — prediction + foresight
LAYER 6: intrinsic_metacognition.py — gap analysis
LAYER 7: 52 distillation modules — tip extraction
LAYER 8: distillation plugin — hooks (pre_tool_call, post_tool_call, pre_llm_call)
LAYER 9: Injection governor — budget enforcement
LAYER 10: Agent receives context — the only layer that matters

       ↑ Data flows up ↑
       ↓ Feedback flows down ↓
```

**Critical insight**: Layer 10 is where value is realized. Layers 0-9 are infrastructure. The flywheel's value = **(tips that reach Layer 10 and improve outcomes) / (total tips created)**. Currently: 9/374 = 2.4%.
