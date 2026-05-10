#!/usr/bin/env python3
"""
hermes_cli_resume.py — Automatic checkpoint restore for new CLI sessions.

Checks for pending checkpoint on startup, restores if found.
Generates handoff summary for human review.

Usage (add to shell profile or hermes startup):
  python3 ~/hermes-agent/agent/hermes_cli_resume.py

This should run automatically when a new Hermes CLI starts.
"""

import json
import time
from pathlib import Path

CHECKPOINT_DIR = Path.home() / ".hermes" / "workspace" / "checkpoints"
HANDOFF_FILE = Path.home() / ".hermes" / "workspace" / "handoff_pending.json"
RESUME_LOG = Path.home() / ".hermes" / "workspace" / "resume_history.jsonl"

def _log_resume_event(event: str, details: dict):
    entry = {
        "timestamp": time.time(),
        "event": event,
        **details
    }
    with open(RESUME_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

def find_latest_checkpoint():
    """Find the most recent checkpoint file."""
    if not CHECKPOINT_DIR.exists():
        return None
    
    checkpoints = sorted(CHECKPOINT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not checkpoints:
        return None
    
    return checkpoints[0]

def check_for_handoff():
    """Check if there's a pending handoff from previous session."""
    if not HANDOFF_FILE.exists():
        return None
    
    try:
        handoff = json.loads(HANDOFF_FILE.read_text())
        
        # Check if handoff is recent (within 24 hours)
        if time.time() - handoff.get("timestamp", 0) < 86400:
            return handoff
        else:
            # Stale handoff - archive it
            archive = HANDOFF_FILE.with_suffix(".archived.json")
            HANDOFF_FILE.rename(archive)
            return None
    except Exception:
        return None

def generate_resume_summary(checkpoint_path: Path, handoff: dict = None):
    """Generate a human-readable resume summary."""
    lines = []
    lines.append("=" * 60)
    lines.append("HERMES SESSION RESUME")
    lines.append("=" * 60)
    
    if handoff:
        lines.append(f"Handoff from: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(handoff.get('timestamp', 0)))}")
        lines.append(f"Reason: {handoff.get('reason', 'unknown')}")
        
        if 'pressure' in handoff:
            p = handoff['pressure']
            lines.append(f"Context was: {p.get('status', 'unknown')} ({p.get('percent_used', 0):.1f}%)")
        
        if 'active_tasks' in handoff and handoff['active_tasks']:
            lines.append("\nActive tasks:")
            for task in handoff['active_tasks']:
                lines.append(f"  - {task}")
        
        if 'next_steps' in handoff:
            lines.append(f"\nNext steps: {handoff['next_steps']}")
    
    if checkpoint_path:
        lines.append(f"\nCheckpoint: {checkpoint_path.name}")
        mtime = checkpoint_path.stat().st_mtime
        lines.append(f"Saved: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))}")
        age_hours = (time.time() - mtime) / 3600
        lines.append(f"Age: {age_hours:.1f} hours")
    
    lines.append("\n" + "=" * 60)
    lines.append("To resume: Use session_restore() or tell Hermes 'resume from checkpoint'")
    lines.append("=" * 60)
    
    return "\n".join(lines)

def auto_resume():
    """Main auto-resume logic. Called on CLI startup."""
    handoff = check_for_handoff()
    checkpoint = find_latest_checkpoint()
    
    if not handoff and not checkpoint:
        _log_resume_event("no_resume_needed", {"reason": "no handoff or checkpoint found"})
        return None
    
    # Generate summary
    summary = generate_resume_summary(checkpoint, handoff)
    
    # Print to terminal (will be seen by user)
    print(summary)
    
    # Log the resume
    _log_resume_event("resume_prompt", {
        "handoff": handoff is not None,
        "checkpoint": str(checkpoint) if checkpoint else None,
    })
    
    return {
        "handoff": handoff,
        "checkpoint": str(checkpoint) if checkpoint else None,
        "summary": summary,
    }

def mark_resumed():
    """Mark that the session has been resumed (clear handoff)."""
    if HANDOFF_FILE.exists():
        HANDOFF_FILE.unlink()
    
    _log_resume_event("resumed", {"timestamp": time.time()})

def save_handoff(context: dict, reason: str = "context_pressure"):
    """Save a handoff for the next CLI session."""
    handoff = {
        "timestamp": time.time(),
        "reason": reason,
        "active_tasks": context.get("active_tasks", []),
        "files_modified": context.get("files_modified", []),
        "next_steps": context.get("next_steps", "Continue from last checkpoint"),
        "notes": context.get("notes", ""),
    }
    
    HANDOFF_FILE.write_text(json.dumps(handoff, indent=2, default=str))
    _log_resume_event("handoff_saved", {"reason": reason})

if __name__ == "__main__":
    print("=== Hermes CLI Resume Check ===\n")
    
    result = auto_resume()
    
    if result:
        print("\n[RESUME] Handoff detected - review summary above")
        print("[RESUME] To mark as resumed, call mark_resumed()")
    else:
        print("No pending handoff or checkpoint. Fresh start.")
    
    print("\n=== Resume Check Complete ===")
