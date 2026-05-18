# 95-Module Integration Reference — May 2026 Session

Complete mapping of subconscious modules to hermes destinations, with verified class names.

## Agent Modules (80 files → agent/)

| File | Classes/Functions | Size |
|------|-------------------|------|
| brain.py | ParallelBrain, BrainRegion, TemporalLobe, PrefrontalCortex, MotorCortex, SquadDispatch | 34KB |
| brain_security.py | BrainSecurity | 23KB |
| cognitive_infrastructure_v2.py | InjectionGovernorV2, CreditAssigner, SessionEndExtractor, ToolIntelligenceRouter, AutoSkillCron | 22KB |
| cognitive_infrastructure_hooks.py | (hooks only, no classes) | 8KB |
| training_gym.py | get_db, get_next_exercise, get_stats, record_attempt (functions only) | 22KB |
| distillation_bridge.py | (functions only) | 38KB |
| llm_judge.py | LLMJudge | 14KB |
| eval_flywheel.py | EloTracker, EvalFlywheel | 30KB |
| cortex_flywheel.py | CortexFlywheel | 16KB |
| cortex_daemon.py | CortexDaemon | 10KB |
| cortex_sentinel.py | HealthCheck, CheckResult, MetricSample | 32KB |
| cortex_unified.py | UnifiedCortex | 13KB |
| capability_registry.py | CapabilityRegistry | 35KB |
| code_intelligence.py | CodeChunk, CodeIntelligenceDB | 23KB |
| confidence_calibrator.py | ConfidenceCalibrator | 4KB |
| anomaly_detector.py | AnomalyDetector | 10KB |
| error_pattern_memory.py | ErrorPatternMemory | 6KB |
| episodic_memory.py | EpisodicBuffer, Operator, Reconciler | 23KB |
| epistemic_guard.py | EpistemicGuard, VerificationPipeline | 20KB |
| uncertainty_estimator.py | (functions only) | 22KB |
| self_critic.py | Reflection, SelfCritic | 19KB |
| self_eval_loop.py | (functions only) | 11KB |
| meta_self_modifier.py | (functions only) | 12KB |
| predictive_router.py | (functions only) | 3KB |
| tool_oracle.py | ToolOracle | 14KB |
| tool_router_v2.py | (functions only) | 6KB |
| tool_sequences.py | (functions only) | 7KB |
| tool_misuse_prevention.py | (functions only) | 6KB |
| agent_scorecard.py | (functions only) | 10KB |
| skill_effectiveness_tracker.py | SkillEffectivenessTracker | 18KB |
| skill_verifier.py | Assertion, AssertionResult, VerificationReport | 19KB |
| skill_scanner.py | (functions only) | 5KB |
| skill_internalizer.py | SkillInternalizer | 4KB |
| memory_auto_pruner.py | prune, get_prunable_count | 8KB |
| memory_consolidation.py | run_consolidation, get_stats | 8KB |
| pruner_integration.py | should_prune, safe_prune | 3KB |
| knowledge_compiler.py | KnowledgeCompiler | 12KB |
| knowledge_synthesis.py | (functions only) | 4KB |
| research_to_distillation.py | (functions only) | 7KB |
| iteration_engine.py | IterationEngine | 28KB |
| flow_graph.py | (functions only) | 18KB |
| sequence_learner.py | SequenceLearner | 13KB |
| step_reward.py | (functions only) | 10KB |
| testing_gym.py | BenchmarkTask, TrajectoryStep, TrajectoryResult | 93KB |
| elo_rating_system.py | EloRatingSystem | 2KB |
| save_finding.py | (functions only) | 2KB |
| token_tracker.py | TokenTracker | 10KB |
| cost_tracker.py | CostTracker | 2KB |
| curiosity_divergence.py | (functions only) | 12KB |
| red_team_hippocampus.py | (functions only) | 29KB |
| phantom_browser.py | TorController, PhantomBrowser, PhantomBrowserSync | 38KB |
| phantom_extractor.py | (functions only) | 33KB |
| twitter_bridge.py | (functions only) | 12KB |
| evey_toolkit.py | BrowserExtractor, KeychainExtractor, NetworkInterceptor | 30KB |
| hermes_harness_v2.py | (functions only) | 4KB |
| adaptive_cortex.py | AdaptiveCortex | 18KB |
| cortex_compat.py | (functions only) | 4KB |
| cortex_compat_shim.py | CortexCursor, CortexConnection | 39KB |
| cortex_dashboard.py | (functions only) | 5KB |
| cortex_dashboard_v2.py | (functions only) | 8KB |
| cortex_quick_stats.py | (functions only) | 4KB |
| cortex_schema_design.py | CortexDB | 31KB |
| cortex_flywheel_v2.py | (functions only) | 4KB |
| error_guard.py | (functions only) | 3KB |
| health_checker.py | HealthChecker | 5KB |
| hermes_dashboard.py | (functions only) | 4KB |
| hermes_cli_resume.py | (functions only) | 5KB |
| vgco_tip_revision.py | (functions only) | 2KB |
| brain_to_toolintel.py | (functions only) | 2KB |
| tool_intelligence_integration.py | (functions only) | 3KB |
| reasoning_analyzer.py | ReasoningAnalyzer | 13KB |

## Tool Modules (14 files → tools/)

| File | Classes/Functions | Size |
|------|-------------------|------|
| hands.py | HermesHands | 10KB |
| context_gauge.py | (functions only) | 7KB |
| plan_executor.py | Step, StepResult, PlanResult | 11KB |
| self_diagnostic.py | (functions only) | 10KB |
| skill_generator.py | (functions only) | 11KB |
| tool_logger.py | (functions only) | 7KB |
| self_manager.py | (functions only) | 10KB |
| health_daemon.py | (functions only) | 5KB |
| manual_triggers.py | (functions only) | 9KB |
| unified_daemon.py | UnifiedDaemon | 8KB |
| autobrowse/tracer.py | ToolTrace, AutobrowseTracer | 9KB |
| autobrowse/analyzer.py | WastePattern, AutobrowseAnalyzer | 11KB |
| autobrowse/graduator.py | AutobrowseGraduator | 10KB |
| autobrowse/synthesizer.py | AutobrowseSynthesizer | 10KB |

## Tip System Modules (10 files → agent/tip_system/)

| File | Classes/Functions | Size |
|------|-------------------|------|
| condition_rewriter.py | (functions only) | 5KB |
| decay_monitor.py | (functions only) | 4KB |
| dedup.py | (functions only) | 3KB |
| evolution.py | (functions only) | 3KB |
| feedback_validator.py | (functions only) | 4KB |
| impact_analyzer.py | (functions only) | 4KB |
| inserter.py | (functions only) | 4KB |
| normalizer.py | TipNormalizer | 11KB |
| quality_scorer.py | (functions only) | 3KB |
| verifier.py | (functions only) | 3KB |

## Critical Integration Points

### run_agent.py injection (line ~2106)
```python
# Subconscious plugin loader
from agent.subconscious_plugin_loader import init_subconscious_plugins
self._subconscious_plugins = init_subconscious_plugins()
```

### cli.py injection (line ~2393)
```python
# Auto-resume handoff detection
self._check_pending_handoff()
```

### cortex_access.py (merged into agent/)
Provides `CortexDB` class with training gym operations using UUID-based `cortex_nodes` schema.

## Class Name Pitfalls

Files where class name ≠ file name:
- `brain.py` → `ParallelBrain` (not `Brain`)
- `training_gym.py` → functions only (no `TrainingGym` class)
- `distillation_bridge.py` → functions only
- `cognitive_infrastructure_hooks.py` → hooks only
- `memory_consolidation.py` → `run_consolidation`, `get_stats`
- `memory_auto_pruner.py` → `prune`, `get_prunable_count`
- `pruner_integration.py` → `should_prune`, `safe_prune`
- `reasoning_analyzer.py` → `ReasoningAnalyzer` (not `ReasoningQualityAnalyzer`)
- `cortex_schema_design.py` → `CortexDB` (not `CortexSchemaDesign`)
- `health_checker.py` → `HealthChecker` (not `HealthCheck`)

## Import Test Pattern

Always use `venv/bin/python`:
```bash
cd ~/hermes-agent && venv/bin/python -c "from agent.MODULE import ClassName"
```

Never retry the same failing import more than 2 times. Use `grep "^class "` to discover actual class names.
