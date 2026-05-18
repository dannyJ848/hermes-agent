"""
Health Check Aggregator with Hierarchical Status.

Features:
1. register health checks with name, check function, and critical flag
2. run all checks concurrently with timeout
3. aggregate status: UP if all pass, DEGRADED if non-critical fail, DOWN if critical fail
4. hierarchical component tree (service -> DB -> connection pool)
5. JSON health report with response time per check
"""

import time
import threading
from typing import Callable, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class HealthStatus:
    UP = "UP"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


class HealthCheckAggregator:
    """Aggregates health checks with hierarchical status reporting."""
    
    def __init__(self):
        self.checks: Dict[str, dict] = {}
        self._lock = threading.Lock()
    
    def register(self, name: str, check_fn: Callable[[], bool], 
                 critical: bool = False):
        """Register a health check.
        
        Args:
            name: Check name. Use '/' for hierarchy (e.g., 'service/db')
            check_fn: Function returning True (healthy) or False (unhealthy)
            critical: If True, failure causes overall DOWN status
        """
        with self._lock:
            self.checks[name] = {
                "fn": check_fn,
                "critical": critical,
            }
    
    def run_all(self, timeout_ms: int = 5000) -> Dict[str, Any]:
        """Run all health checks concurrently with per-task timeout.
        
        Uses threading.Thread.join(timeout) for true execution bounds,
        NOT ThreadPoolExecutor.as_completed(timeout) which only limits
        result waiting time.
        """
        results = {}
        threads = []
        
        # Start all checks in parallel using threads
        for name, check in self.checks.items():
            t = _CheckThread(name, check["fn"])
            t.start()
            threads.append((name, t, check["critical"]))
        
        # Wait for each with timeout using join()
        timeout_sec = timeout_ms / 1000.0
        for name, t, critical in threads:
            t.join(timeout=timeout_sec)
            
            if t.is_alive():
                # Thread still running after timeout - mark as timed out
                # Note: thread continues running in background but we treat it as failed
                results[name] = {
                    "status": HealthStatus.DOWN,
                    "critical": critical,
                    "timed_out": True,
                    "response_time_ms": timeout_ms,
                }
            else:
                elapsed_ms = int((t.end_time - t.start_time) * 1000)
                results[name] = {
                    "status": HealthStatus.UP if t.result else HealthStatus.DOWN,
                    "critical": critical,
                    "timed_out": False,
                    "response_time_ms": elapsed_ms,
                }
        
        # Compute hierarchical status
        self._compute_hierarchical(results)
        
        # Aggregate overall status
        overall = self._aggregate_status(results)
        
        return {
            "status": overall,
            "checks": results,
        }
    
    def _compute_hierarchical(self, results: Dict[str, Any]):
        """Compute parent status from children in hierarchical names."""
        # Group by parent path
        children_map: Dict[str, list] = {}
        
        for name in list(results.keys()):
            parts = name.split("/")
            for i in range(1, len(parts)):
                parent = "/".join(parts[:i])
                if parent not in children_map:
                    children_map[parent] = []
                children_map[parent].append(name)
        
        # Compute parent status from children
        for parent in sorted(children_map.keys(), key=len, reverse=True):
            child_names = children_map[parent]
            child_results = [results[c] for c in child_names if c in results]
            
            if not child_results:
                continue
            
            # Parent status = worst child status
            has_down = any(r["status"] == HealthStatus.DOWN for r in child_results)
            has_degraded = any(r["status"] == HealthStatus.DEGRADED for r in child_results)
            
            if has_down:
                parent_status = HealthStatus.DOWN
            elif has_degraded:
                parent_status = HealthStatus.DEGRADED
            else:
                parent_status = HealthStatus.UP
            
            # Only add parent result if not already a direct check
            if parent not in results:
                results[parent] = {
                    "status": parent_status,
                    "critical": any(r.get("critical", False) for r in child_results),
                    "timed_out": any(r.get("timed_out", False) for r in child_results),
                    "response_time_ms": max(r["response_time_ms"] for r in child_results),
                }
            else:
                # Parent is also a direct check - aggregate
                direct = results[parent]
                if direct["status"] == HealthStatus.UP and has_down:
                    direct["status"] = HealthStatus.DOWN
                elif direct["status"] == HealthStatus.UP and has_degraded:
                    direct["status"] = HealthStatus.DEGRADED
    
    def _aggregate_status(self, results: Dict[str, Any]) -> str:
        """Aggregate overall status from all top-level checks."""
        # Only consider leaf checks (those with no children)
        leaf_checks = []
        for name, result in results.items():
            # A leaf has no children in the results
            has_children = any(c.startswith(name + "/") for c in results.keys() if c != name)
            if not has_children:
                leaf_checks.append(result)
        
        if not leaf_checks:
            return HealthStatus.UP
        
        has_critical_down = any(
            r["status"] == HealthStatus.DOWN and r.get("critical", False) 
            for r in leaf_checks
        )
        has_non_critical_down = any(
            r["status"] == HealthStatus.DOWN and not r.get("critical", False) 
            for r in leaf_checks
        )
        
        if has_critical_down:
            return HealthStatus.DOWN
        elif has_non_critical_down:
            return HealthStatus.DEGRADED
        return HealthStatus.UP


class _CheckThread(threading.Thread):
    """Thread that runs a single health check and captures timing."""
    
    def __init__(self, name: str, check_fn: Callable[[], bool]):
        super().__init__(daemon=True)
        self.name = name
        self.check_fn = check_fn
        self.result = False
        self.start_time = 0.0
        self.end_time = 0.0
    
    def run(self):
        self.start_time = time.time()
        try:
            self.result = self.check_fn()
        except Exception:
            self.result = False
        finally:
            self.end_time = time.time()
