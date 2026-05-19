"""Metrics collector with in-memory counters and histograms.

ZERO-FAILURE GUARANTEE:
- Every method catches ALL exceptions
- Thread-safe with locks
- Invalid data types → silently ignored
- get_summary() always returns a valid dict
"""

import threading
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Thread-safe in-memory metrics collector.
    
    ZERO-FAILURE: All operations are safe. get_summary() always returns a dict.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._total_api_calls = 0
        self._total_api_latency_ms = 0.0
        self._total_tool_calls = 0
        self._total_tool_successes = 0
        self._total_tool_failures = 0
        self._tool_latencies: Dict[str, list[float]] = {}

    def record_api_latency(self, duration_ms: float) -> None:
        """Record an API call latency."""
        try:
            duration = float(duration_ms)
            if duration < 0:
                return
            with self._lock:
                self._total_api_calls += 1
                self._total_api_latency_ms += duration
        except Exception as e:
            logger.debug("[Metrics] record_api_latency failed: %s", e)

    def record_tool_call(self, tool_name: str, success: bool, duration_ms: float) -> None:
        """Record a tool call result."""
        try:
            name = str(tool_name) if tool_name else "unknown"
            duration = float(duration_ms) if duration_ms is not None else 0.0
            with self._lock:
                self._total_tool_calls += 1
                if success:
                    self._total_tool_successes += 1
                else:
                    self._total_tool_failures += 1
                self._tool_latencies.setdefault(name, []).append(duration)
        except Exception as e:
            logger.debug("[Metrics] record_tool_call failed: %s", e)

    def get_summary(self) -> Dict[str, Any]:
        """Return metrics summary. NEVER FAILS."""
        try:
            with self._lock:
                total_tools = self._total_tool_successes + self._total_tool_failures
                return {
                    "total_api_calls": self._total_api_calls,
                    "avg_latency": round(self._total_api_latency_ms / max(self._total_api_calls, 1), 2),
                    "tool_success_rate": round(self._total_tool_successes / max(total_tools, 1), 2),
                    "error_rate": round(self._total_tool_failures / max(total_tools, 1), 2),
                    "total_tool_calls": self._total_tool_calls,
                    "per_tool_latencies": {
                        name: round(sum(latencies) / max(len(latencies), 1), 2)
                        for name, latencies in self._tool_latencies.items()
                    },
                }
        except Exception as e:
            logger.debug("[Metrics] get_summary failed: %s", e)
            return {
                "total_api_calls": 0,
                "avg_latency": 0.0,
                "tool_success_rate": 0.0,
                "error_rate": 0.0,
                "total_tool_calls": 0,
                "per_tool_latencies": {},
            }
