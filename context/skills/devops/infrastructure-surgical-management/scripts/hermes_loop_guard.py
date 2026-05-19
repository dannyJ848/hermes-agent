#!/usr/bin/env python3
"""
Hard loop guard enforcement for Hermes Agent.
Run before every tool call to detect and prevent repetitive loops.

Usage: python3 hermes_loop_guard.py <tool_name> [error_msg]
Exit code 1 if loop detected (3+ same tool calls or 2+ same errors).
"""
import sys
import json

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

def check_loop(tool_name, error_msg=None):
    state = load_state()
    
    # Check same tool called 3+ times
    state["calls"].append(tool_name)
    if len(state["calls"]) > 20:
        state["calls"] = state["calls"][-20:]
    
    same_tool_count = sum(1 for c in state["calls"][-5:] if c == tool_name)
    if same_tool_count >= 3:
        print(f"LOOP GUARD: Same tool '{tool_name}' called {same_tool_count} times. STOP.")
        save_state(state)
        sys.exit(1)
    
    # Check same error 2+ times
    if error_msg:
        state["errors"].append(error_msg)
        if len(state["errors"]) > 10:
            state["errors"] = state["errors"][-10:]
        
        same_error_count = sum(1 for e in state["errors"][-5:] if e == error_msg)
        if same_error_count >= 2:
            print(f"LOOP GUARD: Same error occurred {same_error_count} times. STOP.")
            save_state(state)
            sys.exit(1)
    
    save_state(state)
    print("OK")
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: hermes_loop_guard.py <tool_name> [error_msg]")
        sys.exit(0)
    
    check_loop(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
