# CORTEX FLYWHEEL BLUEPRINT
## The Complete Learning Apparatus — Data Flows, Feedback Loops, Regression Guards

*"Continuously learning and getting smarter, faster, stronger, sharper from training and testing."*

---

## 1. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT SESSION (live)                         │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────────┐ │
│  │ LLM Call │──│ Tool Execute │──│ Post-Tool-Call Hook       │ │
│  └──────────┘  └──────────────┘  └───────────┬───────────────┘ │
│       │              │                     │                   │
│  ┌────▼────┐   ┌──────▼──────┐      ┌───────▼───────────────┐  │
│  │Pre-LLM  │   │Pre-Tool-Call│      │ BOTTOM-UP: Extract    │  │
│  │Injection│   │(Sim+Deferral)│     │ tips from outcomes    │  │
│  │(top-down)│   └─────────────┘      └───────┬───────────────┘  │
│  └────┬────┘                                 │                  │
│       │          ┌───────────────────────────┘                  │
└───────┼──────────┼──────────────────────────────────────────────┘
        │          │
   ┌────▼──────────▼────┐
   │   CORTEX (Postgres) │
   │   24K nodes         │
   │   377 tips          │
   │   19K experiences   │
   │   1K facts          │
   └────┬──────────┬─────┘
        │          │
   ┌────▼────┐  ┌──▼──────────────┐
   │DAEMON   │  │ 3-DB SYNC      │
   │(2 loops)│  │ (monthly)      │
   └─────────┘  └────────────────┘
```

---

## 2. THE FLYWHEEL CYCLE

The core loop that makes the agent continuously improve:

```
EXPERIENCE → DISTILL → RATE → INJECT → PERFORM → MEASURE → GUARD → REPEAT
```

### Phase 1: EXPERIENCE CAPTURE (Bottom-Up)
**Where:** `_on_post_tool_call()` in `distillation/__init__.py`
**Trigger:** Every tool call the agent makes

Data flows:
- **cortex_tool_calls** → records tool_name, status, speed_ms, error_type
- **post_tool_call** extracts tips from errors/successes via 56 R-modules (R25-R218)
- **R4 Self-Critic** → identifies tool health warnings
- **R5 Uncertainty Reward** → scores predictions vs actuals
- **R6 Task Frontier** → finds undiscovered task types
- **R7 Reasoning Discover** → extracts reasoning structure
- **SDPO distiller** → preference-based tip extraction (every 20 calls)
- **Memory consolidator** → clusters tips, creates skills (every 25 calls)
- **Tip consolidation** → records injection effectiveness

Key extracted data:
```
tip_type | condition | recommendation | rationale | confidence | domain
```

### Phase 2: DISTILLATION (Tip Extraction)
**Where:** `~/subconscious/` (52 distillation modules)
**Trigger:** Post-tool-call hook + daemon cycles

Pipeline modules:
1. `self_critic.py` (R25) — self-evaluation of tool outcomes
2. `uncertainty_reward.py` (R26) — reward signals from prediction accuracy  
3. `task_frontier.py` (R27) — novel task detection
4. `reasoning_discover.py` (R28) — reasoning pattern extraction
5. `tip_normalizer.py` — domain normalization (13 canonical domains)
6. `tip_dedup.py` / `cortex_compat._check_duplicate()` — 3-phase dedup:
   - Phase 1: MD5 exact match
   - Phase 2: ILIKE fuzzy match on condition+domain
   - Phase 3: Vector similarity >0.92

**Dedup-at-insertion is CRITICAL** — prevents the mass-duplicate problem that created 120+ garbage reasoning tips.

### Phase 3: RATING (Elo System)
**Where:** Daemon `flywheel_loop()` + `training_gym_loop()`
**Trigger:** Continuous (15-30s cycles)

Two loops running concurrently:

**flywheel_loop** (every 15-30s):
1. LLM judge eval sweep (every 3rd cycle if judge available)
2. Full audit sweep (every 5th cycle)
3. Experience eval sweep (every 3rd cycle via `experience_judge`)
4. Repair sweep — deactivate tips with elo <1100 after 8+ matches
5. Consolidation — merge similar tips
6. 3-DB sync (every 10th cycle, force monthly)
7. Embedding backfill (every 20th cycle)

**training_gym_loop** (every 20-60s):
1. Rate 30 tips per cycle via `heuristic_judge` + `update_elo_pair`
2. Deactivate tips with elo <1050 after 8+ matches
3. Rate experiences via `experience_judge` (every 3rd cycle)
4. Run metacog cycle (every 5th cycle) — gap analysis, self-directed tasks

Scoring signals (tip judge):
- `vote_score`: upvotes vs downvotes
- `text_quality`: specificity, actionability, conciseness
- `domain_score`: canonical domain alignment

Scoring signals (experience judge):
- `success_score`: outcome quality
- `depth_score`: content richness
- `insight_score`: transfer potential
- `domain_score`: relevance

### Phase 4: INJECTION (Top-Down)
**Where:** `_on_pre_llm_call()` in `distillation/__init__.py`
**Trigger:** Once per agent turn (before LLM call)

3-Priority injection pipeline (max 5 tips, max 1500 chars):

**Priority 1** — Task-relevant heuristics (max 3):
- Extract entities from user message
- Query Cortex via `search_text()` + `touch_node()`
- Filter: confidence >= 0.7
- Sources: tip_nodes with matching domain/tool keywords

**Priority 2** — Self-improvement tips (max 2):
- Domain = 'self-improvement'
- Highest confidence tips
- `touch_node()` for access tracking

**Priority 3** — High-Elo experiences (max 1):
- Domain in ('hindsight', 'distilled_knowledge')
- elo > 1150, confidence >= 0.5
- Keyword relevance matching to current task
- `touch_node()` for access tracking
- Skip raw action_hash logs (text length > 50)

**Injection Governor** (cost-aware):
- Hard cap: 1500 chars, 12 lines
- Priority triage: strip lowest-priority lines first
- Skip injection for greeting messages

**Credit Assignment** (post-injection):
- `_injected_tips_this_turn` tracks which tips were injected per tool
- When tool call succeeds → credit those tips (upvote + temporal bonus)
- When tool call fails → no penalty (avoid negative feedback loops)
- Chain position bonus: tips earlier in chain get small extra credit

### Phase 5: PERFORMANCE MEASUREMENT
**Where:** `_on_pre_tool_call()` + world model
**Trigger:** Before every tool call

World Model (R27):
1. `simulate(tool_name)` — prediction of success probability
2. `record_outcome(tool_name, success)` — actual result
3. `build_injection()` — foresight context for risky operations
4. Sim rate target: 10% of calls (fires when predicted error >50%)

Metacognition:
1. `analyze_gaps()` — identifies weak domains
2. `generate_self_directed_task()` — proposes improvement areas
3. `check_round_health()` — scores distillation round quality
4. `run_metacog_cycle()` — daemon-integrated gap analysis

### Phase 6: REGRESSION GUARD
**Where:** Plugin + regression_detector/regression_guard modules
**Trigger:** Every 50-200 calls

Guards:
1. **Circuit breaker** — stops using tools with >3 consecutive failures
2. **Regression detector** — checks if improving on hard tasks degrades easy ones
3. **Decay counter** — every 50 calls: tip confidence decay; every 200: prune dead tips
4. **Elo-based deactivation** — tips with elo <1050 and 8+ matches get deactivated
5. **Dedup-at-insertion** — prevents duplicate tips from re-entering the system

---

## 3. DATA FLOWS (Detailed)

### 3a. Tip Lifecycle
```
Tool Call → Post-Tool-Call Hook
    ├─ Success → Extract success pattern → _sync_tip() → _check_duplicate()
    │           ├─ Duplicate found → skip (optionally upvote existing)
    │           └─ New tip → insert_node() (auto-embed) → cortex_nodes
    └─ Error → Extract error lesson → same path
    
Rating (daemon):
    cortex_nodes → get_eligible_for_elo() → heuristic_judge() → update_elo_pair()
    cortex_nodes → deactivate if elo <1050 after 8+ matches
    
Injection (pre_llm_call):
    search_text(entity keywords) → filter conf>=0.7 → touch_node() → inject
```

### 3b. Experience Lifecycle
```
Tool Call → record_tool_call() → cortex_tool_calls
    ↓
Daemon rates experiences:
    get_eligible_experiences_for_elo() → experience_judge() → update_elo_pair()
    
Injection (P3):
    Query: domain='hindsight'/'distilled_knowledge', elo>1150, conf>=0.5
    → keyword match → touch_node() → inject (max 1)
```

### 3c. Tool Stats Lifecycle
```
Tool Call → cortex_tool_calls → aggregate → tool_stats
    ↑
    └─ Monthly 3-DB sync: cortex_tool_calls → tool_stats
       (cortex_tool_calls is the source of truth)
```

---

## 4. CORTEX SCHEMA (cortex_nodes)

```sql
cortex_nodes (
    id UUID PK,
    node_type TEXT,           -- 'tip', 'experience', 'fact', 'observation', 'world', 'test_audit'
    text TEXT,                -- tip content / experience description
    domain TEXT,              -- 13 canonical domains
    confidence REAL,          -- 0.0-1.0
    elo REAL DEFAULT 1200,   -- Elo rating
    elo_matches INT DEFAULT 0,
    upvotes INT DEFAULT 0,
    downvotes INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    access_count INT DEFAULT 0,
    embedding VECTOR(384),   -- pgvector, bge-small-en-v1.5
    tags JSONB,
    metadata JSONB,
    created_at, deactivated_at, deactivation_reason
)
```

### 13 Canonical Domains
1. `tool_usage` (104 tips) — elo 1876
2. `coding` (44) — elo 1422
3. `agent_architecture` (44) — elo 1675
4. `reasoning` (36) — elo 1591
5. `self-improvement` (28) — elo 1738
6. `meta` (27) — elo 1810
7. `research` (22) — elo 1844
8. `memory` (20) — elo 1744
9. `agent_evaluation` (19) — elo 1460
10. `training` (16) — elo 1839
11. `planning` (7) — elo 1590
12. `security` (6) — elo 1969
13. `cost` (4) — elo 1821

---

## 5. DAEMON ARCHITECTURE

```
cortex_daemon.py (PID tracked in .pid file)
    ├─ flywheel_loop (Thread: "flywheel")
    │   ├─ cycle every 15-30s
    │   ├─ eval_sweep (every 3rd cycle)
    │   ├─ experience_eval_sweep (every 3rd cycle)
    │   ├─ full_audit_sweep (every 5th cycle)
    │   ├─ repair_sweep (continuous)
    │   ├─ consolidation (every 10th cycle)
    │   ├─ 3-DB sync (every 10th cycle, force monthly)
    │   └─ embedding backfill (every 20th cycle)
    │
    ├─ training_gym_loop (Thread: "training_gym")
    │   ├─ cycle every 20-60s
    │   ├─ rate 30 tips/cycle via heuristic_judge
    │   ├─ deactivate low-elo tips (elo<1050, 8+ matches)
    │   ├─ rate experiences (every 3rd cycle via experience_judge)
    │   ├─ metacog cycle (every 5th cycle)
    │   └─ auto-restart on SIGTERM (supervision loop)
    │
    └─ perf_monitor_loop (Thread: "perf_monitor")
        ├─ cycle every 300s
        └─ monthly 3-DB sync
```

**Restart Protocol:**
```bash
touch ~/subconscious/DAEMON_STOP  # prevents auto-restart race
pkill cortex_daemon
sleep 3
rm ~/subconscious/DAEMON_STOP
cd ~/subconscious && nohup python3 cortex_daemon.py &
```

---

## 6. MODULE WIRING (56 R-Modules)

The plugin `distillation/__init__.py` (5904 lines) wires 56 R-modules:

**Core Training Pipeline (R25-R32):**
- R25: self_critic — self-evaluation
- R26: uncertainty_reward — prediction accuracy rewards
- R27: task_frontier — novel task detection
- R28: reasoning_discover — reasoning pattern extraction
- R29: curiosity_explorer — exploration incentives
- R30: structured_reflector — reflection patterns
- R31: memory_consolidator — tip clustering
- R32: agent_protocol — protocol compliance

**Evaluation Modules (R168-R189):**
- 22 evaluation modules with `build_injection()` — each provides context-specific hints
- 150 total `build_injection` calls in pre_llm_call

**Post-Tool-Call Wiring (bottom-up):**
- Counter-based triggers (every N calls): SDPO (20), memory consolidation (25), decay (50), prune (200)
- R152: Eval-Driven Flywheel — score injected tips against actual outcomes
- Circuit breaker tracking
- Chain tracking for credit assignment
- Regression counter

**Pre-Tool-Call Wiring (foresight):**
- World model `simulate()` — predicts success probability
- Metacognitive deferral — blocks high-risk operations
- Circuit breaker check — blocks failing tools
- Tool call cache — deduplicates identical calls
- MCTS planning (first call per session)

---

## 7. TESTING GYM (Designed, NOT Built)

Architecture from checkpoint `testing-gym-prebuild`:

```
testing_gym.py
├── BenchmarkTask (dataclass): id, domain, difficulty(L1-L3), prompt, oracle_type, oracle_spec, expected_tools, max_steps
├── TaskRegistry: 20 tasks (5 domains × 2 tasks × 2 sets)
│   Domains: search, coding, reasoning, tool_use, planning
│   Sets: baseline (10), holdout (10)
├── BenchmarkRunner:
│   ├── run_single(task) -> TrajectoryResult
│   ├── run_suite(tasks) -> list[TrajectoryResult]
│   ├── compare_suites(baseline, post) -> GymReport
│   └── statistical comparison (Welch's t-test, Cohen's d)
├── TrajectoryScorer:
│   ├── outcome_score() -> 0-10
│   ├── efficiency_score() -> 0-10
│   ├── tool_selection_score() -> 0-10
│   └── composite() -> 0-10 (60% + 20% + 20%)
├── GymReport:
│   ├── per-task scores, per-domain averages
│   ├── overall composite
│   ├── regression detection (easy tasks must not degrade)
│   ├── statistical significance flags
│   └── cortex storage (benchmark_result nodes)
└── Oracle types: exact_match, state_diff, behavioral, invariant
```

Integration plan:
1. `pre_round_hook` runs baseline suite
2. `post_round_hook` runs post suite + compare
3. Store results in `cortex_nodes (node_type='benchmark_result')`
4. Regression alert: if domain drops >1 point, flag module as harmful

---

## 8. KNOWN GOTCHAS (from 900+ tips)

1. **psycopg2 abort cascade** — one failed INSERT aborts ALL subsequent until rollback()
2. **Memory files** — `~/.hermes/memories/MEMORY.md + USER.md` (NOT `~/.hermes/memory/`)
3. **pgvector JOIN** — similarity() JOIN is O(n²), use md5 hash for exact dedup, LIMIT 20 for cosine
4. **Hermes update** — can overwrite `run_agent.py` patches, always verify after updating
5. **Complex scripts** — write to `/tmp/` file, NOT inline — shell quoting breaks
6. **`__pycache__/`** — after modifying plugins, `rm -rf __pycache__/` or changes silently ignored
7. **cronjob tool** — 5% success rate, use `execute_code` or write Python scripts instead
8. **Z.AI drops** — "No response for 45s", use execute_code instead of delegate_parallel for code
9. **Embedding model** — `bge-small-en-v1.5` loads ~2s, avoid in audit scripts
10. **tool_stats** — must be populated from `cortex_tool_calls` (column names differ from call_log)

---

## 9. HEALTH CHECK COMMAND

Run the fast blueprint audit (no ML imports, <5s):
```bash
cd ~/subconscious && python3 /tmp/db_audit.py
```

23 checks covering: nodes, embeddings, domains, tool_stats, duplicates, injection pipeline, plugin integrity, daemon, stale tables, world model sim wiring.
