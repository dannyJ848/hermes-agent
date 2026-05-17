#!/usr/bin/env python3
"""
Hermes Cognitive Systems Integration Audit

Run this to check which agent/ modules are actually wired into the agent loop
vs orphaned (files present but never imported/called).

Usage:
    cd ~/hermes-agent && python3 references/cognitive-systems-audit-script.py
"""

import os
import re

MODULES = {
    'iteration_engine': {'hooks': ['before_action', 'after_action']},
    'cortex_learning': {'hooks': ['get_learning_engine', 'store.get_distilled_tips']},
    'error_learning': {'hooks': ['ErrorPatternMemory', 'learn_from_error']},
    'brain': {'hooks': ['run_cycle', 'ParallelBrain']},
    'training_gym': {'hooks': ['run_training_cycle']},
    'self_audit_engine': {'hooks': ['run_audit']},
    'cortex_flywheel': {'hooks': ['run_cycle']},
    'tiered_memory': {'hooks': ['TieredMemory']},
    'memory_cortex_bridge': {'hooks': ['sync']},
    'distillation_bridge': {'hooks': ['process']},
    'subconscious_hook_wiring': {'hooks': ['wire_hooks']},
    'autobrowse_tracer': {'hooks': ['trace']},
    'skill_effectiveness_tracker': {'hooks': ['track']},
}

def audit_file(filepath, label):
    with open(filepath, 'r') as f:
        content = f.read()
    
    results = []
    for name, info in MODULES.items():
        imported = f'from agent.{name}' in content or f'import agent.{name}' in content
        hooks_called = sum(content.count(hook) for hook in info['hooks'])
        
        if imported and hooks_called > 0:
            status = 'WIRED'
        elif imported:
            status = 'IMPORT_ONLY'
        else:
            status = 'ORPHANED'
        
        results.append((name, status, hooks_called))
    
    print(f"\n=== {label} ===")
    wired = sum(1 for _, s, _ in results if s == 'WIRED')
    orphaned = sum(1 for _, s, _ in results if s == 'ORPHANED')
    import_only = sum(1 for _, s, _ in results if s == 'IMPORT_ONLY')
    print(f"WIRED: {wired} | IMPORT_ONLY: {import_only} | ORPHANED: {orphaned}")
    print()
    for name, status, hooks in results:
        marker = '✓' if status == 'WIRED' else '!' if status == 'IMPORT_ONLY' else '✗'
        print(f"  {marker} {name:30s} {status:12s} ({hooks} hook calls)")
    
    return results

def main():
    os.chdir(os.path.expanduser('~/hermes-agent'))
    
    if not os.path.exists('run_agent.py'):
        print("ERROR: Must run from ~/hermes-agent directory")
        return
    
    run_agent_results = audit_file('run_agent.py', 'run_agent.py')
    
    if os.path.exists('cli.py'):
        cli_results = audit_file('cli.py', 'cli.py')
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total_orphaned = sum(1 for _, s, _ in run_agent_results if s == 'ORPHANED')
    total_bytes = 0
    for name, status, _ in run_agent_results:
        if status == 'ORPHANED':
            filepath = f'agent/{name}.py'
            if os.path.exists(filepath):
                total_bytes += os.path.getsize(filepath)
    
    print(f"Orphaned modules: {total_orphaned}")
    print(f"Orphaned code size: {total_bytes:,} bytes (~{total_bytes//40:,} lines)")
    print()
    print("Recommendation: WIRE or DELETE orphaned modules")
    print("  - To wire: import in run_agent.py, call hooks in AIAgent.__init__")
    print("  - To delete: rm agent/<module>.py and update any imports")

if __name__ == '__main__':
    main()
