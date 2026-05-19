# Class Name Mappings — May 2026 Integration

File-to-export mapping discovered during the 95-module integration. Use this to avoid `ImportError` on startup.

## Agent Modules (agent/)

| File | Actual Export | Common Wrong Assumption |
|------|-------------|------------------------|
| `context_compressor.py` | `AdaptiveCompressor` | `ContextCompressor` |
| `llm_judge.py` | `run_llm_eval_sweep`, `call_ensemble_judge` | `LLMJudge` class |
| `cortex_access.py` | `CortexDB`, `cortex_cursor` | — |
| `cortex_flywheel.py` | `heuristic_judge`, `run_consolidation` | — |
| `training_gym.py` | functions only (no class) | `TrainingGym` |
| `brain.py` | `ParallelBrain` | `Brain` |
| `subconscious_plugin_loader.py` | `init_subconscious_plugins`, `SubconsciousPlugin` | — |

## Tool Modules (tools/)

| File | Actual Export | Registry Name |
|------|-------------|---------------|
| `hands.py` | `HermesHands` | not yet registered |
| `self_diagnostic.py` | `self_diagnostic` | `self_diagnostic` |
| `skill_generator.py` | `generate_skill` | `generate_skill` |
| `plan_executor.py` | `execute_plan` | `execute_plan` |
| `context_pressure_gauge.py` | `ContextPressureGauge` | — |
| `health_daemon.py` | `HealthDaemon` | — |
| `unified_daemon.py` | `UnifiedDaemon` | — |

## Tip System (agent/tip_system/)

| File | Actual Export |
|------|-------------|
| `normalizer.py` | `TipNormalizer` |
| `verifier.py` | `TipVerifier` |
| `quality_scorer.py` | `TipQualityScorer` |
| `feedback_validator.py` | `TipFeedbackValidator` |
| `decay_monitor.py` | `TipDecayMonitor` |
| `evolution.py` | `TipEvolution` |
| `inserter.py` | `TipInserter` |
| `dedup.py` | `TipDedup` |
| `condition_rewriter.py` | `TipConditionRewriter` |
| `impact_analyzer.py` | `TipImpactAnalyzer` |

## Autobrowse (tools/autobrowse/)

| File | Actual Export |
|------|-------------|
| `tracer.py` | `AutobrowseTracer` |
| `analyzer.py` | `AutobrowseAnalyzer` |
| `synthesizer.py` | `AutobrowseSynthesizer` |
| `graduator.py` | `AutobrowseGraduator` |

## Critical Fix Applied

`run_agent.py` line 159:
```python
# BEFORE (broken):
from agent.context_compressor import ContextCompressor

# AFTER (fixed):
from agent.context_compressor import AdaptiveCompressor as ContextCompressor
```

This alias preserves the existing variable name `ContextCompressor` throughout `run_agent.py` while importing the actual class `AdaptiveCompressor`.
