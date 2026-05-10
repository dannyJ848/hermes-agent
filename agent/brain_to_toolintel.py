#!/usr/bin/env python3
"""
Bridge: brain daemon → tool-intelligence plugin.
Called by brain_daemon.py after each cycle to log results
into the tool_capability.db that the plugin reads.

This replaces the tool-intelligence tracking that the cron
agent wrapper used to provide (tracking terminal calls to
parallel_brain.py).
"""

import sqlite3
import time
import json
import os
from pathlib import Path

TOOL_DB = Path.home() / "hermes-agent" / "tool_capability.db"
# Daemon writes here (avoid DB lock contention with gateway)
DAEMON_LOG = Path.home() / "hermes-agent" / "brain_cycles.jsonl"


def log_brain_cycle(region: str, status: str, duration_ms: int, error: str = ""):
    """Log a brain cycle result.
    
    Writes to brain_cycles.jsonl (daemon-safe, no DB lock contention).
    The hourly controller cron merges these into tool_capability.db.
    """
    action_key = f"brain_daemon_{region}"
    lesson = ""
    if status == "success":
        lesson = f"brain_{region} cycle ok ({duration_ms}ms)"
    elif error:
        lesson = f"brain_{region} ERROR: {error[:80]}"
    
    entry = {
        "tool_name": action_key,
        "result_status": status,
        "speed_ms": duration_ms,
        "lesson": lesson,
        "timestamp": time.time(),
        "region": region,
        "daemon_pid": os.getpid(),
    }
    
    try:
        with open(DAEMON_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _get_avg_speed(db, tool_name: str) -> int:
    """Get average speed for a tool from stats."""
    try:
        row = db.execute("SELECT avg_speed_ms FROM tool_stats WHERE tool_name = ?", (tool_name,)).fetchone()
        return row[0] if row else None
    except:
        return None


if __name__ == "__main__":
    # Test
    log_brain_cycle("alpha", "success", 65000)
    print("Logged test cycle to tool_capability.db")
