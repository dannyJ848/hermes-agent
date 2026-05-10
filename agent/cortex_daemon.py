#!/usr/bin/env python3
"""
cortex_daemon.py — 24/7 autonomous daemon for the Cortex training gym.

Runs continuously, executing flywheel cycles, monitoring training health,
and injecting high-quality tips back into the agent.

Components:
  1. Flywheel Runner — periodic Elo tournaments
  2. Training Monitor — watch for new tips from research/dojo
  3. Quality Gate — only inject tips above Elo threshold
  4. Health Monitor — heartbeat, disk space, API health
  5. Tip Injector — push top tips into agent context

Usage:
    python3 cortex_daemon.py start    # Start daemon
    python3 cortex_daemon.py stop     # Stop daemon
    python3 cortex_daemon.py status   # Check status
    python3 cortex_daemon.py once     # Run one cycle and exit
"""

import sys
import os
import json
import time
import signal
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

sys.path.insert(0, str(Path.home() / "hermes-agent"))
from agent.cortex_access import CortexDB
from agent.cortex_flywheel import CortexFlywheel

# Configuration
PID_FILE = Path.home() / ".hermes" / "cortex_daemon.pid"
LOG_FILE = Path.home() / ".hermes" / "cortex_daemon.log"
STATE_FILE = Path.home() / ".hermes" / "cortex_daemon_state.json"

FLYWHEEL_INTERVAL = 7200       # 2 hours between flywheel cycles
QUALITY_CHECK_INTERVAL = 3600  # 1 hour between quality checks
HEARTBEAT_INTERVAL = 300       # 5 minutes between heartbeats
INJECTION_INTERVAL = 1800      # 30 minutes between tip injections
ELO_INJECTION_THRESHOLD = 1350 # Only inject tips above this Elo
MAX_INJECTED_TIPS = 50         # Max tips in active injection pool
FLYWHEEL_LLM_EVERY = 50        # Use LLM judge every 50th eval (heuristic for rest)


class CortexDaemon:
    """Autonomous daemon for continuous tip improvement."""
    
    def __init__(self):
        self.db = CortexDB()
        self.flywheel = CortexFlywheel(self.db)
        self.running = False
        self.threads = []
        self.stats = {
            'cycles_completed': 0,
            'tips_injected': 0,
            'last_flywheel': None,
            'last_injection': None,
            'start_time': None
        }
        self._load_state()
    
    def _load_state(self):
        """Load daemon state from disk."""
        if STATE_FILE.exists():
            try:
                self.stats = json.loads(STATE_FILE.read_text())
            except Exception:
                pass
    
    def _save_state(self):
        """Save daemon state to disk."""
        try:
            STATE_FILE.write_text(json.dumps(self.stats, indent=2))
        except Exception:
            pass
    
    def _log(self, message: str):
        """Log to file and stdout."""
        timestamp = datetime.now().isoformat()
        line = f"[{timestamp}] {message}"
        print(line)
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(line + '\n')
        except Exception:
            pass
    
    def _flywheel_worker(self):
        """Background thread: run flywheel cycles."""
        while self.running:
            try:
                self._log("Starting flywheel cycle...")
                result = {
                    'eval': self.flywheel.run_eval_sweep(num_pairs=50, use_llm_every=FLYWHEEL_LLM_EVERY),
                    'repair': self.flywheel.run_repair_sweep(),
                    'consolidate': self.flywheel.run_consolidation_sweep()
                }
                
                self.stats['cycles_completed'] += 1
                self.stats['last_flywheel'] = datetime.now().isoformat()
                self._save_state()
                
                self._log(f"Flywheel complete: {result['eval']['pairs_evaluated']} pairs, "
                         f"{result['repair']['tips_repaired']} repaired, "
                         f"{result['consolidate']['tips_consolidated']} consolidated")
                
                # Sleep until next cycle
                for _ in range(FLYWHEEL_INTERVAL):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self._log(f"Flywheel error: {e}")
                time.sleep(300)  # 5 min cooldown on error
    
    def _injection_worker(self):
        """Background thread: inject high-Elo tips into agent."""
        while self.running:
            try:
                self._inject_top_tips()
                self.stats['last_injection'] = datetime.now().isoformat()
                self._save_state()
                
                for _ in range(INJECTION_INTERVAL):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self._log(f"Injection error: {e}")
                time.sleep(300)
    
    def _inject_top_tips(self):
        """Inject top-rated tips into agent context."""
        tips = self.db.get_tips_for_eval(min_elo=ELO_INJECTION_THRESHOLD, limit=MAX_INJECTED_TIPS)
        
        if not tips:
            self._log("No tips above injection threshold")
            return
        
        # Format tips for injection
        injection_text = "\n".join([
            f"• [{t['elo']:.0f}] {t['text']}" 
            for t in sorted(tips, key=lambda x: x['elo'], reverse=True)
        ])
        
        # Write to injection file that plugin reads
        injection_file = Path.home() / ".hermes" / "cortex_injection.txt"
        injection_file.write_text(injection_text)
        
        self.stats['tips_injected'] = len(tips)
        self._log(f"Injected {len(tips)} tips (Elo >= {ELO_INJECTION_THRESHOLD})")
    
    def _heartbeat_worker(self):
        """Background thread: health monitoring."""
        while self.running:
            try:
                # Check database connectivity
                stats = self.db.get_stats()
                
                # Check disk space
                import shutil
                disk = shutil.disk_usage(str(Path.home()))
                disk_pct = (disk.used / disk.total) * 100
                
                self._log(f"Heartbeat: {stats.get('total_tips', 0)} tips, "
                         f"avg Elo {stats.get('elo_avg', 0):.0f}, "
                         f"disk {disk_pct:.1f}%")
                
                if disk_pct > 90:
                    self._log("WARNING: Disk space critical!")
                
                for _ in range(HEARTBEAT_INTERVAL):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self._log(f"Heartbeat error: {e}")
                time.sleep(60)
    
    def start(self):
        """Start the daemon."""
        if PID_FILE.exists():
            try:
                old_pid = int(PID_FILE.read_text().strip())
                os.kill(old_pid, 0)  # Check if process exists
                print(f"Daemon already running (PID {old_pid})")
                return False
            except (OSError, ValueError):
                PID_FILE.unlink()  # Stale PID file
        
        self.running = True
        self.stats['start_time'] = datetime.now().isoformat()
        
        # Write PID file
        PID_FILE.write_text(str(os.getpid()))
        
        self._log("Cortex daemon starting...")
        
        # Start worker threads
        workers = [
            threading.Thread(target=self._flywheel_worker, name="flywheel"),
            threading.Thread(target=self._injection_worker, name="injection"),
            threading.Thread(target=self._heartbeat_worker, name="heartbeat"),
        ]
        
        for t in workers:
            t.daemon = True
            t.start()
            self.threads.append(t)
        
        self._log("Daemon started with 3 workers")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        
        return True
    
    def stop(self):
        """Stop the daemon."""
        self._log("Stopping daemon...")
        self.running = False
        
        for t in self.threads:
            t.join(timeout=5)
        
        if PID_FILE.exists():
            PID_FILE.unlink()
        
        self._log("Daemon stopped")
        return True
    
    def status(self) -> Dict:
        """Get daemon status."""
        is_running = False
        pid = None
        
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                os.kill(pid, 0)
                is_running = True
            except (OSError, ValueError):
                pass
        
        return {
            'running': is_running,
            'pid': pid,
            'stats': self.stats,
            'db_stats': self.db.get_stats() if is_running else None
        }
    
    def run_once(self):
        """Run one complete cycle and exit."""
        self._log("Running single flywheel cycle...")
        result = self.flywheel.run_eval_sweep(num_pairs=20, use_llm_every=FLYWHEEL_LLM_EVERY)
        self._inject_top_tips()
        
        print(json.dumps(result, indent=2))
        print(f"\nStats: {json.dumps(self.flywheel.get_stats(), indent=2)}")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cortex Daemon')
    parser.add_argument('command', choices=['start', 'stop', 'status', 'once'],
                       help='Command to run')
    
    args = parser.parse_args()
    
    daemon = CortexDaemon()
    
    if args.command == 'start':
        daemon.start()
    elif args.command == 'stop':
        daemon.stop()
    elif args.command == 'status':
        status = daemon.status()
        print(json.dumps(status, indent=2))
    elif args.command == 'once':
        daemon.run_once()


if __name__ == "__main__":
    main()
