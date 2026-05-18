"""
Test suite for Health Check Aggregator with Hierarchical Status.
Features:
1. register health checks with name, check function, and critical flag
2. run all checks concurrently with timeout
3. aggregate status: UP if all pass, DEGRADED if non-critical fail, DOWN if critical fail
4. hierarchical component tree (service -> DB -> connection pool)
5. JSON health report with response time per check
"""

import pytest
import time
import threading
from health_check import HealthCheckAggregator, HealthStatus


class TestFeature1Register:
    """Feature 1: register health checks with name, check function, and critical flag"""
    
    def test_register_basic(self):
        agg = HealthCheckAggregator()
        agg.register("db", lambda: True)
        assert "db" in agg.checks
    
    def test_register_critical(self):
        agg = HealthCheckAggregator()
        agg.register("db", lambda: True, critical=True)
        assert agg.checks["db"]["critical"] is True


class TestFeature2ConcurrentTimeout:
    """Feature 2: run all checks concurrently with timeout
    
    IMPORTANT: ThreadPoolExecutor.as_completed(timeout) only limits result waiting,
    NOT thread execution time. We use threading.Thread.join(timeout) for true per-task bounds.
    """
    
    def test_concurrent_execution(self):
        agg = HealthCheckAggregator()
        order = []
        
        def slow_check():
            time.sleep(0.05)
            order.append(1)
            return True
        
        agg.register("check1", slow_check)
        agg.register("check2", slow_check)
        
        start = time.time()
        result = agg.run_all(timeout_ms=500)
        elapsed = time.time() - start
        
        # Both should run concurrently, not sequentially
        assert elapsed < 0.15  # Should be ~50ms, not 100ms
        assert len(order) == 2
    
    def test_timeout_enforcement(self):
        """Slow checks that exceed timeout should be marked as failed."""
        agg = HealthCheckAggregator()
        
        def very_slow():
            time.sleep(0.5)
            return True
        
        agg.register("slow", very_slow)
        result = agg.run_all(timeout_ms=100)
        
        assert result["checks"]["slow"]["status"] == "DOWN"
        assert result["checks"]["slow"]["timed_out"] is True


class TestFeature3AggregateStatus:
    """Feature 3: aggregate status: UP if all pass, DEGRADED if non-critical fail, DOWN if critical fail"""
    
    def test_all_pass_up(self):
        agg = HealthCheckAggregator()
        agg.register("db", lambda: True, critical=True)
        agg.register("cache", lambda: True, critical=False)
        result = agg.run_all(timeout_ms=500)
        assert result["status"] == "UP"
    
    def test_non_critical_fail_degraded(self):
        agg = HealthCheckAggregator()
        agg.register("db", lambda: True, critical=True)
        agg.register("cache", lambda: False, critical=False)
        result = agg.run_all(timeout_ms=500)
        assert result["status"] == "DEGRADED"
    
    def test_critical_fail_down(self):
        agg = HealthCheckAggregator()
        agg.register("db", lambda: False, critical=True)
        agg.register("cache", lambda: True, critical=False)
        result = agg.run_all(timeout_ms=500)
        assert result["status"] == "DOWN"


class TestFeature4Hierarchical:
    """Feature 4: hierarchical component tree (service -> DB -> connection pool)"""
    
    def test_hierarchical_status(self):
        agg = HealthCheckAggregator()
        
        # Register parent and children
        agg.register("service", lambda: True)
        agg.register("service/db", lambda: True, critical=True)
        agg.register("service/db/pool", lambda: True, critical=True)
        
        result = agg.run_all(timeout_ms=500)
        
        # Parent status should aggregate children
        assert "service" in result["checks"]
        assert result["checks"]["service"]["status"] == "UP"
    
    def test_hierarchical_critical_child_fails(self):
        agg = HealthCheckAggregator()
        
        agg.register("service", lambda: True)
        agg.register("service/db", lambda: False, critical=True)
        agg.register("service/cache", lambda: True, critical=False)
        
        result = agg.run_all(timeout_ms=500)
        
        # Service should be DOWN because critical child failed
        assert result["checks"]["service"]["status"] == "DOWN"


class TestFeature5JsonReport:
    """Feature 5: JSON health report with response time per check"""
    
    def test_response_time_recorded(self):
        agg = HealthCheckAggregator()
        
        def slow_check():
            time.sleep(0.05)
            return True
        
        agg.register("slow", slow_check)
        result = agg.run_all(timeout_ms=500)
        
        assert "response_time_ms" in result["checks"]["slow"]
        assert result["checks"]["slow"]["response_time_ms"] >= 50
    
    def test_json_structure(self):
        agg = HealthCheckAggregator()
        agg.register("db", lambda: True, critical=True)
        result = agg.run_all(timeout_ms=500)
        
        assert "status" in result
        assert "checks" in result
        assert result["checks"]["db"]["status"] == "UP"
        assert result["checks"]["db"]["critical"] is True
