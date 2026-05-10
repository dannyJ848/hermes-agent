"""Autobrowse Tracer — Capture execution traces for proactive self-improvement.

Records every tool call with metadata: tool name, model, tokens, timing,
success/failure/redundancy, task context, and step number.
Stores in CortexDB as node_type="trace" for analysis.
"""

import time
import json
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ToolTrace:
    """Single tool execution trace."""
    trace_id: str
    timestamp: float
    session_id: str
    task_context: str
    step_number: int
    tool_name: str
    model_used: str
    input_size: int
    output_size: int
    input_tokens: int
    output_tokens: int
    execution_time_ms: float
    status: str  # "success", "error", "redundant", "suboptimal"
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    input_preview: str = ""
    output_preview: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class AutobrowseTracer:
    """Captures and stores execution traces."""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.traces: List[ToolTrace] = []
        self._lock = threading.Lock()
        self._step_counter = 0
        self._task_context = ""
        self._cortex = None

    def _get_cortex(self):
        """Lazy-load CortexDB."""
        if self._cortex is None:
            try:
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path.home() / "hermes-agent"))
                from cortex_access import CortexDB
                self._cortex = CortexDB()
            except Exception:
                self._cortex = None
        return self._cortex

    def set_task_context(self, context: str):
        """Set current task context for subsequent traces."""
        self._task_counter = 0
        self._task_context = context[:500]

    def record_call(self,
                    tool_name: str,
                    model_used: str,
                    input_data: Any,
                    output_data: Any,
                    execution_time_ms: float,
                    status: str = "success",
                    error_type: Optional[str] = None,
                    error_message: Optional[str] = None,
                    input_tokens: int = 0,
                    output_tokens: int = 0) -> ToolTrace:
        """Record a tool call trace."""

        with self._lock:
            self._step_counter += 1
            step = self._step_counter

        # Size estimation
        input_str = str(input_data)[:1000]
        output_str = str(output_data)[:1000]
        input_size = len(input_str)
        output_size = len(output_str)

        # Generate trace ID
        trace_id = f"trace_{self.session_id}_{int(time.time()*1000)}_{step}"

        trace = ToolTrace(
            trace_id=trace_id,
            timestamp=time.time(),
            session_id=self.session_id,
            task_context=self._task_context,
            step_number=step,
            tool_name=tool_name,
            model_used=model_used,
            input_size=input_size,
            output_size=output_size,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            execution_time_ms=execution_time_ms,
            status=status,
            error_type=error_type,
            error_message=error_message[:500] if error_message else None,
            input_preview=input_str[:200],
            output_preview=output_str[:200],
            metadata={"recorded_at": datetime.now().isoformat()}
        )

        with self._lock:
            self.traces.append(trace)

        # Persist to CortexDB
        self._persist_trace(trace)

        return trace

    def _persist_trace(self, trace: ToolTrace):
        """Store trace in CortexDB."""
        cortex = self._get_cortex()
        if cortex is None:
            return

        try:
            trace_json = json.dumps(asdict(trace), default=str)
            cortex.insert_node(
                text=trace_json,
                node_type="trace",
                domain="autobrowse",
                confidence=0.95,
                metadata={
                    "tool_name": trace.tool_name,
                    "status": trace.status,
                    "session_id": trace.session_id,
                    "step_number": trace.step_number,
                    "trace_id": trace.trace_id
                }
            )
        except Exception:
            pass  # Silent fail — don't block execution

    def get_recent_traces(self, n: int = 20) -> List[ToolTrace]:
        """Get last N traces."""
        with self._lock:
            return self.traces[-n:]

    def get_traces_by_tool(self, tool_name: str, n: int = 50) -> List[ToolTrace]:
        """Get recent traces for a specific tool."""
        with self._lock:
            matches = [t for t in self.traces if t.tool_name == tool_name]
            return matches[-n:]

    def get_failure_traces(self, n: int = 50) -> List[ToolTrace]:
        """Get recent failure traces."""
        with self._lock:
            failures = [t for t in self.traces if t.status == "error"]
            return failures[-n:]

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate trace statistics."""
        with self._lock:
            total = len(self.traces)
            if total == 0:
                return {"total": 0}

            errors = sum(1 for t in self.traces if t.status == "error")
            redundant = sum(1 for t in self.traces if t.status == "redundant")
            tool_counts = {}
            for t in self.traces:
                tool_counts[t.tool_name] = tool_counts.get(t.tool_name, 0) + 1

            avg_time = sum(t.execution_time_ms for t in self.traces) / total
            total_tokens = sum(t.input_tokens + t.output_tokens for t in self.traces)

            return {
                "total": total,
                "errors": errors,
                "error_rate": errors / total,
                "redundant": redundant,
                "tool_counts": tool_counts,
                "avg_time_ms": avg_time,
                "total_tokens": total_tokens,
                "sessions": len(set(t.session_id for t in self.traces))
            }

    def mark_redundant(self, trace_id: str):
        """Mark a trace as redundant (called after analysis)."""
        with self._lock:
            for t in self.traces:
                if t.trace_id == trace_id:
                    t.status = "redundant"
                    break

    def mark_suboptimal(self, trace_id: str, reason: str):
        """Mark a trace as suboptimal (e.g., wrong model choice)."""
        with self._lock:
            for t in self.traces:
                if t.trace_id == trace_id:
                    t.status = "suboptimal"
                    t.metadata["suboptimal_reason"] = reason
                    break

    def build_injection(self, user_message: str = "") -> str:
        """Build injection hint for pre_llm_call."""
        stats = self.get_stats()
        if stats["total"] < 5:
            return ""

        hints = []

        # Warn about high error rate
        if stats["error_rate"] > 0.3:
            hints.append(f"[AUTO-BROWSE] Error rate {stats['error_rate']:.1%} in recent traces. Consider verification steps.")

        # Warn about redundant calls
        if stats.get("redundant", 0) > 3:
            hints.append(f"[AUTO-BROWSE] {stats['redundant']} redundant calls detected. Check for repeated tool use.")

        # Suggest most reliable tools
        if stats.get("tool_counts"):
            sorted_tools = sorted(stats["tool_counts"].items(), key=lambda x: x[1], reverse=True)
            top_tools = [t[0] for t in sorted_tools[:3]]
            hints.append(f"[AUTO-BROWSE] Most used tools: {', '.join(top_tools)}")

        return " ".join(hints) if hints else ""


# Singleton registry
_INSTANCES: Dict[str, AutobrowseTracer] = {}
_LOCK = threading.Lock()

def get_instance(session_id: str = "default") -> AutobrowseTracer:
    """Thread-safe singleton."""
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = AutobrowseTracer(session_id)
        return _INSTANCES[session_id]


if __name__ == "__main__":
    # Self-test
    print("=== AutobrowseTracer Self-Test ===")
    t = AutobrowseTracer("test")
    t.set_task_context("Test task: verify trace capture")

    # Simulate calls
    t.record_call("web_search", "glm-5.1", {"query": "test"}, {"results": 5}, 1200, "success", input_tokens=50, output_tokens=200)
    t.record_call("execute_code", "glm-5.1", {"code": "print(1)"}, {"output": "1"}, 800, "success", input_tokens=30, output_tokens=10)
    t.record_call("web_search", "glm-5.1", {"query": "test"}, {"results": 5}, 1100, "success", input_tokens=50, output_tokens=200)

    # Mark redundant
    traces = t.get_recent_traces(3)
    if len(traces) >= 3:
        t.mark_redundant(traces[2].trace_id)

    stats = t.get_stats()
    print(f"Total traces: {stats['total']}")
    print(f"Error rate: {stats['error_rate']:.1%}")
    print(f"Redundant: {stats['redundant']}")
    print(f"Avg time: {stats['avg_time_ms']:.0f}ms")
    print(f"Injection: {t.build_injection()}")
    print("=== PASS ===")
