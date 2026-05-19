#!/usr/bin/env python3
"""
Hermes Loop Guard — Hard enforcement against repetitive tool-call loops.

Usage:
    python3 hermes_loop_guard.py <tool_name> [error_msg]

Returns exit code 1 if a loop is detected, 0 otherwise.
Tracks state in a JSON file so it persists across calls.

Rules:
1. Same tool 3+ times consecutively → STOP
2. Same error 2+ times → STOP
3. User says 'loop'/'stop'/'break' → STOP (detected via env var HERMES_USER_STOP)
"""

import sys
import json
import os
from pathlib import Path

STATE_FILE = Path("/tmp/hermes_loop_state.json")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_tools": [], "last_errors": [], "user_stop": False}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def check_loop(tool_name, error_msg=None):
    state = load_state()
    
    # Check user stop signal
    if os.environ.get("HERMES_USER_STOP"):
        print("LOOP GUARD: User stop signal detected. STOP.")
        return 1
    
    # Track tool calls
    state["last_tools"].append(tool_name)
    if len(state["last_tools"]) > 5:
        state["last_tools"] = state["last_tools"][-5:]
    
    # Check same tool 3+ times
    if len(state["last_tools"]) >= 3:
        last_three = state["last_tools"][-3:]
        if all(t == tool_name for t in last_three):
            print(f"LOOP GUARD: Same tool '{tool_name}' called 3+ times consecutively. STOP.")
            return 1
    
    # Track errors
    if error_msg:
        state["last_errors"].append(error_msg)
        if len(state["last_errors"]) > 3:
            state["last_errors"] = state["last_errors"][-3:]
        
        # Check same error 2+ times
        if len(state["last_errors"]) >= 2:
            last_two = state["last_errors"][-2:]
            if last_two[0] == last_two[1]:
                print(f"LOOP GUARD: Same error repeated 2+ times: {error_msg}. STOP.")
                return 1
    
    save_state(state)
    return 0

if __name__ == "__main__":
    tool_name = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    error_msg = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(check_loop(tool_name, error_msg))
