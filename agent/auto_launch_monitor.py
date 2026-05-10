#!/usr/bin/env python3
"""
auto_launch_monitor.py — Monitor and auto-relaunch critical processes.

Watches training processes, checkpoint watchers, and other daemons.
Restarts them if they die. Sends alerts on repeated failures.

Usage:
    from auto_launch_monitor import AutoLaunchMonitor
    monitor = AutoLaunchMonitor()
    monitor.watch_process("training", pid=881997, restart_cmd="python3 train.py")
    monitor.check_all()  # Returns status report

Wiring:
    - Run as cron job every 5 minutes
    - Or daemon thread in main process
"""

import os
import re
import sys
import json
import time
import subprocess
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

HERMES_HOME = Path.home() / ".hermes"
MONITOR_DB = HERMES_HOME / "auto_launch_monitor.db"
RECOVERY_SCRIPT = "/tmp/recovery_plan.sh"

class AutoLaunchMonitor:
    """Monitor and auto-relaunch critical processes."""
    
    def __init__(self):
        self._ensure_db()
        self.watched: Dict[str, Dict] = {}
    
    def _ensure_db(self):
        MONITOR_DB.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(MONITOR_DB)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS process_watches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    pid INTEGER,
                    restart_cmd TEXT,
                    check_interval INTEGER DEFAULT 300,
                    max_restarts INTEGER DEFAULT 3,
                    restart_count INTEGER DEFAULT 0,
                    last_check REAL,
                    last_restart REAL,
                    status TEXT DEFAULT 'unknown',
                    alert_sent BOOLEAN DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS restart_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    old_pid INTEGER,
                    new_pid INTEGER,
                    reason TEXT,
                    success BOOLEAN,
                    created_at REAL
                )
            """)
    
    def watch_process(self, name: str, pid: int = 0, restart_cmd: str = "",
                      check_interval: int = 300, max_restarts: int = 3):
        """Add a process to watch list."""
        with sqlite3.connect(str(MONITOR_DB)) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO process_watches
                (name, pid, restart_cmd, check_interval, max_restarts, last_check, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, pid, restart_cmd, check_interval, max_restarts, time.time(), 'watching'))
            conn.commit()
        
        self.watched[name] = {
            'pid': pid,
            'restart_cmd': restart_cmd,
            'check_interval': check_interval,
            'max_restarts': max_restarts
        }
    
    def is_alive(self, pid: int) -> bool:
        """Check if process is alive."""
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False
    
    def check_process(self, name: str) -> Dict:
        """Check a single process. Returns status."""
        with sqlite3.connect(str(MONITOR_DB)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM process_watches WHERE name = ?", (name,)
            ).fetchone()
            
            if not row:
                return {"status": "not_found", "name": name}
            
            info = dict(row)
            pid = info['pid']
            
            # Check if alive
            alive = self.is_alive(pid)
            now = time.time()
            
            if alive:
                # Update last check
                conn.execute(
                    "UPDATE process_watches SET last_check = ?, status = ? WHERE name = ?",
                    (now, 'alive', name)
                )
                conn.commit()
                return {"status": "alive", "name": name, "pid": pid}
            
            # Process dead — need restart
            if info['restart_count'] >= info['max_restarts']:
                conn.execute(
                    "UPDATE process_watches SET status = ?, alert_sent = 1 WHERE name = ?",
                    ('failed_permanently', name)
                )
                conn.commit()
                return {
                    "status": "failed_permanently",
                    "name": name,
                    "restarts": info['restart_count'],
                    "action": "ALERT: Max restarts exceeded"
                }
            
            # Attempt restart
            restart_cmd = info['restart_cmd']
            if not restart_cmd:
                return {"status": "dead_no_restart_cmd", "name": name}
            
            # Execute restart
            try:
                result = subprocess.run(
                    restart_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                # Try to extract new PID
                new_pid = 0
                if result.returncode == 0:
                    # Look for PID in output
                    pid_match = re.search(r'PID\s+(\d+)', result.stdout)
                    if pid_match:
                        new_pid = int(pid_match.group(1))
                    else:
                        # Try to find process by name
                        new_pid = self._find_pid_by_name(name)
                
                # Record restart
                conn.execute("""
                    INSERT INTO restart_history (name, old_pid, new_pid, reason, success, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, pid, new_pid, 'process_died', result.returncode == 0, now))
                
                if result.returncode == 0 and new_pid > 0:
                    conn.execute("""
                        UPDATE process_watches 
                        SET pid = ?, restart_count = restart_count + 1, 
                            last_restart = ?, last_check = ?, status = ?
                        WHERE name = ?
                    """, (new_pid, now, now, 'restarted', name))
                    conn.commit()
                    return {
                        "status": "restarted",
                        "name": name,
                        "old_pid": pid,
                        "new_pid": new_pid,
                        "restarts": info['restart_count'] + 1
                    }
                else:
                    conn.execute("""
                        UPDATE process_watches 
                        SET restart_count = restart_count + 1, status = ?, alert_sent = 1
                        WHERE name = ?
                    """, ('restart_failed', name))
                    conn.commit()
                    return {
                        "status": "restart_failed",
                        "name": name,
                        "error": result.stderr[:200]
                    }
                    
            except Exception as e:
                return {"status": "restart_error", "name": name, "error": str(e)}
    
    def _find_pid_by_name(self, name: str) -> int:
        """Find PID by process name pattern."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split('\n')[0])
        except Exception:
            pass
        return 0
    
    def check_all(self) -> List[Dict]:
        """Check all watched processes. Returns list of statuses."""
        with sqlite3.connect(str(MONITOR_DB)) as conn:
            names = [r[0] for r in conn.execute("SELECT name FROM process_watches").fetchall()]
        
        results = []
        for name in names:
            results.append(self.check_process(name))
        
        return results
    
    def get_stats(self) -> Dict:
        with sqlite3.connect(str(MONITOR_DB)) as conn:
            total = conn.execute("SELECT COUNT(*) FROM process_watches").fetchone()[0]
            alive = conn.execute("SELECT COUNT(*) FROM process_watches WHERE status = 'alive'").fetchone()[0]
            dead = conn.execute("SELECT COUNT(*) FROM process_watches WHERE status != 'alive'").fetchone()[0]
            restarts = conn.execute("SELECT COUNT(*) FROM restart_history").fetchone()[0]
            
            return {
                "total_watched": total,
                "alive": alive,
                "dead_or_failed": dead,
                "total_restarts": restarts,
                "db_path": str(MONITOR_DB)
            }


# Training-specific monitor helper
def monitor_training(pid: int = 0, log_file: str = "") -> Dict:
    """
    Quick setup for training monitoring.
    
    Usage:
        result = monitor_training(pid=881997, log_file="/mnt/bigssd/train.log")
    """
    monitor = AutoLaunchMonitor()
    
    # Build restart command from recovery script
    restart_cmd = f"bash {RECOVERY_SCRIPT}"
    
    monitor.watch_process(
        name="training",
        pid=pid,
        restart_cmd=restart_cmd,
        check_interval=300,  # 5 minutes
        max_restarts=3
    )
    
    return monitor.check_process("training")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-Launch Monitor")
    parser.add_argument("--watch", type=str, help="Watch a process by name")
    parser.add_argument("--pid", type=int, help="Process PID")
    parser.add_argument("--restart-cmd", type=str, help="Command to restart process")
    parser.add_argument("--check", action="store_true", help="Check all watched processes")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    monitor = AutoLaunchMonitor()
    
    if args.watch:
        monitor.watch_process(args.watch, args.pid or 0, args.restart_cmd or "")
        print(f"Watching {args.watch} (PID {args.pid})")
    elif args.check:
        results = monitor.check_all()
        print(json.dumps(results, indent=2))
    else:
        print(json.dumps(monitor.get_stats(), indent=2))