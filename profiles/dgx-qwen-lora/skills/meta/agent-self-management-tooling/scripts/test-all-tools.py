#!/usr/bin/env python3
"""
Verification script for all 5 self-management tools.
Run after building or modifying tools.
"""

import sys
import subprocess
from pathlib import Path

SUBCONSCIOUS = Path.home() / "subconscious"

TOOLS = [
    "hermes_tool_logger.py",
    "hermes_context_gauge.py",
    "hermes_plan_executor.py",
    "hermes_self_diagnostic.py",
    "hermes_skill_generator.py",
    "hermes_self_manager.py",
    "hermes_cli_resume.py",
]

def test_file_exists():
    print("=== File Existence ===")
    all_ok = True
    for tool in TOOLS:
        path = SUBCONSCIOUS / tool
        ok = path.exists()
        icon = "✓" if ok else "✗"
        size = path.stat().st_size if ok else 0
        print(f"  {icon} {tool} ({size:,} bytes)")
        if not ok:
            all_ok = False
    return all_ok

def test_imports():
    print("\n=== Imports ===")
    sys.path.insert(0, str(SUBCONSCIOUS))
    
    imports = [
        "hermes_tool_logger",
        "hermes_context_gauge",
        "hermes_plan_executor",
        "hermes_self_diagnostic",
        "hermes_skill_generator",
        "hermes_self_manager",
        "hermes_cli_resume",
    ]
    
    all_ok = True
    for mod in imports:
        try:
            __import__(mod)
            print(f"  ✓ {mod}")
        except Exception as e:
            print(f"  ✗ {mod}: {e}")
            all_ok = False
    
    return all_ok

def test_manual_triggers():
    print("\n=== Manual Triggers ===")
    result = subprocess.run(
        ["python3", str(SUBCONSCIOUS / "hermes_manual_triggers.py"), "self-diagnostic"],
        capture_output=True, text=True, timeout=30
    )
    
    if "Overall: GREEN" in result.stdout:
        print("  ✓ self-diagnostic: GREEN")
        return True
    elif "Overall: YELLOW" in result.stdout:
        print("  ⚠ self-diagnostic: YELLOW")
        return True
    else:
        print("  ✗ self-diagnostic: no status found")
        print(result.stdout[:200])
        return False

def test_self_manager():
    print("\n=== Self Manager ===")
    result = subprocess.run(
        ["python3", str(SUBCONSCIOUS / "hermes_self_manager.py"), "--status"],
        capture_output=True, text=True, timeout=10
    )
    
    if result.returncode == 0:
        print(f"  ✓ {result.stdout.strip()}")
        return True
    else:
        print(f"  ✗ {result.stderr}")
        return False

def main():
    print("=" * 50)
    print("HERMES SELF-MANAGEMENT TOOL VERIFICATION")
    print("=" * 50)
    
    results = {
        "files": test_file_exists(),
        "imports": test_imports(),
        "triggers": test_manual_triggers(),
        "self_manager": test_self_manager(),
    }
    
    print("\n" + "=" * 50)
    print("RESULTS:")
    for name, ok in results.items():
        icon = "✓" if ok else "✗"
        print(f"  {icon} {name}")
    
    all_ok = all(results.values())
    print("=" * 50)
    print(f"OVERALL: {'PASS' if all_ok else 'FAIL'}")
    print("=" * 50)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
