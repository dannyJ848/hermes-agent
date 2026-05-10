#!/usr/bin/env python3
"""
hermes_context_gauge.py — Context window pressure monitor and handoff planner.

Monitors context usage, predicts compression timing, suggests checkpoint triggers.
Integrates with session_checkpoint for automatic handoffs.

Usage:
  from hermes_context_gauge import check_context_pressure, suggest_handoff
  
  pressure = check_context_pressure()
  if pressure['percent_used'] > 80:
      suggest_handoff()
"""

import os
import json
import time
from pathlib import Path

# Approximate token limits per model
MODEL_LIMITS = {
    "kimi-for-coding": 128000,
    "deepseek-chat": 64000,
    "deepseek-v4-pro": 64000,
    "glm-5.1": 32000,
    "default": 128000,
}

# Estimate: 4 chars per token (rough)
CHARS_PER_TOKEN = 4

def estimate_context_usage():
    """Estimate current context usage from environment or heuristics."""
    # Try to get from Hermes env if available
    hermes_context = os.environ.get("HERMES_CONTEXT_CHARS", "0")
    try:
        chars_used = int(hermes_context)
    except:
        chars_used = 0
    
    # Fallback: estimate from session file if exists
    if chars_used == 0:
        session_file = Path.home() / ".hermes" / "workspace" / "current_session.json"
        if session_file.exists():
            try:
                data = json.loads(session_file.read_text())
                chars_used = len(json.dumps(data))
            except:
                chars_used = 0
    
    # Get model limit
    model = os.environ.get("HERMES_MODEL", "default")
    limit = MODEL_LIMITS.get(model, MODEL_LIMITS["default"])
    
    tokens_used = chars_used / CHARS_PER_TOKEN
    percent_used = (tokens_used / limit) * 100 if limit else 0
    
    return {
        "chars_used": chars_used,
        "tokens_used": int(tokens_used),
        "token_limit": limit,
        "percent_used": percent_used,
        "model": model,
        "tokens_remaining": limit - int(tokens_used),
    }

def check_context_pressure():
    """Check current context pressure and return status."""
    usage = estimate_context_usage()
    
    percent = usage['percent_used']
    status = "GREEN"
    action = "NONE"
    
    if percent > 90:
        status = "RED"
        action = "CHECKPOINT_NOW"
    elif percent > 80:
        status = "YELLOW"
        action = "PLAN_HANDOFF"
    elif percent > 60:
        status = "ORANGE"
        action = "CONSIDER_CHECKPOINT"
    
    usage['status'] = status
    usage['action'] = action
    usage['timestamp'] = time.time()
    
    return usage

def suggest_handoff(reason: str = "context_pressure"):
    """Suggest and prepare a handoff checkpoint."""
    pressure = check_context_pressure()
    
    print(f"[CONTEXT-GAUGE] Status: {pressure['status']} ({pressure['percent_used']:.1f}%)")
    print(f"[CONTEXT-GAUGE] Tokens: {pressure['tokens_used']}/{pressure['token_limit']}")
    print(f"[CONTEXT-GAUGE] Action: {pressure['action']}")
    
    if pressure['action'] in ["CHECKPOINT_NOW", "PLAN_HANDOFF"]:
        print("[CONTEXT-GAUGE] Handoff recommended:")
        print("  1. Save session_checkpoint with full context")
        print("  2. Summarize active tasks for next CLI")
        print("  3. Clear non-essential context")
        
        # Auto-generate handoff summary
        handoff = {
            "timestamp": time.time(),
            "reason": reason,
            "pressure": pressure,
            "active_tasks": [],  # Would be populated from todo list
            "files_modified": [],  # Would be tracked
            "next_steps": "Resume from checkpoint",
        }
        
        # Save handoff note using cli_resume module
        try:
            from hermes_cli_resume import save_handoff
            save_handoff(handoff, reason=reason)
            print("[CONTEXT-GAUGE] Handoff saved for next CLI")
        except ImportError:
            # Fallback: save directly
            handoff_file = Path.home() / ".hermes" / "workspace" / "handoff_pending.json"
            handoff_file.write_text(json.dumps(handoff, indent=2, default=str))
            print("[CONTEXT-GAUGE] Handoff saved (fallback)")
        
        return handoff
    
    return None

def log_context_event(event: str, details: dict = None):
    """Log context window events for pattern analysis."""
    log_file = Path.home() / ".hermes" / "context_pressure_log.jsonl"
    
    entry = {
        "timestamp": time.time(),
        "event": event,
        "pressure": check_context_pressure(),
        "details": details or {},
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")

def get_context_history(hours: int = 24):
    """Get context pressure history."""
    log_file = Path.home() / ".hermes" / "context_pressure_log.jsonl"
    
    if not log_file.exists():
        return []
    
    since = time.time() - (hours * 3600)
    entries = []
    
    with open(log_file) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry['timestamp'] > since:
                    entries.append(entry)
            except:
                pass
    
    return entries

def predict_compression_time():
    """Predict when context compression will be needed based on growth rate."""
    history = get_context_history(hours=2)
    
    if len(history) < 2:
        return {"prediction": "INSUFFICIENT_DATA"}
    
    # Calculate growth rate
    first = history[0]['pressure']['tokens_used']
    last = history[-1]['pressure']['tokens_used']
    duration_hours = (history[-1]['timestamp'] - history[0]['timestamp']) / 3600
    
    if duration_hours < 0.1:
        return {"prediction": "INSUFFICIENT_DATA"}
    
    growth_rate = (last - first) / duration_hours  # tokens per hour
    
    if growth_rate <= 0:
        return {"prediction": "STABLE", "growth_rate": growth_rate}
    
    limit = history[-1]['pressure']['token_limit']
    remaining = limit - last
    hours_until_full = remaining / growth_rate
    
    return {
        "prediction": "WILL_FILL",
        "growth_rate_tokens_per_hour": growth_rate,
        "hours_until_full": hours_until_full,
        "recommendation": "CHECKPOINT_SOON" if hours_until_full < 2 else "MONITOR"
    }

if __name__ == "__main__":
    print("=== Context Gauge Test ===")
    
    pressure = check_context_pressure()
    print(f"Status: {pressure['status']} ({pressure['percent_used']:.1f}%)")
    print(f"Tokens: {pressure['tokens_used']}/{pressure['token_limit']}")
    
    print("\nPrediction:")
    pred = predict_compression_time()
    print(f"  {pred['prediction']}")
    if 'hours_until_full' in pred:
        print(f"  Hours until full: {pred['hours_until_full']:.1f}")
    
    print("\n=== Context Gauge Ready ===")
