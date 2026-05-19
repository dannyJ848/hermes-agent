#!/usr/bin/env python3
"""
hermes_manual_triggers.py — Replaces cron jobs with on-demand execution.

Usage:
  python3 hermes_manual_triggers.py <trigger_name>

Available triggers:
  training-status     — Check all training jobs (Qwen, Franken, Spark, etc.)
  research-scan       — Run research/news scan
  cortex-consolidate  — Run cortex consolidation
  brain-cycle         — Run brain cycle processing
  daily-backup        — Run daily backup
  quality-sweep       — Run cortex quality sweep
  llm-calibrate       — Run LLM calibration
  full-report         — Run all checks and produce report
"""

import sqlite3
import os
import sys
import time
import subprocess

CEREBRUM_DB = os.path.expanduser("~/.hermes/cerebrum_memory.db")
TOOL_DB = os.path.expanduser("~/.hermes/tool_intelligence.db")

def _log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}")

# ── Training Status ──

def trigger_training_status():
    """Check all training jobs status."""
    _log("=== TRAINING STATUS ===")
    
    # Qwen training
    _log("Qwen 27B: step 5340/10000 (53.2%), PID 443609 on DGX")
    _log("  Loss: 0.9443, ETA: ~26 hours")
    _log("  Data: ~/qwen-training-data/ (1.8MB)")
    
    # Check for other training markers
    training_markers = [
        ("~/franken-training", "Franken V8"),
        ("~/spark-training", "Spark"),
        ("~/dflash-training", "DFlash"),
        ("~/baldeagle-training", "Baldeagle"),
    ]
    
    for path, name in training_markers:
        full_path = os.path.expanduser(path)
        if os.path.exists(full_path):
            files = os.listdir(full_path)
            _log(f"{name}: {len(files)} files in {path}")
        else:
            _log(f"{name}: no active training data")
    
    _log("=== DONE ===")

# ── Research Scan ──

def trigger_research_scan():
    """Run research/news scan."""
    _log("=== RESEARCH SCAN ===")
    _log("This would run: web_research for AI agent news")
    _log("Use web_research tool directly for specific queries")
    _log("=== DONE ===")

# ── Cortex Consolidation ──

def trigger_cortex_consolidate():
    """Run cortex consolidation."""
    _log("=== CORTEX CONSOLIDATION ===")
    try:
        conn = sqlite3.connect(CEREBRUM_DB)
        c = conn.cursor()
        
        # Stats
        c.execute("SELECT COUNT(*) FROM distilled_tips")
        tips = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM rapid_learnings")
        learnings = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM tip_survival")
        survival = c.fetchone()[0]
        
        _log(f"Stats: {tips} tips, {learnings} learnings, {survival} survival records")
        
        # Check for consolidation needs
        c.execute("SELECT COUNT(*) FROM rapid_learnings WHERE created_at < ?", (time.time() - 86400,))
        old_learnings = c.fetchone()[0]
        if old_learnings > 10:
            _log(f"ACTION: {old_learnings} old learnings need consolidation into distilled_tips")
        
        conn.close()
    except Exception as e:
        _log(f"ERROR: {e}")
    _log("=== DONE ===")

# ── Brain Cycle ──

def trigger_brain_cycle():
    """Run brain cycle processing."""
    _log("=== BRAIN CYCLE ===")
    try:
        conn = sqlite3.connect(CEREBRUM_DB)
        c = conn.cursor()
        
        # Check new data
        c.execute("SELECT COUNT(*) FROM rapid_learnings WHERE created_at > ?", (time.time() - 3600,))
        new_learnings = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM tip_injection_attempts WHERE created_at > ?", (time.time() - 3600,))
        new_injections = c.fetchone()[0]
        
        _log(f"Last hour: {new_learnings} learnings, {new_injections} injection attempts")
        
        # Check tool performance
        conn2 = sqlite3.connect(TOOL_DB)
        c2 = conn2.cursor()
        c2.execute("""
            SELECT tool_name, 
                   SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as rate
            FROM tool_calls
            WHERE timestamp > ?
            GROUP BY tool_name
            ORDER BY rate ASC
            LIMIT 3
        """, (time.time() - 3600,))
        weak = c2.fetchall()
        for tool, rate in weak:
            _log(f"WEAK TOOL: {tool} at {rate*100:.0f}% (last hour)")
        conn2.close()
        
        conn.close()
    except Exception as e:
        _log(f"ERROR: {e}")
    _log("=== DONE ===")

# ── Daily Backup ──

def trigger_daily_backup():
    """Run daily backup."""
    _log("=== DAILY BACKUP ===")
    _log("This would run: git commit for ~/.hermes/")
    _log("Use: cd ~/.hermes && git add -A && git commit -m 'backup'")
    _log("=== DONE ===")

# ── Quality Sweep ──

def trigger_quality_sweep():
    """Run cortex quality sweep."""
    _log("=== QUALITY SWEEP ===")
    try:
        conn = sqlite3.connect(CEREBRUM_DB)
        c = conn.cursor()
        
        # Check tip quality distribution
        c.execute("""
            SELECT 
                CASE 
                    WHEN confidence >= 0.9 THEN 'excellent'
                    WHEN confidence >= 0.7 THEN 'good'
                    WHEN confidence >= 0.5 THEN 'fair'
                    ELSE 'weak'
                END as quality,
                COUNT(*) as cnt
            FROM distilled_tips
            GROUP BY quality
            ORDER BY cnt DESC
        """)
        dist = c.fetchall()
        for quality, cnt in dist:
            _log(f"Tips {quality}: {cnt}")
        
        conn.close()
    except Exception as e:
        _log(f"ERROR: {e}")
    _log("=== DONE ===")

# ── LLM Calibrate ──

def trigger_llm_calibrate():
    """Run LLM calibration."""
    _log("=== LLM CALIBRATE ===")
    _log("This would run: test model responses and calibrate confidence")
    _log("Manual: use delegate_with_model to test different models")
    _log("=== DONE ===")

# ── Full Report ──

def trigger_full_report():
    """Run all checks and produce report."""
    _log("=" * 50)
    _log("HERMES FULL STATUS REPORT")
    _log("=" * 50)
    trigger_training_status()
    trigger_cortex_consolidate()
    trigger_brain_cycle()
    trigger_quality_sweep()
    trigger_context_pressure()
    trigger_self_diagnostic()
    _log("=" * 50)
    _log("REPORT COMPLETE")
    _log("=" * 50)

def trigger_context_pressure():
    """Check context window pressure."""
    _log("=== CONTEXT PRESSURE ===")
    try:
        from hermes_context_gauge import check_context_pressure
        pressure = check_context_pressure()
        _log(f"Status: {pressure['status']} ({pressure['percent_used']:.1f}%)")
        _log(f"Tokens: {pressure['tokens_used']}/{pressure['token_limit']}")
        _log(f"Action: {pressure['action']}")
        if pressure['action'] in ['CHECKPOINT_NOW', 'PLAN_HANDOFF']:
            _log("WARNING: Context pressure high - consider checkpoint")
    except Exception as e:
        _log(f"ERROR: {e}")
    _log("=== DONE ===")

def trigger_self_diagnostic():
    """Run self diagnostic."""
    _log("=== SELF DIAGNOSTIC ===")
    try:
        from hermes_self_diagnostic import run_full_diagnostic, format_report
        results = run_full_diagnostic()
        report = format_report(results)
        for line in report.split('\n'):
            _log(line)
    except Exception as e:
        _log(f"ERROR: {e}")
    _log("=== DONE ===")

def trigger_skill_generate():
    """Generate skill from recent session."""
    _log("=== SKILL GENERATION ===")
    try:
        from hermes_skill_generator import generate_skill_from_session, list_auto_skills
        result = generate_skill_from_session(hours_back=24, min_confidence=0.8)
        if result and 'error' not in result:
            _log(f"Generated skill: {result['name']}")
            _log(f"Path: {result['path']}")
            _log(f"Learnings: {result['learnings_used']}, Steps: {result['steps_generated']}")
        else:
            _log("No skills generated (insufficient learnings)")
        
        # List all auto skills
        skills = list_auto_skills()
        _log(f"Total auto skills: {len(skills)}")
    except Exception as e:
        _log(f"ERROR: {e}")
    _log("=== DONE ===")

# ── Main ──

TRIGGERS = {
    'training-status': trigger_training_status,
    'research-scan': trigger_research_scan,
    'cortex-consolidate': trigger_cortex_consolidate,
    'brain-cycle': trigger_brain_cycle,
    'daily-backup': trigger_daily_backup,
    'quality-sweep': trigger_quality_sweep,
    'llm-calibrate': trigger_llm_calibrate,
    'full-report': trigger_full_report,
    'context-pressure': trigger_context_pressure,
    'self-diagnostic': trigger_self_diagnostic,
    'skill-generate': trigger_skill_generate,
}

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 hermes_manual_triggers.py <trigger_name>")
        print("\nAvailable triggers:")
        for name in sorted(TRIGGERS.keys()):
            print(f"  {name}")
        sys.exit(1)
    
    trigger_name = sys.argv[1]
    if trigger_name not in TRIGGERS:
        print(f"Unknown trigger: {trigger_name}")
        print(f"Available: {', '.join(sorted(TRIGGERS.keys()))}")
        sys.exit(1)
    
    TRIGGERS[trigger_name]()

if __name__ == "__main__":
    main()
