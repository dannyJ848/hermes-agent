#!/usr/bin/env python3
"""
Verify cognitive-systems plugin compatibility with actual agent modules.

Run this after ANY change to agent/ modules or the cognitive-systems plugin
to catch class name mismatches and handler signature drift before they
silently break hook execution.

Usage:
    /Users/dannygomez/hermes-agent/venv/bin/python3 verify-cognitive-plugin-compatibility.py
"""

import os
import sys
import inspect

sys.path.insert(0, os.path.expanduser("~/hermes-agent"))


def check_system(name, expected_class, expected_methods, is_module_functions=False):
    """Check that a cognitive system loads and has expected methods."""
    try:
        if is_module_functions:
            mod = __import__(f"agent.{name}", fromlist=["*"])
            print(f"✅ {name}: module loads")
            for method in expected_methods:
                if hasattr(mod, method):
                    print(f"   ✅ .{method}() exists")
                else:
                    print(f"   ❌ .{method}() MISSING")
        else:
            cls = getattr(__import__(f"agent.{name}", fromlist=[expected_class]), expected_class)
            obj = cls()
            print(f"✅ {name}: {expected_class} instantiates")
            for method in expected_methods:
                if hasattr(obj, method):
                    sig = inspect.signature(getattr(obj, method))
                    print(f"   ✅ .{method}{sig}")
                else:
                    print(f"   ❌ .{method}() MISSING")
    except Exception as e:
        print(f"❌ {name}: {e}")


def main():
    print("=" * 60)
    print("   COGNITIVE SYSTEMS PLUGIN COMPATIBILITY CHECK")
    print("=" * 60)

    # These must match what the cognitive-systems plugin expects
    systems = [
        ("iteration_engine", "get_engine", ["before_action", "after_action", "get_learning_stats"]),
        ("cortex_flywheel", "CortexDB", ["get_stats", "start_flywheel_cycle"]),
        ("agent_scorecard", None, ["compute_scorecard", "score_tool_mastery"], True),
        ("tool_misuse_prevention", None, ["validate_tool_call", "get_tool_stats"], True),
        ("red_team_hippocampus", None, ["learn", "attack", "harden"], True),
        ("memory_cortex_bridge", "MemoryCortexBridge", ["is_pressure", "offload_if_needed", "get_stats"]),
        ("hermes_enhancement_suite", "HermesEnhancementSuite", ["get_status", "install_hooks"]),
    ]

    for name, class_or_fn, methods, *rest in systems:
        is_module = rest[0] if rest else False
        check_system(name, class_or_fn, methods, is_module)
        print()

    # Check plugin file itself
    print("=" * 60)
    print("   PLUGIN FILE CHECK")
    print("=" * 60)
    plugin_path = os.path.expanduser("~/.hermes/plugins/cognitive-systems/__init__.py")
    if os.path.exists(plugin_path):
        with open(plugin_path) as f:
            content = f.read()

        # Check that plugin uses correct import patterns
        correct_patterns = [
            "from agent import agent_scorecard",
            "from agent import tool_misuse_prevention",
            "from agent import red_team_hippocampus",
            "MemoryCortexBridge",
            "HermesEnhancementSuite",
        ]
        wrong_patterns = [
            "from agent.agent_scorecard import AgentScorecard",
            "from agent.tool_misuse_prevention import ToolHealthMonitor",
            "from agent.red_team_hippocampus import ErrorMiner",
            "from agent.memory_cortex_bridge import MemoryBridge",
            "from agent.hermes_enhancement_suite import EnhancementTracker",
        ]

        for pattern in correct_patterns:
            status = "✅" if pattern in content else "❌"
            print(f"{status} Plugin uses: {pattern}")

        for pattern in wrong_patterns:
            if pattern in content:
                print(f"⚠️  Plugin still has WRONG import: {pattern}")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
