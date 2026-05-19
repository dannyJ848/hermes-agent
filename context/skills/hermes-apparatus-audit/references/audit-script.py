#!/usr/bin/env python3
"""
Hermes Apparatus Audit Script
Run this to get a complete system state snapshot.
"""

import os, json, sqlite3, glob
from pathlib import Path

def run_audit():
    results = {}
    
    # 1. Knowledge docs
    knowledge_dir = Path.home() / '.hermes' / 'knowledge'
    queued_docs = list(knowledge_dir.glob('*.md')) if knowledge_dir.exists() else []
    results['queued_docs'] = len(queued_docs)
    
    # 2. Health daemon
    health_log = Path('/tmp/hermes_health.log')
    results['health_log_exists'] = health_log.exists()
    if health_log.exists():
        lines = health_log.read_text().split('\n')
        results['health_log_lines'] = len(lines)
    
    # 3. Subconscious modules
    subconscious_dir = Path.home() / 'subconscious'
    modules = list(subconscious_dir.glob('*.py')) if subconscious_dir.exists() else []
    results['subconscious_modules'] = len(modules)
    
    # 4. Cortex DB tables
    cortex_db = Path.home() / '.hermes' / 'cerebrum_memory.db'
    if cortex_db.exists():
        conn = sqlite3.connect(str(cortex_db))
        cursor = conn.cursor()
        
        for table in ['distilled_tips', 'tip_survival', 'prompt_fragments', 
                      'error_patterns_predictive', 'enhancement_effectiveness',
                      'rapid_learnings', 'projects', 'auto_skill_pipeline',
                      'tip_adversarial']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                results[table] = cursor.fetchone()[0]
            except:
                results[table] = 'MISSING'
        
        conn.close()
    
    # 5. Training data
    training_dir = Path.home() / 'qwen-training-data'
    if training_dir.exists():
        files = list(training_dir.glob('*'))
        results['training_total_mb'] = sum(f.stat().st_size for f in files) / (1024*1024)
    
    # 6. Checkpoint
    checkpoint = Path.home() / '.hermes/workspace/checkpoints'
    results['checkpoints'] = len(list(checkpoint.glob('*.json'))) if checkpoint.exists() else 0
    
    return results

if __name__ == '__main__':
    print(json.dumps(run_audit(), indent=2, default=str))
