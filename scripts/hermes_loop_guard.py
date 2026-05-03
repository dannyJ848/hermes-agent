#!/usr/bin/env python3
"""
Hard loop guard enforcement.
Run this before every tool call to check if we're looping.
"""
import sys
import json

# Simple state tracking (in-memory only, resets on restart)
STATE_FILE = "/tmp/hermes_loop_guard_state.json"

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"calls": [], "errors": [], "last_user_msg": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def check_loop(tool_name, expected_error=None):
    state = load_state()
    
    # Add this call
    state["calls"].append(tool_name)
    if len(state["calls"]) > 10:
        state["calls"] = state["calls"][-10:]
    
    # Check 1: Same tool 3+ times in a row
    if len(state["calls"]) >= 3:
        last_3 = state["calls"][-3:]
        if all(c == tool_name for c in last_3):
            return False, f"LOOP GUARD: Same tool '{tool_name}' called 3+ times consecutively. STOP."
    
    # Check 2: Same error 2+ times
    if expected_error:
        state["errors"].append(expected_error)
        if len(state["errors"]) > 5:
            state["errors"] = state["errors"][-5:]
        
        if len(state["errors"]) >= 2:
            last_2 = state["errors"][-2:]
            if last_2[0] == last_2[1]:
                return False, f"LOOP GUARD: Same error '{expected_error}' returned 2+ times. STOP."
    
    save_state(state)
    return True, "OK"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 loop_guard.py <tool_name> [error_msg]")
        sys.exit(1)
    
    tool_name = sys.argv[1]
    error_msg = sys.argv[2] if len(sys.argv) > 2 else None
    
    ok, msg = check_loop(tool_name, error_msg)
    print(msg)
    sys.exit(0 if ok else 1)
