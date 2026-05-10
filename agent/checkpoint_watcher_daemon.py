#!/usr/bin/env python3
"""
checkpoint_watcher_daemon.py — Persistent daemon for training checkpoint monitoring.

Monitors training log for checkpoint save events and OOM errors.
Alerts on failure. Can auto-restart training from latest checkpoint.

Usage:
    from checkpoint_watcher_daemon import CheckpointWatcherDaemon
    watcher = CheckpointWatcherDaemon()
    watcher.start(log_file="/mnt/bigssd/train.log", target_step=1000)
    # Or run as background process:
    # python3 checkpoint_watcher_daemon.py --start --log-file /mnt/bigssd/train.log --target-step 1000

Wiring:
    - Run as nohup daemon on DGX Spark
    - Or cron job every 2 minutes
    - Integrates with auto_launch_monitor for restart on crash
"""

import os
import re
import sys
import json
import time
import sqlite3
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

HERMES_HOME = Path.home() / ".hermes"
WATCHER_DB = HERMES_HOME / "checkpoint_watcher.db"
RECOVERY_SCRIPT = "/tmp/recovery_plan.sh"

class CheckpointWatcherDaemon:
    """Persistent checkpoint watcher with state tracking."""
    
    def __init__(self):
        self._ensure_db()
        self.running = False
        self.state: Dict = {}
    
    def _ensure_db(self):
        WATCHER_DB.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(WATCHER_DB)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watcher_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_file TEXT,
                    target_step INTEGER,
                    start_time REAL,
                    end_time REAL,
                    status TEXT,
                    last_step INTEGER,
                    last_loss REAL,
                    checkpoint_found BOOLEAN,
                    oom_detected BOOLEAN,
                    restart_triggered BOOLEAN,
                    alert_sent BOOLEAN
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS log_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    step INTEGER,
                    loss REAL,
                    gpu_gb REAL,
                    lr REAL,
                    timestamp REAL
                )
            """)
    
    def parse_log_line(self, line: str) -> Optional[Dict]:
        """Parse a training log line. Returns step info or None."""
        # Step line: "Step 60/4000 | Loss: 3.9990 (CE:3.710 D:1.402 SAE:0.574) | W:(0.99,0.20,0.05) | LR: 3.05e-05 | GPU: 85.3GB"
        step_match = re.search(r'Step\s+(\d+)/(\d+)\s+\|\s+Loss:\s+([\d.]+)', line)
        if step_match:
            return {
                'step': int(step_match.group(1)),
                'total': int(step_match.group(2)),
                'loss': float(step_match.group(3)),
                'raw': line
            }
        
        # OOM detection
        if 'OOM' in line or 'out of memory' in line.lower() or 'CUDA error' in line:
            return {'type': 'oom', 'raw': line}
        
        # Checkpoint save
        if 'Saved checkpoint' in line:
            ckpt_match = re.search(r'checkpoint_step_(\d+)', line)
            if ckpt_match:
                return {'type': 'checkpoint', 'step': int(ckpt_match.group(1)), 'raw': line}
        
        return None
    
    def check_log(self, log_file: str, target_step: int) -> Dict:
        """Check log file for status. Returns status dict."""
        if not os.path.exists(log_file):
            return {'status': 'log_missing', 'log_file': log_file}
        
        # Read last 50 lines
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            return {'status': 'read_error', 'error': str(e)}
        
        last_lines = lines[-50:] if len(lines) > 50 else lines
        
        latest_step = 0
        latest_loss = 0.0
        oom_detected = False
        checkpoint_found = False
        
        for line in last_lines:
            parsed = self.parse_log_line(line)
            if not parsed:
                continue
            
            if 'step' in parsed and parsed.get('type') != 'checkpoint':
                latest_step = parsed['step']
                latest_loss = parsed.get('loss', 0)
            elif parsed.get('type') == 'oom':
                oom_detected = True
            elif parsed.get('type') == 'checkpoint':
                if parsed['step'] == target_step:
                    checkpoint_found = True
        
        # Check if process is alive
        pid_file = Path(log_file).parent / "train.pid"
        pid = 0
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
            except Exception:
                pass
        
        alive = False
        if pid > 0:
            try:
                os.kill(pid, 0)
                alive = True
            except (OSError, ProcessLookupError):
                pass
        
        return {
            'status': 'oom' if oom_detected else ('checkpoint_found' if checkpoint_found else 'running'),
            'latest_step': latest_step,
            'latest_loss': latest_loss,
            'target_step': target_step,
            'checkpoint_found': checkpoint_found,
            'oom_detected': oom_detected,
            'pid': pid,
            'alive': alive,
            'log_lines_read': len(last_lines)
        }
    
    def trigger_recovery(self, log_file: str) -> Dict:
        """Trigger recovery via recovery script."""
        if not os.path.exists(RECOVERY_SCRIPT):
            return {'status': 'no_recovery_script', 'path': RECOVERY_SCRIPT}
        
        try:
            result = subprocess.run(
                ["bash", RECOVERY_SCRIPT],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                'status': 'recovery_triggered' if result.returncode == 0 else 'recovery_failed',
                'stdout': result.stdout[:500],
                'stderr': result.stderr[:500],
                'returncode': result.returncode
            }
        except Exception as e:
            return {'status': 'recovery_error', 'error': str(e)}
    
    def start(self, log_file: str, target_step: int, interval: int = 30) -> None:
        """
        Start persistent watching loop.
        
        Usage:
            watcher = CheckpointWatcherDaemon()
            watcher.start("/mnt/bigssd/train.log", 1000)
        """
        self.running = True
        
        with sqlite3.connect(str(WATCHER_DB)) as conn:
            cur = conn.execute("""
                INSERT INTO watcher_runs (log_file, target_step, start_time, status)
                VALUES (?, ?, ?, ?)
            """, (log_file, target_step, time.time(), 'running'))
            run_id = cur.lastrowid
            conn.commit()
        
        print(f"[WATCHER] Started monitoring {log_file} for step {target_step}")
        
        try:
            while self.running:
                status = self.check_log(log_file, target_step)
                
                # Record snapshot
                if status['latest_step'] > 0:
                    with sqlite3.connect(str(WATCHER_DB)) as conn:
                        conn.execute("""
                            INSERT INTO log_snapshots (run_id, step, loss, timestamp)
                            VALUES (?, ?, ?, ?)
                        """, (run_id, status['latest_step'], status['latest_loss'], time.time()))
                        conn.commit()
                
                # Handle states
                if status['oom_detected']:
                    print(f"[WATCHER] OOM detected at step {status['latest_step']}!")
                    recovery = self.trigger_recovery(log_file)
                    
                    with sqlite3.connect(str(WATCHER_DB)) as conn:
                        conn.execute("""
                            UPDATE watcher_runs SET status = ?, oom_detected = 1, restart_triggered = ?
                            WHERE id = ?
                        """, ('oom_recovery', recovery['status'] == 'recovery_triggered', run_id))
                        conn.commit()
                    
                    if recovery['status'] == 'recovery_triggered':
                        print("[WATCHER] Recovery triggered successfully")
                    else:
                        print(f"[WATCHER] Recovery failed: {recovery}")
                
                elif status['checkpoint_found']:
                    print(f"[WATCHER] SUCCESS: Checkpoint at step {target_step} found!")
                    with sqlite3.connect(str(WATCHER_DB)) as conn:
                        conn.execute("""
                            UPDATE watcher_runs SET status = ?, checkpoint_found = 1, end_time = ?
                            WHERE id = ?
                        """, ('checkpoint_found', time.time(), run_id))
                        conn.commit()
                    break  # Done
                
                elif not status['alive'] and status['pid'] > 0:
                    print(f"[WATCHER] Process dead (PID {status['pid']})! Triggering recovery...")
                    recovery = self.trigger_recovery(log_file)
                    
                    with sqlite3.connect(str(WATCHER_DB)) as conn:
                        conn.execute("""
                            UPDATE watcher_runs SET status = ?, restart_triggered = ?
                            WHERE id = ?
                        """, ('process_dead', recovery['status'] == 'recovery_triggered', run_id))
                        conn.commit()
                
                else:
                    print(f"[WATCHER] Step {status['latest_step']}/{target_step} | Loss: {status['latest_loss']:.4f} | {'ALIVE' if status['alive'] else 'DEAD'}")
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("[WATCHER] Stopped by user")
            with sqlite3.connect(str(WATCHER_DB)) as conn:
                conn.execute("UPDATE watcher_runs SET status = ?, end_time = ? WHERE id = ?",
                           ('stopped', time.time(), run_id))
                conn.commit()
    
    def stop(self):
        self.running = False
    
    def get_stats(self) -> Dict:
        with sqlite3.connect(str(WATCHER_DB)) as conn:
            total_runs = conn.execute("SELECT COUNT(*) FROM watcher_runs").fetchone()[0]
            oom_runs = conn.execute("SELECT COUNT(*) FROM watcher_runs WHERE oom_detected = 1").fetchone()[0]
            ckpt_runs = conn.execute("SELECT COUNT(*) FROM watcher_runs WHERE checkpoint_found = 1").fetchone()[0]
            restarts = conn.execute("SELECT COUNT(*) FROM watcher_runs WHERE restart_triggered = 1").fetchone()[0]
            
            return {
                'total_runs': total_runs,
                'oom_detected': oom_runs,
                'checkpoints_found': ckpt_runs,
                'restarts_triggered': restarts,
                'db_path': str(WATCHER_DB)
            }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Checkpoint Watcher Daemon")
    parser.add_argument("--start", action="store_true", help="Start watching")
    parser.add_argument("--log-file", type=str, help="Training log file path")
    parser.add_argument("--target-step", type=int, help="Target checkpoint step")
    parser.add_argument("--interval", type=int, default=30, help="Check interval seconds")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    watcher = CheckpointWatcherDaemon()
    
    if args.start and args.log_file and args.target_step:
        watcher.start(args.log_file, args.target_step, args.interval)
    elif args.stats:
        print(json.dumps(watcher.get_stats(), indent=2))
    else:
        print("Usage: python3 checkpoint_watcher_daemon.py --start --log-file PATH --target-step N")