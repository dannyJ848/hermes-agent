#!/usr/bin/env python3
"""
memory_pruner.py — Post-restart memory restoration from Cortex

Usage:
    python3 memory_pruner.py --verify    # Check Cortex has all entries
    python3 memory_pruner.py --restore   # Restore critical entries to Hermes memory
    python3 memory_pruner.py --prune     # Mark old entries for pruning (manual)

This script is designed to run AFTER restarting Hermes CLI (which clears local memory).
It restores only the most critical recent entries from Cortex DB.
"""

import os
os.environ["CORTEX_DSN"] = "postgresql://hindsight:***@localhost:5432/hindsight"

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path.home() / ".hermes"))
sys.path.insert(0, str(Path.home() / "subconscious"))

import importlib.util
spec = importlib.util.spec_from_file_location("cortex_memory_tool", 
                                              str(Path.home() / ".hermes/tools/cortex_memory_tool.py"))
cortex_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cortex_module)
cortex = cortex_module.handler

# Critical entries to restore after restart (most recent + most important)
CRITICAL_KEYS = [
    "apr26_iteration_fix",
    "apr26_deadlock_rule", 
    "apr25_merged_checkpoint",
    "apr25_profile_configs",
    "apr25_dflash_restart",
    "apr24_phase1_complete",
    "apr24_franken_v8",
    "apr23_custom_eagle3",
    "apr23_hermes_v011",
    "apr23_checkpoint_final",
    "apr22_qwen27b_wired",
    "apr22_danny_directive",
    "apr22_bf16_confirmed",
    "apr22_franken_pipeline",
    "apr22_checkpoint_corrupt",
    "apr21_abliteration",
    "apr21_flashkda_abandoned",
    "apr21_dflash_pattern",
    "apr20_kimi_k26",
    "apr20_dgx_scripts",
]


def verify_migration():
    """Verify all critical keys exist in Cortex."""
    print("=== Verifying Cortex Migration ===")
    found = 0
    missing = []
    
    for key in CRITICAL_KEYS:
        result = cortex('get', key=key)
        if result.get('found'):
            found += 1
        else:
            missing.append(key)
    
    print(f"Found: {found}/{len(CRITICAL_KEYS)}")
    if missing:
        print(f"Missing: {missing}")
    return len(missing) == 0


def restore_critical_entries():
    """Restore critical entries to a format that can be manually added."""
    print("\n=== Restoring Critical Entries ===")
    print("Copy these into Hermes memory using the memory tool:\n")
    
    for key in CRITICAL_KEYS:
        result = cortex('get', key=key)
        if result.get('found'):
            mem = result['memory']
            print(f"--- {key} ---")
            print(f"{mem['text'][:200]}...")
            print()


def generate_memory_commands():
    """Generate memory add commands for the most critical entries."""
    print("\n=== Hermes Memory Commands ===")
    print("Run these in Hermes to restore critical memory:\n")
    
    # Only the most critical (to stay under 50KB)
    top_keys = CRITICAL_KEYS[:10]
    
    for key in top_keys:
        result = cortex('get', key=key)
        if result.get('found'):
            mem = result['memory']
            # Truncate to save space
            text = mem['text'][:300] + "..." if len(mem['text']) > 300 else mem['text']
            print(f'memory add "{key}: {text}"')
            print()


def show_status():
    """Show both memory systems status."""
    cortex_status = cortex('status')
    
    print("=== Memory Systems Status ===")
    print(f"\nCortex DB:")
    print(f"  Total entries: {cortex_status['total']}")
    print(f"  World facts: {cortex_status['world_facts']}")
    print(f"  Experiences: {cortex_status['experiences']}")
    print(f"  Date range: {cortex_status['earliest']} to {cortex_status['latest']}")
    
    print(f"\nHermes Memory:")
    print(f"  Status: CLEARED (restart required to free)")
    print(f"  Capacity: 50,000 chars")
    print(f"  Action: Use cortex_memory tool for long-term storage")


def main():
    parser = argparse.ArgumentParser(description="Memory Pruner")
    parser.add_argument("--verify", action="store_true", help="Verify migration complete")
    parser.add_argument("--restore", action="store_true", help="Show entries to restore")
    parser.add_argument("--commands", action="store_true", help="Generate memory commands")
    parser.add_argument("--status", action="store_true", help="Show status")
    args = parser.parse_args()
    
    if args.verify:
        success = verify_migration()
        sys.exit(0 if success else 1)
    elif args.restore:
        restore_critical_entries()
    elif args.commands:
        generate_memory_commands()
    elif args.status:
        show_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
