#!/usr/bin/env python3
"""Working Memory — Per-Session Structured Scratchpad.

The biggest cognitive gap: all task understanding lives in conversation history.
When compression fires, nuanced state is lost — which file I was editing, what I
already tried, what the user's constraint was, what failed.

This tool provides a structured JSON scratchpad that persists on disk between
turns and survives compression. The model writes task state to disk and reads
it back on demand — the file outlives any context window eviction.

Design:
- File-backed at ~/.hermes/workspace/wm_<session>.json
- Structured defaults (task, steps, files, constraints, failures, notes)
- Free-form notes dict for anything not covered by the schema
- Checkpoint/restore for branching work
- Old sessions auto-expire (configurable, default 7 days)

The state is NOT injected into the system prompt (unlike memory_tool) — the
model must explicitly call working_memory(action="get") to read it. This keeps
the system prompt stable for prefix caching while giving the model a reliable
external memory.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from hermes_constants import get_hermes_home
from utils import atomic_json_write
from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)

# How long to keep old session scratchpads before cleanup (seconds).
_SESSION_TTL = 7 * 24 * 3600  # 7 days


def _workspace_dir() -> Path:
    """Return the workspace directory for ephemeral session state."""
    d = get_hermes_home() / "workspace"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _resolve_session(session_id: Optional[str], explicit: Optional[str] = None) -> str:
    """Pick the session identifier to use."""
    return (explicit or session_id or "default").replace("/", "_")[:128]


def _scratch_path(session: str) -> Path:
    return _workspace_dir() / f"wm_{session}.json"


def _default_state() -> Dict[str, Any]:
    """Fresh scratchpad structure."""
    return {
        "task": "",
        "task_description": "",
        "current_step": 0,
        "total_steps": 0,
        "step_descriptions": [],
        "files_changed": [],
        "files_read": [],
        "constraints": [],
        "what_failed": [],
        "what_worked": [],
        "decisions": [],
        "notes": {},
        "checkpoints": {},
        "created_at": time.time(),
        "updated_at": time.time(),
    }


def _load(session: str) -> Dict[str, Any]:
    """Load the scratchpad for a session, creating defaults if absent."""
    path = _scratch_path(session)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            # Merge with defaults to handle schema evolution
            merged = _default_state()
            merged.update(data)
            return merged
        except (json.JSONDecodeError, OSError):
            logger.warning("Working memory file corrupted for %s, starting fresh", session)
    return _default_state()


def _save(session: str, state: Dict[str, Any]) -> None:
    """Persist the scratchpad atomically."""
    state["updated_at"] = time.time()
    path = _scratch_path(session)
    atomic_json_write(path, state)


def working_memory_handler(
    args: Dict[str, Any],
    session_id: Optional[str] = None,
    **kwargs,
) -> str:
    """Handle working_memory tool calls."""
    action = args.get("action", "get")
    session = _resolve_session(session_id, args.get("session"))

    if action == "get":
        state = _load(session)
        # Don't return checkpoints dict in full (can be large)
        display = {k: v for k, v in state.items() if k != "checkpoints"}
        display["checkpoints"] = list(state.get("checkpoints", {}).keys())
        return json.dumps({"status": "success", "state": display}, ensure_ascii=False)

    elif action == "set":
        state = _load(session)
        updates = args.get("state", {})
        if not isinstance(updates, dict):
            return tool_error("'state' must be an object for 'set' action")
        # Only update known fields; unknown fields go to notes
        known_keys = set(_default_state().keys())
        for k, v in updates.items():
            if k in known_keys:
                state[k] = v
            else:
                state["notes"][k] = v
        _save(session, state)
        return json.dumps({"status": "success", "message": f"Updated {len(updates)} field(s)"}, ensure_ascii=False)

    elif action == "update":
        """Update a single field with merge semantics."""
        state = _load(session)
        field = args.get("field", "")
        value = args.get("value")
        if not field:
            return tool_error("'field' is required for 'update' action")
        known_keys = set(_default_state().keys())
        if field in known_keys:
            current = state.get(field)
            if isinstance(current, list) and isinstance(value, list):
                # Merge lists (dedup preserving order)
                existing = set(map(str, current))
                for item in value:
                    if str(item) not in existing:
                        current.append(item)
                        existing.add(str(item))
                state[field] = current
            elif isinstance(current, dict) and isinstance(value, dict):
                current.update(value)
                state[field] = current
            else:
                state[field] = value
        else:
            state["notes"][field] = value
        _save(session, state)
        return json.dumps({"status": "success", "message": f"Updated '{field}'"}, ensure_ascii=False)

    elif action == "push":
        """Append an item to a list field."""
        state = _load(session)
        field = args.get("field", "")
        item = args.get("item")
        if not field:
            return tool_error("'field' is required for 'push' action")
        if field not in state:
            state[field] = []
        if not isinstance(state[field], list):
            return tool_error(f"'{field}' is not a list (current type: {type(state[field]).__name__})")
        # Avoid duplicate entries
        item_str = json.dumps(item, sort_keys=True) if not isinstance(item, str) else item
        if item_str not in {json.dumps(x, sort_keys=True) if not isinstance(x, str) else x for x in state[field]}:
            state[field].append(item)
        _save(session, state)
        return json.dumps({"status": "success", "message": f"Pushed to '{field}' (now {len(state[field])} items)"}, ensure_ascii=False)

    elif action == "checkpoint":
        """Save a named snapshot of current state."""
        state = _load(session)
        name = args.get("name", f"cp_{int(time.time())}")
        state["checkpoints"][name] = json.loads(json.dumps(state))  # deep copy without checkpoints
        # Remove nested checkpoints from the snapshot to avoid unbounded growth
        state["checkpoints"][name].pop("checkpoints", None)
        _save(session, state)
        return json.dumps({"status": "success", "message": f"Checkpoint '{name}' saved"}, ensure_ascii=False)

    elif action == "restore":
        """Restore from a named checkpoint."""
        state = _load(session)
        name = args.get("name", "")
        if name not in state.get("checkpoints", {}):
            return tool_error(f"Checkpoint '{name}' not found. Available: {list(state.get('checkpoints', {}).keys())}")
        cp = state["checkpoints"][name]
        checkpoints = state.get("checkpoints", {})  # preserve checkpoint history
        state.clear()
        state.update(cp)
        state["checkpoints"] = checkpoints
        _save(session, state)
        return json.dumps({"status": "success", "message": f"Restored from checkpoint '{name}'"}, ensure_ascii=False)

    elif action == "clear":
        """Reset to empty state (optionally preserving specific fields)."""
        keep_fields = args.get("keep", [])
        old = _load(session)
        fresh = _default_state()
        for f in keep_fields:
            if f in old:
                fresh[f] = old[f]
        _save(session, fresh)
        return json.dumps({"status": "success", "message": "Working memory cleared"}, ensure_ascii=False)

    elif action == "list_sessions":
        """List all session scratchpads."""
        ws = _workspace_dir()
        sessions = []
        for p in sorted(ws.glob("wm_*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                sessions.append({
                    "session": p.stem.replace("wm_", ""),
                    "task": data.get("task", "")[:80],
                    "updated": data.get("updated_at", 0),
                    "age_hours": round((time.time() - data.get("updated_at", 0)) / 3600, 1),
                })
            except (json.JSONDecodeError, OSError):
                pass
        return json.dumps({"status": "success", "sessions": sessions[:20]}, ensure_ascii=False)

    elif action == "cleanup":
        """Remove scratchpads older than TTL."""
        ws = _workspace_dir()
        cutoff = time.time() - _SESSION_TTL
        removed = 0
        for p in ws.glob("wm_*.json"):
            try:
                if p.stat().st_mtime < cutoff:
                    p.unlink()
                    removed += 1
            except OSError:
                pass
        return json.dumps({"status": "success", "message": f"Removed {removed} expired scratchpad(s)"}, ensure_ascii=False)

    else:
        return tool_error(f"Unknown action '{action}'. Valid: get, set, update, push, checkpoint, restore, clear, list_sessions, cleanup")


WORKING_MEMORY_SCHEMA = {
    "name": "working_memory",
    "description": (
        "Per-session structured scratchpad that persists across turns and survives context "
        "compression. Use this to track task state that you'd otherwise lose: current step, "
        "files changed, constraints, what failed, decisions made. "
        "Call working_memory(action='get') at the start of complex tasks to recover state "
        "from a previous turn or after compression. "
        "Call working_memory(action='update', field='...', value=...) to save progress. "
        "This is DIFFERENT from the memory tool — memory is for durable cross-session facts; "
        "working_memory is for ephemeral per-session task state."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get", "set", "update", "push", "checkpoint", "restore", "clear", "list_sessions", "cleanup"],
                "description": (
                    "get: read current scratchpad state. "
                    "set: replace multiple fields at once (pass 'state' object). "
                    "update: merge a single field (lists merge with dedup, dicts merge, scalars replace). "
                    "push: append an item to a list field (deduplicates). "
                    "checkpoint: save named snapshot for later restore. "
                    "restore: roll back to a named checkpoint. "
                    "clear: reset to empty (optionally keep specific fields). "
                    "list_sessions: see all session scratchpads. "
                    "cleanup: remove expired scratchpads."
                ),
            },
            "field": {
                "type": "string",
                "description": "Field name for update/push actions. Known fields: task, task_description, current_step, total_steps, step_descriptions, files_changed, files_read, constraints, what_failed, what_worked, decisions. Unknown fields go to notes.",
            },
            "value": {
                "description": "Value for 'update' action. Type depends on the field (string, int, list, dict, etc.).",
            },
            "item": {
                "description": "Item to append for 'push' action.",
            },
            "state": {
                "type": "object",
                "description": "Full or partial state object for 'set' action. Keys not in the default schema go to notes.",
            },
            "name": {
                "type": "string",
                "description": "Checkpoint name for 'checkpoint'/'restore' actions.",
            },
            "session": {
                "type": "string",
                "description": "Override session ID (defaults to current session).",
            },
            "keep": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Fields to preserve when using 'clear' action.",
            },
        },
        "required": ["action"],
    },
}


registry.register(
    name="working_memory",
    toolset="cognitive",
    schema=WORKING_MEMORY_SCHEMA,
    handler=working_memory_handler,
    emoji="🧠",
)
