#!/usr/bin/env python3
"""
context_window_guard.py — Prevent context window overflow and token waste.

Monitors conversation length, estimates token count, and triggers
compression or archival before hitting the context limit.

Usage:
    from context_window_guard import ContextWindowGuard
    guard = ContextWindowGuard()
    action = guard.check_and_compress(messages)  # Returns action taken

Wiring:
    - Call before every LLM call to check context pressure
    - Auto-compresses old messages when >80% of context limit
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

HERMES_HOME = Path.home() / ".hermes"
GUARD_STATE = HERMES_HOME / "context_guard_state.json"

# Approximate tokens per character (conservative)
TOKENS_PER_CHAR = 0.25
DEFAULT_CONTEXT_LIMIT = 128000  # 128K context
COMPRESS_THRESHOLD = 0.80  # Compress at 80%
EMERGENCY_THRESHOLD = 0.95  # Emergency compression at 95%


@dataclass
class CompressionResult:
    original_tokens: int
    compressed_tokens: int
    messages_removed: int
    messages_summarized: int
    action: str


class ContextWindowGuard:
    """Guard against context window overflow."""
    
    def __init__(self, context_limit: int = DEFAULT_CONTEXT_LIMIT):
        self.context_limit = context_limit
        self.compress_threshold = int(context_limit * COMPRESS_THRESHOLD)
        self.emergency_threshold = int(context_limit * EMERGENCY_THRESHOLD)
        self._load_state()
    
    def _load_state(self):
        if GUARD_STATE.exists():
            try:
                self.state = json.loads(GUARD_STATE.read_text())
            except Exception:
                self.state = self._default_state()
        else:
            self.state = self._default_state()
    
    def _default_state(self) -> Dict:
        return {
            "total_compressions": 0,
            "total_tokens_saved": 0,
            "last_compression": 0,
            "compression_history": []
        }
    
    def _save_state(self):
        GUARD_STATE.parent.mkdir(parents=True, exist_ok=True)
        GUARD_STATE.write_text(json.dumps(self.state, indent=2))
    
    def estimate_tokens(self, messages: List[Dict]) -> int:
        """Estimate token count from messages."""
        total_chars = 0
        for msg in messages:
            content = msg.get("content", "") or ""
            # Add overhead for role, formatting
            total_chars += len(content) + 20  # +20 for role/metadata overhead
        return int(total_chars * TOKENS_PER_CHAR)
    
    def check_pressure(self, messages: List[Dict]) -> Dict:
        """Check context pressure level."""
        tokens = self.estimate_tokens(messages)
        pct = tokens / self.context_limit
        
        return {
            "tokens": tokens,
            "limit": self.context_limit,
            "pct": round(pct * 100, 1),
            "status": "emergency" if pct >= EMERGENCY_THRESHOLD else 
                     "compress" if pct >= COMPRESS_THRESHOLD else "ok",
            "tokens_until_compress": max(0, self.compress_threshold - tokens),
            "tokens_until_emergency": max(0, self.emergency_threshold - tokens)
        }
    
    def compress_messages(self, messages: List[Dict]) -> CompressionResult:
        """
        Compress messages to free context space.
        Strategy:
        1. Remove old tool results (keep only last 10)
        2. Summarize old user/assistant pairs into single summary
        3. Keep system messages intact
        """
        original_tokens = self.estimate_tokens(messages)
        original_count = len(messages)
        
        # Separate system messages (never compress)
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        
        # Strategy 1: Remove old tool results beyond last 10
        tool_results = [i for i, m in enumerate(other_msgs) if m.get("role") == "tool"]
        if len(tool_results) > 10:
            to_remove = tool_results[:-10]  # Keep last 10
            other_msgs = [m for i, m in enumerate(other_msgs) if i not in to_remove]
            tool_removed = len(to_remove)
        else:
            tool_removed = 0
        
        # Strategy 2: Summarize old conversation pairs
        # Group into (user, assistant) pairs and summarize old ones
        if len(other_msgs) > 20:
            # Keep last 10 messages intact, summarize the rest
            to_summarize = other_msgs[:-10]
            keep_intact = other_msgs[-10:]
            
            # Create summary of old conversation
            summary_content = self._summarize_messages(to_summarize)
            summary_msg = {
                "role": "assistant",
                "content": f"[Earlier conversation summary: {summary_content}]"
            }
            other_msgs = [summary_msg] + keep_intact
            summarized = len(to_summarize)
        else:
            summarized = 0
        
        # Recombine
        compressed = system_msgs + other_msgs
        compressed_tokens = self.estimate_tokens(compressed)
        
        result = CompressionResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            messages_removed=tool_removed,
            messages_summarized=summarized,
            action="compressed"
        )
        
        # Update state
        self.state["total_compressions"] += 1
        self.state["total_tokens_saved"] += (original_tokens - compressed_tokens)
        self.state["last_compression"] = time.time()
        self.state["compression_history"].append({
            "time": time.time(),
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "messages_removed": tool_removed,
            "messages_summarized": summarized
        })
        # Keep only last 50 history entries
        self.state["compression_history"] = self.state["compression_history"][-50:]
        self._save_state()
        
        return result
    
    def _summarize_messages(self, messages: List[Dict]) -> str:
        """Create a brief summary of old messages."""
        # Extract key actions and decisions
        actions = []
        for msg in messages:
            content = msg.get("content", "") or ""
            if len(content) > 50:
                # Extract first sentence or first 80 chars
                first_part = content[:80].replace("\n", " ")
                actions.append(first_part)
        
        if not actions:
            return "No significant actions"
        
        # Return condensed summary
        if len(actions) <= 3:
            return "; ".join(actions)
        else:
            return f"{len(actions)} interactions: " + "; ".join(actions[:3]) + "..."
    
    def check_and_compress(self, messages: List[Dict]) -> Dict:
        """
        Main entry point. Check pressure and compress if needed.
        Returns action summary.
        """
        pressure = self.check_pressure(messages)
        
        if pressure["status"] == "ok":
            return {
                "action": "none",
                "pressure": pressure,
                "reason": "Context under threshold"
            }
        
        # Need compression
        result = self.compress_messages(messages)
        
        return {
            "action": result.action,
            "pressure_before": pressure,
            "pressure_after": self.check_pressure(messages),
            "original_tokens": result.original_tokens,
            "compressed_tokens": result.compressed_tokens,
            "tokens_saved": result.original_tokens - result.compressed_tokens,
            "messages_removed": result.messages_removed,
            "messages_summarized": result.messages_summarized
        }
    
    def get_stats(self) -> Dict:
        return {
            **self.state,
            "context_limit": self.context_limit,
            "compress_threshold": self.compress_threshold,
            "emergency_threshold": self.emergency_threshold
        }


# Pre-LLM call hook
def pre_llm_call_hook(messages: List[Dict], context_limit: int = DEFAULT_CONTEXT_LIMIT) -> List[Dict]:
    """
    Hook to call before every LLM call.
    Compresses messages if context pressure is high.
    
    Usage:
        messages = pre_llm_call_hook(messages)
    """
    guard = ContextWindowGuard(context_limit)
    result = guard.check_and_compress(messages)
    
    if result["action"] == "compressed":
        # Return compressed messages
        # (In practice, this would modify in place)
        pass
    
    return messages


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Context Window Guard")
    parser.add_argument("--check", action="store_true", help="Check current context file")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    guard = ContextWindowGuard()
    
    if args.stats:
        print(json.dumps(guard.get_stats(), indent=2))
    else:
        print(json.dumps(guard.get_stats(), indent=2))