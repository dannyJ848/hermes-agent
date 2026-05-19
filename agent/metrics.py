"""In-memory metrics collection for agent operations.

Provides thread-safe counters and histograms for tracking API latency,
tool call success rates, and overall error rates.
"""

import threading
from collections import defaultdict
from typing import Dict, Any


class MetricsCollector:
    """Thread-safe in-memory metrics collector.

    Tracks:
        - total_api_calls: number of API latency recordings
        - avg_latency: mean API latency in milliseconds
        - tool_success_rate: percentage of successful tool calls
        - error_rate: percentage of failed tool calls
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()

        # API latency tracking
        self._api_call_count = 0
        self._api_latency_total_ms = 0.0

        # Tool call tracking
        self._tool_calls_total = 0
        self._tool_calls_successful = 0
        self._tool_calls_failed = 0

        # Per-tool histograms: tool_name -> list of durations
        self._tool_latencies: Dict[str, list] = defaultdict(list)

    def record_api_latency(self, duration_ms: float) -> None:
        """Record an API call latency observation.

        Args:
            duration_ms: Latency of the API call in milliseconds.
        """
        with self._lock:
            self._api_call_count += 1
            self._api_latency_total_ms += duration_ms

    def record_tool_call(
        self, tool_name: str, success: bool, duration_ms: float
    ) -> None:
        """Record a tool call observation.

        Args:
            tool_name: Name of the tool that was invoked.
            success: True if the tool call succeeded, False otherwise.
            duration_ms: Duration of the tool call in milliseconds.
        """
        with self._lock:
            self._tool_calls_total += 1
            if success:
                self._tool_calls_successful += 1
            else:
                self._tool_calls_failed += 1
            self._tool_latencies[tool_name].append(duration_ms)

    def get_summary(self) -> Dict[str, Any]:
        """Return a snapshot of current metrics.

        Returns:
            Dictionary containing:
                - total_api_calls (int)
                - avg_latency (float | None)
                - tool_success_rate (float | None)
                - error_rate (float | None)
                - total_tool_calls (int)
                - per_tool_latencies (Dict[str, list])
        """
        with self._lock:
            avg_latency = (
                self._api_latency_total_ms / self._api_call_count
                if self._api_call_count > 0
                else None
            )
            tool_success_rate = (
                self._tool_calls_successful / self._tool_calls_total
                if self._tool_calls_total > 0
                else None
            )
            error_rate = (
                self._tool_calls_failed / self._tool_calls_total
                if self._tool_calls_total > 0
                else None
            )

            return {
                "total_api_calls": self._api_call_count,
                "avg_latency": avg_latency,
                "tool_success_rate": tool_success_rate,
                "error_rate": error_rate,
                "total_tool_calls": self._tool_calls_total,
                "per_tool_latencies": dict(self._tool_latencies),
            }
