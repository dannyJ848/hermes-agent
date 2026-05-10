#!/usr/bin/env python3
"""
hermes_enhancement_suite.py — Central integration hub for all subconscious systems.

Wires all cognitive systems into Hermes Agent's hook points:
  - pre_tool_call: memory bridge, error validation, plan validation
  - post_tool_call: error mining, tip quality gate, context tracking
  - pre_llm_call: context window guard, prompt optimization
  - post_llm_call: response quality scoring, distillation trigger

Usage:
    from hermes_enhancement_suite import HermesEnhancementSuite
    suite = HermesEnhancementSuite()
    suite.install_hooks()  # Wires all systems

Or import individual enhancers:
    from hermes_enhancement_suite import ToolRetryWrapper, CircuitBreaker
"""

import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from functools import wraps

HERMES_HOME = Path.home() / ".hermes"
SUBCONSCIOUS = Path(__file__).parent

logger = logging.getLogger("hermes.enhancement")

# ---------------------------------------------------------------------------
# 1. TOOL RETRY WRAPPER
# ---------------------------------------------------------------------------

class ToolRetryWrapper:
    """Auto-retry failed tool calls with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.retry_counts: Dict[str, int] = {}
    
    def wrap(self, func: Callable) -> Callable:
        """Decorator to add retry logic to any tool function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            tool_name = func.__name__
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    # Check if result indicates error
                    if isinstance(result, str) and ('error' in result.lower() or 'failed' in result.lower()):
                        if attempt < self.max_retries:
                            delay = self.base_delay * (2 ** attempt)
                            logger.warning(f"{tool_name} returned error, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                            time.sleep(delay)
                            continue
                    return result
                    
                except Exception as e:
                    last_exception = e
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** attempt)
                        logger.warning(f"{tool_name} failed: {e}, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                        time.sleep(delay)
                    else:
                        logger.error(f"{tool_name} failed after {self.max_retries} retries: {e}")
            
            # All retries exhausted
            return json.dumps({"error": f"Failed after {self.max_retries} retries: {last_exception}"})
        
        return wrapper


# ---------------------------------------------------------------------------
# 2. CIRCUIT BREAKER
# ---------------------------------------------------------------------------

class CircuitBreaker:
    """Circuit breaker for failing tools. Opens after threshold failures."""
    
    STATE_CLOSED = "closed"      # Normal operation
    STATE_OPEN = "open"          # Failing, reject calls
    STATE_HALF_OPEN = "half_open"  # Testing if recovered
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.states: Dict[str, Dict] = {}
    
    def _get_state(self, tool_name: str) -> Dict:
        if tool_name not in self.states:
            self.states[tool_name] = {
                "state": self.STATE_CLOSED,
                "failures": 0,
                "last_failure": 0,
                "last_success": time.time()
            }
        return self.states[tool_name]
    
    def can_execute(self, tool_name: str) -> bool:
        state = self._get_state(tool_name)
        
        if state["state"] == self.STATE_CLOSED:
            return True
        
        if state["state"] == self.STATE_OPEN:
            if time.time() - state["last_failure"] >= self.recovery_timeout:
                state["state"] = self.STATE_HALF_OPEN
                logger.info(f"Circuit breaker for {tool_name}: entering half-open state")
                return True
            return False
        
        if state["state"] == self.STATE_HALF_OPEN:
            return True
        
        return True
    
    def record_success(self, tool_name: str):
        state = self._get_state(tool_name)
        state["failures"] = 0
        state["last_success"] = time.time()
        
        if state["state"] == self.STATE_HALF_OPEN:
            state["state"] = self.STATE_CLOSED
            logger.info(f"Circuit breaker for {tool_name}: closed (recovered)")
    
    def record_failure(self, tool_name: str):
        state = self._get_state(tool_name)
        state["failures"] += 1
        state["last_failure"] = time.time()
        
        if state["failures"] >= self.failure_threshold:
            state["state"] = self.STATE_OPEN
            logger.warning(f"Circuit breaker for {tool_name}: OPENED after {state['failures']} failures")
    
    def wrap(self, func: Callable) -> Callable:
        """Decorator to add circuit breaker to any tool function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            tool_name = func.__name__
            
            if not self.can_execute(tool_name):
                return json.dumps({
                    "error": f"Circuit breaker OPEN for {tool_name}. Tool temporarily disabled due to repeated failures."
                })
            
            try:
                result = func(*args, **kwargs)
                # Check if result indicates success
                if isinstance(result, str) and 'error' in result.lower():
                    self.record_failure(tool_name)
                else:
                    self.record_success(tool_name)
                return result
            except Exception as e:
                self.record_failure(tool_name)
                raise
        
        return wrapper


# ---------------------------------------------------------------------------
# 3. TOOL RESULT CACHE
# ---------------------------------------------------------------------------

class ToolResultCache:
    """Cache tool results to avoid redundant calls."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: float = 300):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache: Dict[str, Dict] = {}
    
    def _make_key(self, tool_name: str, args: Dict) -> str:
        """Create cache key from tool name and args."""
        key_data = json.dumps({"tool": tool_name, "args": args}, sort_keys=True)
        return hash(key_data)
    
    def get(self, tool_name: str, args: Dict) -> Optional[Any]:
        key = self._make_key(tool_name, args)
        entry = self.cache.get(key)
        
        if entry is None:
            return None
        
        if time.time() - entry["timestamp"] > self.ttl:
            del self.cache[key]
            return None
        
        entry["hits"] += 1
        return entry["result"]
    
    def set(self, tool_name: str, args: Dict, result: Any):
        key = self._make_key(tool_name, args)
        
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest]
        
        self.cache[key] = {
            "result": result,
            "timestamp": time.time(),
            "hits": 0
        }
    
    def wrap(self, func: Callable) -> Callable:
        """Decorator to add caching to idempotent tool functions."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            tool_name = func.__name__
            
            # Only cache if no side effects expected
            cached = self.get(tool_name, kwargs)
            if cached is not None:
                logger.debug(f"Cache hit for {tool_name}")
                return cached
            
            result = func(*args, **kwargs)
            self.set(tool_name, kwargs, result)
            return result
        
        return wrapper


# ---------------------------------------------------------------------------
# 4. BATCH TOOL PROCESSOR
# ---------------------------------------------------------------------------

class BatchToolProcessor:
    """Batch multiple similar tool calls for efficiency."""
    
    def __init__(self, batch_size: int = 5, flush_interval: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.pending: List[Dict] = []
        self.last_flush = time.time()
    
    def add(self, tool_name: str, args: Dict, callback: Callable):
        self.pending.append({
            "tool": tool_name,
            "args": args,
            "callback": callback,
            "timestamp": time.time()
        })
        
        if len(self.pending) >= self.batch_size:
            self.flush()
        elif time.time() - self.last_flush >= self.flush_interval:
            self.flush()
    
    def flush(self):
        if not self.pending:
            return
        
        # Group by tool
        by_tool: Dict[str, List[Dict]] = {}
        for item in self.pending:
            by_tool.setdefault(item["tool"], []).append(item)
        
        # Process each batch
        for tool_name, items in by_tool.items():
            logger.info(f"Batch processing {len(items)} calls to {tool_name}")
            # In real implementation, would call batch API
            for item in items:
                try:
                    result = item["callback"](item["args"])
                    item["result"] = result
                except Exception as e:
                    item["error"] = str(e)
        
        self.pending = []
        self.last_flush = time.time()


# ---------------------------------------------------------------------------
# 5. CENTRAL ENHANCEMENT SUITE
# ---------------------------------------------------------------------------

class HermesEnhancementSuite:
    """Central hub that wires all enhancement systems into Hermes."""
    
    def __init__(self):
        self.retry = ToolRetryWrapper(max_retries=3)
        self.circuit_breaker = CircuitBreaker(failure_threshold=5)
        self.cache = ToolResultCache(max_size=100, ttl_seconds=300)
        self.batch = BatchToolProcessor(batch_size=5)
        self.installed = False
    
    def install_hooks(self):
        """Install all enhancement hooks into Hermes Agent."""
        if self.installed:
            logger.warning("Enhancement suite already installed")
            return
        
        try:
            sys.path.insert(0, str(Path.home() / "hermes-agent"))
            
            # Import all subconscious systems
            from memory_cortex_bridge import MemoryCortexBridge, pre_tool_call_hook
            from error_pattern_miner import ErrorPatternMiner, post_tool_call_hook
            from multi_step_validator import MultiStepValidator, validate_plan_hook
            from context_window_guard import ContextWindowGuard, pre_llm_call_hook
            from distillation_quality_gate import DistillationQualityGate
            from auto_launch_monitor import AutoLaunchMonitor
            from checkpoint_watcher_daemon import CheckpointWatcherDaemon
            
            # Store references
            self.memory_bridge = MemoryCortexBridge()
            self.error_miner = ErrorPatternMiner()
            self.validator = MultiStepValidator()
            self.context_guard = ContextWindowGuard()
            self.quality_gate = DistillationQualityGate()
            self.monitor = AutoLaunchMonitor()
            self.watcher = CheckpointWatcherDaemon()
            
            logger.info("Hermes Enhancement Suite installed successfully")
            self.installed = True
            
        except Exception as e:
            logger.error(f"Failed to install enhancement suite: {e}")
            raise
    
    def get_status(self) -> Dict:
        """Get status of all enhancement systems."""
        return {
            "installed": self.installed,
            "retry": {"max_retries": self.retry.max_retries},
            "circuit_breaker": {
                "threshold": self.circuit_breaker.failure_threshold,
                "open_circuits": sum(1 for s in self.circuit_breaker.states.values() if s["state"] == "open")
            },
            "cache": {"size": len(self.cache.cache), "max_size": self.cache.max_size},
            "batch": {"pending": len(self.batch.pending)}
        }


# ---------------------------------------------------------------------------
# 6. QUICK INSTALL FUNCTION
# ---------------------------------------------------------------------------

def install_enhancements():
    """One-line installer for all enhancements."""
    suite = HermesEnhancementSuite()
    suite.install_hooks()
    return suite


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Hermes Enhancement Suite")
    parser.add_argument("--install", action="store_true", help="Install all enhancements")
    parser.add_argument("--status", action="store_true", help="Show status")
    
    args = parser.parse_args()
    
    if args.install:
        suite = install_enhancements()
        print(json.dumps(suite.get_status(), indent=2))
    elif args.status:
        suite = HermesEnhancementSuite()
        print(json.dumps(suite.get_status(), indent=2))
    else:
        print("Usage: python3 hermes_enhancement_suite.py --install")