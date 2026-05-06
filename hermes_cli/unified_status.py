#!/usr/bin/env python3
# Unified Hermes Status — shows ALL systems at once

import json
import os
import sqlite3
import subprocess

def get_status():
    """Get unified status of all Hermes systems."""
    
    # Load registry
    with open('hermes_cli/systems_registry.json', 'r') as f:
        registry = json.load(f)
    
    print("=" * 70)
    print("HERMES UNIFIED STATUS")
    print("=" * 70)
    
    # Core
    print("\n[CORE]")
    print(f"  Hermes CLI: {registry['hermes_core']['status']}")
    
    # Gateway
    print("\n[GATEWAY]")
    print(f"  Status: {registry['gateway']['status']}")
    
    # Subconscious / Judge
    print("\n[SUBCONSCIOUS / JUDGE]")
    judge = registry['subconscious']['components']['llm_judge.py']
    print(f"  Model: {judge['default_model']}")
    print(f"  Cost: ${judge['cost_per_1m']} per 1M tokens")
    print(f"  Discount: until {judge['discount_until']}")
    print(f"  Status: {judge['status']}")
    
    # Flywheel
    print("\n[FLYWHEEL]")
    flywheel = registry['subconscious']['components']['cortex_flywheel.py']
    print(f"  Heuristic alignment: {flywheel['heuristic_alignment']}")
    print(f"  Eval frequency: {flywheel['eval_frequency']}")
    print(f"  Status: {flywheel['status']}")
    
    # Cortex DB
    print("\n[CORTEX DB]")
    cortex = registry['subconscious']['components']['cortex_access.py']
    print(f"  Tables: {cortex['tables']}")
    print(f"  Tips: {cortex['tips']}")
    print(f"  Status: {cortex['status']}")
    
    # Training
    print("\n[TRAINING]")
    training = registry['training']
    print(f"  Script: {training['script']}")
    print(f"  PID: {training['pid']}")
    print(f"  Step: {training['step']}")
    print(f"  Status: {training['status']}")
    
    # Monitoring
    print("\n[MONITORING TOOLS]")
    for tool, desc in registry['monitoring']['tools'].items():
        print(f"  {tool}: {desc}")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    get_status()
