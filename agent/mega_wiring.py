"""
Mega Enhancement Wiring Module
Integrates all new cognitive systems into the AIAgent without modifying run_agent.py directly.

ZERO-FAILURE GUARANTEE:
- Every subsystem has lazy initialization with try/except
- Missing modules → silently skipped
- Missing config → defaults used
- All monkey-patches wrapped in try/except
"""

import time
import logging
import threading
from typing import Optional, Dict, Any, List
from functools import wraps

logger = logging.getLogger(__name__)

# ── Lazy imports (modules load only when first used) ──
_semantic_cache = None
_model_router = None
_code_intel = None
_vector_memory = None
_metrics = None
_cognitive_orch = None

_config_cache = {}

def _load_config():
    global _config_cache
    if _config_cache:
        return _config_cache
    try:
        import yaml
        from hermes_constants import get_hermes_home
        config_path = get_hermes_home() / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                _config_cache = yaml.safe_load(f) or {}
    except Exception:
        _config_cache = {}
    return _config_cache

def _get_semantic_cache():
    global _semantic_cache
    if _semantic_cache is not None:
        return _semantic_cache
    try:
        cfg = _load_config().get("cache", {})
        if not cfg.get("enabled", True):
            return None
        from agent.semantic_cache import SemanticCache
        _semantic_cache = SemanticCache()
        logger.info("[MEGA] Semantic cache initialized")
    except Exception as e:
        logger.warning("[MEGA] Semantic cache failed to load: %s", e)
        _semantic_cache = False
    return _semantic_cache if _semantic_cache is not False else None

def _get_model_router():
    global _model_router
    if _model_router is not None:
        return _model_router
    try:
        cfg = _load_config().get("model_routing", {})
        if not cfg.get("enabled", True):
            return None
        from agent.model_router import ModelRouter
        _model_router = ModelRouter()
        logger.info("[MEGA] Model router initialized")
    except Exception as e:
        logger.warning("[MEGA] Model router failed to load: %s", e)
        _model_router = False
    return _model_router if _model_router is not False else None

def _get_code_intel():
    global _code_intel
    if _code_intel is not None:
        return _code_intel
    try:
        cfg = _load_config().get("code_intelligence", {})
        if not cfg.get("enabled", True):
            return None
        from agent.code_intelligence_bridge import CodeIntelligenceBridge
        _code_intel = CodeIntelligenceBridge()
        logger.info("[MEGA] Code intelligence bridge initialized")
    except Exception as e:
        logger.warning("[MEGA] Code intelligence failed to load: %s", e)
        _code_intel = False
    return _code_intel if _code_intel is not False else None

def _get_vector_memory():
    global _vector_memory
    if _vector_memory is not None:
        return _vector_memory
    try:
        cfg = _load_config().get("vector_memory", {})
        if not cfg.get("enabled", True):
            return None
        from agent.vector_memory import VectorMemory
        _vector_memory = VectorMemory()
        logger.info("[MEGA] Vector memory initialized")
    except Exception as e:
        logger.warning("[MEGA] Vector memory failed to load: %s", e)
        _vector_memory = False
    return _vector_memory if _vector_memory is not False else None

def _get_metrics():
    global _metrics
    if _metrics is not None:
        return _metrics
    try:
        cfg = _load_config().get("metrics", {})
        if not cfg.get("enabled", True):
            return None
        from agent.metrics import MetricsCollector
        _metrics = MetricsCollector()
        logger.info("[MEGA] Metrics collector initialized")
    except Exception as e:
        logger.warning("[MEGA] Metrics failed to load: %s", e)
        _metrics = False
    return _metrics if _metrics is not False else None

def _get_cognitive_orch():
    global _cognitive_orch
    if _cognitive_orch is not None:
        return _cognitive_orch
    try:
        cfg = _load_config().get("cognitive_orchestrator", {})
        if not cfg.get("enabled", True):
            return None
        from agent.cognitive_orchestrator import CognitiveOrchestrator
        _cognitive_orch = CognitiveOrchestrator()
        logger.info("[MEGA] Cognitive orchestrator initialized")
    except Exception as e:
        logger.warning("[MEGA] Cognitive orchestrator failed to load: %s", e)
        _cognitive_orch = False
    return _cognitive_orch if _cognitive_orch is not False else None


# ── Patch decorators ──

def _patch_api_call(agent_class):
    """Wrap _interruptible_api_call to add cache + metrics + model routing."""
    original = agent_class._interruptible_api_call

    @wraps(original)
    def wrapped(self, api_kwargs: dict):
        try:
            # ── Model Routing ──
            router = _get_model_router()
            if router and api_kwargs.get("messages"):
                try:
                    last_msg = api_kwargs["messages"][-1].get("content", "")
                    if isinstance(last_msg, str) and last_msg:
                        routed_model = router.route_task(last_msg)
                        if routed_model and routed_model != api_kwargs.get("model"):
                            api_kwargs = dict(api_kwargs)
                            api_kwargs["model"] = routed_model
                            logger.info("[MEGA] Model routed: %s", routed_model)
                except Exception:
                    pass

            # ── Semantic Cache ──
            cache = _get_semantic_cache()
            cache_key = None
            if cache and api_kwargs.get("messages"):
                try:
                    cache_key = _cache_key_from_messages(api_kwargs["messages"])
                    cached = cache.get(cache_key)
                    if cached:
                        logger.info("[MEGA] Semantic cache HIT")
                        return _build_fake_response(cached)
                except Exception:
                    pass

            # ── Code Intelligence Injection ──
            code_intel = _get_code_intel()
            if code_intel and api_kwargs.get("messages"):
                try:
                    last_msg = api_kwargs["messages"][-1].get("content", "")
                    if isinstance(last_msg, str) and len(last_msg) > 20:
                        snippets = code_intel.get_relevant_code(last_msg)
                        if snippets:
                            _inject_code_context(api_kwargs, snippets)
                except Exception:
                    pass
        except Exception:
            pass

        # ── Metrics: API latency ──
        metrics = _get_metrics()
        start = time.time()
        try:
            response = original(self, api_kwargs)
            try:
                duration = (time.time() - start) * 1000
                if metrics:
                    metrics.record_api_latency(duration)
            except Exception:
                pass
            # Cache the response
            try:
                if cache and cache_key and response:
                    content = _extract_response_content(response)
                    if content:
                        cache.put(cache_key, content)
            except Exception:
                pass
            return response
        except Exception as e:
            try:
                duration = (time.time() - start) * 1000
                if metrics:
                    metrics.record_api_latency(duration)
            except Exception:
                pass
            raise

    agent_class._interruptible_api_call = wrapped


def _patch_tool_execution(agent_class):
    """Wrap _invoke_tool to add metrics + vector memory + cognitive orchestrator."""
    original = agent_class._invoke_tool

    @wraps(original)
    def wrapped(self, function_name: str, function_args: dict, effective_task_id: str, **kwargs):
        metrics = _get_metrics()
        start = time.time()
        success = True
        try:
            result = original(self, function_name, function_args, effective_task_id, **kwargs)
            return result
        except Exception:
            success = False
            raise
        finally:
            try:
                duration = (time.time() - start) * 1000
                if metrics:
                    metrics.record_tool_call(function_name, success, duration)
            except Exception:
                pass

            # ── Vector Memory ──
            try:
                vm = _get_vector_memory()
                if vm and function_name in ("memory", "session_search", "skill_view"):
                    try:
                        query = str(function_args)[:500]
                        vm.add_memory(f"tool:{function_name} args={query}", {"tool": function_name, "task_id": effective_task_id})
                    except Exception:
                        pass
            except Exception:
                pass

            # ── Cognitive Orchestrator ──
            try:
                orch = _get_cognitive_orch()
                if orch:
                    try:
                        orch.before_action(function_name, function_args)
                    except Exception:
                        pass
            except Exception:
                pass

    agent_class._invoke_tool = wrapped


def _patch_run_conversation(agent_class):
    """Wrap run_conversation to add cognitive orchestrator lifecycle hooks."""
    original = agent_class.run_conversation

    @wraps(original)
    def wrapped(self, *args, **kwargs):
        try:
            orch = _get_cognitive_orch()
            if orch:
                try:
                    orch.session_start(self.session_id)
                except Exception:
                    pass
        except Exception:
            pass

        try:
            result = original(self, *args, **kwargs)
            return result
        finally:
            try:
                orch = _get_cognitive_orch()
                if orch:
                    try:
                        orch.session_end(self.session_id)
                    except Exception:
                        pass
            except Exception:
                pass

            # Print metrics summary on session end
            try:
                metrics = _get_metrics()
                if metrics:
                    try:
                        summary = metrics.get_summary()
                        if summary.get("total_api_calls", 0) > 0:
                            logger.info("[MEGA] Session metrics: %s", summary)
                    except Exception:
                        pass
            except Exception:
                pass

    agent_class.run_conversation = wrapped


# ── Helpers ──

def _cache_key_from_messages(messages: List[Dict]) -> str:
    """Build a cache key from the last user message + recent context."""
    try:
        parts = []
        for msg in messages[-3:]:
            content = msg.get("content", "")
            if isinstance(content, str):
                parts.append(content[:500])
        return "\n".join(parts)
    except Exception:
        return ""


def _build_fake_response(content: str):
    """Build a minimal OpenAI-compatible response object from cached content."""
    try:
        from types import SimpleNamespace
        choice = SimpleNamespace(
            message=SimpleNamespace(
                content=content,
                role="assistant",
                tool_calls=None,
            ),
            finish_reason="stop",
            index=0,
        )
        return SimpleNamespace(
            choices=[choice],
            model="cached",
            usage=SimpleNamespace(prompt_tokens=0, completion_tokens=0, total_tokens=0),
        )
    except Exception:
        return None


def _extract_response_content(response) -> Optional[str]:
    """Extract text content from an API response."""
    try:
        if hasattr(response, "choices") and response.choices:
            msg = response.choices[0].message
            if hasattr(msg, "content"):
                return msg.content
    except Exception:
        pass
    return None


def _inject_code_context(api_kwargs: Dict, snippets: List[Dict]):
    """Inject relevant code snippets into the system prompt area."""
    try:
        if not snippets:
            return
        messages = api_kwargs.get("messages", [])
        if not messages:
            return

        sys_idx = None
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                sys_idx = i
                break

        context = "\n\n📚 Relevant code context:\n"
        for snip in snippets[:3]:
            fp = snip.get("file_path", "unknown")
            text = snip.get("chunk_text", "")[:300]
            context += f"\n--- {fp} ---\n{text}\n"

        if sys_idx is not None:
            orig = messages[sys_idx].get("content", "")
            messages[sys_idx]["content"] = orig + context
        else:
            messages.insert(0, {"role": "system", "content": context})
    except Exception:
        pass


# ── Main entry point ──

def wire_all(agent_class=None):
    """Wire all mega enhancements into the AIAgent class.

    ZERO-FAILURE: If anything fails, the agent still works normally.
    """
    if agent_class is None:
        try:
            from run_agent import AIAgent as _AIAgent
            agent_class = _AIAgent
        except Exception as e:
            logger.error("[MEGA] Could not auto-import AIAgent: %s", e)
            return

    try:
        _patch_api_call(agent_class)
    except Exception as e:
        logger.warning("[MEGA] API call patch failed: %s", e)

    try:
        _patch_tool_execution(agent_class)
    except Exception as e:
        logger.warning("[MEGA] Tool execution patch failed: %s", e)

    try:
        _patch_run_conversation(agent_class)
    except Exception as e:
        logger.warning("[MEGA] Run conversation patch failed: %s", e)

    # Wire smart iteration pipeline
    try:
        from agent.smart_iteration_pipeline import enhance_iteration_budget
        from run_agent import IterationBudget
        enhance_iteration_budget(IterationBudget)
    except Exception as e:
        logger.warning("[MEGA] Smart iteration pipeline failed: %s", e)

    logger.info("[MEGA] All enhancements wired into AIAgent")


# Auto-wire on import if AIAgent is already loaded
try:
    import run_agent
    if hasattr(run_agent, "AIAgent"):
        wire_all(run_agent.AIAgent)
except Exception:
    pass
