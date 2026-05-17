# APPARATUS BLUEPRINT — Full System Map
Generated: 2026-04-15
Purpose: Single source of truth for all components, connections, data flows, and known issues.

---

## ARCHITECTURE OVERVIEW

```
┌──────────────────────────────────────────────────────────┐
│                    HERMES AGENT RUNTIME                     │
│                                                            │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   LLM Provider   │  │  Gateway/API   │                  │
│  │  FriendliAI      │  │  Telegram/CLI   │                  │
│  │  GLM-5.1        │  │                 │                  │
│  └────────┬────────┘  └────────┬────────┘                  │
│           │                    │                            │
│  ┌────────▼────────────────────▼────────┐                  │
│  │        AGENT LOOP (run_agent.py)     │                  │
│  │  pre_llm_call → LLM → tool_call →   │                  │
│  │  post_tool_call → post_llm_call      │                  │
│  └────────┬────────────────────┬────────┘                  │
│           │                    │                            │
│  ┌────────▼────────┐  ┌───────▼──────────┐                │
│  │  DISTILLATION    │  │  CONTEXT ENGINE   │                │
│  │  PLUGIN (5903ln) │  │  LCM (active)     │                │
│  │  Hooks below ↓   │  │  Hindsight (standby)│             │
│  └─────────────────┘  └──────────────────┘                │
│                                                            │
│  ┌─────────────────────────────────────┐                  │
│  │     CORTEX DAEMON (483ln, 3 threads)│                  │
│  │  flywheel_loop | training_gym_loop  │                  │
│  │  perf_monitor_loop                   │                  │
│  └──────────────────┬──────────────────┘                  │
│                     │                                      │
│           ┌─────────▼──────────┐                           │
│           │  CORTEX POSTGRES   │                           │
│           │  26 tables, 28K+   │                           │
│           │  nodes             │                           │
│           └───────────────────┘                            │
└──────────────────────────────────────────────────────────┘
```

---

## 1. CORTEX POSTGRES DB
DSN: `postgresql://hindsight:hindsight@localhost:5432/cortex`
Schema: 26 tables

### TABLE INVENTORY (with row counts)
| Table | Rows | Purpose | Health |
|-------|------|---------|--------|
| cortex_nodes | 28,728 | Main knowledge graph (tips, experiences, facts, etc.) | ACTIVE |
| cortex_eval_history | 84,507 | Elo match results | ACTIVE |
| cortex_edges | 369,285 | Entity relationships | ACTIVE |
| cortex_kv_store | 5,084 | Generic key-value storage | ACTIVE |
| cortex_migration_log | 18,228 | Migration tracking | STALE (1x use) |
| cortex_documents | 6,414 | Document chunks for RAG | ACTIVE |
| cortex_flywheel | 4,935 | Flywheel cycle records | ACTIVE |
| cortex_predictions | 5,255 | Prediction tracking | ACTIVE |
| cortex_entities | 4,369 | Named entities | ACTIVE |
| cortex_chunks | 741 | Document sub-chunks | ACTIVE |
| cortex_calibration | 651 | Calibration records | ACTIVE |
| cortex_tool_calls | 651 | Tool call audit trail | ACTIVE |
| tool_stats | 14 | Per-tool aggregate stats | ACTIVE |
| cortex_circuit_breakers | 38 | CB state tracking | EPHEMERAL |
| cortex_life_events | 56 | Life event records | ACTIVE |
| cortex_identity | 3 | Agent identity keys | ACTIVE |
| cortex_mastery | 8 | Tool mastery levels | ACTIVE |
| cortex_epistemic_facts | 6 | Trusted facts | ACTIVE |
| cortex_debug_sessions | 0 | Debug session tracking | EMPTY |
| cortex_exploration | 0 | Exploration tasks | EMPTY |
| cortex_entity_cooccurrences | 0 | Entity co-occurrence | EMPTY |
| cortex_node_entities | 0 | Node→Entity mapping | EMPTY |
| cortex_reasoning | 0 | Reasoning chains | EMPTY |
| cortex_step_rewards | 0 | Step-level rewards | EMPTY |
| cortex_token_usage | 0 | Token tracking | EMPTY |
| call_log | 0 | Tool call log | EMPTY (was populated, now 0!) |

### cortex_nodes SCHEMA (primary table)
```
id: uuid PK
text: text (the content)
node_type: text (tip, experience, fact, world, observation, etc.)
domain: text (13 canonical domains)
parent_id: uuid FK → cortex_nodes
source_doc_id: uuid FK → cortex_documents
embedding: vector(384) — BAAI/bge-small-en-v1.5
elo: real (default 1000)
elo_matches: int (default 0)
elo_wins: int
elo_losses: int  
confidence: real (0-1)
upvotes: int (default 0)
downvotes: int (default 0)
frequency: int
salience: real
trust: real
metadata: jsonb
tags: text[] (Postgres array, NOT jsonb)
source_ids: text
created_at, updated_at, last_accessed, last_evaluated, last_consolidated: timestamp
access_count: int (default 0)
consolidation_count: int
is_active: boolean
provenance: text
```

### 13 CANONICAL DOMAINS
reasoning, tool_usage, coding, agent_architecture, agent_evaluation,
self_improvement, meta, research, memory, training, planning, security, cost

---

## 2. CORTEX DAEMON
File: `~/subconscious/cortex_daemon.py` (483 lines)
PID file: `~/subconscious/cortex_daemon.pid`
Log: `~/subconscious/cortex_daemon.jsonl`
Heartbeat: `~/subconscious/cortex_daemon.heartbeat`
STOP file: `~/subconscious/DAEMON_STOP` (touch before kill to prevent auto-restart)

### 3 THREADS

**flywheel_loop** (thread: "flywheel", 15s sleep)
- Elo evaluation sweep: 50 tip pairs per cycle via heuristic_judge
- Experience Elo sweep: 20 experience pairs per cycle (every 3rd cycle only)
- Repair sweep: deactivate tips below elo 1100 with 3+ matches
- Consolidation: merge similar tips
- Writes: cortex_nodes (elo updates, deactivation), cortex_eval_history, cortex_flywheel

**training_gym_loop** (thread: "training_gym", 20s sleep)
- Reads cortex_nodes for tip/experience evaluation
- Metacog cycle every 5th cycle via `run_metacog_cycle()`
- Reads/writes cortex_nodes

**perf_monitor_loop** (thread: "perf_monitor", 300s sleep)
- Reports: total active nodes, tip count, avg elo, avg confidence
- Monthly 3-DB sync: resync tool_stats.total_calls from call_log
- Circuit breaker purge: DELETE cortex_nodes WHERE node_type='circuit_breaker' AND created_at < NOW()-1hr
- Monthly: tracks `_last_monthly_sync` string (YYYY-MM format)

### SIGNAL HANDLING
- SIGTERM: sets `_restart_requested=True`, loops check it and restart
- SIGINT: sets `_running=False`, clean shutdown
- STOP file protocol: `touch DAEMON_STOP` before kill prevents auto-restart race

---

## 3. DISTILLATION PLUGIN
File: `~/.hermes/plugins/distillation/__init__.py` (5903 lines)
Entry: `register(ctx)` at line 5861

### HOOKS

**_on_post_tool_call** (line 659)
Called after every tool execution. Biggest hook (~1300 lines).
- R158 Next-State Signal Extractor
- R160 Turn-Level Credit Assignment
- R161 Trajectory Intelligence Extractor
- R168 Self-Critic Reflection Module
- R169 ReasoningDiscover — record task outcome
- R170 TaskFrontier — record tool outcome
- R171 UncertaintyReward — shaped reward
- R172 ToolAdaptor — failure patterns
- R174 ReflectionSynth — rule synthesis
- R175 Curriculum — E2H progression
- R178 RecoverySelector — recovery strategies
- R181 InteractionLogger — turn quality
- R182 ExecTracer — decision audit
- R183 SkillGapDetector — mismatches
- R184 PromptOptimizer — injection effectiveness
- R185 RewardEvolver — reward co-evolution
- R186 ContextBudget — turn budget
- R187 AdaptationSpeed — recovery time
- R188 ToolDiversity — variety
- R189 OutputQuality — pattern quality
- R163 Curriculum Difficulty Tracker
- R165 Adaptive Compute Allocation
- R177 FadeMem decay
- R186 PASTE Speculative Executor
- R187 ToolTree
- R188 Empirical MCTS
- R193a DGM Version Archive
- R193b Speculative Actions
- R194 Memory Consolidation
- World model: record_outcome (line 1291)
- Reliability tracker: record_outcome (line 1223)
- Cost tracker: record_outcome (line 1539/1548)
- Trajectory validator: record_outcome (line 1582)
- Error profiler: record_outcome (line 1645)
- Arg feedback recording
- Tip confidence updates
- Tip maintenance (decay, every 50th/100th/200th/300th call)
- Hindsight sync (every 5 min)
- Cerebrum distilled_tips writes (SQLite dual-write)
- Cortex sync via cortex_compat

**_on_pre_tool_call** (line 2676)
Called before every tool execution.
- World model simulate (foresight) — line ~2720
- Metacognitive deferral check
- P1 injection: retrieve tool-specific tips from cortex
- P2 injection: retrieve self-improvement tips from cortex
- P3 injection: retrieve high-elo experiences from cortex
- Injection tracking: `_injected_tips_this_turn`
- touch_node() after cortex tip retrieval

**_on_pre_llm_call** (line 2970)
Called before every LLM call. Biggest injection point.
- Retrieves weakest tools
- Queries cortex for relevant tips
- Queries SQLite distilled_tips as fallback
- Metacognitive injection
- Cost-aware governor: _INJECTION_MAX_CHARS=1500, _INJECTION_MAX_LINES=12
- P1/P2/P3 priority triage
- 429 rate limit tracking
- Builds injection string, appends to messages

**_on_post_api_request** (line 5686)
- Token usage logging
- Rate limit tracking

### INJECTION PIPELINE (3 PRIORITIES)
- **P1**: Tool-specific tips (highest priority) — matched by tool_name
- **P2**: Self-improvement tips — domain=self-improvement, high elo
- **P3**: High-elo experiences — elo>1150, confidence>=0.5 (7897 eligible)
- Governor: 1500 chars max, 12 lines max per turn

### DB ACCESSES
- SQLite: cerebrum_memory.db (dual-write via cortex_compat)
- Postgres: cortex_nodes (via cortex_access)
- SQLite: arg_feedback.db, skill_reward.db, predictor.db, api.db (tool-local)

---

## 4. CORTEX ACCESS LAYER
File: `~/subconscious/cortex_access.py` (483 lines)

### CortexDB CLASS
Key methods:
- `insert_node()` — insert with auto-embedding, domain normalization, dedup
- `touch_node()` — increment access_count, update last_accessed
- `deactivate_node()` — soft delete
- `get_node()` — fetch by ID
- `search_text()` — ILIKE text search
- `vector_search()` — pure vector similarity (takes embedding list, NOT text)
- `semantic_search()` — text→embedding→vector search
- `hybrid_search()` — reciprocal rank fusion of text + vector
- `get_eligible_for_elo()` — tips with 3+ matches for Elo
- `get_eligible_experiences_for_elo()` — experiences for Elo
- `update_elo()` — Elo update after match
- `get_tips_for_eval()`, `get_top_tips()`, `get_low_elo_tips()`
- `record_flywheel_cycle()`, `complete_flywheel_cycle()`
- `set_elo()` — direct elo set (for reseeding)
- `record_tool_call()`, `record_prediction()`, `resolve_prediction()`
- `record_eval()`, `get_stats()`

### Helper functions
- `cortex_cursor()` — context manager for DB cursor
- `get_connection()` — raw connection
- `embed_text()` — BAAI/bge-small-en-v1.5 (384d)
- `get_db()` — singleton accessor

---

## 5. CORTEX FLYWHEEL
File: `~/subconscious/cortex_flywheel.py`

### Functions
- `expected_score()`, `update_elo_pair()` — Elo math
- `heuristic_judge()` — tip comparison (vote_score, text_quality, domain_score)
- `experience_judge()` — experience comparison (success_score, depth_score, insight_score, domain_score)
- `run_eval_sweep()` — 50 tip pair evaluations per call
- `run_experience_eval_sweep()` — 20 experience pair evaluations
- `run_repair_sweep()` — deactivate low-elo tips
- `run_consolidation()` — merge similar tips
- `run_stats_report()` — current stats
- `run_full_cycle()` — all of the above

---

## 6. CORTEX COMPAT SHIM
File: `~/subconscious/cortex_compat.py`

### Purpose: Dual-write bridge between SQLite (cerebrum_memory.db) and Postgres (cortex)

Key functions:
- `_normalize_domain()` — canonical domain enforcement
- `_check_duplicate()` — dedup before insert
- `cortex_sync()` — main sync router
- `_sync_tip()` — tip write-through
- `_sync_elo()` — elo sync
- `cortex_retrieve_tips()` — query tips from both sources
- `cortex_count_tips()` — count active tips

### Status: cerebrum_memory.db (13MB) still exists for backward compat
The pre_tool_call hook still reads SQLite distilled_tips as fallback.
NEW: Hindsight context engine now queries Postgres directly (Apr 15 fix).

---

## 7. WORLD MODEL R27
File: `~/subconscious/world_model_r27.py`

### Classes
- `TransitionTracker` — records tool→outcome transitions, predicts next outcome
- `SimulationGate` — decides whether to simulate (target rate 10%)
- `PredictionTracker` — tracks prediction accuracy
- `WorldModel` (main class):
  - `record_outcome()` — post-tool-call recording
  - `simulate()` — pre-tool-call foresight (NEWLY WIRED Apr 15)
  - `build_injection()` — builds context string for pre_llm_call

### Integration
- `record_outcome` called from: plugin _on_post_tool_call (line 1291)
- `simulate` called from: plugin _on_pre_tool_call (line ~2720) — NEW
- `build_injection` called from: plugin _on_pre_llm_call

---

## 8. INTRINSIC METACOGNITION
File: `~/subconscious/intrinsic_metacognition.py`

### Class: IntrinsicMetacognition
- `analyze_gaps()` — find weak domains
- `generate_self_directed_task()` — create improvement tasks
- `score_step()` / `_score_research/distill/insert/verify()` — step quality
- `check_round_health()` — round-level health
- `start_round()`, `record_step()`, `end_round()` — round lifecycle
- `get_status()` — current status with trend
- `_get_recommendation()` — trending recommendation

### Functions
- `get_metacognitive_injection()` — injection string for pre_llm_call
- `run_metacog_cycle()` — standalone cycle (called by daemon every 5th cycle)

### Integration
- Plugin _on_pre_llm_call calls `get_metacognitive_injection()` (line 3620)
- Daemon training_gym_loop calls `run_metacog_cycle()` every 5th cycle

---

## 9. CONTEXT ENGINES

### Hindsight (our engine)
File: `~/hermes-agent/plugins/context_engine/hindsight/__init__.py` (15825 bytes)
- Queries Cortex Postgres directly (updated Apr 15, was SQLite + dead API)
- Extracts entities from messages being compressed
- Queries cortex_nodes tips and facts/experiences
- Enriches compression with preserved knowledge block
- Config: `context.engine: hindsight` (line 39, overridden by line 230)

### LCM (third-party, ACTIVE)
File: `~/hermes-agent/plugins/context_engine/lcm/`
- Lossless Context Management — hierarchical summarization
- Config: `context.engine: lcm` (line 230 — this one wins)
- Has own engine.py, config.py, etc.

---

## 10. TRAINING GYM MODULES (~/subconscious/)
Active modules imported by the plugin:
| R# | Module | File | Size |
|----|--------|------|------|
| R168 | Self-Critic | self_critic.py | 19KB |
| R169 | ReasoningDiscover | reasoning_discover.py | 26KB |
| R170 | TaskFrontier | task_frontier.py | 19KB |
| R171 | UncertaintyReward | uncertainty_reward.py | 17KB |
| R163 | CurriculumTracker | (in plugin) | - |
| R165 | AdaptiveCompute | adaptive_compute.py | 7KB |
| R177 | FadeMem | (imported) | - |
| R186a | PASTE Executor | (imported) | - |
| R187 | ToolTree | (imported) | - |
| R188 | Empirical MCTS | (imported) | - |
| R193a | DGM Version | (imported) | - |
| R193b | SpeculativeActions | (imported) | - |
| R194 | MemoryConsolidation | (imported) | - |
| R184 | PromptOptimizer | prompt_optimizer.py | 5KB |
| R100 | ArgFeedbackCache | (in plugin SQLite) | - |
| R158 | NextStateSignals | next_state_signals.py | - |
| R160 | TurnCredit | turn_credit.py | - |
| R161 | TrajectoryIntel | trajectory_intel.py | - |
| R172 | ToolAdaptor | tool_adaptor.py | - |
| R174 | ReflectionSynth | reflection_synth.py | - |
| R175 | Curriculum | curriculum.py | - |
| R178 | RecoverySelector | recovery_selector.py | - |
| R181 | InteractionLogger | interaction_logger.py | - |
| R182 | ExecTracer | exec_tracer.py | - |
| R183 | SkillGapDetector | skill_gap_detector.py | - |
| R185 | RewardEvolver | reward_evolver.py | - |
| R186b | ContextBudget | (imported) | - |
| R187b | AdaptationSpeed | adaptation_speed.py | 4KB |
| R188b | ToolDiversity | tool_diversity.py | - |
| R189 | OutputQuality | (imported) | - |

Total: ~30 R-modules wired into plugin
Total subconscious/ .py files: 436

---

## 11. CRON JOBS (17 total)
| Name | Schedule | Purpose |
|------|----------|---------|
| daily-intelligence-scan | 0 7 * * * | GitHub trending + web research |
| X AI News Scanner | 0 9,15,21 * * * | X/Twitter AI news |
| Cortex Dojo | 0 3 * * * | Self-improvement at 3am |
| Jack of All Trades | 0 9,21 * * * | Daily research |
| cortex-consolidation | 0 4 * * * | Memory consolidation |
| brain-cycle-alpha | */2 * * * * | Brain cycle (even min) |
| brain-cycle-bravo | 1-59/2 * * * * | Brain cycle (odd min) |
| brain-cycle-charlie | 1-59/2 * * * * | Brain cycle (odd min) |
| controller-hourly | 0 * * * * | Hourly control check |
| AGI Continuous Loop | */3 * * * * | AGI self-improvement |
| Training Gym Infinite Loop | */15 * * * * | Training exercises |
| training-restart-pickup | every 15m | Restart pickup |
| Cortex Quality Sweep | every 120m | Tip quality sweep |
| Twitter Vision Bridge | every 240m | X content |
| cortex-flywheel-baseline | every 120m | Flywheel baseline |
| sentinel-health-check | every 30m | Health monitoring |
| hermes-daily-backup | 0 3 * * * | Git backup |

---

## 12. BACKUP
Script: `~/hermes-backup.sh`
- Git commit 3 repos + tar.gz
- 7-day retention at `~/.hermes-backups/`
- Cron: 3am daily

---

## 13. KNOWN ISSUES & GAPS

### CRITICAL (apparatus-breaking)
1. **call_log EMPTY** — Was populated (303 rows), now 0. Monthly 3-DB sync has no source data.
2. **Brain cycles alpha/bravo/charlie overlap** — bravo and charlie both on 1-59/2 schedule, redundant
3. **436 subconscious .py files** — many are stale/unused, only ~30 actively wired

### HIGH (data quality)
4. **19,145 experiences never accessed** — P3 injection only fires in agent sessions, daemon doesn't exercise it
5. **396 tips with matches but 0 access** — touch_node was only recently fixed, cold start
6. **Empty tables**: debug_sessions, exploration, entity_cooccurrences, node_entities, reasoning, step_rewards, token_usage — dead code writes to these?
7. **Dual-write overhead**: cortex_compat still writes to SQLite cerebrum_memory.db (13MB) on every operation

### MEDIUM (efficiency)
8. **cortex_migration_log: 18,228 rows** — one-time use, should be truncated
9. **cortex_edges: 369,285 rows** — expensive, is this actually used by anything?
10. **Config duplicate context.engine** — line 39 (hindsight) vs line 230 (lcm), lcm wins but confusing
11. **World model sim rate 0.0%** — simulate() was wired but never triggered in a real session yet
12. **Metacog singleton not shared** — daemon runs its own instance, agent has separate instance

### LOW (cleanup)
13. **5 duplicate tip groups** — JSON-format tips that look same when truncated (6 already deactivated)
14. **cortex_circuit_breakers table** — 38 rows, but also circuit_breaker nodes in cortex_nodes. Dual storage.
15. **tip_consolidation.py** — references old SQLite, may not work with Postgres

---

## 14. DATA FLOWS

```
USER MESSAGE
    │
    ▼
┌────────────────────────────────┐
│ _on_pre_llm_call               │
│ ├─ P1: cortex tips (tool-match) │ ──→ cortex_nodes (tips)
│ ├─ P2: self-improvement tips    │ ──→ cortex_nodes (domain=self_improvement)
│ ├─ P3: high-elo experiences     │ ──→ cortex_nodes (experience, elo>1150)
│ ├─ Metacog injection            │ ──→ intrinsic_metacognition.py
│ ├─ World model build_injection │ ──→ world_model_r27.py
│ └─ Governor (1500ch/12lines)    │
└────────────────────────────────┘
    │
    ▼
LLM RESPONSE → TOOL CALL
    │
    ▼
┌────────────────────────────────┐
│ _on_pre_tool_call              │
│ ├─ World model simulate()      │ ──→ world_model_r27.simulate()
│ ├─ Metacog deferral check      │
│ ├─ tip retrieval + touch_node  │ ──→ cortex_nodes (access_count++)
│ └─ injection tracking          │
└────────────────────────────────┘
    │
    ▼
TOOL EXECUTION
    │
    ▼
┌────────────────────────────────┐
│ _on_post_tool_call             │
│ ├─ 30 R-modules record_outcome │ ──→ various .py modules
│ ├─ cortex_sync (dual-write)    │ ──→ cortex_nodes + cerebrum_memory.db
│ ├─ World model record_outcome  │ ──→ world_model_r27.py
│ ├─ Tip confidence updates      │ ──→ cerebrum_memory.db
│ ├─ Tip maintenance (periodic)  │ ──→ decay, consolidation
│ └─ Hindsight batch sync        │ ──→ (API unreachable, silently fails)
└────────────────────────────────┘
    │
    ▼
LLM RESPONSE TO USER

=== DAEMON FLOWS (24/7) ===

flywheel_loop (15s):
  cortex_nodes tips → heuristic_judge → elo update → cortex_eval_history
  cortex_nodes experiences → experience_judge → elo update
  cortex_nodes low-elo → deactivate

training_gym_loop (20s):
  cortex_nodes → evaluation
  every 5th: metacog cycle → cortex_nodes

perf_monitor_loop (300s):
  cortex_nodes → count/stats
  monthly: call_log → tool_stats resync
  hourly: DELETE stale circuit_breaker nodes
```
