#!/usr/bin/env python3
# Persistence Health Checker
# Monitors all databases and reports status

import sqlite3
import os
import json
from datetime import datetime

def check_cerebrum():
    """Check cerebrum memory health."""
    conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
    c = conn.cursor()
    
    health = {}
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    health['tables'] = [t[0] for t in c.fetchall()]
    
    c.execute("SELECT COUNT(*) FROM cortex_nodes WHERE node_type='tip'")
    health['tips'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM tool_intelligence")
    health['tools_tracked'] = c.fetchone()[0]
    
    c.execute("SELECT tool_name, consecutive_failures FROM tool_intelligence WHERE consecutive_failures > 0")
    health['failing_tools'] = c.fetchall()
    
    conn.close()
    return health

def check_training_gym():
    """Check training gym health."""
    conn = sqlite3.connect('/Users/dannygomez/.hermes/training_gym.db')
    c = conn.cursor()
    
    health = {}
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    health['tables'] = [t[0] for t in c.fetchall()]
    
    c.execute("SELECT run_id, current_step, total_steps, status FROM training_runs ORDER BY start_time DESC LIMIT 1")
    row = c.fetchone()
    if row:
        health['current_run'] = {
            'run_id': row[0],
            'step': row[1],
            'total': row[2],
            'status': row[3]
        }
    
    conn.close()
    return health

def full_health_report():
    """Generate full health report."""
    print("=" * 70)
    print("PERSISTENCE HEALTH - " + datetime.now().isoformat())
    print("=" * 70)
    
    cerebrum = check_cerebrum()
    print("
[CEREBRUM]")
    print("  Tables: " + str(len(cerebrum['tables'])))
    print("  Tips: " + str(cerebrum['tips']))
    print("  Tools tracked: " + str(cerebrum['tools_tracked']))
    if cerebrum['failing_tools']:
        failing = ", ".join(t[0] for t in cerebrum['failing_tools'])
        print("  WARNING Failing tools: " + failing)
    
    training = check_training_gym()
    print("
[TRAINING GYM]")
    print("  Tables: " + str(len(training['tables'])))
    if 'current_run' in training:
        r = training['current_run']
        print("  Current: " + r['run_id'] + " - Step " + str(r['step']) + "/" + str(r['total']) + " (" + r['status'] + ")")
    
    print("
" + "=" * 70)

if __name__ == '__main__':
    full_health_report()
