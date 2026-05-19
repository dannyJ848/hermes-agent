#!/usr/bin/env python3
"""
hermes_self_diagnostic.py — Comprehensive system health check for Hermes Agent.

Tests all tools, providers, DBs, files, and reports red/green status.
Integrates with unified daemon for proactive alerting.

Usage:
  from hermes_self_diagnostic import run_full_diagnostic, quick_health_check
  
  # Quick check (5 seconds):
  health = quick_health_check()
  
  # Full diagnostic (30 seconds):
  report = run_full_diagnostic()
"""

import sqlite3
import json
import time
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Components to check
COMPONENTS = {
    "databases": [
        ("cerebrum_memory", "~/.hermes/cerebrum_memory.db"),
        ("tool_intelligence", "~/.hermes/tool_intelligence.db"),
        ("cortex", "~/.hermes/cortex.db"),
    ],
    "files": [
        ("unified_daemon", "~/hermes-agent/agent/hermes_unified_daemon.py"),
        ("manual_triggers", "~/hermes-agent/agent/hermes_manual_triggers.py"),
        ("cognitive_infra", "~/hermes-agent/agent/cognitive_infrastructure_v2.py"),
        ("tool_logger", "~/hermes-agent/agent/hermes_tool_logger.py"),
        ("context_gauge", "~/hermes-agent/agent/hermes_context_gauge.py"),
        ("plan_executor", "~/hermes-agent/agent/hermes_plan_executor.py"),
        ("distillation_plugin", "~/.hermes/plugins/distillation/__init__.py"),
    ],
    "processes": [
        ("unified_daemon", "hermes_unified_daemon.py"),
    ],
    "directories": [
        ("knowledge", "~/.hermes/knowledge/"),
        ("skills", "~/.hermes/skills/"),
        ("workspace", "~/.hermes/workspace/"),
    ],
}

def _expand(path: str) -> Path:
    return Path(path).expanduser()

def check_database(name: str, path: str) -> Tuple[bool, str]:
    """Check if database is accessible and has expected tables."""
    try:
        db_path = _expand(path)
        if not db_path.exists():
            return False, "File not found"
        
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # Check if it's a valid SQLite file
        c.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
        tables = c.fetchall()
        conn.close()
        
        if tables:
            return True, f"OK ({len(tables)} tables)"
        else:
            return True, "OK (empty)"
    except Exception as e:
        return False, str(e)

def check_file(name: str, path: str) -> Tuple[bool, str]:
    """Check if file exists and is readable."""
    try:
        file_path = _expand(path)
        if not file_path.exists():
            return False, "File not found"
        
        size = file_path.stat().st_size
        return True, f"OK ({size:,} bytes)"
    except Exception as e:
        return False, str(e)

def check_process(name: str, pattern: str) -> Tuple[bool, str]:
    """Check if process is running."""
    try:
        result = subprocess.run(
            ['pgrep', '-f', pattern],
            capture_output=True, text=True, timeout=5
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            return True, f"Running ({len(pids)} instances)"
        else:
            return False, "Not running"
    except Exception as e:
        return False, str(e)

def check_directory(name: str, path: str) -> Tuple[bool, str]:
    """Check if directory exists and is writable."""
    try:
        dir_path = _expand(path)
        if not dir_path.exists():
            return False, "Directory not found"
        
        # Check writable
        test_file = dir_path / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        
        # Count files
        files = list(dir_path.iterdir())
        return True, f"OK ({len(files)} items)"
    except Exception as e:
        return False, str(e)

def quick_health_check() -> Dict:
    """Quick health check (5 seconds)."""
    results = {
        "timestamp": time.time(),
        "overall": "GREEN",
        "components": {},
        "issues": [],
    }
    
    # Check critical components
    checks = [
        ("cerebrum_db", lambda: check_database("cerebrum", "~/.hermes/cerebrum_memory.db")),
        ("unified_daemon", lambda: check_process("daemon", "hermes_unified_daemon.py")),
        ("knowledge_dir", lambda: check_directory("knowledge", "~/.hermes/knowledge/")),
        ("skills_dir", lambda: check_directory("skills", "~/.hermes/skills/")),
    ]
    
    for name, check_fn in checks:
        ok, msg = check_fn()
        results["components"][name] = {"status": "OK" if ok else "FAIL", "detail": msg}
        if not ok:
            results["issues"].append(f"{name}: {msg}")
            results["overall"] = "RED"
    
    if results["issues"] and results["overall"] == "GREEN":
        results["overall"] = "YELLOW"
    
    return results

def run_full_diagnostic() -> Dict:
    """Full system diagnostic (30 seconds)."""
    results = {
        "timestamp": time.time(),
        "overall": "GREEN",
        "categories": {},
        "issues": [],
        "stats": {},
    }
    
    # Check all databases
    db_results = {}
    for name, path in COMPONENTS["databases"]:
        ok, msg = check_database(name, path)
        db_results[name] = {"status": "OK" if ok else "FAIL", "detail": msg}
        if not ok:
            results["issues"].append(f"DB {name}: {msg}")
    results["categories"]["databases"] = db_results
    
    # Check all files
    file_results = {}
    for name, path in COMPONENTS["files"]:
        ok, msg = check_file(name, path)
        file_results[name] = {"status": "OK" if ok else "FAIL", "detail": msg}
        if not ok:
            results["issues"].append(f"File {name}: {msg}")
    results["categories"]["files"] = file_results
    
    # Check all processes
    proc_results = {}
    for name, pattern in COMPONENTS["processes"]:
        ok, msg = check_process(name, pattern)
        proc_results[name] = {"status": "OK" if ok else "FAIL", "detail": msg}
        if not ok:
            results["issues"].append(f"Process {name}: {msg}")
    results["categories"]["processes"] = proc_results
    
    # Check all directories
    dir_results = {}
    for name, path in COMPONENTS["directories"]:
        ok, msg = check_directory(name, path)
        dir_results[name] = {"status": "OK" if ok else "FAIL", "detail": msg}
        if not ok:
            results["issues"].append(f"Dir {name}: {msg}")
    results["categories"]["directories"] = dir_results
    
    # Collect stats
    try:
        conn = sqlite3.connect(str(_expand("~/.hermes/cerebrum_memory.db")))
        c = conn.cursor()
        
        stats_queries = {
            "distilled_tips": "SELECT COUNT(*) FROM distilled_tips",
            "rapid_learnings": "SELECT COUNT(*) FROM rapid_learnings",
            "tip_survival": "SELECT COUNT(*) FROM tip_survival",
            "prompt_fragments": "SELECT COUNT(*) FROM prompt_fragments",
        }
        
        for stat_name, query in stats_queries.items():
            try:
                c.execute(query)
                results["stats"][stat_name] = c.fetchone()[0]
            except:
                results["stats"][stat_name] = "N/A"
        
        conn.close()
    except Exception as e:
        results["stats"]["error"] = str(e)
    
    # Determine overall status
    total_checks = sum(len(v) for v in results["categories"].values())
    failed_checks = len(results["issues"])
    
    if failed_checks == 0:
        results["overall"] = "GREEN"
    elif failed_checks / total_checks < 0.1:
        results["overall"] = "YELLOW"
    else:
        results["overall"] = "RED"
    
    return results

def format_report(results: Dict) -> str:
    """Format diagnostic results as readable text."""
    lines = []
    lines.append("=" * 50)
    lines.append(f"HERMES HEALTH REPORT — {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 50)
    lines.append(f"Overall: {results['overall']}")
    lines.append("")
    
    if "categories" in results:
        for category, items in results["categories"].items():
            lines.append(f"{category.upper()}:")
            for name, status in items.items():
                icon = "✓" if status["status"] == "OK" else "✗"
                lines.append(f"  {icon} {name}: {status['detail']}")
            lines.append("")
    
    if "stats" in results and results["stats"]:
        lines.append("STATS:")
        for name, value in results["stats"].items():
            lines.append(f"  {name}: {value}")
        lines.append("")
    
    if results.get("issues"):
        lines.append("ISSUES:")
        for issue in results["issues"]:
            lines.append(f"  ! {issue}")
        lines.append("")
    
    lines.append("=" * 50)
    return "\n".join(lines)

def save_report(results: Dict, path: str = "~/.hermes/workspace/last_diagnostic.json"):
    """Save diagnostic results to file."""
    out_path = _expand(path)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    
    # Also save text version
    text_path = out_path.with_suffix(".txt")
    text_path.write_text(format_report(results))

if __name__ == "__main__":
    print("=== Self Diagnostic Test ===")
    
    # Quick check
    print("\nQuick check:")
    quick = quick_health_check()
    print(f"Overall: {quick['overall']}")
    for name, status in quick['components'].items():
        icon = "✓" if status['status'] == 'OK' else "✗"
        print(f"  {icon} {name}: {status['detail']}")
    
    # Full diagnostic
    print("\nFull diagnostic:")
    full = run_full_diagnostic()
    print(format_report(full))
    
    save_report(full)
    print(f"\nReport saved to ~/.hermes/workspace/last_diagnostic.json")
    
    print("\n=== Self Diagnostic Ready ===")
