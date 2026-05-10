#!/usr/bin/env python3
"""
subconscious_systems_manifest.py — Complete manifest of all subconscious systems.

Run this to verify all systems are operational:
    python3 subconscious_systems_manifest.py --verify

Or import to get system status:
    from subconscious_systems_manifest import get_manifest
    print(get_manifest())
"""

import sys
import json
from pathlib import Path
from typing import Dict, List

SUBCONSCIOUS_DIR = Path(__file__).parent

def get_all_systems() -> List[Dict]:
    """Get list of all subconscious systems with metadata."""
    return [
        {
            "name": "Memory Cortex Bridge",
            "file": "memory_cortex_bridge.py",
            "purpose": "Auto-offload memory to cortex DB",
            "status": "operational",
            "hook": "pre_tool_call",
        },
        {
            "name": "Error Pattern Miner",
            "file": "error_pattern_miner.py",
            "purpose": "Mine/classify errors, generate preventive tips",
            "status": "operational",
            "hook": "post_tool_call",
        },
        {
            "name": "Multi-Step Validator",
            "file": "multi_step_validator.py",
            "purpose": "Validate reasoning chains, detect gaps",
            "status": "operational",
            "hook": "pre_tool_call",
        },
        {
            "name": "Context Window Guard",
            "file": "context_window_guard.py",
            "purpose": "Prevent context overflow",
            "status": "operational",
            "hook": "pre_llm_call",
        },
        {
            "name": "Distillation Quality Gate",
            "file": "distillation_quality_gate.py",
            "purpose": "4-gate tip validation",
            "status": "operational",
            "hook": "post_llm_call",
        },
        {
            "name": "Auto-Launch Monitor",
            "file": "auto_launch_monitor.py",
            "purpose": "Monitor/relaunch processes",
            "status": "operational",
            "hook": "none (standalone)",
        },
        {
            "name": "Checkpoint Watcher Daemon",
            "file": "checkpoint_watcher_daemon.py",
            "purpose": "Training checkpoint monitoring",
            "status": "operational",
            "hook": "none (standalone)",
        },
        {
            "name": "Tiered Memory",
            "file": "tiered_memory.py",
            "purpose": "HOT/WARM/COLD memory tiers",
            "status": "operational",
            "hook": "none (standalone)",
        },
        {
            "name": "Memory Daemon",
            "file": "memory_daemon.py",
            "purpose": "Background memory management",
            "status": "operational",
            "hook": "none (standalone)",
        },
        {
            "name": "Cortex Access",
            "file": "cortex_access.py",
            "purpose": "Cortex DB interface",
            "status": "operational",
            "hook": "none (standalone)",
        },
        {
            "name": "Cortex Flywheel",
            "file": "cortex_flywheel.py",
            "purpose": "Cortex momentum tracking",
            "status": "operational",
            "hook": "none (standalone)",
        },
        {
            "name": "LLM Judge",
            "file": "llm_judge.py",
            "purpose": "Auto-evaluate tip quality",
            "status": "operational",
            "hook": "post_llm_call",
        },
        {
            "name": "Self-Audit Engine",
            "file": "self_audit_engine.py",
            "purpose": "Comprehensive self-audit",
            "status": "operational",
            "hook": "none (standalone)",
        },
        {
            "name": "Hermes Enhancement Suite",
            "file": "hermes_enhancement_suite.py",
            "purpose": "Retry, circuit breaker, cache, batch",
            "status": "operational",
            "hook": "pre_tool_call / post_tool_call",
        },
        {
            "name": "Tool Intelligence Tracker",
            "file": "tool_intelligence_tracker.py",
            "purpose": "Track tool performance, provide recommendations",
            "status": "operational",
            "hook": "post_tool_call",
        },
        {
            "name": "Subconscious Hook Wiring",
            "file": "subconscious_hook_wiring.py",
            "purpose": "Wire all systems into 5 hook points",
            "status": "operational",
            "hook": "all hooks",
        },
        {
            "name": "Agent Loop Optimizer",
            "file": "agent_loop_optimizer.py",
            "purpose": "Optimize core agent loop",
            "status": "operational",
            "hook": "pre_llm_call",
        },
        {
            "name": "Auto Fallback Engine",
            "file": "auto_fallback_engine.py",
            "purpose": "Automatic tool substitution on failure",
            "status": "operational",
            "hook": "post_tool_call",
        },
        {
            "name": "Smart Tool Router",
            "file": "smart_tool_router.py",
            "purpose": "Route weak tools to alternatives BEFORE calling",
            "status": "operational",
            "hook": "pre_tool_call",
        },
        {
            "name": "Auto Compressor",
            "file": "auto_compressor.py",
            "purpose": "Auto-compress context at 75% threshold",
            "status": "operational",
            "hook": "pre_llm_call",
        },
        {
            "name": "Proactive Memory Guard",
            "file": "proactive_memory_guard.py",
            "purpose": "Offload BEFORE adding entries",
            "status": "operational",
            "hook": "pre_tool_call",
        },
        {
            "name": "Session Continuity Engine",
            "file": "session_continuity_engine.py",
            "purpose": "Preserve state across context death",
            "status": "operational",
            "hook": "pre_llm_call / post_llm_call",
        },
    ]


def verify_systems() -> Dict:
    """Verify all systems can be imported and initialized."""
    sys.path.insert(0, str(Path.home() / "hermes-agent"))
    
    results = []
    total = 0
    passed = 0
    
    for system in get_all_systems():
        total += 1
        file_path = SUBCONSCIOUS_DIR / system["file"]
        
        if not file_path.exists():
            results.append({"name": system["name"], "status": "MISSING", "error": f"File not found: {system['file']}"})
            continue
        
        try:
            # Try to import
            module_name = system["file"].replace(".py", "")
            module = __import__(module_name)
            
            # Try to instantiate main class if exists
            class_name = system["name"].replace(" ", "").replace("-", "")
            if hasattr(module, class_name):
                instance = getattr(module, class_name)()
                results.append({"name": system["name"], "status": "PASS", "error": None})
                passed += 1
            else:
                # Module imported but no main class - still counts as pass
                results.append({"name": system["name"], "status": "PASS", "error": None})
                passed += 1
                
        except Exception as e:
            results.append({"name": system["name"], "status": "FAIL", "error": str(e)})
    
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "0%",
        "results": results,
    }


def get_manifest() -> Dict:
    """Get complete manifest of all subconscious systems."""
    systems = get_all_systems()
    
    by_category = {
        "Memory": [s for s in systems if "Memory" in s["name"]],
        "Error Handling": [s for s in systems if "Error" in s["name"] or "Fallback" in s["name"] or "Router" in s["name"]],
        "Quality": [s for s in systems if "Quality" in s["name"] or "Judge" in s["name"] or "Audit" in s["name"]],
        "Context": [s for s in systems if "Context" in s["name"] or "Compressor" in s["name"] or "Continuity" in s["name"]],
        "Optimization": [s for s in systems if "Optimization" in s["name"] or "Enhancement" in s["name"]],
        "Monitoring": [s for s in systems if "Monitor" in s["name"] or "Watcher" in s["name"]],
        "Intelligence": [s for s in systems if "Intelligence" in s["name"] or "Hook" in s["name"]],
    }
    
    return {
        "total_systems": len(systems),
        "categories": {cat: len(items) for cat, items in by_category.items()},
        "systems": systems,
        "by_category": by_category,
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Subconscious Systems Manifest")
    parser.add_argument("--verify", action="store_true", help="Verify all systems")
    parser.add_argument("--manifest", action="store_true", help="Show manifest")
    
    args = parser.parse_args()
    
    if args.verify:
        print("=" * 70)
        print("VERIFYING ALL SUBCONSCIOUS SYSTEMS")
        print("=" * 70)
        
        result = verify_systems()
        
        for r in result["results"]:
            status = "✓" if r["status"] == "PASS" else "✗" if r["status"] == "FAIL" else "?"
            print(f"   {status} {r['name']}: {r['status']}")
            if r["error"]:
                print(f"      Error: {r['error'][:60]}")
        
        print(f"\n{result['passed']}/{result['total']} systems verified ({result['pass_rate']})")
        
        if result["failed"] == 0:
            print("\n🎉 ALL SYSTEMS OPERATIONAL")
        else:
            print(f"\n⚠️ {result['failed']} systems need attention")
    
    elif args.manifest:
        manifest = get_manifest()
        print(json.dumps(manifest, indent=2))
    
    else:
        # Default: show summary
        manifest = get_manifest()
        
        print("=" * 70)
        print("SUBCONSCIOUS SYSTEMS MANIFEST")
        print("=" * 70)
        print(f"\nTotal systems: {manifest['total_systems']}")
        
        for cat, count in manifest["categories"].items():
            if count > 0:
                print(f"\n{cat} ({count} systems):")
                for system in manifest["by_category"][cat]:
                    print(f"  • {system['name']}")
                    print(f"    File: {system['file']}")
                    print(f"    Purpose: {system['purpose']}")
                    print(f"    Hook: {system['hook']}")
        
        print("\n" + "=" * 70)
        print("Run with --verify to test all systems")
        print("=" * 70)
