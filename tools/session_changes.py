#!/usr/bin/env python3
"""Session Changes Tracker — File Modification Tracking with Diffs.

Tracks every file modified in the current session with structured diffs.
The model can query what changed, see diffs for specific files, and export
a session summary for handoff.

Works by wrapping write_file/patch operations: the model calls
session_changes(action="track") after any file modification, and the tool
records the change with a before/after diff from git.

Storage: ~/.hermes/workspace/changes_<session>.json
"""

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_hermes_home
from utils import atomic_json_write
from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)


def _workspace_dir() -> Path:
    d = get_hermes_home() / "workspace"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _resolve_session(session_id: Optional[str], explicit: Optional[str] = None) -> str:
    return (explicit or session_id or "default").replace("/", "_")[:128]


def _changes_path(session: str) -> Path:
    return _workspace_dir() / f"changes_{session}.json"


def _load_changes(session: str) -> Dict[str, Any]:
    path = _changes_path(session)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "changes": [],
        "started_at": time.time(),
        "files": {},  # path -> {ops: [...], last_modified}
    }


def _save_changes(session: str, data: Dict[str, Any]) -> None:
    atomic_json_write(_changes_path(session), data)


def _git_diff(filepath: str) -> str:
    """Get git diff for a file. Returns empty string if not in git or no changes."""
    try:
        result = subprocess.run(
            ["git", "diff", "--no-color", "--", filepath],
            capture_output=True, text=True, timeout=10,
            cwd=os.path.dirname(os.path.abspath(filepath)) or ".",
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout[:4000]  # Cap at 4KB
        # Try diff against HEAD for staged changes
        result2 = subprocess.run(
            ["git", "diff", "--no-color", "HEAD", "--", filepath],
            capture_output=True, text=True, timeout=10,
            cwd=os.path.dirname(os.path.abspath(filepath)) or ".",
        )
        return result2.stdout[:4000] if result2.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def _git_status_short() -> str:
    """Get git status --short output."""
    try:
        result = subprocess.run(
            ["git", "status", "--short", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def session_changes_handler(
    args: Dict[str, Any],
    session_id: Optional[str] = None,
    **kwargs,
) -> str:
    """Handle session_changes tool calls."""
    action = args.get("action", "list")
    session = _resolve_session(session_id, args.get("session"))

    if action == "track":
        """Record a file modification."""
        filepath = args.get("file", "")
        operation = args.get("operation", "modified")  # created, modified, deleted
        description = args.get("description", "")
        lines_added = args.get("lines_added")
        lines_removed = args.get("lines_removed")

        if not filepath:
            return tool_error("'file' is required for 'track' action")

        data = _load_changes(session)
        change_entry = {
            "file": filepath,
            "operation": operation,
            "description": description,
            "timestamp": time.time(),
            "lines_added": lines_added,
            "lines_removed": lines_removed,
        }
        data["changes"].append(change_entry)

        # Update file index
        if filepath not in data["files"]:
            data["files"][filepath] = {"ops": [], "first_modified": time.time()}
        data["files"][filepath]["ops"].append(operation)
        data["files"][filepath]["last_modified"] = time.time()

        _save_changes(session, data)
        return json.dumps({
            "status": "success",
            "message": f"Tracked: {filepath} ({operation})",
            "total_changes": len(data["changes"]),
            "total_files": len(data["files"]),
        }, ensure_ascii=False)

    elif action == "list":
        data = _load_changes(session)
        # Summarize by file
        file_summary = []
        for fp, info in data["files"].items():
            ops = info["ops"]
            file_summary.append({
                "file": fp,
                "operations": list(dict.fromkeys(ops)),  # unique, ordered
                "change_count": len(ops),
                "last_modified": info.get("last_modified", 0),
            })
        return json.dumps({
            "status": "success",
            "total_files": len(data["files"]),
            "total_changes": len(data["changes"]),
            "files": file_summary,
        }, ensure_ascii=False)

    elif action == "diff":
        """Get git diff for a specific file or all changed files."""
        filepath = args.get("file")
        if filepath:
            diff = _git_diff(filepath)
            return json.dumps({
                "status": "success",
                "file": filepath,
                "diff": diff if diff else "No changes detected (file may be untracked or unchanged in git)",
            }, ensure_ascii=False)
        else:
            # All changes
            status = _git_status_short()
            return json.dumps({
                "status": "success",
                "git_status": status if status else "Working tree clean or not a git repo",
            }, ensure_ascii=False)

    elif action == "summary":
        """Brief overview suitable for session handoff."""
        data = _load_changes(session)
        duration = time.time() - data.get("started_at", time.time())

        # Group by operation type
        by_op = {}
        for change in data["changes"]:
            op = change["operation"]
            by_op.setdefault(op, []).append(change["file"])

        return json.dumps({
            "status": "success",
            "session_duration_minutes": round(duration / 60, 1),
            "total_files_modified": len(data["files"]),
            "total_operations": len(data["changes"]),
            "by_operation": {k: len(v) for k, v in by_op.items()},
            "files_by_type": by_op,
        }, ensure_ascii=False)

    elif action == "export":
        """Export full change log for handoff to another session."""
        data = _load_changes(session)
        return json.dumps({
            "status": "success",
            "export": data,
        }, ensure_ascii=False)

    elif action == "clear":
        """Reset the change tracker."""
        fresh = {
            "changes": [],
            "started_at": time.time(),
            "files": {},
        }
        _save_changes(session, fresh)
        return json.dumps({"status": "success", "message": "Change tracker cleared"}, ensure_ascii=False)

    else:
        return tool_error(f"Unknown action '{action}'. Valid: track, list, diff, summary, export, clear")


SESSION_CHANGES_SCHEMA = {
    "name": "session_changes",
    "description": (
        "Track file modifications in the current session with structured diffs. "
        "Call session_changes(action='track', file='...', operation='modified') after "
        "any write_file, patch, or terminal file edit to maintain a session change log. "
        "Query with 'list' to see all modified files, 'diff' to see git diffs, "
        "'summary' for a handoff-ready overview, 'export' for full change data. "
        "Prevents losing track of what was modified across long sessions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["track", "list", "diff", "summary", "export", "clear"],
                "description": (
                    "track: record a file modification. "
                    "list: show all modified files. "
                    "diff: git diff for a file or all changes. "
                    "summary: brief handoff-ready overview. "
                    "export: full change log. "
                    "clear: reset the tracker."
                ),
            },
            "file": {
                "type": "string",
                "description": "File path for track/diff actions.",
            },
            "operation": {
                "type": "string",
                "enum": ["created", "modified", "deleted", "renamed"],
                "description": "Type of operation for 'track' action.",
            },
            "description": {
                "type": "string",
                "description": "What was changed and why (for 'track' action).",
            },
            "lines_added": {"type": "integer", "description": "Lines added (optional, for track)."},
            "lines_removed": {"type": "integer", "description": "Lines removed (optional, for track)."},
            "session": {"type": "string", "description": "Override session ID."},
        },
        "required": ["action"],
    },
}


registry.register(
    name="session_changes",
    toolset="cognitive",
    schema=SESSION_CHANGES_SCHEMA,
    handler=session_changes_handler,
    emoji="📝",
    max_result_size_chars=30_000,
)
