"""YantrikDB memory provider — Hermes MemoryProvider ABC adapter template.

Copy this file to plugins/memory/yantrikdb/__init__.py in your Hermes installation,
then set `memory.provider: yantrikdb` in config.yaml.

Key design decisions:
- Lazy import of YantrikDB to handle Python version mismatches (Rust .so compiled
  for specific Python version, e.g. 3.8 vs 3.11).
- Direct SQLite insertion for writes — the ingest queue is unreliable (fills at
  256 ops, background thread may deadlock).
- Safe top_k cap (25) to avoid SQLite parameter limit (32,766) in IN clauses.
- Prefetch returns formatted markdown for system prompt injection.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# YantrikDB lazy import
# ---------------------------------------------------------------------------

_YantrikDB = None
_TenantManager = None


def _load_yantrikdb():
    """Import YantrikDB, adding the user plugin src directory to sys.path.

    The Rust extension (.so) is compiled for a specific Python version.
    If Hermes runs on a different Python, the import fails with undefined
    symbol errors. We keep the import local and add the plugin src to path.
    """
    global _YantrikDB, _TenantManager
    if _YantrikDB is not None:
        return _YantrikDB, _TenantManager

    try:
        from hermes_cli.config import get_hermes_home
        hermes_home = get_hermes_home()
    except Exception:
        hermes_home = Path.home() / ".hermes"

    plugin_src = hermes_home / "plugins" / "yantrikdb" / "src"
    if str(plugin_src) not in sys.path:
        sys.path.insert(0, str(plugin_src))

    from yantrikdb import YantrikDB, TenantManager
    _YantrikDB = YantrikDB
    _TenantManager = TenantManager
    return _YantrikDB, _TenantManager


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

RECALL_SCHEMA = {
    "name": "yantrikdb_recall",
    "description": (
        "Semantic search over YantrikDB cognitive memory. "
        "Retrieves relevant past memories, tips, and learned patterns. "
        "Use when you need to recall specific knowledge or past decisions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural language search query."},
            "namespace": {"type": "string", "default": "", "description": "Memory namespace (e.g. 'cerebrum_tips', 'user')."},
            "top_k": {"type": "integer", "default": 5, "description": "Max results (safe max: 25)."},
        },
        "required": ["query"],
    },
}

STORE_SCHEMA = {
    "name": "yantrikdb_store",
    "description": (
        "Save a memory to YantrikDB. Use for important facts, decisions, "
        "or learned patterns that should persist across sessions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Memory text to store."},
            "memory_type": {"type": "string", "default": "semantic", "description": "semantic | episodic | procedural"},
            "importance": {"type": "number", "default": 0.5, "description": "0.0-1.0 importance score."},
            "namespace": {"type": "string", "default": "default", "description": "Logical grouping."},
            "domain": {"type": "string", "default": "general", "description": "Domain tag (e.g. 'coding', 'devops')."},
            "source": {"type": "string", "default": "session", "description": "Source identifier."},
        },
        "required": ["text"],
    },
}


# ---------------------------------------------------------------------------
# Provider implementation
# ---------------------------------------------------------------------------

class YantrikDBMemoryProvider(MemoryProvider):
    """YantrikDB-backed memory provider for Hermes Agent."""

    _db = None
    _db_path: Optional[Path] = None

    @property
    def name(self) -> str:
        return "yantrikdb"

    def is_available(self) -> bool:
        try:
            _load_yantrikdb()
            return True
        except Exception as e:
            logger.debug("YantrikDB not available: %s", e)
            return False

    def initialize(self, session_id: str, **kwargs) -> None:
        YantrikDB, _ = _load_yantrikdb()
        hermes_home = kwargs.get("hermes_home", str(Path.home() / ".hermes"))
        self._db_path = Path(hermes_home) / "yantrikdb_copy.db"
        self._db = YantrikDB.with_default(str(self._db_path))
        logger.info("YantrikDB memory provider initialized: %s", self._db_path)

    def shutdown(self) -> None:
        if self._db is not None:
            try:
                self._db.close()
            except Exception as e:
                logger.warning("YantrikDB shutdown error: %s", e)
            self._db = None

    def system_prompt_block(self) -> str:
        return (
            "You have access to a persistent cognitive memory system (YantrikDB) "
            "that stores learned tips, user preferences, and past decisions. "
            "Use yantrikdb_recall to retrieve relevant context when needed. "
            "Use yantrikdb_store to save important new learnings."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if self._db is None:
            return ""
        try:
            results = self._db.recall(query, namespace="cerebrum_tips", top_k=5)
            if not results:
                return ""
            lines = ["### Relevant learned behaviors from memory:"]
            for r in results:
                text = r.get("text", "")
                if text:
                    lines.append(f"- {text[:200]}")
            return "\n".join(lines)
        except Exception as e:
            logger.warning("YantrikDB prefetch error: %s", e)
            return ""

    def sync_turn(self, user_message: str, assistant_message: str) -> None:
        pass  # Skip automatic turn storage to avoid queue issues

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [RECALL_SCHEMA, STORE_SCHEMA]

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if self._db is None:
            return json.dumps({"success": False, "error": "YantrikDB not initialized"})
        try:
            if tool_name == "yantrikdb_recall":
                return self._handle_recall(arguments)
            elif tool_name == "yantrikdb_store":
                return self._store_direct_sqlite(**arguments)
            else:
                return json.dumps({"success": False, "error": f"Unknown tool: {tool_name}"})
        except Exception as e:
            logger.exception("YantrikDB tool error: %s", tool_name)
            return json.dumps({"success": False, "error": str(e)})

    def _handle_recall(self, args: Dict[str, Any]) -> str:
        query = args.get("query", "")
        namespace = args.get("namespace", "")
        top_k = min(args.get("top_k", 5), 25)  # SAFE: avoid SQLite param limit

        results = self._db.recall(query, namespace=namespace or None, top_k=top_k)

        formatted = []
        for r in results:
            formatted.append({
                "text": r.get("text", "")[:500],
                "importance": r.get("importance", 0.0),
                "namespace": r.get("namespace", ""),
                "domain": r.get("domain", ""),
                "source": r.get("source", ""),
            })

        return json.dumps({
            "success": True,
            "query": query,
            "namespace": namespace,
            "results": formatted,
            "count": len(formatted),
        }, indent=2)

    def _store_direct_sqlite(self, text: str, memory_type: str = "semantic",
                             importance: float = 0.5, namespace: str = "default",
                             domain: str = "general", source: str = "session") -> str:
        """Store memory via direct SQLite — bypasses the broken ingest queue."""
        import sqlite3
        import struct

        emb = self._db.embed(text)
        emb_blob = struct.pack(f"{len(emb)}f", *emb)

        rid = f"manual_{int(time.time() * 1000)}"
        now = time.time()

        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO memories (rid, type, text, embedding, created_at, updated_at,
                                importance, half_life, last_access, access_count, valence,
                                consolidation_status, storage_tier, metadata, namespace,
                                certainty, domain, source, created_at_unix_micros)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rid, memory_type, text, emb_blob, now, now, importance,
            604800.0, now, 0, 0.0, "active", "hot",
            json.dumps({"source": source}),
            namespace, 0.8, domain, source,
            int(now * 1e6),
        ))
        conn.commit()
        conn.close()

        return json.dumps({
            "success": True,
            "stored": True,
            "namespace": namespace,
            "method": "direct_sqlite",
        })

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        if self._db is not None:
            try:
                self._db.think()
            except Exception:
                pass

    def on_memory_write(self, action: str, target: str, content: str,
                        metadata: Optional[Dict] = None) -> None:
        if self._db is None or not content:
            return
        try:
            self._store_direct_sqlite(
                text=f"[{action}] {target}: {content}",
                memory_type="semantic",
                importance=0.6,
                namespace="default",
                domain=metadata.get("domain", "general") if metadata else "general",
                source="memory_mirror",
            )
        except Exception:
            pass


def register_memory_provider():
    """Return a provider instance for the memory plugin loader."""
    return YantrikDBMemoryProvider()


MemoryProviderClass = YantrikDBMemoryProvider  # Backwards-compat alias
