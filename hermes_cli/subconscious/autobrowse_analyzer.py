"""Autobrowse Analyzer — Detect inefficiency patterns in execution traces.

Identifies: redundant loops, suboptimal model choices, token waste,
failure clusters, and tool selection mistakes.
"""

import json
import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class WastePattern:
    """Detected inefficiency pattern."""
    pattern_type: str  # "redundant_loop", "suboptimal_model", "token_waste", "failure_cluster", "tool_mismatch"
    severity: float  # 0.0-1.0
    description: str
    affected_traces: List[str]  # trace_ids
    recommendation: str
    confidence: float
    domain: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AutobrowseAnalyzer:
    """Analyzes execution traces for waste patterns."""

    # Model cost ranking (lower = cheaper/faster)
    MODEL_COST_RANK = {
        "phi-3": 1, "local": 1, "nomic": 1,
        "glm-5.1": 2, "gemini-flash": 2, "nemotron-free": 2,
        "mimo-v2-pro": 3, "claude-sonnet": 4, "claude-opus": 5,
        "gpt-4": 5, "deepseek-v4-pro": 4,
    }

    # Tool complexity mapping (simple tools should use cheap models)
    SIMPLE_TOOLS = {"web_search", "web_extract", "web_research", "read_file", "search_files"}
    COMPLEX_TOOLS = {"delegate_task", "delegate_with_model", "claude_bridge_task", "execute_code"}

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.patterns: List[WastePattern] = []
        self._lock = threading.Lock()

    def analyze_traces(self, traces: List[Any]) -> List[WastePattern]:
        """Run full analysis on a batch of traces."""
        patterns = []

        patterns.extend(self._detect_redundant_loops(traces))
        patterns.extend(self._detect_suboptimal_models(traces))
        patterns.extend(self._detect_token_waste(traces))
        patterns.extend(self._detect_failure_clusters(traces))
        patterns.extend(self._detect_tool_mismatches(traces))

        with self._lock:
            self.patterns.extend(patterns)

        return patterns

    def _detect_redundant_loops(self, traces: List[Any]) -> List[WastePattern]:
        """Detect same tool called >2x with similar input."""
        patterns = []
        tool_input_map = defaultdict(list)

        for trace in traces:
            # Group by tool + input preview hash
            key = (trace.tool_name, trace.input_preview[:50])
            tool_input_map[key].append(trace)

        for (tool, input_preview), group in tool_input_map.items():
            if len(group) >= 3:
                trace_ids = [t.trace_id for t in group]
                patterns.append(WastePattern(
                    pattern_type="redundant_loop",
                    severity=min(1.0, len(group) * 0.2),
                    description=f"{tool} called {len(group)}x with similar input: '{input_preview[:80]}...'",
                    affected_traces=trace_ids,
                    recommendation=f"WHEN calling {tool} repeatedly, DO cache results or batch requests",
                    confidence=min(0.95, 0.7 + len(group) * 0.05),
                    domain="efficiency"
                ))

        return patterns

    def _detect_suboptimal_models(self, traces: List[Any]) -> List[WastePattern]:
        """Detect expensive models used for simple tasks."""
        patterns = []

        for trace in traces:
            if trace.tool_name in self.SIMPLE_TOOLS:
                model_rank = self.MODEL_COST_RANK.get(trace.model_used, 3)
                if model_rank >= 4:  # Expensive model for simple tool
                    patterns.append(WastePattern(
                        pattern_type="suboptimal_model",
                        severity=0.6,
                        description=f"Expensive model '{trace.model_used}' used for simple tool {trace.tool_name}",
                        affected_traces=[trace.trace_id],
                        recommendation=f"WHEN using {trace.tool_name}, DO use glm-5.1 or gemini-flash instead of {trace.model_used}",
                        confidence=0.85,
                        domain="cost_optimization"
                    ))

        return patterns

    def _detect_token_waste(self, traces: List[Any]) -> List[WastePattern]:
        """Detect oversized outputs when smaller would suffice."""
        patterns = []

        for trace in traces:
            # Heuristic: if output > 10x input and tool is search/extract
            if trace.tool_name in {"web_search", "web_extract", "web_research"}:
                if trace.output_tokens > 2000 and trace.input_tokens < 100:
                    patterns.append(WastePattern(
                        pattern_type="token_waste",
                        severity=min(1.0, trace.output_tokens / 4000),
                        description=f"{trace.tool_name} returned {trace.output_tokens} tokens for {trace.input_tokens} input tokens",
                        affected_traces=[trace.trace_id],
                        recommendation="WHEN searching, DO limit max_chars or use targeted queries to reduce token waste",
                        confidence=0.8,
                        domain="cost_optimization"
                    ))

        return patterns

    def _detect_failure_clusters(self, traces: List[Any]) -> List[WastePattern]:
        """Detect same error pattern repeating."""
        patterns = []
        error_map = defaultdict(list)

        for trace in traces:
            if trace.status == "error" and trace.error_type:
                key = trace.error_type
                error_map[key].append(trace)

        for error_type, group in error_map.items():
            if len(group) >= 2:
                trace_ids = [t.trace_id for t in group]
                patterns.append(WastePattern(
                    pattern_type="failure_cluster",
                    severity=min(1.0, len(group) * 0.25),
                    description=f"{error_type} occurred {len(group)} times in recent traces",
                    affected_traces=trace_ids,
                    recommendation=f"WHEN seeing {error_type}, DO check preconditions before calling the tool",
                    confidence=min(0.9, 0.7 + len(group) * 0.05),
                    domain="reliability"
                ))

        return patterns

    def _detect_tool_mismatches(self, traces: List[Any]) -> List[WastePattern]:
        """Detect cases where a better tool was available but not used."""
        patterns = []

        # Pattern: web_search followed by web_extract on same URL
        url_searches = {}
        for trace in traces:
            if trace.tool_name == "web_search":
                # Extract URL from output preview if present
                url = self._extract_url(trace.output_preview)
                if url:
                    url_searches[url] = trace

        for trace in traces:
            if trace.tool_name == "browser_navigate":
                url = self._extract_url(trace.input_preview)
                if url and url in url_searches:
                    patterns.append(WastePattern(
                        pattern_type="tool_mismatch",
                        severity=0.5,
                        description=f"browser_navigate used for URL that was already in web_search results: {url[:60]}",
                        affected_traces=[trace.trace_id, url_searches[url].trace_id],
                        recommendation="WHEN URL is already known from search, DO use web_extract instead of browser_navigate",
                        confidence=0.75,
                        domain="efficiency"
                    ))

        return patterns

    def _extract_url(self, text: str) -> Optional[str]:
        """Simple URL extraction from text."""
        import re
        urls = re.findall(r'https?://[^\s<>"\')]+', text)
        return urls[0] if urls else None

    def get_top_patterns(self, n: int = 5) -> List[WastePattern]:
        """Get highest-severity patterns."""
        with self._lock:
            sorted_patterns = sorted(self.patterns, key=lambda p: p.severity * p.confidence, reverse=True)
            return sorted_patterns[:n]

    def clear_patterns(self):
        """Clear all detected patterns."""
        with self._lock:
            self.patterns = []

    def build_injection(self, user_message: str = "") -> str:
        """Build injection hint from top patterns."""
        top = self.get_top_patterns(3)
        if not top:
            return ""

        hints = []
        for p in top:
            hints.append(f"[AUTO-BROWSE] {p.pattern_type}: {p.recommendation}")

        return " ".join(hints)


# Singleton registry
_INSTANCES: Dict[str, AutobrowseAnalyzer] = {}
_LOCK = threading.Lock()

def get_instance(session_id: str = "default") -> AutobrowseAnalyzer:
    """Thread-safe singleton."""
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = AutobrowseAnalyzer(session_id)
        return _INSTANCES[session_id]


if __name__ == "__main__":
    print("=== AutobrowseAnalyzer Self-Test ===")

    # Create mock traces
    class MockTrace:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    traces = [
        MockTrace(trace_id="t1", tool_name="web_search", model_used="claude-opus",
                  input_preview="query: python tutorial", output_preview="results...",
                  input_tokens=50, output_tokens=3000, status="success"),
        MockTrace(trace_id="t2", tool_name="web_search", model_used="glm-5.1",
                  input_preview="query: python tutorial", output_preview="results...",
                  input_tokens=50, output_tokens=200, status="success"),
        MockTrace(trace_id="t3", tool_name="web_search", model_used="glm-5.1",
                  input_preview="query: python tutorial", output_preview="results...",
                  input_tokens=50, output_tokens=200, status="success"),
        MockTrace(trace_id="t4", tool_name="execute_code", model_used="glm-5.1",
                  input_preview="code: print(1)", output_preview="1",
                  input_tokens=30, output_tokens=10, status="error", error_type="TimeoutError"),
        MockTrace(trace_id="t5", tool_name="execute_code", model_used="glm-5.1",
                  input_preview="code: print(2)", output_preview="2",
                  input_tokens=30, output_tokens=10, status="error", error_type="TimeoutError"),
    ]

    a = AutobrowseAnalyzer("test")
    patterns = a.analyze_traces(traces)

    print(f"Patterns detected: {len(patterns)}")
    for p in patterns:
        print(f"  - {p.pattern_type}: {p.description[:80]} (severity={p.severity:.2f})")

    print(f"Top patterns: {len(a.get_top_patterns(3))}")
    print(f"Injection: {a.build_injection()}")
    print("=== PASS ===")
