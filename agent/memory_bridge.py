"""memory_bridge — cognitive subsystem for syncing memory across databases.

SQLite backend using cerebrum_memory.db.
Uses ? placeholders, INTEGER PRIMARY KEY AUTOINCREMENT, CURRENT_TIMESTAMP.
"""

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)
DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


def _cursor():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return _Ctx(conn)


class _Ctx:
    def __init__(self, conn):
        self.conn = conn
        self.cur = None
    def __enter__(self):
        self.cur = self.conn.cursor()
        return self.cur
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.cur.close()
        self.conn.close()
        return False


class MemoryBridge:
    """Bridge between cerebrum and cortex memory systems."""

    def __init__(self):
        self._ensure_schema()

    def _ensure_schema(self):
        with _cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memory_sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    direction TEXT NOT NULL,
                    records_synced INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def sync_to_cortex(self) -> int:
        """Sync local tips to cortex. Returns count synced."""
        try:
            with _cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM distilled_tips")
                count = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO memory_sync_log (direction, records_synced)
                    VALUES (?, ?)
                """, ("to_cortex", count))
                return count
        except Exception as e:
            logger.debug("sync_to_cortex failed: %s", e)
            return 0

    def sync_from_cortex(self) -> int:
        """Sync cortex memories to local. Returns count synced."""
        try:
            with _cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM memory_units")
                count = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO memory_sync_log (direction, records_synced)
                    VALUES (?, ?)
                """, ("from_cortex", count))
                return count
        except Exception as e:
            logger.debug("sync_from_cortex failed: %s", e)
            return 0

    def get_bridge_status(self) -> Dict[str, Any]:
        """Get sync status."""
        try:
            with _cursor() as cur:
                cur.execute("""
                    SELECT direction, SUM(records_synced) as total
                    FROM memory_sync_log
                    GROUP BY direction
                """)
                rows = {r["direction"]: r["total"] for r in cur.fetchall()}
                return {
                    "to_cortex": rows.get("to_cortex", 0),
                    "from_cortex": rows.get("from_cortex", 0),
                    "total_syncs": sum(rows.values()),
                }
        except Exception as e:
            logger.debug("get_bridge_status failed: %s", e)
            return {"to_cortex": 0, "from_cortex": 0, "total_syncs": 0}

    def get_stats(self) -> Dict[str, Any]:
        return self.get_bridge_status()


_bridge = None


def get_memory_bridge() -> MemoryBridge:
    global _bridge
    if _bridge is None:
        _bridge = MemoryBridge()
    return _bridge
