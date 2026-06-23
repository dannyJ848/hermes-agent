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
import os
import sys
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
_cerebrum = None
_cortex = None
_distillation = None
_knowledge_graph = None

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
        # Initialize with a lightweight agent proxy so subsystems register
        try:
            _cognitive_orch.initialize(_AgentProxy())
        except Exception:
            pass
        logger.info("[MEGA] Cognitive orchestrator initialized")
    except Exception as e:
        logger.warning("[MEGA] Cognitive orchestrator failed to load: %s", e)
        _cognitive_orch = False
    return _cognitive_orch if _cognitive_orch is not False else None


def _before_action_enabled() -> bool:
    """Whether to call cognitive_orchestrator.before_action() per tool call.

    before_action builds a rich lesson string whose return value is
    currently discarded (the injection path was never wired). It opens 2
    SQLite connections and runs 6 subsystem aggregations per tool call for
    no model-facing benefit. Defaults to True for backward compatibility;
    set ``cognitive_orchestrator.before_action_enabled: false`` in config
    to skip the dead work and save ~3-15ms + 2 DB connects per tool call.
    after_action (which persists real learning) is unaffected.
    """
    try:
        cfg = _load_config().get("cognitive_orchestrator", {})
        return bool(cfg.get("before_action_enabled", True))
    except Exception:
        return True

def _get_cerebrum():
    global _cerebrum
    if _cerebrum is not None:
        return _cerebrum
    try:
        cfg = _load_config().get("cerebrum", {})
        if not cfg.get("enabled", True):
            return None
        from agent.cerebrum import get_cerebrum
        _cerebrum = get_cerebrum()
        logger.info("[MEGA] Cerebrum memory initialized")
    except Exception as e:
        logger.warning("[MEGA] Cerebrum failed to load: %s", e)
        _cerebrum = False
    return _cerebrum if _cerebrum is not False else None

def _get_cortex():
    global _cortex
    if _cortex is not None:
        return _cortex
    try:
        cfg = _load_config().get("cortex", {})
        if not cfg.get("enabled", True):
            return None
        from agent.cortex_flywheel import get_cortex
        _cortex = get_cortex()
        logger.info("[MEGA] Cortex flywheel initialized")
    except Exception as e:
        logger.warning("[MEGA] Cortex failed to load: %s", e)
        _cortex = False
    return _cortex if _cortex is not False else None

def _get_distillation():
    global _distillation
    if _distillation is not None:
        return _distillation
    try:
        cfg = _load_config().get("distillation", {})
        if not cfg.get("enabled", True):
            return None
        from agent.distillation import get_pipeline
        _distillation = get_pipeline()
        logger.info("[MEGA] Distillation pipeline initialized")
    except Exception as e:
        logger.warning("[MEGA] Distillation failed to load: %s", e)
        _distillation = False
    return _distillation if _distillation is not False else None

def _get_knowledge_graph():
    global _knowledge_graph
    if _knowledge_graph is not None:
        return _knowledge_graph
    try:
        cfg = _load_config().get("knowledge_graph", {})
        if not cfg.get("enabled", True):
            return None
        from agent.knowledge_graph import get_knowledge_graph as get_kg
        _knowledge_graph = get_kg()
        logger.info("[MEGA] Knowledge graph initialized")
    except Exception as e:
        logger.warning("[MEGA] Knowledge graph failed to load: %s", e)
        _knowledge_graph = False
    return _knowledge_graph if _knowledge_graph is not False else None


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
            # Skip during tests to avoid cross-test state pollution
            cache = None
            if not _is_test_environment():
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
    def wrapped(self, function_name: str, function_args: dict, effective_task_id: str, *args, **kwargs):
        # ── Cognitive Orchestrator: BEFORE action ──
        # before_action builds a ~150-line lesson string from 6 subsystems
        # (2 SQLite connects, error_learning scan, skill_tracker write) whose
        # return value is DISCARDED below — it never reaches the model. Gate
        # it behind cognitive_orchestrator.before_action_enabled (default
        # True for backward compat; set false to skip the dead work).
        # after_action below is NOT affected — its DB writes persist.
        try:
            orch = _get_cognitive_orch()
            if orch and _before_action_enabled():
                try:
                    orch.before_action(function_name, str(function_args)[:500])
                except Exception:
                    pass
        except Exception:
            pass

        metrics = _get_metrics()
        start = time.time()
        success = True
        result = None
        try:
            result = original(self, function_name, function_args, effective_task_id, *args, **kwargs)
            return result
        except Exception:
            success = False
            raise
        finally:
            duration = (time.time() - start) * 1000
            try:
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

            # ── Cognitive Orchestrator: AFTER action ──
            try:
                orch = _get_cognitive_orch()
                if orch:
                    try:
                        result_str = str(result)[:500] if result else ""
                        error_str = "" if success else str(result)[:500]
                        orch.after_action(function_name, str(function_args)[:500], result_str, int(duration), error=error_str)
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
                    # Flush batched per-tool DB writes (skill_tracker +
                    # cognitive_actions) accumulated during this turn.
                    # In gateway mode session_end fires per-turn, so this
                    # is the batch boundary. Saves ~5-15ms mid-turn.
                    try:
                        if hasattr(orch, 'flush_pending_writes'):
                            orch.flush_pending_writes()
                    except Exception:
                        pass
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

class _AgentProxy:
    """Lightweight proxy for initializing cognitive orchestrator without full agent."""
    def __init__(self):
        self.session_id = "bootstrap"
        self.tools = {}
        self.memory = {}


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
    # Skip during tests to avoid xdist state pollution
    if _is_test_environment():
        return
    
    if agent_class is None:
        try:
            from run_agent import AIAgent as _AIAgent
            agent_class = _AIAgent
        except Exception as e:
            logger.error("[MEGA] Could not auto-import AIAgent: %s", e)
            return

    # ── Patch __init__ FIRST (before other patches that depend on it) ──
    try:
        _wire_learning_system(agent_class)
    except Exception as e:
        logger.warning("[MEGA] Learning system wiring failed: %s", e)

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


def _wire_learning_system(agent_class):
    """Wire cerebrum, cortex, distillation, cognitive orchestrator, iteration engine, and subconscious plugins into the agent lifecycle.
    
    Hooks:
    - session_start: initialize learning context + cognitive subsystems + iteration engine
    - tool_success/error: capture experiences
    - session_end: run reflection + distillation
    """
    original_init = agent_class.__init__
    
    @wraps(original_init)
    def wrapped_init(self, *args, **kwargs):
        result = original_init(self, *args, **kwargs)
        try:
            cerebrum = _get_cerebrum()
            cortex = _get_cortex()
            if cerebrum and hasattr(self, 'session_id'):
                cerebrum.capture_episode(
                    self.session_id, "session_start", "Agent initialized",
                    importance=0.3
                )
            if cortex and hasattr(self, 'session_id'):
                cortex.capture_experience(
                    self.session_id, "session", "Session started",
                    tags=["lifecycle"]
                )
        except Exception as e:
            logger.debug("[MEGA] Learning init hook failed: %s", e)
        
        # ── Initialize cognitive orchestrator ──────────────────────────
        try:
            from agent.cognitive_orchestrator import get_orchestrator
            orch = get_orchestrator()
            if hasattr(orch, 'initialize'):
                orch.initialize(self)
            if hasattr(self, '_print_fn') and self._print_fn:
                stats = orch.get_stats() if hasattr(orch, 'get_stats') else {}
                active = stats.get('active', 0)
                total = stats.get('total', 0)
                # Skip banner during tests to avoid polluting captured output
                if not ('pytest' in sys.modules or os.environ.get('PYTEST_CURRENT_TEST')):
                    self._print_fn(f"🧠 Cognitive orchestrator ready: {active}/{total} subsystems active")
                    for name, info in stats.get('subsystems', {}).items():
                        if info.get('active'):
                            self._print_fn(f"   ✓ {name}")
        except Exception as e:
            logger.debug("[MEGA] Cognitive orchestrator init failed: %s", e)
        
        # ── Initialize iteration engine ──────────────────────────────────
        try:
            from agent.iteration_engine import get_engine as _get_iteration_engine
            self.iteration_engine = _get_iteration_engine()
            if hasattr(self, '_print_fn') and self._print_fn:
                self._print_fn("🔄 Iteration engine ready: experiential learning loop active")
        except Exception as e:
            logger.debug("[MEGA] Iteration engine init failed: %s", e)
            self.iteration_engine = None
        
        # ── Initialize subconscious plugins ──────────────────────────────
        try:
            from agent.subconscious_plugin_loader import init_subconscious_plugins
            init_subconscious_plugins()
            if hasattr(self, '_print_fn') and self._print_fn:
                self._print_fn("🌊 Subconscious plugins initialized")
        except Exception as e:
            logger.debug("[MEGA] Subconscious plugins init failed: %s", e)
        
        return result
    agent_class.__init__ = wrapped_init
    
    # Hook tool execution for experience capture
    original_invoke = agent_class._invoke_tool
    
    @wraps(original_invoke)
    def wrapped_invoke(self, tool_name, tool_input, *args, **kwargs):
        result = original_invoke(self, tool_name, tool_input, *args, **kwargs)
        try:
            cerebrum = _get_cerebrum()
            cortex = _get_cortex()
            session_id = getattr(self, 'session_id', 'unknown')
            if isinstance(result, dict) and result.get('error'):
                # Error experience
                if cerebrum:
                    cerebrum.capture_episode(
                        session_id, "tool_error",
                        f"Tool {tool_name} failed: {result.get('error')}",
                        context={"tool": tool_name, "input": tool_input},
                        importance=0.8, emotional_valence=-0.5
                    )
                if cortex:
                    cortex.capture_experience(
                        session_id, "error",
                        f"Tool {tool_name} failed: {result.get('error')}",
                        outcome="failed",
                        lessons=f"Check {tool_name} inputs and prerequisites",
                        tags=["tool", tool_name, "error"]
                    )
            else:
                # Success experience
                if cerebrum:
                    cerebrum.capture_episode(
                        session_id, "tool_success",
                        f"Tool {tool_name} succeeded",
                        context={"tool": tool_name},
                        importance=0.4
                    )
        except Exception as e:
            logger.debug("[MEGA] Learning tool hook failed: %s", e)
        return result
    agent_class._invoke_tool = wrapped_invoke
    
    # Hook session end for reflection
    # AIAgent uses shutdown_memory_provider() for actual session end
    # and commit_memory_session() for session rotation (e.g. /new, compression)
    end_methods = []
    if hasattr(agent_class, 'shutdown_memory_provider'):
        end_methods.append(('shutdown_memory_provider', agent_class.shutdown_memory_provider))
    if hasattr(agent_class, 'commit_memory_session'):
        end_methods.append(('commit_memory_session', agent_class.commit_memory_session))
    if hasattr(agent_class, 'session_end'):
        end_methods.append(('session_end', agent_class.session_end))
    if hasattr(agent_class, 'cleanup'):
        end_methods.append(('cleanup', agent_class.cleanup))
    
    for method_name, original_end in end_methods:
        @wraps(original_end)
        def wrapped_end(self, *args, **kwargs):
            try:
                session_id = getattr(self, 'session_id', 'unknown')
                # Run reflection
                cortex = _get_cortex()
                if cortex:
                    reflection = cortex.run_reflection_cycle()
                    logger.info("[MEGA] Reflection cycle: %s", reflection)
                # Run distillation
                distillation = _get_distillation()
                if distillation:
                    tips = distillation.distill_last_24h()
                    logger.info("[MEGA] Distilled %d tips", len(tips))
                # Cleanup old episodes
                cerebrum = _get_cerebrum()
                if cerebrum:
                    deleted = cerebrum.cleanup_old_episodes(days=7)
                    logger.info("[MEGA] Cleaned up %d old episodes", deleted)
            except Exception as e:
                logger.debug("[MEGA] Learning end hook failed: %s", e)
            return original_end(self, *args, **kwargs)
        
        setattr(agent_class, method_name, wrapped_end)
        logger.info("[MEGA] Wired learning hook into %s", method_name)
    
    logger.info("[MEGA] Learning system wired into AIAgent lifecycle")


# Auto-wire on import if AIAgent is already loaded
# Skip during tests to avoid xdist state pollution — check multiple signals
def _is_test_environment():
    """Check if we're running in a test environment.
    
    Checks multiple signals to catch pytest in various import scenarios."""
    import sys
    if 'pytest' in sys.modules:
        return True
    if os.environ.get('PYTEST_CURRENT_TEST'):
        return True
    # Check if pytest is in the call stack (catches late imports during test collection)
    import inspect
    for frame in inspect.stack():
        if 'pytest' in frame.filename or '_pytest' in frame.filename:
            return True
    return False

try:
    import run_agent
    if hasattr(run_agent, "AIAgent") and not _is_test_environment():
        wire_all(run_agent.AIAgent)
except Exception:
    pass
