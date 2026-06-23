"""
Centralized Cortex Database Access Module

Provides a single, robust connection point to the Cortex PostgreSQL database.
Eliminates scattered connection strings and duplicate error handling across modules.

Usage:
    from agent.cortex_access import cortex_cursor, cortex_query, cortex_insert
    
    with cortex_cursor() as cur:
        cur.execute("SELECT * FROM cortex_documents LIMIT 10")
        rows = cur.fetchall()
    
    # Or use convenience functions:
    results = cortex_query("SELECT * FROM cortex_documents WHERE id = %s", (doc_id,))
    cortex_insert("cortex_documents", {"original_text": "...", "doc_type": "memory"})
"""

import logging
import os
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────

DEFAULT_CORTEX_DSN = "dbname=cortex user=hindsight host=localhost port=5432"
CORTEX_DSN = os.environ.get("CORTEX_DSN", DEFAULT_CORTEX_DSN)

# Connection pool (thread-local)
_connection_pool: Dict[int, Any] = {}
_pool_lock = threading.Lock()

# Health tracking
_last_successful_connect = 0.0
_connect_failures = 0
_MAX_FAILURES = 5
_CIRCUIT_BREAKER_SECONDS = 30

# ── Connection Management ──────────────────────────────────────────────────

def _get_connection():
    """Get or create a thread-local Cortex connection."""
    global _last_successful_connect, _connect_failures
    
    tid = threading.get_ident()
    
    # Check circuit breaker
    if _connect_failures >= _MAX_FAILURES:
        since_last = time.time() - _last_successful_connect
        if since_last < _CIRCUIT_BREAKER_SECONDS:
            raise RuntimeError(
                f"Cortex circuit breaker OPEN ({_connect_failures} failures, "
                f"retry in {_CIRCUIT_BREAKER_SECONDS - since_last:.0f}s)"
            )
        # Reset circuit breaker
        _connect_failures = 0
        logger.info("Cortex circuit breaker reset, attempting reconnect")
    
    with _pool_lock:
        conn = _connection_pool.get(tid)
        if conn is not None:
            try:
                # Verify connection is alive
                conn.cursor().execute("SELECT 1")
                return conn
            except Exception:
                # Connection dead, remove it
                try:
                    conn.close()
                except Exception:
                    pass
                del _connection_pool[tid]
    
    # Create new connection
    try:
        import psycopg2
        conn = psycopg2.connect(CORTEX_DSN)
        conn.autocommit = False
        with _pool_lock:
            _connection_pool[tid] = conn
        _last_successful_connect = time.time()
        _connect_failures = 0
        return conn
    except Exception as e:
        _connect_failures += 1
        logger.error(f"Cortex connection failed ({_connect_failures}/{_MAX_FAILURES}): {e}")
        raise


@contextmanager
def cortex_cursor():
    """Context manager for a Cortex database cursor.
    
    Automatically handles connection lifecycle and rollback on error.
    Usage:
        with cortex_cursor() as cur:
            cur.execute("SELECT * FROM table")
            rows = cur.fetchall()
    """
    conn = None
    cur = None
    try:
        conn = _get_connection()
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error(f"Cortex query failed: {e}")
        raise
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass


# ── Convenience Functions ──────────────────────────────────────────────────

def cortex_query(sql: str, params: Tuple = ()) -> List[Tuple]:
    """Execute a SELECT query and return all rows.
    
    Args:
        sql: SQL query string (use %s placeholders)
        params: Query parameters
        
    Returns:
        List of row tuples
        
    Raises:
        RuntimeError: If circuit breaker is open
        psycopg2.Error: On query failure
    """
    with cortex_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def cortex_query_one(sql: str, params: Tuple = ()) -> Optional[Tuple]:
    """Execute a SELECT query and return first row, or None."""
    with cortex_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def cortex_insert(table: str, data: Dict[str, Any]) -> str:
    """Insert a single row and return the generated ID.
    
    Args:
        table: Table name
        data: Column->value dictionary
        
    Returns:
        The generated UUID (for tables with gen_random_uuid())
    """
    if not data:
        raise ValueError("No data provided for insert")
    
    columns = list(data.keys())
    placeholders = ["%s"] * len(columns)
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
    
    with cortex_cursor() as cur:
        cur.execute(sql, tuple(data.values()))
        result = cur.fetchone()
        return result[0] if result else ""


def cortex_upsert(table: str, data: Dict[str, Any], conflict_column: str) -> str:
    """Insert or update a row (PostgreSQL ON CONFLICT DO UPDATE).
    
    Args:
        table: Table name
        data: Column->value dictionary
        conflict_column: Column to check for conflicts
        
    Returns:
        The row ID
    """
    if not data:
        raise ValueError("No data provided for upsert")
    
    columns = list(data.keys())
    placeholders = ["%s"] * len(columns)
    updates = [f"{col} = EXCLUDED.{col}" for col in columns if col != conflict_column]
    
    sql = f"""
        INSERT INTO {table} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        ON CONFLICT ({conflict_column}) DO UPDATE SET
        {', '.join(updates)}
        RETURNING id
    """
    
    with cortex_cursor() as cur:
        cur.execute(sql, tuple(data.values()))
        result = cur.fetchone()
        return result[0] if result else ""


# ── Health Check ───────────────────────────────────────────────────────────

def cortex_health_check() -> Dict[str, Any]:
    """Check Cortex database health and return status.
    
    Returns:
        Dict with keys: connected, latency_ms, document_count, kv_count,
        last_success, failures, circuit_breaker_open
    """
    result = {
        "connected": False,
        "latency_ms": 0,
        "node_count": 0,
        "flywheel_count": 0,
        "last_success": _last_successful_connect,
        "failures": _connect_failures,
        "circuit_breaker_open": _connect_failures >= _MAX_FAILURES,
    }
    
    start = time.time()
    try:
        with cortex_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM cortex_nodes")
            result["node_count"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM cortex_flywheel")
            result["flywheel_count"] = cur.fetchone()[0]
        result["connected"] = True
        result["latency_ms"] = (time.time() - start) * 1000
    except Exception as e:
        result["error"] = str(e)
    
    return result


# ── Cleanup ────────────────────────────────────────────────────────────────

def close_all_connections():
    """Close all pooled connections. Call on shutdown."""
    global _connection_pool
    with _pool_lock:
        for tid, conn in list(_connection_pool.items()):
            try:
                conn.close()
            except Exception:
                pass
        _connection_pool.clear()
    logger.info("All Cortex connections closed")


# Register cleanup on module exit
import atexit
atexit.register(close_all_connections)
