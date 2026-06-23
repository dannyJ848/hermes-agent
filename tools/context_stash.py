#!/usr/bin/env python3
"""Context Stash — Offload Large Outputs to Disk.

When a tool returns a 500-line file or a large search result, that output
occupies context window space for the rest of the session. This tool lets
the model stash large outputs to disk and keep only a compact handle (a few
lines summarizing key facts) in context. The full data can be fetched back
on demand if needed.

Usage pattern:
1. After receiving a large tool output (file read, search results, etc.):
   context_stash(action="stash", content=..., summary="key facts here")
   → Returns a compact handle with the stash ID and your summary
2. When you need the full data later:
   context_stash(action="fetch", id="stash_3")
   → Returns the full content

Storage: ~/.hermes/workspace/stash_<session>/
TTL: Stashes auto-expire after 24 hours (ephemeral, not durable).
"""

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from hermes_constants import get_hermes_home
from utils import atomic_json_write
from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)

_STASH_TTL = 24 * 3600  # 24 hours
_MANIFEST_NAME = "_manifest.json"


def _workspace_dir() -> Path:
    d = get_hermes_home() / "workspace"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _stash_dir(session: str) -> Path:
    d = _workspace_dir() / f"stash_{session}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _resolve_session(session_id: Optional[str], explicit: Optional[str] = None) -> str:
    return (explicit or session_id or "default").replace("/", "_")[:128]


def _load_manifest(session: str) -> Dict[str, Any]:
    path = _stash_dir(session) / _MANIFEST_NAME
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"stashes": {}, "created": time.time()}


def _save_manifest(session: str, manifest: Dict[str, Any]) -> None:
    path = _stash_dir(session) / _MANIFEST_NAME
    atomic_json_write(path, manifest)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return max(1, len(text) // 4)


def context_stash_handler(
    args: Dict[str, Any],
    session_id: Optional[str] = None,
    **kwargs,
) -> str:
    """Handle context_stash tool calls."""
    action = args.get("action", "list")
    session = _resolve_session(session_id, args.get("session"))

    if action == "stash":
        content = args.get("content", "")
        summary = args.get("summary", "")
        label = args.get("label", "")
        source = args.get("source", "")

        if not content:
            return tool_error("'content' is required for 'stash' action")

        content_str = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2)
        stash_id = f"stash_{uuid.uuid4().hex[:8]}"
        est_tokens = _estimate_tokens(content_str)

        # Write the full content to disk
        stash_file = _stash_dir(session) / f"{stash_id}.txt"
        stash_file.write_text(content_str, encoding="utf-8")

        # Update manifest
        manifest = _load_manifest(session)
        manifest["stashes"][stash_id] = {
            "id": stash_id,
            "label": label,
            "source": source,
            "summary": summary,
            "char_count": len(content_str),
            "est_tokens": est_tokens,
            "stashed_at": time.time(),
            "file": stash_file.name,
        }
        _save_manifest(session, manifest)

        # Return compact handle
        return json.dumps({
            "status": "success",
            "stash_id": stash_id,
            "summary": summary,
            "label": label,
            "offloaded_tokens": est_tokens,
            "message": f"Stashed {len(content_str)} chars (~{est_tokens} tokens). Use fetch to retrieve full content.",
        }, ensure_ascii=False)

    elif action == "fetch":
        stash_id = args.get("id", "")
        if not stash_id:
            return tool_error("'id' is required for 'fetch' action")

        manifest = _load_manifest(session)
        if stash_id not in manifest["stashes"]:
            return tool_error(f"Stash '{stash_id}' not found. Available: {list(manifest['stashes'].keys())}")

        info = manifest["stashes"][stash_id]
        stash_file = _stash_dir(session) / info["file"]
        if not stash_file.exists():
            return tool_error(f"Stash file for '{stash_id}' is missing (may have been cleaned up)")

        content = stash_file.read_text(encoding="utf-8")
        return json.dumps({
            "status": "success",
            "stash_id": stash_id,
            "summary": info.get("summary", ""),
            "content": content,
            "char_count": len(content),
        }, ensure_ascii=False)

    elif action == "list":
        manifest = _load_manifest(session)
        stashes = []
        for sid, info in manifest["stashes"].items():
            stashes.append({
                "id": sid,
                "label": info.get("label", ""),
                "summary": info.get("summary", "")[:100],
                "est_tokens": info.get("est_tokens", 0),
                "age_minutes": round((time.time() - info.get("stashed_at", 0)) / 60, 1),
            })
        total_tokens = sum(s.get("est_tokens", 0) for s in stashes)
        return json.dumps({
            "status": "success",
            "count": len(stashes),
            "total_offloaded_tokens": total_tokens,
            "stashes": stashes,
        }, ensure_ascii=False)

    elif action == "drop":
        stash_id = args.get("id", "")
        manifest = _load_manifest(session)
        if stash_id == "all":
            count = len(manifest["stashes"])
            for info in manifest["stashes"].values():
                try:
                    (_stash_dir(session) / info["file"]).unlink()
                except OSError:
                    pass
            manifest["stashes"] = {}
            _save_manifest(session, manifest)
            return json.dumps({"status": "success", "message": f"Dropped {count} stash(es)"}, ensure_ascii=False)
        if stash_id not in manifest["stashes"]:
            return tool_error(f"Stash '{stash_id}' not found")
        info = manifest["stashes"].pop(stash_id)
        try:
            (_stash_dir(session) / info["file"]).unlink()
        except OSError:
            pass
        _save_manifest(session, manifest)
        return json.dumps({"status": "success", "message": f"Dropped stash '{stash_id}'"}, ensure_ascii=False)

    elif action == "cleanup":
        """Remove expired stashes."""
        manifest = _load_manifest(session)
        cutoff = time.time() - _STASH_TTL
        removed = []
        for sid, info in list(manifest["stashes"].items()):
            if info.get("stashed_at", 0) < cutoff:
                try:
                    (_stash_dir(session) / info["file"]).unlink()
                except OSError:
                    pass
                manifest["stashes"].pop(sid)
                removed.append(sid)
        if removed:
            _save_manifest(session, manifest)
        return json.dumps({"status": "success", "message": f"Cleaned up {len(removed)} expired stash(es)"}, ensure_ascii=False)

    else:
        return tool_error(f"Unknown action '{action}'. Valid: stash, fetch, list, drop, cleanup")


CONTEXT_STASH_SCHEMA = {
    "name": "context_stash",
    "description": (
        "Offload large tool outputs to disk to free context window space. "
        "Stash a large result with a short summary; keep only the compact handle in context. "
        "Fetch the full content later only if needed. "
        "Actions: stash (store content + summary), fetch (retrieve full content), "
        "list (show all stashes), drop (remove one or all), cleanup (expire old stashes). "
        "Use after receiving large file reads, search results, or verbose tool outputs "
        "that you need to reference later but don't need in full every turn."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["stash", "fetch", "list", "drop", "cleanup"],
                "description": "stash: store content with summary. fetch: get full content back. list: show all stashes. drop: remove one (or all). cleanup: expire old stashes.",
            },
            "content": {
                "description": "The large content to stash (string or object). Required for 'stash'.",
            },
            "summary": {
                "type": "string",
                "description": "Short summary of the stashed content — key facts, decisions, structure. This stays in context as the handle.",
            },
            "label": {
                "type": "string",
                "description": "Optional human-readable label for the stash.",
            },
            "source": {
                "type": "string",
                "description": "What produced this content (e.g., 'read_file:registry.py', 'web_search:python async').",
            },
            "id": {
                "type": "string",
                "description": "Stash ID for fetch/drop actions. Use 'all' with drop to clear everything.",
            },
            "session": {
                "type": "string",
                "description": "Override session ID.",
            },
        },
        "required": ["action"],
    },
}


registry.register(
    name="context_stash",
    toolset="cognitive",
    schema=CONTEXT_STASH_SCHEMA,
    handler=context_stash_handler,
    emoji="📦",
)
