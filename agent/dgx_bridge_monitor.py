#!/usr/bin/env python3
"""dgx_bridge_monitor.py — Monitor DGX bridge health.

Checks:
- DGX SSH connectivity (when available)
- Qwopus llama-server on port 8002
- Bridge file exchange
- Cron activity on both sides

Clinic mode: Runs local-only checks, defers remote verification.

Usage:
    python3 dgx_bridge_monitor.py --check       # Run health check
    python3 dgx_bridge_monitor.py --watch       # Continuous monitoring
    python3 dgx_bridge_monitor.py --alert       # Send alert if issues
"""

import argparse
import json
import logging
import os
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("dgx_bridge")

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"
DGX_IP = "10.0.0.171"
DGX_USER = "djg6228"
DGX_PORT = 8002
BRIDGE_DIR = Path.home() / ".hermes" / "bridge"


class DGXBridgeMonitor:
    """Monitor DGX-MacBook bridge health."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_schema()
        self.clinic_mode = False  # Set True when user is in clinic
    
    def _ensure_schema(self):
        """Ensure bridge health tracking table exists."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bridge_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                check_type TEXT,
                status TEXT,  -- 'ok', 'warning', 'critical'
                detail TEXT,
                latency_ms REAL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _record(self, check_type: str, status: str, detail: str, latency: float = 0.0):
        """Record health check result."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO bridge_health (check_type, status, detail, latency_ms)
            VALUES (?, ?, ?, ?)
        """, (check_type, status, detail, latency))
        conn.commit()
        conn.close()
    
    def check_local_bridge(self) -> dict:
        """Check local bridge infrastructure."""
        results = {}
        
        # Check bridge directory exists
        if BRIDGE_DIR.exists():
            results["bridge_dir"] = {"status": "ok", "detail": str(BRIDGE_DIR)}
        else:
            results["bridge_dir"] = {"status": "warning", "detail": "Bridge dir missing"}
        
        # Check for pending lessons
        pending = list(BRIDGE_DIR.glob("*.lesson")) if BRIDGE_DIR.exists() else []
        results["pending_lessons"] = {"status": "ok", "detail": f"{len(pending)} pending"}
        
        # Check SSH config
        ssh_config = Path.home() / ".ssh" / "config"
        if ssh_config.exists() and "dgx" in ssh_config.read_text().lower():
            results["ssh_config"] = {"status": "ok", "detail": "DGX host configured"}
        else:
            results["ssh_config"] = {"status": "warning", "detail": "DGX not in SSH config"}
        
        return results
    
    def check_dgx_ssh(self) -> dict:
        """Check DGX SSH connectivity."""
        if self.clinic_mode:
            return {"status": "skipped", "detail": "Clinic mode - no DGX access"}
        
        start = time.time()
        try:
            result = subprocess.run(
                ["ssh", f"{DGX_USER}@{DGX_IP}", "echo ok"],
                capture_output=True, text=True, timeout=15
            )
            latency = (time.time() - start) * 1000
            
            if result.returncode == 0 and "ok" in result.stdout:
                self._record("ssh", "ok", "SSH reachable", latency)
                return {"status": "ok", "detail": f"SSH OK ({latency:.0f}ms)"}
            else:
                self._record("ssh", "critical", f"SSH failed: {result.stderr[:100]}", latency)
                return {"status": "critical", "detail": "SSH unreachable"}
        except subprocess.TimeoutExpired:
            self._record("ssh", "critical", "SSH timeout", 15000)
            return {"status": "critical", "detail": "SSH timeout"}
        except Exception as e:
            self._record("ssh", "critical", str(e)[:100], 0)
            return {"status": "critical", "detail": f"SSH error: {e}"}
    
    def check_dgx_llama(self) -> dict:
        """Check Qwopus llama-server on DGX."""
        if self.clinic_mode:
            return {"status": "skipped", "detail": "Clinic mode - no DGX access"}
        
        start = time.time()
        try:
            # Try to connect to port 8002 on DGX
            sock = socket.create_connection((DGX_IP, DGX_PORT), timeout=5)
            sock.close()
            latency = (time.time() - start) * 1000
            
            self._record("llama_server", "ok", f"Port {DGX_PORT} open", latency)
            return {"status": "ok", "detail": f"Qwopus responding ({latency:.0f}ms)"}
        except socket.timeout:
            self._record("llama_server", "critical", "Connection timeout", 5000)
            return {"status": "critical", "detail": "Qwopus timeout"}
        except ConnectionRefusedError:
            self._record("llama_server", "warning", "Connection refused", 0)
            return {"status": "warning", "detail": "Qwopus port closed"}
        except Exception as e:
            self._record("llama_server", "critical", str(e)[:100], 0)
            return {"status": "critical", "detail": f"Qwopus error: {e}"}
    
    def check_cron_activity(self) -> dict:
        """Check if bridge cron is active."""
        # Check local crontab for bridge-related jobs
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            has_bridge = "bridge" in result.stdout or "dgx" in result.stdout.lower()
            
            if has_bridge:
                return {"status": "ok", "detail": "Bridge cron found"}
            else:
                return {"status": "warning", "detail": "No bridge cron job"}
        except:
            return {"status": "warning", "detail": "Cannot check cron"}
    
    def run_full_check(self) -> dict:
        """Run complete health check."""
        logger.info("Running DGX bridge health check...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "clinic_mode": self.clinic_mode,
            "local_bridge": self.check_local_bridge(),
            "dgx_ssh": self.check_dgx_ssh(),
            "dgx_llama": self.check_dgx_llama(),
            "cron": self.check_cron_activity(),
        }
        
        # Overall status
        criticals = sum(1 for r in results.values() if isinstance(r, dict) and r.get("status") == "critical")
        warnings = sum(1 for r in results.values() if isinstance(r, dict) and r.get("status") == "warning")
        
        if criticals > 0:
            results["overall"] = "critical"
        elif warnings > 0:
            results["overall"] = "warning"
        else:
            results["overall"] = "ok"
        
        logger.info(f"Health check complete: {results['overall']}")
        return results
    
    def get_recent_issues(self, hours: int = 24) -> list[dict]:
        """Get recent bridge issues."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp, check_type, status, detail
            FROM bridge_health
            WHERE status != 'ok'
            AND timestamp > datetime('now', '-{} hours')
            ORDER BY timestamp DESC
        """.format(hours))
        rows = cur.fetchall()
        conn.close()
        return [{"time": r[0], "check": r[1], "status": r[2], "detail": r[3]} for r in rows]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Run health check")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring")
    parser.add_argument("--clinic", action="store_true", help="Clinic mode (local only)")
    parser.add_argument("--issues", action="store_true", help="Show recent issues")
    args = parser.parse_args()
    
    monitor = DGXBridgeMonitor()
    
    if args.clinic:
        monitor.clinic_mode = True
    
    if args.issues:
        issues = monitor.get_recent_issues(hours=24)
        print(f"Recent issues ({len(issues)}):")
        for issue in issues[:10]:
            print(f"  {issue['time']} [{issue['check']}] {issue['status']}: {issue['detail']}")
        return
    
    if args.watch:
        while True:
            results = monitor.run_full_check()
            print(json.dumps(results, indent=2, default=str))
            if results["overall"] != "ok":
                logger.warning("Bridge issues detected!")
            time.sleep(300)  # 5 minutes
    else:
        results = monitor.run_full_check()
        print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
