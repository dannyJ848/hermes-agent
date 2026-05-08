#!/usr/bin/env python3
"""
self_audit_engine.py — Hermes Agent self-audit and performance optimization system.

Tracks: loop detection, token waste, pre-flight checks, recovery patterns.
Wires into learning-brain plugin for continuous improvement.

Usage:
    from self_audit_engine import SelfAuditEngine
    audit = SelfAuditEngine()
    audit.record_call(tool_name, args, result)
    audit.check_loop()  # Returns True if looping detected
    audit.get_waste_report()  # Shows token waste analysis
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import deque

HERMES_HOME = Path.home() / ".hermes"
AUDIT_DB = HERMES_HOME / "self_audit.db"


class SelfAuditEngine:
    """Tracks tool-use patterns, detects loops, learns recovery strategies."""
    
    def __init__(self, loop_window: int = 5, similarity_threshold: float = 0.85):
        self.loop_window = loop_window  # How many recent calls to check
        self.similarity_threshold = similarity_threshold
        self._call_history: deque = deque(maxlen=50)
        self._loop_count = 0
        self._wasted_calls = 0
        self._recovery_successes = []
        
    def _hash_call(self, tool_name: str, args: Dict) -> str:
        """Hash a tool call for similarity comparison."""
        # Normalize: ignore values that change every call (timestamps, temp paths)
        normalized = {k: v for k, v in args.items() 
                       if k not in ('timestamp', 'temp_path', 'random_seed')}
        content = f"{tool_name}:{json.dumps(normalized, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def record_call(self, tool_name: str, args: Dict, result: Any, 
                    tokens_used: int = 0, duration_ms: float = 0) -> Dict:
        """Record a tool call and analyze patterns."""
        call_hash = self._hash_call(tool_name, args)
        
        entry = {
            "timestamp": time.time(),
            "tool": tool_name,
            "hash": call_hash,
            "args_keys": list(args.keys()),
            "success": self._is_success(result),
            "tokens": tokens_used,
            "duration_ms": duration_ms,
            "result_preview": str(result)[:200] if result else "",
        }
        
        self._call_history.append(entry)
        
        # Check for loops
        loop_detected = self._detect_loop()
        
        # Check for waste
        waste_detected = self._detect_waste(entry)
        
        return {
            "loop_detected": loop_detected,
            "waste_detected": waste_detected,
            "loop_count": self._loop_count,
            "total_calls": len(self._call_history),
        }
    
    def _is_success(self, result: Any) -> bool:
        """Heuristic: did the call produce value?"""
        if result is None:
            return False
        if isinstance(result, dict):
            if result.get("error") or result.get("status") == "failed":
                return False
            # Check for empty but "successful" results
            if result.get("total_count") == 0 or result.get("count") == 0:
                return False
        if isinstance(result, str):
            if result.strip() == "" or result.startswith("Warning:"):
                return False
        return True
    
    def _detect_loop(self) -> bool:
        """Detect if we're repeating similar calls without progress."""
        if len(self._call_history) < self.loop_window:
            return False
        
        recent = list(self._call_history)[-self.loop_window:]
        hashes = [c["hash"] for c in recent]
        
        # Check for exact repeats (3+ identical calls)
        unique_hashes = set(hashes)
        if len(unique_hashes) == 1 and len(hashes) >= 3:
            self._loop_count += 1
            return True
        
        # Check for tool-level loops (same tool, all failing, 3+ calls)
        tools = [c["tool"] for c in recent]
        if len(set(tools)) == 1 and all(not c["success"] for c in recent) and len(recent) >= 3:
            self._loop_count += 1
            return True
        
        return False
    
    def _detect_waste(self, entry: Dict) -> bool:
        """Detect calls that consumed tokens but produced no value."""
        if entry["tokens"] > 100 and not entry["success"]:
            self._wasted_calls += 1
            return True
        # Repeated successful calls with same output = waste
        if len(self._call_history) > 1:
            prev = list(self._call_history)[-2]
            if (entry["hash"] == prev["hash"] and 
                entry["result_preview"] == prev["result_preview"]):
                self._wasted_calls += 1
                return True
        return False
    
    def get_loop_status(self) -> Dict:
        """Current loop detection status."""
        recent = list(self._call_history)[-self.loop_window:]
        return {
            "loop_detected": self._detect_loop(),
            "loop_count": self._loop_count,
            "recent_calls": len(recent),
            "unique_tools": len(set(c["tool"] for c in recent)),
            "success_rate_recent": sum(c["success"] for c in recent) / len(recent) if recent else 0,
        }
    
    def get_waste_report(self) -> Dict:
        """Token waste analysis."""
        total_calls = len(self._call_history)
        return {
            "total_calls": total_calls,
            "wasted_calls": self._wasted_calls,
            "waste_pct": (self._wasted_calls / total_calls * 100) if total_calls else 0,
            "top_wasted_tools": self._get_top_wasted_tools(),
        }
    
    def _get_top_wasted_tools(self) -> List[Dict]:
        """Which tools waste the most tokens."""
        tool_waste = {}
        for entry in self._call_history:
            if not entry["success"] and entry["tokens"] > 100:
                tool = entry["tool"]
                tool_waste[tool] = tool_waste.get(tool, 0) + entry["tokens"]
        
        sorted_tools = sorted(tool_waste.items(), key=lambda x: x[1], reverse=True)
        return [{"tool": t, "wasted_tokens": w} for t, w in sorted_tools[:5]]
    
    def suggest_recovery(self) -> List[str]:
        """Suggest recovery actions based on current state."""
        suggestions = []
        
        loop_status = self.get_loop_status()
        if loop_status["loop_detected"]:
            suggestions.append("[RESCUE] Loop detected! Break pattern:")
            suggestions.append("  1. Stop repeating the same tool")
            suggestions.append("  2. Switch to a different approach (write_file instead of patch)")
            suggestions.append("  3. Ask user for clarification")
            suggestions.append("  4. Use execute_code for complex multi-step logic")
        
        # Tool-specific advice
        recent_tools = [c["tool"] for c in list(self._call_history)[-3:]]
        if "cronjob" in recent_tools:
            suggestions.append("[RESCUE] cronjob failing — use terminal crontab or python schedule instead")
        if "patch" in recent_tools:
            suggestions.append("[RESCUE] patch failing — use write_file for complex edits, verify uniqueness")
        if "skill_manage" in recent_tools:
            suggestions.append("[RESCUE] skill_manage failing — check frontmatter 'name' field, use write_file for SKILL.md")
        
        return suggestions
    
    def export_for_learning_brain(self) -> Dict:
        """Export audit data for learning-brain plugin ingestion."""
        return {
            "loop_count": self._loop_count,
            "wasted_calls": self._wasted_calls,
            "total_calls": len(self._call_history),
            "tool_success_rates": self._calculate_tool_rates(),
            "recovery_patterns": self._recovery_successes,
            "timestamp": time.time(),
        }
    
    def _calculate_tool_rates(self) -> Dict[str, float]:
        """Per-tool success rates from history."""
        tool_stats = {}
        for entry in self._call_history:
            tool = entry["tool"]
            if tool not in tool_stats:
                tool_stats[tool] = {"success": 0, "total": 0}
            tool_stats[tool]["total"] += 1
            if entry["success"]:
                tool_stats[tool]["success"] += 1
        
        return {
            tool: stats["success"] / stats["total"] 
            for tool, stats in tool_stats.items() 
            if stats["total"] > 0
        }


# Pre-flight context checker
class PreflightChecker:
    """Verify all needed context before expensive operations."""
    
    CHECKLIST = {
        "terminal": ["command"],
        "execute_code": ["code"],
        "write_file": ["path", "content"],
        "patch": ["path", "old_string", "new_string"],
        "delegate_task": ["goal"],
        "delegate_with_model": ["goal", "model"],
        "web_search": ["query"],
        "web_extract": ["url"],
        "browser_navigate": ["url"],
        "read_file": ["path"],
        "search_files": ["pattern"],
    }
    
    @classmethod
    def check(cls, tool_name: str, args: Dict) -> Dict:
        """Check if all required args are present."""
        required = cls.CHECKLIST.get(tool_name, [])
        missing = [r for r in required if r not in args or not args[r]]
        
        return {
            "tool": tool_name,
            "ready": len(missing) == 0,
            "missing": missing,
            "advice": f"Missing required args: {missing}" if missing else "Ready to call",
        }


if __name__ == "__main__":
    # Demo
    audit = SelfAuditEngine()
    
    # Simulate some calls
    for i in range(3):
        audit.record_call("cronjob", {"action": "list"}, {"error": "failed"}, tokens_used=500)
    
    # Detect loop
    status = audit.get_loop_status()
    print(f"Loop detected: {status['loop_detected']}")
    print(f"Suggestions: {audit.suggest_recovery()}")
    
    # Pre-flight check
    check = PreflightChecker.check("patch", {"path": "/tmp/test.py"})
    print(f"Preflight: {check}")
