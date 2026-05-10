#!/Users/dannygomez/hermes-agent/venv/bin/python3
"""
TOOL MISUSE PREVENTION MODULE (Cycle 8)
Analyzes tool call patterns and generates pre-call validation rules.
"""

import json
import sqlite3
import time
import os
from pathlib import Path

TOOL_DB = Path.home() / "hermes-agent" / "tool_capability.db"
BRAIN_DB = Path.home() / "hermes-agent" / "brain.db"

FAIL_RATE_DANGER = 0.30
FAIL_RATE_CAUTION = 0.15
CONFIDENCE_MIN = 0.10
MIN_CALLS_FOR_STATS = 5

TOOL_RULES = {
    "terminal": {
        "avoid_patterns": ["cat ", "head ", "tail ", "grep ", "rg ", "find ", "ls ", "echo '> >", "cat <<", "sed -i", "awk "],
        "preferred_alternatives": {
            "cat": "read_file", "head": "read_file with limit", "tail": "read_file with offset",
            "grep": "search_files", "find": "search_files target=files", "ls": "search_files target=files",
            "echo": "write_file", "sed": "patch tool",
        },
        "max_command_length": 500,
        "require_timeout": True,
    },
    "read_file": {
        "check_file_exists_first": True,
        "avoid_binary_files": True,
        "max_file_size_chars": 100000,
    },
    "delegate_parallel": {
        "max_tasks": 3,
        "avoid_models": ["cerebrum"],
        "fallback_to_delegate_with_model": True,
    },
}

def get_tool_stats(tool_name):
    if not TOOL_DB.exists():
        return None
    conn = sqlite3.connect(str(TOOL_DB))
    c = conn.cursor()
    c.execute("SELECT tool_name, total_calls, successes, failures, confidence, CAST(failures AS REAL) / NULLIF(total_calls, 0) as fail_rate FROM tool_stats WHERE tool_name = ?", (tool_name,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"tool": row[0], "total": row[1], "successes": row[2], "failures": row[3], "confidence": row[4], "fail_rate": row[5] or 0}
    return None

def validate_tool_call(tool_name, args_dict=None):
    warnings = []
    alternative = None
    should_proceed = True
    stats = get_tool_stats(tool_name)
    
    if stats and stats["total"] >= MIN_CALLS_FOR_STATS:
        fr = stats["fail_rate"]
        if fr > FAIL_RATE_DANGER:
            pct = int(fr * 100)
            warnings.append("DANGER: %s has %d%% failure rate" % (tool_name, pct))
            should_proceed = False
        elif fr > FAIL_RATE_CAUTION:
            pct = int(fr * 100)
            warnings.append("CAUTION: %s has %d%% failure rate" % (tool_name, pct))
        
        conf = stats["confidence"]
        if conf < CONFIDENCE_MIN:
            warnings.append("LOW CONFIDENCE: %s confidence=%.2f" % (tool_name, conf))
    
    rules = TOOL_RULES.get(tool_name, {})
    
    if tool_name == "terminal" and args_dict:
        cmd = args_dict.get("command", "")
        for bad_cmd, alt in rules.get("preferred_alternatives", {}).items():
            if bad_cmd in cmd:
                warnings.append("PREFER %s over %s" % (alt, bad_cmd))
                alternative = alt
    
    if tool_name == "read_file" and args_dict:
        path = args_dict.get("path", "")
        if path and not os.path.exists(os.path.expanduser(path)):
            warnings.append("FILE NOT FOUND: %s" % path)
            should_proceed = False
    
    if tool_name == "delegate_parallel" and args_dict:
        tasks = args_dict.get("tasks", [])
        if len(tasks) > 3:
            warnings.append("TOO MANY TASKS: %d > 3 max" % len(tasks))
    
    return should_proceed, warnings, alternative

def generate_pre_call_report():
    report_lines = ["[TOOL HEALTH CHECK]"]
    if not TOOL_DB.exists():
        return "[TOOL HEALTH] Database not found"
    
    conn = sqlite3.connect(str(TOOL_DB))
    c = conn.cursor()
    c.execute("SELECT tool_name, total_calls, successes, failures, confidence, CAST(failures AS REAL) / NULLIF(total_calls, 0) as fail_rate FROM tool_stats WHERE total_calls >= ? ORDER BY fail_rate DESC", (MIN_CALLS_FOR_STATS,))
    
    danger_tools = []
    caution_tools = []
    reliable_tools = []
    
    for row in c.fetchall():
        name, total, succ, fail, conf, fr = row
        fr = fr or 0
        if fr > FAIL_RATE_DANGER:
            danger_tools.append("  - %s: %d%% fail (%d/%d)" % (name, int(fr*100), fail, total))
        elif fr > FAIL_RATE_CAUTION:
            caution_tools.append("  + %s: %d%% fail, conf=%.2f" % (name, int(fr*100), conf))
        else:
            reliable_tools.append("  OK %s: conf=%.2f" % (name, conf))
    
    conn.close()
    
    if danger_tools:
        report_lines.append("AVOID (high fail rate):")
        report_lines.extend(danger_tools)
    if caution_tools:
        report_lines.append("CAUTION:")
        report_lines.extend(caution_tools)
    if reliable_tools:
        report_lines.append("RELIABLE:")
        report_lines.extend(reliable_tools[:5])
    
    return "\n".join(report_lines)


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    
    if cmd == "report":
        print(generate_pre_call_report())
    elif cmd == "validate":
        tool = sys.argv[2] if len(sys.argv) > 2 else ""
        if tool:
            proceed, warnings, alt = validate_tool_call(tool)
            print("Tool: %s" % tool)
            print("Proceed: %s" % proceed)
            for w in warnings:
                print("Warning: %s" % w)
            if alt:
                print("Alternative: %s" % alt)
    elif cmd == "recommend":
        recs = get_tool_recommendation("general")
        if recs:
            for r in recs:
                print("  %s: conf=%.2f, success=%.0f%%" % (r["tool"], r["confidence"], r["success_rate"]*100))
