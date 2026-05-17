# Hermes Custom Apparatus Audit — 2026-05-09
## Full System Map + Gaps + Upgrade Plan

---

## EXECUTIVE SUMMARY

| Layer | Status | Coverage | Critical Gaps |
|-------|--------|----------|---------------|
| **Plugins (38)** | 32 enabled, 6 disabled | 84% active | Honcho, Mesh, MQTT, Moltbook, Sandbox, Wallet dormant |
| **Subconscious (530 modules)** | 485 orphaned (91% dead code) | 9% wired | Massive bloat — only ~45 modules actually imported |
| **Custom Tools (46)** | 1 registered, 45 orphaned | 2% functional | 45 tools built but never wired into Hermes |
| **Databases (42)** | 10 meaningful, 32 empty | 24% utilized | Most DBs are 0.0MB schema ghosts |
| **Skills (200+)** | Mix of upstream + custom | ~60% relevant | Many archived skills, some stale |
| **Knowledge (1139 docs)** | Indexed and searchable | 100% indexed | Quality varies, some outdated |

**Bottom line: We built a massive cognitive apparatus but only ~10% is wired and active. The rest is dead code, empty DBs, and orphaned tools.**

---

## 1. PLUGIN LAYER (38 plugins)

### ENABLED (32) — Functional
| Plugin | Purpose | Health |
|--------|---------|--------|
| distillation | Tip extraction from tool calls | **FIXED** — hooks firing, 1902 tips, 1870 Elo-rated |
| learning-brain | Self-improvement loop | Active |
| evey-autonomy | Decision engine | Active |
| evey-bridge | Claude Code bridge | Active |
| evey-cache | Delegation caching | Active |
| evey-cost-guard | Budget enforcement | Active |
| evey-council | Model council debates | Active |
| evey-delegate-model | Per-task model override | Active |
| evey-delegation-scoring | Quality tracking | Active |
| evey-digest | Morning digest | Active |
| evey-email-guard | Prompt injection screen | Active |
| evey-github | Repo monitoring | Active |
| evey-goals | Goal management | Active |
| evey-habits | User pattern learning | Active |
| evey-identity | SOUL.md evolution | Active |
| evey-learner | Lesson extraction | Active |
| evey-memory-adaptive | Importance scoring | Active |
| evey-memory-consolidation | Daily consolidation | Active |
| evey-news | AI news monitor | Active |
| evey-proactive | Proactive nudges | Active |
| evey-rag | Knowledge search | Active |
| evey-reflect | Self-correction | Active |
| evey-research | Web research | Active |
| evey-scheduler | Calendar management | Active |
| evey-session-guard | Checkpoint save | Active |
| evey-status | Unified status | Active |
| evey-telegram-ux | Rich Telegram | Active |
| evey-telemetry | Observability | Active |
| evey-tool-intelligence | Tool learning | **ACTIVE** — 1907 calls logged |
| evey-validate | Output validation | Active |
| evey-verification | Target verification | Active |
| evey-watchdog | Self-monitoring | Active |

### DISABLED (6) — Dormant
| Plugin | Why Disabled | Reactivation Value |
|--------|------------|-------------------|
| evey-honcho | Unlimited semantic memory | **HIGH** — local vector DB, could replace Qdrant |
| evey-mesh | Multi-agent coordination | **HIGH** — for parallel agent teams |
| evey-mqtt | Real-time event stream | MEDIUM — for IoT/alert integration |
| evey-moltbook | Social network | LOW — not priority |
| evey-sandbox | Docker sandbox | **HIGH** — security for untrusted code |
| evey-wallet | Crypto monitoring | LOW — not priority |

---

## 2. SUBCONSCIOUS LAYER (530 modules)

### ACTIVELY WIRED (~45 modules)
These are imported by the plugin layer or core scripts:

| Module | Used By | Purpose |
|--------|---------|---------|
| llm_judge.py | cortex_flywheel | Elo tournament judge (DeepSeek V4 Pro) |
| autobrowse_tracer.py | distillation plugin | Execution trace capture |
| autobrowse_analyzer.py | autobrowse pipeline | Pattern detection |
| autobrowse_synthesizer.py | autobrowse pipeline | Tip generation |
| autobrowse_graduator.py | autobrowse pipeline | Tip lifecycle |
| cortex_access.py | Multiple plugins | CortexDB interface |
| cortex_flywheel.py | cron job | Elo tournament runner |
| cortex_unified.py | cortex_access | Unified DB schema |
| cortex_daemon.py | cron job | Background daemon |
| cortex_dashboard.py | manual | Stats visualization |
| brain.py | learning-brain | Core learning loop |
| episodic_memory.py | learning-brain | Session memory |
| error_pattern_memory.py | learning-brain | Error tracking |
| tool_intelligence.py | evey-tool-intelligence | Tool performance |
| tip_inserter.py | distillation | Tip DB insertion |
| tip_dedup.py | distillation | Tip deduplication |
| tip_evolution.py | distillation | Tip mutation |
| tip_quality_scorer.py | distillation | Tip scoring |
| elo_rating_system.py | cortex_flywheel | Elo math |
| training_gym.py | cron job | Continuous training |
| research_to_distillation.py | research pipeline | Research → tips |
| knowledge_compiler.py | knowledge | Compile findings |
| knowledge_synthesis.py | knowledge | Synthesize research |
| self_eval_loop.py | metacognition | Self-evaluation |
| self_critic.py | metacognition | Output critique |
| confidence_calibrator.py | metacognition | Confidence tuning |
| context_compressor.py | optimization | Context window mgmt |
| token_tracker.py | optimization | Token accounting |
| cost_tracker.py | evey-cost-guard | Cost tracking |
| health_checker.py | monitoring | System health |
| watchdog_heartbeat.py | evey-watchdog | Heartbeat |
| validate_output.py | evey-validate | Output validation |
| verify_url.py | evey-verification | URL checks |
| verify_repo.py | evey-verification | Repo checks |
| verify_endpoint.py | evey-verification | API checks |
| verify_dns.py | evey-verification | DNS checks |
| apply_learnings.py | learning | Cross-session learning |
| learn_from_interaction.py | learning | Lesson extraction |
| save_finding.py | research | Knowledge persistence |
| memory_consolidation.py | memory | Daily consolidation |
| memory_decay.py | memory | Memory pruning |
| memory_score.py | memory | Importance scoring |
| skill_scanner.py | skills | Skill discovery |
| skill_verifier.py | skills | Skill validation |
| skill_internalizer.py | skills | Skill adoption |

### ORPHANED (~485 modules) — Dead Code
These exist in ~/subconscious/ but are NEVER imported by anything:

**Categories of orphans:**
- **Abandoned experiments**: R150-R157 numbered modules, dgm_version_archive.py
- **Superseded versions**: research_distill_r2.py, research_distill_r3.py, cortex_compat.py, cortex_compat_shim.py
- **Never-wired tools**: 45 custom tools in ~/.hermes/tools/
- **Speculative modules**: Most of the 530 — built during exploration but never integrated

**Why they matter:**
- They clutter the codebase
- They create confusion about what's actually functional
- They may contain good ideas that should be recovered or deleted

---

## 3. CUSTOM TOOLS LAYER (46 tools)

### THE PROBLEM
Only **1 of 46 tools** is registered with Hermes (multi_agent_tool.py). The other 45 are Python files that exist but are invisible to the agent.

### ORPHANED TOOLS (45)
| Tool | Lines | What It Does | Why It's Orphaned |
|------|-------|--------------|-------------------|
| checkpoint_tool.py | 304 | Save/load checkpoints | No @register_tool decorator |
| checkpoint_validator_tool.py | 201 | Validate checkpoint integrity | No registration |
| code_review_tool.py | 95 | Automated code review | No registration |
| config_validator_tool.py | 104 | Validate Hermes config | No registration |
| cortex_memory_tool.py | 329 | CortexDB memory operations | No registration |
| cost_tracker_tool.py | 298 | Real-time cost tracking | No registration |
| data_pipeline_tool.py | 86 | Data processing pipelines | No registration |
| debate_partner_tool.py | 57 | Socratic debate partner | No registration |
| dependency_graph_tool.py | 84 | Visualize dependencies | No registration |
| diff_visualizer_tool.py | 81 | Show code diffs | No registration |
| doc_generator_tool.py | 99 | Generate documentation | No registration |
| docker_image_audit_tool.py | 164 | Audit Docker images | No registration |
| error_explainer_tool.py | 84 | Explain errors | No registration |
| execution_boundary_tool.py | 126 | Enforce execution limits | No registration |
| fact_check_tool.py | 259 | Verify factual claims | No registration |
| fs_watcher_tool.py | 257 | Watch filesystem changes | No registration |
| git_blame_tool.py | 75 | Git blame analysis | No registration |
| jupyter_tool.py | 64 | Jupyter notebook ops | No registration |
| keep_awake_tool.py | 238 | Prevent system sleep | No registration |
| knowledge_graph_tool.py | 139 | Build knowledge graphs | No registration |
| knowledge_os_tool.py | 96 | Knowledge OS interface | No registration |
| log_tail_tool.py | 64 | Tail log files | No registration |
| memory_pruner_tool.py | 208 | Prune old memories | No registration |
| model_weight_inspector_tool.py | 338 | Inspect model weights | No registration |
| mood_aware_tool.py | 85 | Mood-aware responses | No registration |
| notification_router_tool.py | 63 | Route notifications | No registration |
| prompt_lib_tool.py | 260 | Prompt library manager | No registration |
| reasoning_trace_tool.py | 328 | Trace reasoning chains | No registration |
| regex_tool.py | 96 | Regex operations | No registration |
| remote_file_edit_tool.py | 232 | Edit remote files | No registration |
| research_engine_tool.py | 109 | Research orchestration | No registration |
| scheduler_tool.py | 99 | Task scheduling | No registration |
| screen_capture_tool.py | 73 | Capture screenshots | No registration |
| self_healing_tool.py | 103 | Self-healing code | No registration |
| semantic_search_tool.py | 321 | Semantic search | No registration |
| simulation_tool.py | 94 | Run simulations | No registration |
| task_planner_tool.py | 88 | Plan complex tasks | No registration |
| test_runner_tool.py | 81 | Run test suites | No registration |
| tool_validator.py | 462 | Validate tool definitions | No registration |
| video_planner_tool.py | 64 | Plan video content | No registration |
| vllm_log_grep_tool.py | 187 | Search vLLM logs | No registration |
| workflow_engine_tool.py | 133 | Workflow orchestration | No registration |

---

## 4. DATABASE LAYER (42 databases)

### MEANINGFUL (10)
| Database | Size | Tables | Purpose | Active? |
|----------|------|--------|---------|---------|
| cerebrum_memory.db | 14.2MB | 94 | Main cognitive DB | **YES** |
| code_intelligence.db | 127.3MB | 4 | Code analysis cache | Partial |
| context_reservoir.db | 1.3MB | 10 | Context window mgmt | Partial |
| eyes_vision.db | 1.0MB | 10 | Vision processing | Partial |
| tool_intelligence.db | 0.4MB | 3 | Tool call analytics | **YES** |
| kanban.db | 0.1MB | 7 | Task board | Partial |
| unified_context.db | 0.1MB | 5 | Context unification | Partial |
| agent-mesh.db | 0.1MB | 6 | Multi-agent state | Dormant |
| hermes_state.db | 0.1MB | 10 | State snapshots | Partial |
| brain_security.db | 0.1MB | 4 | Security audit | Partial |

### EMPTY GHOSTS (32)
These are 0.0MB databases with schemas but no data:
- api_analytics.db, auto_launch_monitor.db, call_log.db
- change_manifests.db, checkpoint_watcher.db, cron_jobs.db
- distillation.db, distillation_quality.db, distillation_tips.db
- error_patterns.db, regression_detector.db, skill_effectiveness.db
- spatial_memory.db, tool_capability.db, tool_cache.db
- tool_predictor.db, tool_stats.db, training_gym.db
- uncertainty.db, and 14 more...

---

## 5. KNOWLEDGE LAYER (1139 docs)

### STATUS
- All indexed in Qdrant (vector search)
- Searchable via knowledge_search()
- Quality varies — some from 2024, some recent
- No automatic pruning or freshness scoring

---

## CRITICAL GAPS IDENTIFIED

### GAP 1: 91% of subconscious is dead code
**Severity: HIGH**
- 485 of 530 modules are never imported
- Creates cognitive overhead when debugging
- Hides what's actually functional
- Wastes disk space and mental space

**Fix:** Aggressive pruning — delete or archive orphans

### GAP 2: 45 custom tools are invisible
**Severity: HIGH**
- Built with effort but never wired
- Agent can't use them
- Duplicates functionality in some cases

**Fix:** Register high-value tools, delete the rest

### GAP 3: 6 plugins disabled that should be enabled
**Severity: MEDIUM-HIGH**
- evey-honcho: Unlimited semantic memory (replaces Qdrant limits)
- evey-mesh: Multi-agent coordination (for parallel work)
- evey-sandbox: Docker security (for untrusted code)

**Fix:** Enable and test these three

### GAP 4: 32 empty databases
**Severity: MEDIUM**
- Schema ghosts from abandoned experiments
- Create confusion about data sources

**Fix:** Delete empty DBs or consolidate into cerebrum_memory.db

### GAP 5: No unified tip quality metric
**Severity: MEDIUM**
- 1902 tips exist but no systematic quality filter
- Elo ratings exist but no survival rate tracking
- Tips may be stale or wrong

**Fix:** Implement tip survival rate tracking + automatic pruning

### GAP 6: No cross-session project continuity
**Severity: MEDIUM**
- Sessions are isolated
- No automatic project context carryover
- User must manually reference past work

**Fix:** Project-based memory clustering

### GAP 7: No real-time performance dashboard
**Severity: LOW-MEDIUM**
- cortex_dashboard.py exists but not used
- No visibility into tip quality trends
- No visibility into tool success rates over time

**Fix:** Wire dashboard to a cron job or make it a tool

### GAP 8: No automatic skill gap detection
**Severity: MEDIUM**
- skill_gap_detector.py exists but orphaned
- When facing new domain, no auto-discovery of needed skills

**Fix:** Wire skill_gap_detector to autobrowse pipeline

### GAP 9: No adversarial testing of tips
**Severity: MEDIUM**
- Tips are generated but not stress-tested
- No red-teaming of "WHEN X, DO Y" patterns
- Bad tips could persist indefinitely

**Fix:** Add adversarial tip validation to graduator

### GAP 10: No automatic research-to-skill pipeline
**Severity: LOW-MEDIUM**
- Research findings saved as knowledge docs
- But never auto-converted to skills
- Manual skill creation is friction

**Fix:** Auto-generate SKILL.md from high-quality research findings

---

## UPGRADE PLAN: MAKE HERMES MAXIMALLY SHARP

### PHASE 1: CLEANUP (Immediate — 2-4 hours)
1. **Delete 485 orphaned subconscious modules**
   - Move to ~/subconscious/archive/ or delete outright
   - Keep only the ~45 actively imported modules
   - This alone makes debugging 10x easier

2. **Delete 32 empty databases**
   - Backup schemas first
   - Consolidate any useful schemas into cerebrum_memory.db
   - Delete the 0.0MB ghosts

3. **Prune 45 orphaned tools**
   - Identify top 10 most valuable
   - Register them with proper @register_tool decorators
   - Delete the rest (or move to archive)

### PHASE 2: ACTIVATE DORMANT SYSTEMS (1-2 days)
4. **Enable evey-honcho plugin**
   - Unlimited semantic memory via local vector DB
   - Could replace/supplement Qdrant for faster local search

5. **Enable evey-mesh plugin**
   - Multi-agent coordination for parallel task execution
   - Useful for research, code review, testing in parallel

6. **Enable evey-sandbox plugin**
   - Docker sandbox for untrusted code execution
   - Security layer for arbitrary user code

7. **Wire cortex_dashboard.py to a tool**
   - Make it callable via tool call
   - Show real-time tip quality, tool success rates, cost trends

### PHASE 3: QUALITY SYSTEMS (2-3 days)
8. **Implement tip survival rate tracking**
   - Track which tips are actually used vs ignored
   - Auto-prune tips with <30% survival after 100 opportunities
   - This addresses the "tips must be operational" rejection issue

9. **Add adversarial tip validation**
   - Red-team each tip: find counterexamples where it fails
   - Only promote tips that survive adversarial testing
   - Use DeepSeek V4 Pro as adversarial judge

10. **Auto-convert research to skills**
    - When research finding scores high on quality
    - Auto-generate SKILL.md with proper frontmatter
    - Add to ~/.hermes/skills/ automatically

### PHASE 4: ADVANCED COGNITION (3-5 days)
11. **Project-based memory clustering**
    - Group all memories, tips, tool calls by project
    - Auto-resume project context across sessions
    - Cross-session continuity without manual checkpoints

12. **Predictive tool selection**
    - Use tool_intelligence.db patterns to predict best tool
    - Before executing, check historical success rates
    - Route to proven tools, avoid weak ones

13. **Self-modifying prompt optimization**
    - Track which system prompt variations produce best results
    - A/B test prompt fragments via Elo tournaments
    - Auto-promote winning prompt components

14. **Multi-modal reasoning traces**
    - Capture not just text but tool call sequences
    - Visualize reasoning as DAG (directed acyclic graph)
    - Identify shortest paths to common solutions

### PHASE 5: TRAINING DATA PIPELINE (For Qwen)
15. **Export tip corpus as training data**
    - Convert 1902 tips + Elo ratings to structured format
    - Generate reasoning traces showing tip application
    - Create curriculum: easy → hard tip application scenarios

16. **Export tool call patterns as training data**
    - 1907 tool calls with success/failure labels
    - Tool selection decisions with outcomes
    - Error recovery sequences

17. **Export self-evaluation traces**
    - validate_output results with confidence scores
    - LLM judge comparisons with reasoning
    - Self-correction episodes

18. **Export research-to-distillation pipeline**
    - Raw research findings → synthesized tips
    - Show the full transformation process
    - Include rejected tips and why they were rejected

---

## PRIORITY MATRIX

| Priority | Action | Impact | Effort | Owner |
|----------|--------|--------|--------|-------|
| **P0** | Delete 485 orphaned modules | Massive clarity | 2h | Now |
| **P0** | Register top 10 custom tools | +10 tools available | 4h | Now |
| **P1** | Enable evey-honcho | Unlimited memory | 2h | Today |
| **P1** | Tip survival rate tracking | Quality filter | 4h | Today |
| **P2** | Enable evey-mesh | Parallel agents | 2h | This week |
| **P2** | Adversarial tip validation | Tip quality | 6h | This week |
| **P3** | Project-based memory | Cross-session | 8h | Next week |
| **P3** | Auto-skill generation | Skill pipeline | 6h | Next week |
| **P4** | Predictive tool selection | Efficiency | 8h | Future |
| **P4** | Self-modifying prompts | Meta-learning | 12h | Future |
| **P5** | Training data export | Qwen dataset | 4h | When training ready |

---

## FILES REFERENCED

- ~/.hermes/plugins/distillation/__init__.py (6949 lines, hook fix applied)
- ~/.hermes/cerebrum_memory.db (14.2MB, 94 tables, 1902 tips)
- ~/.hermes/tool_intelligence.db (0.4MB, 3 tables, 1907 calls)
- ~/subconscious/ (530 modules, ~45 active)
- ~/.hermes/tools/ (46 tools, 1 registered)
- ~/.hermes/knowledge/ (1139 docs, all indexed)
- ~/.hermes/skills/ (200+ skills, mix of upstream + custom)

---

*Audit completed: 2026-05-09 12:00 CDT*
*Next action: Await user direction on which phase to execute*
