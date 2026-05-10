"""R165: Health checker - periodic health checks for integrated modules."""
import threading, time
from typing import Dict, List

_INSTANCES: Dict[str, "HealthChecker"] = {}
_LOCK = threading.Lock()

def get_instance(session_id: str = "default") -> "HealthChecker":
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = HealthChecker(session_id)
        return _INSTANCES[session_id]

class HealthChecker:
    MODULES_TO_CHECK = [
        "stack_trace_analyzer", "code_pattern_matcher", "dependency_graph_builder", "code_diff_analyzer", "type_flow_tracker",
        "test_coverage_estimator", "code_execution_sandbox", "api_contract_validator", "code_complexity_scorer", "code_generation_validator",
        "module_orchestrator", "cascade_coordinator", "state_machine_engine", "event_bus", "retry_policy_engine",
        "circuit_breaker_manager", "load_balancer", "health_checker", "error_aggregator", "feedback_loop_manager",
        "real_world_validator", "regression_guard", "tool_selection_optimizer", "command_composer", "argument_optimizer",
        "output_validator", "adaptive_timeout", "context_budget_manager", "compression_strategy", "quality_gate",
        "strategy_pattern_library", "decision_tree_builder", "trade_analyzer", "constraint_solver", "root_cause_analyzer",
        "hypothesis_generator", "anomaly_detector", "performance_profiler", "knowledge_graph_extractor", "metric_dashboard",
        "medical_terminology_validator", "drug_interaction_checker", "clinical_decision_support", "evidence_based_recommender", "multi_agent_coordinator",
        "task_decomposition_engine", "result_merger", "self_improvement_tracker", "meta_learning_engine", "production_readiness_checker",
        "context_window_manager", "prompt_chaining_engine", "uncertainty_quantifier", "causal_inference_engine", "semantic_similarity_scorer",
        "explanation_generator", "ablation_study_manager", "resource_contention_resolver", "feedback_signal_processor", "graceful_degradation_manager",
        "observability_tracer", "log_aggregator", "metrics_collector", "alert_manager", "deployment_validator",
        "toxicity_detector", "bias_detector", "fact_checker", "consistency_checker", "version_compatibility_checker",
        "benchmark_runner", "regression_detector", "elo_rating_system", "knowledge_distiller", "curriculum_scheduler",
        "validation_pipeline", "error_taxonomy", "recovery_strategy_selector", "conversation_state_tracker", "intent_classifier",
        "priority_scheduler", "memory_consolidator", "attention_manager", "workflow_engine", "template_engine",
        "safety_guard", "context_bridger", "progress_tracker", "delegation_optimizer", "compression_optimizer",
        "token_budget_allocator", "response_quality_scorer", "error_pattern_miner", "dependency_resolver", "performance_budget_enforcer",
        "synthesis_engine", "review_checklist_generator", "adaptive_injection_controller", "impact_estimator", "final_integration_validator",
    ]

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._injections = 0
        self._checks = 0
        self._last_check = {}

    def build_injection(self, context: str = "") -> str:
        ctx = (context or "").lower()
        if not any(k in ctx for k in ["health", "module status", "alive", "heartbeat", "check modules"]):
            return ""
        self._injections += 1
        return "[HEALTH-CHECK (1) test import of each module, (2) call get_instance() on each, (3) report healthy/unhealthy count, (4) flag modules that throw on instantiation]"

    def check_all(self) -> Dict:
        self._checks += 1
        healthy, unhealthy = [], []
        for mod_name in self.MODULES_TO_CHECK:
            try:
                mod = __import__(mod_name)
                inst = mod.get_instance(self.session_id)
                status = inst.get_status()
                healthy.append(mod_name)
                self._last_check[mod_name] = {"healthy": True, "time": time.time()}
            except Exception as e:
                unhealthy.append({"module": mod_name, "error": str(e)[:100]})
                self._last_check[mod_name] = {"healthy": False, "error": str(e)[:100], "time": time.time()}
        return {"healthy": len(healthy), "unhealthy": len(unhealthy), "total": len(self.MODULES_TO_CHECK),
                "unhealthy_details": unhealthy, "timestamp": time.time()}

    def get_status(self) -> Dict:
        return {"session": self.session_id, "injections": self._injections, "checks": self._checks}
