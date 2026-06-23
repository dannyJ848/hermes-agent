"""Process-level SQLite connection pool for the cognitive subsystems.

The cognitive layer (cerebrum, skill_tracker, error_learning, cortex_flywheel,
orchestrator) opens a fresh sqlite3.connect()/close() on every query. On a
busy turn with N tool calls that's ~4-6N connect/close cycles — each paying
filesystem + WAL setup cost for a single statement.

This module keeps one persistent connection per DB path, configured with WAL
journaling (concurrent readers, single writer — the exact workload). Callers
swap `sqlite3.connect(path)` for `get_connection(path)`; the connection is
reused across calls within the process.

Thread safety: each get_connection() call returns a thread-local connection
for that DB path. SQLite connections are not safe to share across threads,
but the cognitive layer is single-threaded per agent turn. The thread-local
design handles the gateway's "fresh AIAgent per turn" model correctly —
each turn gets its own connection on its own thread, and the connection
persists for the turn's lifetime.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# Thread-local storage: each thread gets its own connection per DB path.
# Keyed by resolved absolute DB path string.
_local = threading.local()

# Track all connections ever opened (for diagnostics/shutdown). Protected
# by a module-level lock since _local attrs can't be iterated across threads.
_all_connections: Dict[str, sqlite3.Connection] = {}
_lock = threading.Lock()


def _tls() -> Dict[str, sqlite3.Connection]:
    """Return this thread's connection dict, creating it if needed."""
    conns = getattr(_local, "conns", None)
    if conns is None:
        conns = {}
        _local.conns = conns
    return conns


def get_connection(db_path: "str | Path") -> sqlite3.Connection:
    """Return a cached, reusable SQLite connection for ``db_path``.

    The connection is configured with:
      - WAL journal mode (concurrent readers, single writer)
      - 5s busy timeout (waits for locks instead of raising)
      - Row factory set to sqlite3.Row (consistent with the cognitive layer)

    Safe to call repeatedly from the same thread — returns the same
    connection each time. Each thread gets its own connection (SQLite
    connections are not thread-safe to share).

    The connection is NOT closed automatically; it lives for the process
    lifetime. SQLite handles WAL checkpointing internally. For long-running
    gateway processes this is a net win: the connection amortizes schema
    parsing, journal setup, and the cognitive layer's CREATE TABLE IF NOT
    EXISTS guards across turns.
    """
    path = str(Path(db_path).resolve())
    conns = _tls()
    conn = conns.get(path)
    if conn is not None:
        # Verify the connection is still usable. sqlite3.Connection has no
        # public .closed attribute, so probe with a trivial query. This is
        # cheap (no I/O on a live connection) and catches externally-closed
        # connections. Our pool never closes its own connections, so this
        # normally returns immediately.
        try:
            conn.execute("SELECT 1").fetchone()
            return conn
        except (sqlite3.ProgrammingError, sqlite3.DatabaseError):
            # Connection was closed/invalidated externally — recreate.
            conns.pop(path, None)
            with _lock:
                _all_connections.pop(path, None)

    # Open a fresh connection.
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=5.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    # Enable WAL for concurrent read access and better write throughput.
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
    except sqlite3.DatabaseError:
        # WAL not supported (e.g. :memory: or restricted filesystem) —
        # fall back to defaults. The connection still works.
        pass
    conns[path] = conn

    with _lock:
        _all_connections[path] = conn

    return conn


def close_all() -> None:
    """Close every pooled connection. Intended for tests / shutdown."""
    conns = _tls()
    for path, conn in list(conns.items()):
        try:
            conn.close()
        except Exception:
            pass
    conns.clear()
    with _lock:
        _all_connections.clear()


def pool_stats() -> Dict[str, int]:
    """Return {db_path: open_count} for diagnostics."""
    return {path: 1 for path in _tls()}
