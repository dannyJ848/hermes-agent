#!/usr/bin/env python3
"""
hermes_health_daemon.py — Persistent background health monitor.

Runs as a self-looping daemon (no cron needed):
  terminal(background=True): python3 /Users/dannygomez/hermes-agent/agent/hermes_health_daemon.py

Checks every 5 minutes:
1. Tip survival rates — prune weak tips
2. Tool performance — flag degrading tools
3. Database size — alert if cerebrum >100MB
4. Error pattern frequency — escalate recurring issues
5. Plugin health — verify all enabled plugins load
"""

import sqlite3
import os
import time
import sys
import signal

CEREBRUM_DB = os.path.expanduser("~/.hermes/cerebrum_memory.db")
TOOL_DB = os.path.expanduser("~/.hermes/tool_intelligence.db")
LOG_FILE = "/tmp/hermes_health.log"
INTERVAL = 300  # 5 minutes

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

def check_tip_health():
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
        _log(f"[TIPS] Pruned {len(weak)} weak tips (<30% survival)")
    else:
        _log("[TIPS] OK: no weak tips to prune")
    
    conn.commit()
    conn.close()

def check_tool_health():
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
        _log(f"[TOOLS] DEGRADED: {tool} at {rate*100:.0f}% (last hour)")
    if not degraded:
        _log("[TOOLS] OK: no degraded tools")
    
    conn.close()

def check_db_size():
    size = os.path.getsize(CEREBRUM_DB) / (1024*1024)
    if size > 100:
        _log(f"[DB] WARNING: cerebrum_memory.db is {size:.1f}MB (>100MB threshold)")
    else:
        _log(f"[DB] OK: {size:.1f}MB")

def check_error_patterns():
    conn = sqlite3.connect(CEREBRUM_DB)
    c = conn.cursor()
    
    c.execute("SELECT pattern_name, occurrence_count FROM error_patterns_predictive WHERE occurrence_count > 10")
    hot_patterns = c.fetchall()
    
    for pattern, count in hot_patterns:
        _log(f"[ERRORS] HOT PATTERN: {pattern} ({count} occurrences)")
    if not hot_patterns:
        _log("[ERRORS] OK: no hot error patterns")
    
    conn.close()

def check_plugin_health():
    import subprocess
    
    try:
        result = subprocess.run(
            ['/Users/dannygomez/.local/bin/hermes', 'plugins', 'list'],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        
        for plugin in ['evey-honcho', 'evey-mesh', 'evey-sandbox']:
            if plugin in output:
                for line in output.split('\n'):
                    if plugin in line:
                        if 'enabled' in line:
                            _log(f"[PLUGINS] {plugin}: enabled")
                        elif 'disabled' in line:
                            _log(f"[PLUGINS] {plugin}: disabled (enable with 'hermes plugins enable {plugin}')")
                        else:
                            _log(f"[PLUGINS] {plugin}: present")
                        break
            else:
                _log(f"[PLUGINS] {plugin}: MISSING")
    except Exception as e:
        _log(f"[PLUGINS] check failed: {e}")

def run_check():
    _log("=== Hermes Health Check ===")
    check_tip_health()
    check_tool_health()
    check_db_size()
    check_error_patterns()
    check_plugin_health()
    _log("=== Done ===")

def main():
    _log("[DAEMON] Starting Hermes health monitor (interval=300s)")
    
    while _running:
        run_check()
        
        # Sleep in small increments to allow graceful shutdown
        slept = 0
        while slept < INTERVAL and _running:
            time.sleep(5)
            slept += 5
    
    _log("[DAEMON] Exited")

if __name__ == "__main__":
    main()
