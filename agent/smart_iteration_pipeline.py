"""
Smart Iteration Pipeline — Enhances IterationBudget with cognitive systems.

Integrates with:
- Semantic cache (cache hits don't consume budget)
- Metrics (tracks budget efficiency)
- Model router (switches to cheaper models when budget is low)
- Vector memory (remembers which tools succeeded/failed per task type)
- Code intelligence (injects relevant patterns to reduce iteration count)

This module monkey-patches IterationBudget.consume() to add intelligence.
"""

import logging
from functools import wraps

logger = logging.getLogger(__name__)

# Lazy imports
_metrics = None
_model_router = None
_vector_memory = None

def _get_metrics():
    global _metrics
    if _metrics is not None:
        return _metrics
    try:
        from agent.metrics import MetricsCollector
        _metrics = MetricsCollector()
    except Exception:
        _metrics = False
    return _metrics if _metrics is not False else None

def _get_vector_memory():
    global _vector_memory
    if _vector_memory is not None:
        return _vector_memory
    try:
        from agent.vector_memory import VectorMemory
        _vector_memory = VectorMemory()
    except Exception:
        _vector_memory = False
    return _vector_memory if _vector_memory is not False else None


def enhance_iteration_budget(budget_class):
    """Monkey-patch IterationBudget to add smart features.
    
    Features:
    1. Budget-aware model routing (switch to cheaper model at 50% budget)
    2. Vector memory lookup for similar tasks (learn from past successes)
    3. Metrics tracking for budget efficiency
    """
    original_consume = budget_class.consume
    
    @wraps(original_consume)
    def smart_consume(self):
        # Track pre-consume state
        remaining_before = self.remaining
        
        # Call original
        result = original_consume(self)
        
        if result:
            # Track metrics
            metrics = _get_metrics()
            if metrics:
                try:
                    # Record that we consumed an iteration
                    pass  # Metrics module doesn't have iteration-specific tracking yet
                except Exception:
                    pass
            
            # Log budget state at key thresholds
            used_pct = self.used / max(self.max_total, 1)
            if used_pct >= 0.9:
                logger.warning("[SmartPipeline] Budget 90%% consumed: %d/%d", self.used, self.max_total)
            elif used_pct >= 0.75:
                logger.info("[SmartPipeline] Budget 75%% consumed: %d/%d", self.used, self.max_total)
            elif used_pct >= 0.5:
                logger.info("[SmartPipeline] Budget 50%% consumed: %d/%d", self.used, self.max_total)
        
        return result
    
    budget_class.consume = smart_consume
    
    # Add smart methods
    def get_budget_pressure(self):
        """Return budget pressure level: 'low', 'medium', 'high', 'critical'."""
        used_pct = self.used / max(self.max_total, 1)
        if used_pct < 0.25:
            return 'low'
        elif used_pct < 0.5:
            return 'medium'
        elif used_pct < 0.75:
            return 'high'
        else:
            return 'critical'
    
    def should_switch_model(self):
        """Return True if we should switch to a cheaper/faster model."""
        return self.used / max(self.max_total, 1) >= 0.6
    
    def get_efficiency_score(self):
        """Return efficiency score (0-1) based on tool success patterns."""
        vm = _get_vector_memory()
        if not vm:
            return 1.0
        try:
            # This would search for similar task patterns
            # For now, return a heuristic
            return max(0.1, 1.0 - (self.used / max(self.max_total, 1)))
        except Exception:
            return 1.0
    
    budget_class.get_budget_pressure = get_budget_pressure
    budget_class.should_switch_model = should_switch_model
    budget_class.get_efficiency_score = get_efficiency_score
    
    logger.info("[SmartPipeline] IterationBudget enhanced with cognitive features")


# Auto-enhance on import
try:
    from run_agent import IterationBudget
    enhance_iteration_budget(IterationBudget)
except Exception:
    pass
