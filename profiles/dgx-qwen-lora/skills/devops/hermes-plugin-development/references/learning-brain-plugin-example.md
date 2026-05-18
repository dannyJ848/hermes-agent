# Learning Brain Plugin — Complete Working Example

A self-improvement plugin that wires loop detection, error analysis, and tool intelligence into the agent runtime.

## Files

```
plugins/learning-brain/
  plugin.yaml      # Manifest
  __init__.py      # Hooks + brain singleton
  plugin.py        # (optional) Additional module code
```

## plugin.yaml

```yaml
name: learning-brain
version: 1.0.0
description: Self-improvement learning loop — loop guard, error analysis, tool intelligence
author: Hermes Agent
kind: standalone
provides_hooks:
  - pre_tool_call
  - post_tool_call
  - on_session_start
  - on_session_end
```

## __init__.py

```python
"""
Hermes Learning Brain Plugin
Wires self-improvement systems into the agent runtime.
"""

import json
import sys
from pathlib import Path

HERMES_ROOT = Path(__file__).resolve().parent.parent.parent
if str(HERMES_ROOT / "hermes_cli") not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT / "hermes_cli"))

from hermes_brain import HermesBrain
from context_updater import ContextUpdater

_brain = None
_updater = None

def _get_brain():
    global _brain
    if _brain is None:
        _brain = HermesBrain()
    return _brain

def _get_updater():
    global _updater
    if _updater is None:
        _updater = ContextUpdater()
    return _updater


def pre_tool_call_hook(**kwargs):
    """Loop guard — blocks repetitive tool calls."""
    brain = _get_brain()
    tool_name = kwargs.get("tool_name", "")
    args = kwargs.get("args", {})
    session_id = kwargs.get("session_id", "")

    check = brain.before_tool_call(tool_name, args, session_id)

    if check.get("action") == "BLOCK":
        # MUST return dict with action="block" — plain string won't block
        return {
            "action": "block",
            "message": f"[LEARNING BRAIN] {check.get('reason', 'Loop detected')}. "
                       f"Suggestion: {check.get('alternative', 'Try a different approach')}"
        }

    return None  # Allow the call


def post_tool_call_hook(**kwargs):
    """Error analysis + tool intelligence update."""
    brain = _get_brain()
    updater = _get_updater()

    tool_name = kwargs.get("tool_name", "")
    args = kwargs.get("args", {})
    result = kwargs.get("result", "")
    duration_ms = kwargs.get("duration_ms", 0)
    session_id = kwargs.get("session_id", "")

    # Detect errors in result
    success = True
    error = None
    try:
        parsed = json.loads(result) if isinstance(result, str) else result
        if isinstance(parsed, dict) and "error" in parsed:
            success = False
            error = parsed["error"]
    except (json.JSONDecodeError, TypeError):
        pass

    # Run post-flight analysis
    analysis = brain.after_tool_call(tool_name, args, result, error)

    # Update tool intelligence
    updater.update_tool_result(tool_name, success, duration_ms, error)

    if error:
        fix = analysis.get("lesson", "Review error and try alternative approach")
        updater.record_error(tool_name, error, fix)

    return {"success": success, "analyzed": True}


def on_session_start_hook(**kwargs):
    """Task initialization + tip preload."""
    brain = _get_brain()
    updater = _get_updater()

    session_id = kwargs.get("session_id", "unknown")
    user_message = kwargs.get("user_message", "")

    task_info = brain.on_task_start(user_message)
    updater.update_session(session_id, task=user_message[:100])

    return {
        "learning_tips": task_info.get("tips", []),
        "confidence": task_info.get("confidence", {}),
        "should_verify": task_info.get("should_verify", False),
    }


def on_session_end_hook(**kwargs):
    """Intent verification + budget check."""
    brain = _get_brain()
    session_id = kwargs.get("session_id", "")
    final_response = kwargs.get("final_response", "")

    budget = brain.on_task_end(session_id, "", final_response)
    return {"budget_status": budget.get("budget_status", {})}


def register(ctx):
    """Register all hooks."""
    ctx.register_hook("on_session_start", on_session_start_hook)
    ctx.register_hook("pre_tool_call", pre_tool_call_hook)
    ctx.register_hook("post_tool_call", post_tool_call_hook)
    ctx.register_hook("on_session_end", on_session_end_hook)
    print(f"[learning-brain] Learning loop wired: pre_tool_call, post_tool_call, "
          f"on_session_start, on_session_end")
```

## Loop Guard (hermes_cli/loop_guard.py)

```python
import sqlite3
import json
import hashlib

class LoopGuard:
    def __init__(self, threshold=3, window_seconds=60):
        self.threshold = int(threshold)      # Coerce to int
        self.window = int(window_seconds)    # Coerce to int
        self.conn = sqlite3.connect('/path/to/cerebrum_memory.db')
        self._ensure_table()

    def _ensure_table(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS loop_detection (
                id INTEGER PRIMARY KEY,
                tool_name TEXT,
                args_hash TEXT,
                timestamp TIMESTAMP,
                session_id TEXT
            )
        ''')
        self.conn.commit()

    def check_loop(self, tool_name, args, session_id="default"):
        args_hash = hashlib.md5(
            json.dumps(args, sort_keys=True).encode()
        ).hexdigest()[:16]

        c = self.conn.cursor()
        c.execute('''
            SELECT COUNT(*) FROM loop_detection
            WHERE tool_name = ? AND args_hash = ?
            AND timestamp > datetime('now', '-{} seconds')
        '''.format(self.window), (tool_name, args_hash))

        count = int(c.fetchone()[0])  # Coerce to int — SQLite may return string

        # Log this attempt
        c.execute('''
            INSERT INTO loop_detection (tool_name, args_hash, timestamp, session_id)
            VALUES (?, ?, datetime('now'), ?)
        ''', (tool_name, args_hash, session_id))
        self.conn.commit()

        if count >= self.threshold:
            return {
                'is_loop': True,
                'count': count + 1,
                'recommendation': self._get_alternative(tool_name),
                'action': 'BLOCK'
            }

        return {'is_loop': False, 'count': count + 1}

    def _get_alternative(self, tool_name):
        alternatives = {
            'patch': 'Use write_file or terminal sed instead',
            'skill_manage': 'Use write_file to create SKILL.md directly',
            'cronjob': 'Use terminal crontab or python schedule library',
        }
        return alternatives.get(tool_name, 'Try a different approach')
```

## Behavior

| Call # | Result |
|--------|--------|
| 1-3 | Allowed (count < threshold=3) |
| 4+ | Blocked with message suggesting alternative |

## Config Activation

Add to `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - learning-brain
```

## Testing

```python
from hermes_cli.plugins import discover_plugins, get_pre_tool_call_block_message

discover_plugins(force=True)

for i in range(6):
    block = get_pre_tool_call_block_message(
        tool_name='web_search',
        args={'query': 'same'},
        session_id='test'
    )
    print(f"Call {i+1}: {block or 'ALLOWED'}")
```

Output:
```
Call 1: ALLOWED
Call 2: ALLOWED
Call 3: ALLOWED
Call 4: [LEARNING BRAIN] Loop detected (4 repeats). Suggestion: Try a different approach
Call 5: [LEARNING BRAIN] Loop detected (5 repeats). Suggestion: Try a different approach
```
