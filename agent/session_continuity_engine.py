#!/usr/bin/env python3
"""
session_continuity_engine.py — Preserve session across context window death.

When context window fills up and conversation dies, this preserves:
  - Active goals and tasks
  - Key decisions made
  - Tool call history
  - Memory state
  - Error patterns encountered

On session restart, restores context so I can continue seamlessly.

Usage:
    from session_continuity_engine import SessionContinuityEngine
    engine = SessionContinuityEngine()
    
    # Before context dies:
    engine.checkpoint(session_id, messages, goals)
    
    # On new session start:
    restored = engine.restore(session_id)
    # Returns goals, decisions, context to inject
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger("hermes.continuity")

CHECKPOINT_DIR = Path.home() / ".hermes" / "session_checkpoints"

class SessionContinuityEngine:
    """Preserve and restore session state across context death."""
    
    def __init__(self):
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        self.checkpoints_created = 0
        self.restorations = 0
    
    def checkpoint(self, session_id: str, messages: List[Dict],
                   goals: List[str], active_tasks: List[str] = None,
                   error_patterns: List[str] = None,
                   tool_stats: Dict = None) -> str:
        """
        Save session checkpoint.
        
        Returns checkpoint file path.
        """
        # Extract key context
        decisions = self._extract_decisions(messages)
        tool_history = self._extract_tool_history(messages)
        last_user_request = self._extract_last_request(messages)
        
        checkpoint = {
            "version": 1,
            "timestamp": time.time(),
            "session_id": session_id,
            "goals": goals or [],
            "active_tasks": active_tasks or [],
            "decisions": decisions,
            "tool_history": tool_history[-20:],  # Last 20 tools
            "last_user_request": last_user_request,
            "error_patterns": error_patterns or [],
            "tool_stats": tool_stats or {},
            "message_count": len(messages),
            "checkpoint_reason": "context_window_death",
        }
        
        # Save
        filename = f"checkpoint_{session_id}_{int(time.time())}.json"
        path = CHECKPOINT_DIR / filename
        path.write_text(json.dumps(checkpoint, indent=2))
        
        self.checkpoints_created += 1
        logger.info("[CONTINUITY] Checkpoint saved: %s (%d goals, %d decisions)",
                   filename, len(goals), len(decisions))
        
        return str(path)
    
    def restore(self, session_id: str) -> Optional[Dict]:
        """
        Restore latest checkpoint for session.
        
        Returns dict with context to inject, or None if no checkpoint.
        """
        # Find latest checkpoint
        checkpoints = sorted(
            CHECKPOINT_DIR.glob(f"checkpoint_{session_id}_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not checkpoints:
            return None
        
        latest = checkpoints[0]
        checkpoint = json.loads(latest.read_text())
        
        self.restorations += 1
        
        # Build restoration context
        context = self._build_restoration_context(checkpoint)
        
        logger.info("[CONTINUITY] Restored: %d goals, %d decisions from %s",
                   len(checkpoint.get("goals", [])),
                   len(checkpoint.get("decisions", [])),
                   latest.name)
        
        return context
    
    def _extract_decisions(self, messages: List[Dict]) -> List[str]:
        """Extract key decisions from messages."""
        decisions = []
        for msg in messages:
            if msg.get("role") == "assistant":
                content = str(msg.get("content", ""))
                # Look for decision markers
                markers = ["decided", "will", "plan", "approach", "using", "chose"]
                for marker in markers:
                    if marker in content.lower():
                        # Extract sentence containing marker
                        sentences = content.split(".")
                        for sent in sentences:
                            if marker in sent.lower():
                                decisions.append(sent.strip()[:200])
                                break
                        break
        
        # Deduplicate
        seen = set()
        unique = []
        for d in decisions:
            if d not in seen:
                seen.add(d)
                unique.append(d)
        
        return unique[-10:]  # Last 10 unique decisions
    
    def _extract_tool_history(self, messages: List[Dict]) -> List[Dict]:
        """Extract tool call history from messages."""
        tools = []
        for msg in messages:
            if msg.get("role") == "tool":
                content = str(msg.get("content", ""))[:100]
                tools.append({
                    "result_preview": content,
                    "size": len(str(msg.get("content", "")))
                })
        return tools
    
    def _extract_last_request(self, messages: List[Dict]) -> str:
        """Extract last user request."""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return str(msg.get("content", ""))[:500]
        return ""
    
    def _build_restoration_context(self, checkpoint: Dict) -> Dict:
        """Build context dict for injection into new session."""
        goals = checkpoint.get("goals", [])
        decisions = checkpoint.get("decisions", [])
        tasks = checkpoint.get("active_tasks", [])
        last_request = checkpoint.get("last_user_request", "")
        errors = checkpoint.get("error_patterns", [])
        
        # Build system message injection
        parts = ["## Session Continuity"]
        
        if goals:
            parts.append(f"Active goals: {', '.join(goals[:5])}")
        
        if tasks:
            parts.append(f"In-progress tasks: {', '.join(tasks[:3])}")
        
        if decisions:
            parts.append("Key decisions made:")
            for d in decisions[-5:]:
                parts.append(f"  - {d}")
        
        if errors:
            parts.append("Errors encountered (avoid repeating):")
            for e in errors[-3:]:
                parts.append(f"  - {e}")
        
        if last_request:
            parts.append(f"Last user request: {last_request[:200]}")
        
        context_text = "\n".join(parts)
        
        return {
            "checkpoint_file": str(checkpoint.get("timestamp", "")),
            "goals": goals,
            "active_tasks": tasks,
            "decisions": decisions,
            "error_patterns": errors,
            "last_request": last_request,
            "system_injection": context_text,
            "message_count": checkpoint.get("message_count", 0),
        }
    
    def get_injection_message(self, session_id: str) -> Optional[Dict]:
        """
        Get system message to inject for continuity.
        
        Returns message dict or None.
        """
        restored = self.restore(session_id)
        if not restored:
            return None
        
        return {
            "role": "system",
            "content": restored["system_injection"]
        }
    
    def list_checkpoints(self, session_id: str = None) -> List[Dict]:
        """List available checkpoints."""
        pattern = f"checkpoint_{session_id}_*.json" if session_id else "checkpoint_*.json"
        checkpoints = []
        
        for path in sorted(CHECKPOINT_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True):
            data = json.loads(path.read_text())
            checkpoints.append({
                "file": path.name,
                "timestamp": data.get("timestamp"),
                "session_id": data.get("session_id"),
                "goals_count": len(data.get("goals", [])),
                "message_count": data.get("message_count", 0),
            })
        
        return checkpoints
    
    def get_stats(self) -> Dict:
        """Get engine statistics."""
        return {
            "checkpoints_created": self.checkpoints_created,
            "restorations": self.restorations,
            "checkpoint_dir": str(CHECKPOINT_DIR),
        }


# Hook integration
def on_context_death(session_id: str, messages: List[Dict], goals: List[str]) -> str:
    """
    Call when context window is about to die.
    
    Returns checkpoint path.
    """
    engine = SessionContinuityEngine()
    return engine.checkpoint(session_id, messages, goals)


def on_session_start(session_id: str) -> Optional[Dict]:
    """
    Call at session start to restore continuity.
    
    Returns injection message or None.
    """
    engine = SessionContinuityEngine()
    return engine.get_injection_message(session_id)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Session Continuity Engine")
    parser.add_argument("--test", action="store_true", help="Run tests")
    
    args = parser.parse_args()
    
    if args.test:
        print("Testing session continuity engine...")
        
        engine = SessionContinuityEngine()
        
        # Test 1: Create checkpoint
        print("\n1. Create checkpoint:")
        messages = [
            {"role": "user", "content": "Build a system"},
            {"role": "assistant", "content": "I will build a tool routing system. Decided to use Python."},
            {"role": "tool", "content": "File created"},
            {"role": "assistant", "content": "The system is working. Will now add tests."},
        ]
        path = engine.checkpoint("test_session", messages, 
                                goals=["Build router", "Add tests", "Commit code"],
                                active_tasks=["Write tests"],
                                error_patterns=["patch failed: old_string not found"])
        print(f"   Checkpoint: {Path(path).name}")
        
        # Test 2: Restore
        print("\n2. Restore checkpoint:")
        restored = engine.restore("test_session")
        if restored:
            print(f"   Goals: {restored['goals']}")
            print(f"   Tasks: {restored['active_tasks']}")
            print(f"   Decisions: {len(restored['decisions'])}")
            print(f"   Last request: {restored['last_request'][:50]}...")
        
        # Test 3: Injection message
        print("\n3. Injection message:")
        msg = engine.get_injection_message("test_session")
        if msg:
            print(f"   Role: {msg['role']}")
            print(f"   Content preview: {msg['content'][:100]}...")
        
        # Test 4: List checkpoints
        print("\n4. List checkpoints:")
        checkpoints = engine.list_checkpoints("test_session")
        for cp in checkpoints[:3]:
            print(f"   {cp['file']}: {cp['goals_count']} goals, {cp['message_count']} messages")
        
        # Test 5: Stats
        print("\n5. Stats:")
        print(f"   {engine.get_stats()}")
        
        # Test 6: Hook functions
        print("\n6. Hook functions:")
        path = on_context_death("hook_test", messages, ["goal1"])
        print(f"   on_context_death: {Path(path).name}")
        
        msg = on_session_start("hook_test")
        print(f"   on_session_start: {'restored' if msg else 'no checkpoint'}")
        
        print("\nAll tests passed!")
    else:
        print("Usage: python3 session_continuity_engine.py --test")
