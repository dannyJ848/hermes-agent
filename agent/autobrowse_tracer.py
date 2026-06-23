"""autobrowse_tracer — records browser-action traces for the learning loop.

Stores browser interaction patterns (navigate, click, type) so domain_transfer
can identify web-task patterns and the learning loop can learn from browsing
sessions. Also records tool-call traces for any tool, providing execution
telemetry that feeds the brain's synthesis cycle.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


class AutobrowseTracer:
    """Records execution traces for the learning loop."""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._traces: List[Dict] = []
        self._ensure_schema()

    def _ensure_schema(self):
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS execution_traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp REAL,
                    tool_name TEXT,
                    action_type TEXT,
                    input_data TEXT,
                    output_data TEXT,
                    execution_time_ms INTEGER,
                    status TEXT,
                    created_at REAL DEFAULT (unixepoch())
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_traces_session ON execution_traces(session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_traces_tool ON execution_traces(tool_name)"
            )
            conn.commit()
        except Exception as e:
            logger.debug("autobrowse_tracer: schema init failed: %s", e)

    def trace(self, action: str, result: Dict = None) -> Dict[str, Any]:
        """Trace an action and its result."""
        entry = {
            "action": action,
            "result": result,
            "timestamp": time.time(),
            "session_id": self.session_id,
        }
        self._traces.append(entry)
        return entry

    def record(
        self,
        event_type: str,
        data: Dict,
        tool_name: str = "",
        execution_time_ms: int = 0,
        status: str = "success",
    ) -> bool:
        """Record a traced event to the DB."""
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            conn.execute(
                "INSERT INTO execution_traces "
                "(session_id, timestamp, tool_name, action_type, input_data, output_data, execution_time_ms, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self.session_id,
                    time.time(),
                    tool_name,
                    event_type,
                    json.dumps(data, default=str)[:500],
                    json.dumps(data, default=str)[:500],
                    execution_time_ms,
                    status,
                ),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.debug("autobrowse_tracer: record failed: %s", e)
            return False

    def record_call(
        self,
        tool_name: str = "",
        model_used: str = "",
        input_data: str = "",
        output_data: str = "",
        execution_time_ms: int = 0,
        status: str = "success",
    ) -> bool:
        """Record a tool call trace (backward-compat with orchestrator)."""
        return self.record(
            event_type="tool_call",
            data={"input": input_data[:200], "output": output_data[:200]},
            tool_name=tool_name,
            execution_time_ms=execution_time_ms,
            status=status,
        )

    def get_trace(self, session_id: str = "") -> List[Dict]:
        """Get traces for a session."""
        try:
            from agent.db_pool import get_connection
            conn = get_connection(_DB_PATH)
            sid = session_id or self.session_id
            rows = conn.execute(
                "SELECT * FROM execution_traces WHERE session_id = ? "
                "ORDER BY timestamp DESC LIMIT 50",
                (sid,),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return self._traces
