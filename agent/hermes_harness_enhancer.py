#!/usr/bin/env python3
"""
hermes_harness_enhancer.py — Identifies missing tools and suggests/builds enhancements.

Scans current toolset, identifies gaps, proposes new tools based on:
- Tool intelligence data (weak tools, failure patterns)
- User workflow patterns (what tasks recur)
- Performance bottlenecks (where time is wasted)

Usage:
    from hermes_harness_enhancer import HarnessEnhancer
    enhancer = HarnessEnhancer()
    gaps = enhancer.identify_gaps()
    for gap in gaps:
        print(gap['name'], gap['impact'])
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

HERMES_HOME = Path.home() / ".hermes"

# Known tool weaknesses and their replacements
TOOL_REPLACEMENTS = {
    "cronjob": {
        "replacement": "terminal + python schedule library",
        "reason": "13% success rate, 'id' parameter errors",
        "workaround": "Use terminal(background=True) for daemons, or python schedule",
    },
    "skill_manage": {
        "replacement": "write_file + patch",
        "reason": "56% success, frontmatter validation issues, pinned skill blocks",
        "workaround": "Use write_file for SKILL.md, patch for updates. Check frontmatter 'name' field.",
    },
    "patch": {
        "replacement": "write_file (for complex edits)",
        "reason": "59% success, old_string uniqueness failures",
        "workaround": "Use write_file for multi-line strings, verify old_string uniqueness before patch.",
    },
}

# Missing tool categories based on workflow analysis
MISSING_CATEGORIES = [
    {
        "name": "loop_detector",
        "description": "Auto-detect when agent repeats same tool call without progress",
        "impact": "high",
        "evidence": "Agent repeated cronjob query 16x, patch verification loops",
        "implementation": "Track call hashes in window, alert on 3+ identical calls",
    },
    {
        "name": "token_waste_tracker",
        "description": "Log and report calls that consumed tokens but produced no value",
        "impact": "high",
        "evidence": "Failed cronjob calls used 500+ tokens each with no result",
        "implementation": "Count tokens on failed calls, report top waste sources",
    },
    {
        "name": "preflight_checker",
        "description": "Verify all required args present before expensive tool calls",
        "impact": "medium",
        "evidence": "patch calls missing old_string, skill_manage missing frontmatter",
        "implementation": "Per-tool checklist, validate before dispatch",
    },
    {
        "name": "recovery_suggester",
        "description": "When stuck, suggest proven recovery patterns",
        "impact": "high",
        "evidence": "Agent loops instead of switching approaches",
        "implementation": "Pattern matching on failure type → suggest alternative tool",
    },
    {
        "name": "context_window_monitor",
        "description": "Track context usage and suggest compression before overflow",
        "impact": "medium",
        "evidence": "Long sessions lose early context, need proactive management",
        "implementation": "Monitor token count, trigger compression at 80%",
    },
    {
        "name": "skill_auto_loader",
        "description": "Auto-detect which skills match current task and load them",
        "impact": "medium",
        "evidence": "User has 360 skills, manual scanning is slow",
        "implementation": "Keyword matching on task description → skill suggestions",
    },
    {
        "name": "multi_step_validator",
        "description": "Validate multi-step plans before execution",
        "impact": "high",
        "evidence": "Plans often miss steps or use wrong tools",
        "implementation": "Parse plan, check tool availability, verify dependencies",
    },
    {
        "name": "error_pattern_miner",
        "description": "Mine error logs for recurring patterns and auto-suggest fixes",
        "impact": "high",
        "evidence": "Same errors repeat (patch uniqueness, skill frontmatter)",
        "implementation": "Cluster errors by type, map to known solutions",
    },
    {
        "name": "delegation_optimizer",
        "description": "Decide when to delegate vs do inline based on complexity",
        "impact": "medium",
        "evidence": "Over-delegating simple tasks wastes tokens, under-delegating complex ones fails",
        "implementation": "Score task complexity, route to delegate if >threshold",
    },
    {
        "name": "file_operation_batch",
        "description": "Batch multiple file operations into single execute_code call",
        "impact": "medium",
        "evidence": "Multiple write_file/patch calls in sequence are inefficient",
        "implementation": "Queue file ops, flush as batch when 3+ accumulate",
    },
]


class HarnessEnhancer:
    """Analyzes tool performance and suggests/builds improvements."""
    
    def __init__(self):
        self.gaps = MISSING_CATEGORIES
        self.replacements = TOOL_REPLACEMENTS
    
    def identify_gaps(self) -> List[Dict]:
        """Return identified tool gaps sorted by impact."""
        return sorted(self.gaps, key=lambda x: x["impact"], reverse=True)
    
    def get_workarounds(self) -> Dict[str, str]:
        """Current workarounds for weak tools."""
        return {
            tool: info["workaround"] 
            for tool, info in self.replacements.items()
        }
    
    def build_tool(self, gap: Dict) -> Optional[str]:
        """Generate implementation for a missing tool."""
        name = gap["name"]
        
        if name == "loop_detector":
            return self._build_loop_detector()
        elif name == "preflight_checker":
            return self._build_preflight_checker()
        elif name == "recovery_suggester":
            return self._build_recovery_suggester()
        
        return None
    
    def _build_loop_detector(self) -> str:
        """Generate loop detector code."""
        return '''
# Auto-generated loop detector
# Usage: from loop_detector import LoopDetector
class LoopDetector:
    def __init__(self, window=3):
        self.history = []
        self.window = window
    
    def check(self, tool_name, args):
        call_hash = f"{tool_name}:{str(args)}"
        self.history.append(call_hash)
        
        if len(self.history) >= self.window:
            recent = self.history[-self.window:]
            if len(set(recent)) == 1:
                return {"loop": True, "count": len(recent)}
        return {"loop": False}
'''
    
    def _build_preflight_checker(self) -> str:
        """Generate preflight checker code."""
        return '''
# Auto-generated preflight checker
class PreflightChecker:
    REQUIRED = {
        "patch": ["path", "old_string", "new_string"],
        "write_file": ["path", "content"],
        "delegate_task": ["goal"],
    }
    
    @staticmethod
    def check(tool, args):
        required = PreflightChecker.REQUIRED.get(tool, [])
        missing = [r for r in required if r not in args]
        return {"ready": len(missing) == 0, "missing": missing}
'''
    
    def _build_recovery_suggester(self) -> str:
        """Generate recovery suggester code."""
        return '''
# Auto-generated recovery suggester
RECOVERY_PATTERNS = {
    "patch_old_string_not_found": "Use write_file instead, or verify old_string uniqueness",
    "skill_manage_frontmatter": "Add 'name' field to frontmatter, or use write_file",
    "cronjob_id_error": "Use terminal with background=True, or python schedule library",
    "process_not_found": "Process may have exited, check with ps aux",
}

class RecoverySuggester:
    @staticmethod
    def suggest(error_text):
        for pattern, advice in RECOVERY_PATTERNS.items():
            if pattern.replace("_", " ") in error_text.lower():
                return advice
        return "Try a different approach or ask user for guidance"
'''
    
    def generate_report(self) -> str:
        """Generate comprehensive harness enhancement report."""
        lines = [
            "=" * 60,
            "HERMES HARNESS ENHANCEMENT REPORT",
            "=" * 60,
            "",
            "[CURRENT WEAK TOOLS — Use Workarounds]",
        ]
        
        for tool, info in self.replacements.items():
            lines.append(f"  {tool}: {info['reason']}")
            lines.append(f"    → {info['workaround']}")
        
        lines.extend(["", "[MISSING TOOLS — Build These]"])
        
        for gap in self.identify_gaps():
            lines.append(f"  {gap['name']} ({gap['impact']})")
            lines.append(f"    {gap['description']}")
            lines.append(f"    Evidence: {gap['evidence']}")
        
        lines.extend(["", "[RECOMMENDED PRIORITY]"])
        lines.append("  1. loop_detector — Stop wasting tokens on repeats")
        lines.append("  2. recovery_suggester — Auto-fix common failures")
        lines.append("  3. preflight_checker — Catch missing args before call")
        lines.append("  4. token_waste_tracker — Accountability for token spend")
        lines.append("  5. error_pattern_miner — Learn from repeated mistakes")
        
        return "\n".join(lines)


if __name__ == "__main__":
    enhancer = HarnessEnhancer()
    print(enhancer.generate_report())
