#!/usr/bin/env python3
"""
Verification script for Hermes cognitive system wiring.
Run after any refactor of agent/ modules or cognitive_systems_plugin.py.

Usage:
    python scripts/verify-cognitive-systems.py
    # Or from project root:
    python ~/.hermes/skills/devops/hermes-apparatus-audit/scripts/verify-cognitive-systems.py
"""

import sys
import os

# Auto-detect project root
HERMES_HOME = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
sys.path.insert(0, HERMES_HOME)

def main():
    errors = []
    warnings = []

    # 1. Import the plugin loader
    try:
        import agent.cognitive_systems_plugin as csp
        print("✓ cognitive_systems_plugin imports successfully")
    except Exception as e:
        print(f"✗ cognitive_systems_plugin import FAILED: {e}")
        return 1

    # 2. Check all 7 systems are loaded
    systems = {
        "iteration_engine": csp.iteration_engine,
        "cortex_flywheel": csp.cortex_flywheel,
        "agent_scorecard": csp.agent_scorecard,
        "red_team_hippocampus": csp.red_team_hippocampus,
        "tool_misuse_prevention": csp.tool_misuse_prevention,
        "memory_cortex_bridge": csp.memory_cortex_bridge,
        "hermes_enhancement_suite": csp.hermes_enhancement_suite,
    }

    expected_apis = {
        "iteration_engine": ["get_learning_stats", "on_task_end"],
        "cortex_flywheel": ["record_turn"],
        "agent_scorecard": ["record_tool_call", "get_recent_tool_stats"],
        "red_team_hippocampus": ["mine_error"],
        "tool_misuse_prevention": ["check_misuse"],
        "memory_cortex_bridge": ["consolidate_turn"],
        "hermes_enhancement_suite": ["track_turn"],
    }

    for name, sys_obj in systems.items():
        if sys_obj is None:
            errors.append(f"{name}: NOT LOADED (None)")
            continue

        obj_type = type(sys_obj).__name__
        print(f"  {name}: {obj_type}", end="")

        missing = []
        for api in expected_apis.get(name, []):
            if not hasattr(sys_obj, api):
                missing.append(api)

        if missing:
            errors.append(f"{name}.{', '.join(missing)} missing")
            print(f" — ✗ missing: {', '.join(missing)}")
        else:
            print(" — ✓")

    # 3. Quick hook simulation
    print("\n  Hook simulation:")
    try:
        stats = csp.iteration_engine.get_learning_stats()
        print(f"    iteration_engine.get_learning_stats() → {len(stats)} keys")
    except Exception as e:
        errors.append(f"get_learning_stats() failed: {e}")

    try:
        result = csp.tool_misuse_prevention.check_misuse("web_search", {"query": "test"})
        print(f"    tool_misuse_prevention.check_misuse() → safe={result.get('safe', '?')}")
    except Exception as e:
        errors.append(f"check_misuse() failed: {e}")

    try:
        csp.cortex_flywheel.record_turn("user", "Hello")
        print(f"    cortex_flywheel.record_turn() → ok")
    except Exception as e:
        errors.append(f"record_turn() failed: {e}")

    # 4. Summary
    print(f"\n{'='*50}")
    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    else:
        print("ALL COGNITIVE SYSTEMS VERIFIED ✓")
        return 0

if __name__ == "__main__":
    sys.exit(main())
