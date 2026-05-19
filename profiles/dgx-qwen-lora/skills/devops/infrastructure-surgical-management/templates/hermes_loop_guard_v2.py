#!/usr/bin/env python3
"""
Hermes Loop Guard v2 — Intent-based loop detection.

Usage:
    python3 /tmp/hermes_loop_guard_v2.py <tool_name> <intent_desc> [error_msg]

Intent hash = short description of what you're trying to do (e.g., "find-training-logs", "check-gpu-status")
Returns exit code 1 if a loop is detected, 0 otherwise.

Rules:
1. Same tool + same intent 3+ times → STOP
2. Same error 2+ times → STOP  
3. Same tool 5+ times regardless of intent → STOP (fallback)
4. User says 'loop'/'stop'/'break' → STOP (env var HERMES_USER_STOP)
5. Diminishing returns: 3+ calls to same host/target with no new actionable data → STOP
"""

import sys
import json
import os
import hashlib
from pathlib import Path

STATE_FILE = Path("/tmp/hermes_loop_state_v2.json")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"calls": [], "user_stop": False, "last_alert": None}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def make_intent_hash(tool_name, intent_desc):
    raw = f"{tool_name}:{intent_desc}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def check_loop(tool_name, intent_desc, error_msg=None):
    state = load_state()
    now = __import__('datetime').datetime.now().isoformat()
    
    if os.environ.get("HERMES_USER_STOP"):
        print("LOOP GUARD: User stop signal detected. STOP.", file=sys.stderr)
        return 1
    
    intent_hash = make_intent_hash(tool_name, intent_desc)
    
    call_record = {
        "time": now,
        "tool": tool_name,
        "intent": intent_desc,
        "intent_hash": intent_hash,
        "error": error_msg
    }
    state["calls"].append(call_record)
    state["calls"] = state["calls"][-10:]
    
    # Same intent 3+ times
    recent_intents = [c["intent_hash"] for c in state["calls"][-3:]]
    if len(recent_intents) >= 3 and all(h == intent_hash for h in recent_intents):
        print(f"LOOP GUARD: Same intent '{intent_desc}' with tool '{tool_name}' 3+ times. STOP.", file=sys.stderr)
        save_state(state)
        return 1
    
    # Same error 2+ times
    if error_msg:
        recent_errors = [c.get("error") for c in state["calls"][-2:] if c.get("error")]
        if len(recent_errors) >= 2 and all(e == error_msg for e in recent_errors):
            print(f"LOOP GUARD: Same error repeated 2+ times: {error_msg}. STOP.", file=sys.stderr)
            save_state(state)
            return 1
    
    # Same tool 5+ times (fallback)
    recent_tools = [c["tool"] for c in state["calls"][-5:]]
    if len(recent_tools) >= 5 and all(t == tool_name for t in recent_tools):
        print(f"LOOP GUARD: Tool '{tool_name}' used 5+ times consecutively. STOP.", file=sys.stderr)
        save_state(state)
        return 1
    
    # Diminishing returns: SSH calls
    if tool_name == "terminal" and "ssh" in intent_desc.lower():
        ssh_calls = [c for c in state["calls"][-5:] if c["tool"] == "terminal" and "ssh" in c["intent"].lower()]
        if len(ssh_calls) >= 3:
            last_3_ssh = ssh_calls[-3:]
            ssh_intents = [c["intent_hash"] for c in last_3_ssh]
            if len(set(ssh_intents)) <= 2:
                print(f"LOOP GUARD: 3+ SSH calls with similar intent '{intent_desc}'. STOP.", file=sys.stderr)
                save_state(state)
                return 1
    
    save_state(state)
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 hermes_loop_guard_v2.py <tool_name> <intent_desc> [error_msg]", file=sys.stderr)
        sys.exit(2)
    
    tool_name = sys.argv[1]
    intent_desc = sys.argv[2]
    error_msg = sys.argv[3] if len(sys.argv) > 3 else None
    
    sys.exit(check_loop(tool_name, intent_desc, error_msg))
