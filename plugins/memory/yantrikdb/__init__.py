"""YantrikDB memory provider — Hermes MemoryProvider adapter.

Provides semantic memory recall and storage via YantrikDB cognitive memory engine.
This adapter implements the MemoryProvider ABC so YantrikDB can be selected
via ``memory.provider: yantrikdb`` in config.yaml.

Config (config.yaml):
  memory:
    provider: yantrikdb
    # Optional: override default DB path
    # yantrikdb_db_path: ~/.hermes/yantrikdb_copy.db

Requires:
  - yantrikdb Python package (Rust extension + Python wrapper)
  - The YantrikDB plugin installed at $HERMES_HOME/plugins/yantrikdb/

The provider exposes two tools to the agent:
  - yantrikdb_recall — semantic search over stored memories
  - yantrikdb_store — save a new memory to the database
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
# YantrikDB lazy import — the Rust .so is compiled for a specific Python
# version, so we keep the import local to avoid startup crashes on
# interpreter mismatch.
# ---------------------------------------------------------------------------

_YantrikDB = None
_TenantManager = None


def _load_yantrikdb():
    """Import YantrikDB."""
    global _YantrikDB, _TenantManager
    if _YantrikDB is not None:
        return _YantrikDB, _TenantManager

    # Try importing from the installed package first (pip installed wheel)
    try:
        from yantrikdb import YantrikDB, TenantManager
        _YantrikDB = YantrikDB
        _TenantManager = TenantManager
        return _YantrikDB, _TenantManager
    except ImportError:
        pass  # Fall through to src/ path

    # Fallback: try from the plugin src directory
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
        "Retrieves relevant past memories, tips, and learned patterns "
        "based on a natural-language query. "
        "Use this when you need to recall specific knowledge, past decisions, "
        "or learned behaviors that may be relevant to the current task."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "What to search for in memory (natural language).",
            },
            "namespace": {
                "type": "string",
                "description": "Memory namespace to search (default: all). Common: 'cerebrum_tips', 'user', 'default'.",
                "default": "",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (default 5, max 50). Keep small for speed.",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}

STORE_SCHEMA = {
    "name": "yantrikdb_store",
    "description": (
        "Save a new memory to YantrikDB cognitive memory engine. "
        "Use this to persist important facts, decisions, or learned patterns "
        "that should be recalled in future sessions. "
        "Memories are automatically embedded for semantic search."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The memory text to store.",
            },
            "memory_type": {
                "type": "string",
                "description": "Type of memory: 'semantic' (default), 'episodic', 'procedural'.",
                "default": "semantic",
            },
            "importance": {
                "type": "number",
                "description": "Importance score 0.0-1.0 (default 0.5). Higher = more likely to be recalled.",
                "default": 0.5,
            },
            "namespace": {
                "type": "string",
                "description": "Memory namespace (default: 'default'). Use 'user' for user preferences, 'cerebrum_tips' for learned behaviors.",
                "default": "default",
            },
            "domain": {
                "type": "string",
                "description": "Domain tag for categorization (e.g., 'coding', 'devops', 'research').",
                "default": "general",
            },
            "source": {
                "type": "string",
                "description": "Source identifier (e.g., 'session', 'distillation', 'user_input').",
                "default": "session",
            },
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

    # -- Availability --------------------------------------------------------

    def is_available(self) -> bool:
        """Check if YantrikDB plugin is installed and the Rust extension loads."""
        try:
            _load_yantrikdb()
            return True
        except Exception as e:
            logger.debug("YantrikDB not available: %s", e)
            return False

    # -- Lifecycle -----------------------------------------------------------

    def initialize(self, session_id: str, **kwargs) -> None:
        """Open the YantrikDB database for this session."""
        YantrikDB, _ = _load_yantrikdb()

        # Resolve DB path
        hermes_home = kwargs.get("hermes_home", str(Path.home() / ".hermes"))
        hermes_path = Path(hermes_home)

        # Config override
        config_path = kwargs.get("config", {})
        db_override = config_path.get("yantrikdb_db_path") if isinstance(config_path, dict) else None

        if db_override:
            self._db_path = Path(db_override).expanduser()
        else:
            self._db_path = hermes_path / "yantrikdb_copy.db"

        if not self._db_path.exists():
            # Try fallback: create fresh DB
            logger.info("YantrikDB not found at %s, creating fresh DB", self._db_path)
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._db = YantrikDB.with_default(str(self._db_path))
        logger.info("YantrikDB memory provider initialized: %s", self._db_path)

    def shutdown(self) -> None:
        """Close the database connection."""
        if self._db is not None:
            try:
                self._db.close()
            except Exception as e:
                logger.warning("YantrikDB shutdown error: %s", e)
            self._db = None

    # -- System prompt -------------------------------------------------------

    def system_prompt_block(self) -> str:
        return (
            "You have access to a persistent cognitive memory system (YantrikDB) "
            "that stores learned tips, user preferences, and past decisions. "
            "Use yantrikdb_recall to retrieve relevant context when needed. "
            "Use yantrikdb_store to save important new learnings."
        )

    # -- Prefetch ------------------------------------------------------------

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        """Recall relevant memories before the turn."""
        if self._db is None:
            return ""

        try:
            # Search cerebrum_tips namespace (learned behaviors)
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

    # -- Turn sync ------------------------------------------------------------

    def sync_turn(self, user_message: str, assistant_message: str) -> None:
        """Optional: store turn summary. Currently no-op to avoid queue issues."""
        # The YantrikDB ingest queue has a 256-op limit that can deadlock.
        # We skip automatic turn storage; use yantrikdb_store tool explicitly.
        pass

    # -- Tool schemas ---------------------------------------------------------

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [RECALL_SCHEMA, STORE_SCHEMA]

    # -- Tool dispatch --------------------------------------------------------

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if self._db is None:
            return json.dumps({"success": False, "error": "YantrikDB not initialized"})

        try:
            if tool_name == "yantrikdb_recall":
                return self._handle_recall(arguments)
            elif tool_name == "yantrikdb_store":
                return self._handle_store(arguments)
            else:
                return json.dumps({"success": False, "error": f"Unknown tool: {tool_name}"})
        except Exception as e:
            logger.exception("YantrikDB tool error: %s", tool_name)
            return json.dumps({"success": False, "error": str(e)})

    def _handle_recall(self, args: Dict[str, Any]) -> str:
        query = args.get("query", "")
        namespace = args.get("namespace", "")
        top_k = min(args.get("top_k", 5), 50)

        # Workaround: YantrikDB recall with large top_k hits SQLite parameter limit
        # Use smaller top_k and filter manually if needed
        safe_top_k = min(top_k, 25)

        results = self._db.recall(query, namespace=namespace or None, top_k=safe_top_k)

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

    def _handle_store(self, args: Dict[str, Any]) -> str:
        text = args.get("text", "")
        if not text:
            return json.dumps({"success": False, "error": "text is required"})

        memory_type = args.get("memory_type", "semantic")
        importance = float(args.get("importance", 0.5))
        namespace = args.get("namespace", "default")
        domain = args.get("domain", "general")
        source = args.get("source", "session")

        # Use direct SQLite insertion to bypass the broken ingest queue
        # (the queue fills at 256 ops and never drains)
        return self._store_direct_sqlite(text, memory_type, importance, namespace, domain, source)

    def _store_direct_sqlite(self, text: str, memory_type: str, importance: float,
                             namespace: str, domain: str, source: str) -> str:
        """Fallback: insert directly into SQLite to bypass queue."""
        import sqlite3
        import struct

        try:
            # Generate embedding
            emb = self._db.embed(text)
            emb_blob = struct.pack(f"{len(emb)}f", *emb)

            rid = f"manual_{int(time.time() * 1000)}"
            now = time.time()

            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (rid, type, text, embedding, created_at, updated_at, importance,
                                    half_life, last_access, access_count, valence, consolidation_status,
                                    storage_tier, metadata, namespace, certainty, domain, source,
                                    created_at_unix_micros)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rid, memory_type, text, emb_blob, now, now, importance,
                  604800.0, now, 0, 0.0, "active", "hot",
                  json.dumps({"source": source}),
                  namespace, 0.8, domain, source,
                  int(now * 1e6)))
            conn.commit()
            conn.close()

            return json.dumps({
                "success": True,
                "stored": True,
                "namespace": namespace,
                "method": "direct_sqlite",
            })
        except Exception as e:
            logger.exception("Direct SQLite store failed")
            return json.dumps({"success": False, "error": f"Direct store failed: {e}"})

    # -- Session hooks (optional) ---------------------------------------------

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        """Optional: flush any pending operations on session end."""
        if self._db is not None:
            try:
                self._db.think()
            except Exception:
                pass

    def on_memory_write(self, action: str, target: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Mirror built-in memory writes to YantrikDB."""
        if self._db is None or not content:
            return
        try:
            self._db.record(
                text=f"[{action}] {target}: {content}",
                memory_type="semantic",
                importance=0.6,
                namespace="default",
                domain=metadata.get("domain", "general") if metadata else "general",
                source="memory_mirror",
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_memory_provider():
    """Return a provider instance for the memory plugin loader."""
    return YantrikDBMemoryProvider()


# Backwards-compat alias used by the plugin loader
MemoryProviderClass = YantrikDBMemoryProvider
