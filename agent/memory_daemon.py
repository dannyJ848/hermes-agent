#!/usr/bin/env python3
"""
memory_daemon.py — Background daemon for tiered memory maintenance.

Runs continuously (or via cron) to:
  1. Check hot tier overflow → offload to warm
  2. Evaluate warm tips in batches → send quality tips to cortex
  3. Promote golden rules from cold → hot
  4. Demote stale hot entries → warm

Usage:
    python3 memory_daemon.py --interval 300  # Run every 5 minutes
    python3 memory_daemon.py --once            # Single run, then exit
    python3 memory_daemon.py --stats           # Print current stats, exit
"""

import sys
import time
import json
import argparse
from pathlib import Path

# sys.path removed — modules now in hermes-agent
from agent.tiered_memory import TieredMemory


def run_maintenance(tm: TieredMemory, verbose: bool = False) -> dict:
    """Run one maintenance cycle. Returns action summary."""
    actions = tm.check_overflow()
    
    # Additional: evaluate warm batch if enough accumulated
    if tm.warm.count_unrated() >= 10:
        if verbose:
            print(f"[daemon] Evaluating warm batch ({tm.warm.count_unrated()} unrated)")
        sent = tm._evaluate_warm_batch()
        actions["distilled"] = sent
        if verbose:
            print(f"[daemon] Sent {sent} tips to cortex")
    
    return actions


def main():
    parser = argparse.ArgumentParser(description="Tiered memory maintenance daemon")
    parser.add_argument("--interval", type=int, default=300,
                        help="Seconds between maintenance runs (default: 300)")
    parser.add_argument("--once", action="store_true",
                        help="Run once and exit")
    parser.add_argument("--stats", action="store_true",
                        help="Print stats and exit")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")
    args = parser.parse_args()
    
    tm = TieredMemory()
    
    if args.stats:
        print(json.dumps(tm.get_stats(), indent=2))
        return
    
    if args.once:
        actions = run_maintenance(tm, verbose=args.verbose)
        print(json.dumps(actions, indent=2))
        return
    
    # Daemon loop
    print(f"[memory_daemon] Starting. Interval: {args.interval}s")
    print(f"[memory_daemon] Initial stats: {json.dumps(tm.get_stats())}")
    
    try:
        while True:
            actions = run_maintenance(tm, verbose=args.verbose)
            if any(actions.values()):
                print(f"[memory_daemon] Actions: {actions}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[memory_daemon] Shutting down.")


if __name__ == "__main__":
    main()
