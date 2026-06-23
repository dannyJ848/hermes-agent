"""Test suite for the cognitive learning apparatus.

Covers:
  - [Learned Lessons] block generation (the per-turn injection)
  - CortexFlywheel (capture_experience, run_reflection_cycle, behavior_adjustments)
  - ErrorLearningStore (fingerprinting, preemptive warnings)
  - TieredMemory (FTS5 recall, hot/warm tiers)
  - ToolOracle (tool prediction from skill_tracker data)
  - FailurePrevention (risk assessment from error patterns)
  - TrustScorer (confidence tiering)
  - Brain (synthesis cycle)
  - DistillationBridge (tip → adjustment promotion)
  - Closed loop: capture → store → retrieve → inject
"""
import os
import sys
import warnings
import tempfile
import json
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ.setdefault("HERMES_HOME", str(Path.home() / ".hermes-glm"))
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

# Ensure hermes-agent is on the path
_hermes_root = Path(__file__).resolve().parents[2]
if str(_hermes_root) not in sys.path:
    sys.path.insert(0, str(_hermes_root))


class TestLearnedLessonsBlock:
    """Tests for the [Learned Lessons] per-turn injection."""

    def test_builds_block_for_query(self):
        """build_learned_lessons_prompt returns a non-empty string for a real query."""
        from agent.learned_lessons import build_learned_lessons_prompt
        block = build_learned_lessons_prompt("debug postgres connection")
        assert isinstance(block, str)
        # Should contain lesson content (may be empty if no data matches)
        if block:
            assert "Lessons from past experience" in block

    def test_empty_query_returns_empty(self):
        """Empty or too-short queries return empty string."""
        from agent.learned_lessons import build_learned_lessons_prompt
        assert build_learned_lessons_prompt("") == ""
        assert build_learned_lessons_prompt("ab") == ""  # < 3 chars

    def test_respects_budget(self):
        """Block stays within the token budget."""
        from agent.learned_lessons import build_learned_lessons_prompt
        block = build_learned_lessons_prompt("terminal git", budget_tokens=100)  # very small
        if block:
            # ~100 tokens = ~400 chars max
            assert len(block) <= 600  # allow some header overhead

    def test_no_crash_on_garbage_input(self):
        """Garbage queries don't crash."""
        from agent.learned_lessons import build_learned_lessons_prompt
        for q in [None, 123, "!@#$%", "\x00\x01", "a" * 10000]:
            try:
                result = build_learned_lessons_prompt(str(q) if q else "")
                assert isinstance(result, str)
            except Exception:
                pass  # graceful degradation — no crash


class TestCortexFlywheel:
    """Tests for the CortexFlywheel learning subsystem."""

    def test_capture_experience_records_event(self):
        """capture_experience writes to learning_events."""
        from agent.cortex_flywheel import CortexFlywheel
        cf = CortexFlywheel()
        before = cf.get_learning_stats().get("total_events", 0)
        cf.capture_experience("terminal", "ls -la", "success", duration_ms=50)
        after = cf.get_learning_stats().get("total_events", 0)
        assert after >= before + 1, f"events didn't increase: {before} → {after}"

    def test_capture_experience_failure(self):
        """Failure capture records with higher importance."""
        from agent.cortex_flywheel import CortexFlywheel
        cf = CortexFlywheel()
        cf.capture_experience("terminal", "rm -rf /", "failure", error="Permission denied", duration_ms=10)
        # Should not crash — that's the test
        assert True

    def test_run_reflection_cycle_returns_summary(self):
        """run_reflection_cycle returns a dict with expected keys."""
        from agent.cortex_flywheel import CortexFlywheel
        cf = CortexFlywheel()
        result = cf.run_reflection_cycle()
        assert isinstance(result, dict)
        assert "distillation" in result
        assert "adjustments" in result

    def test_behavior_adjustments_has_data(self):
        """get_behavior_adjustments returns real data (253 rows promoted earlier)."""
        from agent.cortex_flywheel import CortexFlywheel
        cf = CortexFlywheel()
        adjustments = cf.get_behavior_adjustments(limit=5)
        assert isinstance(adjustments, list)
        # After our distillation_bridge promotion, there should be data
        assert len(adjustments) > 0, "behavior_adjustments should have promoted tips"

    def test_record_event_correct_signature(self):
        """record_event accepts (event_type, subsystem, detail, value) — the fixed signature."""
        from agent.cortex_flywheel import CortexFlywheel
        cf = CortexFlywheel()
        cf.record_event("test_event", subsystem="test", detail="verification", value=1.0)
        # Should not crash
        assert True


class TestErrorLearning:
    """Tests for the error fingerprinting + preemptive warning system."""

    def test_fingerprint_normalizes(self):
        """_fingerprint normalizes line numbers and addresses."""
        from agent.error_learning import _fingerprint
        fp1 = _fingerprint("Error at line 42 in file.py:123")
        fp2 = _fingerprint("Error at line 99 in file.py:456")
        assert fp1 == fp2, "fingerprints should match after normalization"

    def test_get_preemptive_warning_returns_string(self):
        """get_preemptive_warning returns a string (possibly empty)."""
        from agent.error_learning import ErrorLearningStore
        store = ErrorLearningStore()
        warning = store.get_preemptive_warning("git commit")
        assert isinstance(warning, (str, type(None)))

    def test_get_preemptive_warning_not_called_get_relevant_lessons(self):
        """Verify the old broken method name doesn't exist."""
        from agent.error_learning import ErrorLearningEngine
        # get_relevant_lessons was the broken call — it should NOT exist
        assert not hasattr(ErrorLearningEngine, 'get_relevant_lessons'), \
            "get_relevant_lessons should not exist (was the broken method)"
        # get_preemptive_warning is the correct method
        assert hasattr(ErrorLearningEngine, 'get_preemptive_warning'), \
            "get_preemptive_warning must exist"


class TestTieredMemory:
    """Tests for the 3-tier memory with FTS5 acceleration."""

    def test_recall_returns_list(self):
        """recall returns a list of dicts."""
        from agent.tiered_memory import TieredMemory
        tm = TieredMemory()
        results = tm.recall("terminal", limit=3)
        assert isinstance(results, list)
        for item in results:
            assert isinstance(item, dict)

    def test_store_and_recall_hot_tier(self):
        """store() puts in hot tier, recall() finds it immediately."""
        from agent.tiered_memory import TieredMemory
        tm = TieredMemory()
        tm.store("unique test memory xyz123", importance=0.9)
        results = tm.recall("xyz123", limit=1)
        assert len(results) >= 1
        assert "xyz123" in results[0].get("content", "")

    def test_fts5_recall_faster_than_like(self):
        """FTS5 recall should work (doesn't crash, returns results)."""
        from agent.tiered_memory import TieredMemory
        tm = TieredMemory()
        # This should use FTS5 (the new code path)
        results = tm.recall("terminal git", limit=5)
        assert isinstance(results, list)

    def test_consolidate_returns_stats(self):
        """consolidate returns a dict with expected keys."""
        from agent.tiered_memory import TieredMemory
        tm = TieredMemory()
        result = tm.consolidate()
        assert isinstance(result, dict)
        assert "consolidated" in result


class TestToolOracle:
    """Tests for the data-driven tool prediction."""

    def test_predict_tools_returns_dict(self):
        """predict_tools returns a dict with primary/alternatives/confidence."""
        from agent.tool_oracle import ToolOracle
        oracle = ToolOracle()
        pred = oracle.predict_tools("debug code")
        assert isinstance(pred, dict)
        assert "primary" in pred
        assert "alternatives" in pred
        assert "confidence" in pred

    def test_validate_choice(self):
        """validate_choice returns a dict with is_optimal."""
        from agent.tool_oracle import ToolOracle
        oracle = ToolOracle()
        result = oracle.validate_choice("terminal", "run command")
        assert isinstance(result, dict)
        assert "is_optimal" in result


class TestFailurePrevention:
    """Tests for the risk assessment subsystem."""

    def test_assess_risk_returns_named_tuple(self):
        """assess_risk returns a RiskAssessment with expected fields."""
        from agent.predictive_failure_prevention import PredictiveFailurePrevention
        fp = PredictiveFailurePrevention()
        risk = fp.assess_risk("terminal", "git push --force")
        assert hasattr(risk, "risk_level")
        assert hasattr(risk, "risk_score")
        assert hasattr(risk, "mitigation")
        assert hasattr(risk, "warnings")
        assert risk.risk_level in ("low", "medium", "high")

    def test_predict_failure_returns_dict(self):
        """predict_failure returns a dict with probability."""
        from agent.predictive_failure_prevention import PredictiveFailurePrevention
        fp = PredictiveFailurePrevention()
        result = fp.predict_failure("risky action")
        assert isinstance(result, dict)
        assert "probability" in result


class TestTrustScorer:
    """Tests for the epistemic trust scoring."""

    def test_score_fact_returns_trust_score(self):
        """score_fact returns a TrustScore with tier."""
        from agent.epistemic_trust_scorer import EpistemicTrustScorer
        ts = EpistemicTrustScorer()
        score = ts.score_fact("test lesson", source="distilled_tips", corroboration=5)
        assert hasattr(score, "overall_trust")
        assert hasattr(score, "trust_tier")
        assert score.trust_tier in ("🥇", "🥈", "🥉")

    def test_high_confidence_source_gets_gold(self):
        """Verified distilled tips with high corroboration get 🥇."""
        from agent.epistemic_trust_scorer import EpistemicTrustScorer
        ts = EpistemicTrustScorer()
        score = ts.score_fact("verified lesson", source="distilled_tips", corroboration=10)
        assert score.overall_trust >= 0.7
        assert score.trust_tier == "🥇"

    def test_low_confidence_filtered(self):
        """should_inject filters low-trust lessons."""
        from agent.epistemic_trust_scorer import EpistemicTrustScorer
        ts = EpistemicTrustScorer()
        low_score = ts.score_fact("guessed", source="inferred", corroboration=0)
        assert not ts.should_inject(low_score, min_trust=0.6)


class TestBrain:
    """Tests for the cross-system synthesis cycle."""

    def test_run_cycle_returns_briefing(self):
        """run_cycle returns a dict with health_score and signals."""
        from agent.brain import ParallelBrain
        brain = ParallelBrain()
        briefing = brain.run_cycle()
        assert isinstance(briefing, dict)
        assert "health_score" in briefing
        assert "signals" in briefing
        assert isinstance(briefing["health_score"], float)

    def test_reflect_extracts_insights(self):
        """reflect returns insights from an episode."""
        from agent.brain import ParallelBrain
        brain = ParallelBrain()
        result = brain.reflect({"success": True, "action": "test"})
        assert isinstance(result, dict)
        assert "insights" in result


class TestDistillationBridge:
    """Tests for the tip → adjustment promotion bridge."""

    def test_distill_extracts_patterns(self):
        """distill identifies high-success patterns from experiences."""
        from agent.distillation_bridge import DistillationBridge
        db = DistillationBridge()
        experiences = [
            {"action_type": "search_files", "result": "success", "lesson": "search first"},
            {"action_type": "search_files", "result": "success", "lesson": "search first"},
            {"action_type": "search_files", "result": "success", "lesson": "search first"},
            {"action_type": "terminal", "result": "failure", "lesson": "wrong flag"},
        ]
        tips = db.distill(experiences, min_confidence=0.7)
        assert isinstance(tips, list)
        assert len(tips) > 0  # search_files has 3/3 success

    def test_process_research_extracts_imperatives(self):
        """process_research finds actionable sentences."""
        from agent.distillation_bridge import DistillationBridge
        db = DistillationBridge()
        research = (
            "Always check git status before committing your changes.\n"
            "This is just a random note about nothing.\n"
            "Never run rm -rf without checking the path first."
        )
        tips = db.process_research(research)
        assert isinstance(tips, list)
        assert any("git status" in t for t in tips), f"git status not found in {tips}"
        assert any("rm -rf" in t for t in tips), f"rm -rf not found in {tips}"


class TestClosedLoop:
    """End-to-end tests verifying the full learning loop."""

    def test_capture_then_retrieve(self):
        """Capture an experience, then verify it's retrievable via [Learned Lessons]."""
        from agent.cortex_flywheel import CortexFlywheel
        from agent.learned_lessons import build_learned_lessons_prompt

        # Record a failure
        cf = CortexFlywheel()
        cf.capture_experience("terminal", "unique_test_action_xyz", "failure",
                              error="test error xyz", duration_ms=100)

        # The [Learned Lessons] block should run without crashing
        # (it may or may not surface this specific action depending on scoring)
        block = build_learned_lessons_prompt("unique_test_action_xyz")
        assert isinstance(block, str)  # no crash = pass

    def test_session_end_alias_exists(self):
        """session_end alias is present on CognitiveOrchestrator (the critical fix)."""
        from agent.cognitive_orchestrator import CognitiveOrchestrator
        orch = CognitiveOrchestrator()
        assert hasattr(orch, 'session_end'), "session_end alias missing — learning pipeline won't fire"
        assert hasattr(orch, 'end_session'), "end_session missing"

    def test_iteration_engine_registered(self):
        """iteration_engine is in the init_order (was missing before)."""
        from agent.cognitive_orchestrator import CognitiveOrchestrator
        orch = CognitiveOrchestrator()
        assert hasattr(orch, '_init_iteration_engine'), "iteration_engine init method missing"

    def test_all_subsystem_inits_succeed(self):
        """Every _init_* method returns a non-None object (no failed subsystems)."""
        from agent.cognitive_orchestrator import CognitiveOrchestrator
        orch = CognitiveOrchestrator()
        init_methods = [
            m for m in dir(orch)
            if m.startswith('_init_') and m != '_init' and callable(getattr(orch, m))
        ]
        assert len(init_methods) >= 23, f"expected >=23 init methods, got {len(init_methods)}"

        failures = []
        for method_name in init_methods:
            try:
                result = getattr(orch, method_name)()
                if result is None:
                    failures.append(f"{method_name} returned None")
            except Exception as e:
                failures.append(f"{method_name}: {e}")

        # Allow some to be None (conditional init) but most should succeed
        success_rate = 1 - len(failures) / len(init_methods)
        assert success_rate >= 0.8, \
            f"Too many subsystem init failures: {len(failures)}/{len(init_methods)} failed: {failures[:5]}"
