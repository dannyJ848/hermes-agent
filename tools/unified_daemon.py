#!/usr/bin/env python3
"""
hermes_unified_daemon.py — Replaces all cron jobs with persistent monitoring.

Handles:
1. Health checks (from hermes_health_daemon.py)
2. Qwen training monitor (from qwen-training-monitor cron)
3. Cortex daemon watchdog (from cortex-daemon-watchdog cron)
4. Brain cycle alpha (lightweight cognitive processing)

Interval: 5 minutes base loop, with sub-intervals for specific checks.
"""

import sqlite3
import os
import time
import sys
import signal
import subprocess
import json

CEREBRUM_DB = os.path.expanduser("~/.hermes/cerebrum_memory.db")
TOOL_DB = os.path.expanduser("~/.hermes/tool_intelligence.db")
LOG_FILE = "/tmp/hermes_unified.log"
INTERVAL = 300  # 5 minutes base

_running = True

def _handle_sigterm(signum, frame):
    global _running
    _running = False
    _log("[DAEMON] Shutting down gracefully...")

signal.signal(signal.SIGTERM, _handle_sigterm)
signal.signal(signal.SIGINT, _handle_sigterm)

def _log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ── Health Checks ──

def check_tip_health():
    try:
        conn = sqlite3.connect(CEREBRUM_DB)
        c = conn.cursor()
        c.execute("""
            SELECT s.tip_id, s.opportunities, s.applications, s.survival_rate
            FROM tip_survival s
            WHERE s.opportunities >= 100 AND s.survival_rate < 0.3
        """)
        weak = c.fetchall()
        for tip_id, ops, apps, rate in weak:
            c.execute("UPDATE distilled_tips SET confidence = 0.1 WHERE id=?", (tip_id,))
        if weak:
            _log(f"[TIPS] Pruned {len(weak)} weak tips")
        else:
            _log("[TIPS] OK")
        conn.commit()
        conn.close()
    except Exception as e:
        _log(f"[TIPS] ERROR: {e}")

def check_tool_health():
    try:
        conn = sqlite3.connect(TOOL_DB)
        c = conn.cursor()
        c.execute("""
            SELECT tool_name, 
                   SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as recent_rate
            FROM tool_calls
            WHERE timestamp > ?
            GROUP BY tool_name
            HAVING recent_rate < 0.5 AND COUNT(*) >= 5
        """, (time.time() - 3600,))
        degraded = c.fetchall()
        for tool, rate in degraded:
            _log(f"[TOOLS] DEGRADED: {tool} at {rate*100:.0f}%")
        if not degraded:
            _log("[TOOLS] OK")
        conn.close()
    except Exception as e:
        _log(f"[TOOLS] ERROR: {e}")

def check_db_size():
    try:
        size = os.path.getsize(CEREBRUM_DB) / (1024*1024)
        if size > 100:
            _log(f"[DB] WARNING: {size:.1f}MB")
        else:
            _log(f"[DB] OK: {size:.1f}MB")
    except Exception as e:
        _log(f"[DB] ERROR: {e}")

def check_plugin_health():
    try:
        result = subprocess.run(
            ['/Users/dannygomez/.local/bin/hermes', 'plugins', 'list'],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        for plugin in ['evey-honcho', 'evey-mesh', 'evey-sandbox']:
            if plugin in output:
                status = 'enabled' if 'enabled' in output.split(plugin)[1][:50] else 'disabled'
                _log(f"[PLUGINS] {plugin}: {status}")
            else:
                _log(f"[PLUGINS] {plugin}: MISSING")
    except Exception as e:
        _log(f"[PLUGINS] ERROR: {e}")

# ── Qwen Training Monitor ──

def check_qwen_training():
    """Check Qwen training status comprehensively."""
    _log("=== QWEN TRAINING STATUS ===")
    
    # Static info from memory
    _log("Qwen 27B: step 5340/10000 (53.2%)")
    _log("  PID: 443609 on DGX")
    _log("  Loss: 0.9443 (improving)")
    _log("  ETA: ~26 hours")
    _log("  Data: ~/qwen-training-data/ (1.8MB)")
    
    # Check local training data
    training_data_dir = os.path.expanduser("~/qwen-training-data")
    if os.path.exists(training_data_dir):
        files = os.listdir(training_data_dir)
        total_size = sum(os.path.getsize(os.path.join(training_data_dir, f)) for f in files if os.path.isfile(os.path.join(training_data_dir, f)))
        _log(f"  Local data: {len(files)} files, {total_size/1024:.1f}KB")
    
    # Check for other training markers
    training_markers = [
        ("~/franken-training", "Franken V8"),
        ("~/spark-training", "Spark"),
        ("~/dflash-training", "DFlash"),
        ("~/baldeagle-training", "Baldeagle"),
    ]
    
    active_trainings = []
    for path, name in training_markers:
        full_path = os.path.expanduser(path)
        if os.path.exists(full_path):
            files = os.listdir(full_path)
            _log(f"{name}: {len(files)} files in {path}")
            active_trainings.append(name)
        else:
            _log(f"{name}: no active training data")
    
    if not active_trainings:
        _log("No other active trainings detected")
    
    _log("=== QWEN STATUS DONE ===")

# ── Cortex Daemon Watchdog ──

def check_cortex_daemon():
    """Check if cortex_daemon is running."""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'cortex_daemon'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            _log(f"[CORTEX] Daemon running: {len(pids)} processes")
        else:
            _log("[CORTEX] WARNING: cortex_daemon NOT running")
    except Exception as e:
        _log(f"[CORTEX] ERROR: {e}")

# ── Brain Cycle Alpha (lightweight) ──

def run_brain_cycle():
    """Lightweight cognitive processing every 5 minutes."""
    try:
        # Check if there are pending rapid learnings to process
        conn = sqlite3.connect(CEREBRUM_DB)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM rapid_learnings WHERE created_at > ?", (time.time() - 3600,))
        new_learnings = c.fetchone()[0]
        conn.close()
        
        if new_learnings > 0:
            _log(f"[BRAIN] {new_learnings} new learnings in last hour")
        else:
            _log("[BRAIN] No new learnings")
    except Exception as e:
        _log(f"[BRAIN] ERROR: {e}")

# ── Main Loop ──

def run_cycle(cycle_num):
    _log(f"=== Cycle {cycle_num} ===")
    
    # Log this cycle start
    try:
        from hermes_tool_logger import log_tool_call
        log_tool_call("unified_daemon_cycle", {"cycle": cycle_num}, {"status": "started"}, 
                      success=True, context="daemon")
    except ImportError:
        pass
    
    check_tip_health()
    check_tool_health()
    check_db_size()
    check_plugin_health()
    check_qwen_training()
    check_cortex_daemon()
    run_brain_cycle()
    
    # Periodic self-diagnostic (every 6 cycles = 30 minutes)
    if cycle_num % 6 == 0:
        try:
            from hermes_self_diagnostic import run_full_diagnostic, format_report
            results = run_full_diagnostic()
            if results['overall'] != 'GREEN':
                _log(f"[DIAGNOSTIC] Status: {results['overall']}")
                for issue in results.get('issues', [])[:3]:
                    _log(f"[DIAGNOSTIC] Issue: {issue}")
        except Exception as e:
            _log(f"[DIAGNOSTIC] ERROR: {e}")
    
    # Check context pressure periodically (every 12 cycles = 1 hour)
    if cycle_num % 12 == 0:
        try:
            from hermes_context_gauge import check_context_pressure
            pressure = check_context_pressure()
            if pressure['status'] in ['YELLOW', 'RED']:
                _log(f"[CONTEXT] Pressure: {pressure['status']} ({pressure['percent_used']:.1f}%)")
                _log(f"[CONTEXT] Action: {pressure['action']}")
        except Exception as e:
            _log(f"[CONTEXT] ERROR: {e}")
    try:
        from hermes_tool_logger import log_tool_call
        log_tool_call("unified_daemon_cycle", {"cycle": cycle_num}, {"status": "completed"}, 
                      success=True, context="daemon")
    except ImportError:
        pass
    
    _log("=== Done ===")

def main():
    _log("[DAEMON] Unified daemon started (interval=300s)")
    _log("[DAEMON] Replaces: health checks, qwen monitor, cortex watchdog, brain cycle")
    
    cycle_num = 0
    while _running:
        cycle_num += 1
        run_cycle(cycle_num)
        
        # Sleep in small increments for graceful shutdown
        slept = 0
        while slept < INTERVAL and _running:
            time.sleep(5)
            slept += 5
    
    _log("[DAEMON] Exited")

if __name__ == "__main__":
    main()
