#!/usr/bin/env python3
"""
cortex_sentinel.py — Continuous Diagnostic Apparatus for the Cortex Unified DB.

A real-time monitoring daemon that watches every trace of the apparatus
and immediately notifies if something is amiss.

Architecture:
  - Health Checks (every 60s): PG connectivity, embedding server, process liveness
  - DB Metrics (every 5min): dead tuples, cache hit ratio, node counts, lock waits
  - System Metrics (every 60s): disk, memory, CPU
  - Anomaly Detection: threshold-based with configurable alert levels
  - Notification: log file + Telegram (for critical alerts)
  - State persistence: JSON state file for external consumption

Usage:
  python3 cortex_sentinel.py [--config path] [--once] [--verbose]

  --once    Run a single check cycle and exit (for testing)
  --verbose Print all metrics to stdout
  --config  Path to config YAML (default: ~/.hermes/.hermes_sentinel.yaml)
"""

import os
import sys
import time
import json
import logging
import signal
import argparse
import subprocess
import traceback
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Tuple
from collections import deque

# ── Configuration ──────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "check_interval_sec": 60,
    "metrics_interval_sec": 300,       # 5 min for deep metrics
    "state_file": "~/.hermes/sentinel_state.json",
    "log_file": "/tmp/cortex_sentinel.log",
    "history_size": 1440,              # Keep 24h of 1-min samples
    # Thresholds
    "thresholds": {
        "pg_latency_ms": 500,
        "dead_tuples": 10000,
        "cache_hit_ratio_pct": 95,
        "embedding_coverage_pct": 95,
        "disk_free_pct": 10,
        "memory_free_pct": 5,
        "cpu_load_pct": 90,
        "active_nodes_min": 10000,
        "lock_wait_count": 5,
        "embedding_server_latency_ms": 2000,
    },
    # Processes to monitor
    "watched_processes": [
        # {"name": "cortex_daemon", "pattern": "cortex_daemon.py"},  # DISABLED Apr 16
        {"name": "embedding_server", "port": 8083},
    ],
    # Notification settings
    "notify_log": True,
    "notify_telegram": False,  # Set True to enable Telegram alerts
    "alert_cooldown_sec": 300, # Don't repeat same alert for 5 min
}

# ── Data Classes ───────────────────────────────────────────────────────────────

@dataclass
class HealthCheck:
    name: str
    status: str = "unknown"  # ok, warn, crit, unknown
    message: str = ""
    value: Any = None
    timestamp: str = ""

@dataclass
class CheckResult:
    checks: List[HealthCheck] = field(default_factory=list)
    overall: str = "unknown"
    alert_count: int = 0
    timestamp: str = ""
    
    @property
    def critical_count(self):
        return sum(1 for c in self.checks if c.status == "crit")
    
    @property
    def warning_count(self):
        return sum(1 for c in self.checks if c.status == "warn")

@dataclass 
class MetricSample:
    timestamp: float
    pg_latency_ms: float = 0
    dead_tuples: int = 0
    cache_hit_ratio: float = 100
    active_nodes: int = 0
    embedding_coverage: float = 100
    disk_free_pct: float = 100
    memory_free_pct: float = 100
    cpu_load_1m: float = 0
    lock_waits: int = 0
    connection_count: int = 0

# ── Sentinel Core ──────────────────────────────────────────────────────────────

class CortexSentinel:
    """Continuous diagnostic apparatus for the Cortex system."""
    
    def __init__(self, config: Dict = None):
        self.config = config or DEFAULT_CONFIG.copy()
        self.thresholds = self.config.get("thresholds", DEFAULT_CONFIG["thresholds"])
        self.history: deque = deque(maxlen=self.config.get("history_size", 1440))
        self.alert_history: Dict[str, float] = {}  # alert_key -> last_alert_time
        self.running = False
        self._pg_conn = None
        self._last_deep_metrics = 0
        self._cycle_count = 0
        
        # Setup logging
        self.logger = logging.getLogger("cortex_sentinel")
        self.logger.setLevel(logging.DEBUG)
        
        log_file = self.config.get("log_file", "/tmp/cortex_sentinel.log")
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(fh)
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
        self.logger.addHandler(ch)
    
    # ── PG Connection ──────────────────────────────────────────────────────
    
    def _get_pg(self):
        """Get or create PG connection."""
        if self._pg_conn is not None:
            try:
                cur = self._pg_conn.cursor()
                cur.execute("SELECT 1")
                cur.close()
                return self._pg_conn
            except Exception:
                try: self._pg_conn.close()
                except: pass
                self._pg_conn = None
        
        dsn = os.environ.get('CORTEX_DSN', 
            'postgresql://hindsight:hindsight@localhost:5432/cortex')
        try:
            import psycopg2
            self._pg_conn = psycopg2.connect(dsn)
            self._pg_conn.autocommit = True
            return self._pg_conn
        except Exception as e:
            self.logger.error(f"PG connection failed: {e}")
            return None
    
    # ── Individual Checks ──────────────────────────────────────────────────
    
    def check_pg_connectivity(self) -> HealthCheck:
        """Check PostgreSQL is reachable and responsive."""
        hc = HealthCheck(name="pg_connectivity", timestamp=self._now())
        conn = self._get_pg()
        if conn is None:
            hc.status = "crit"
            hc.message = "Cannot connect to PostgreSQL"
            return hc
        
        t0 = time.time()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            latency = (time.time() - t0) * 1000
            hc.value = round(latency, 1)
            if latency > self.thresholds["pg_latency_ms"]:
                hc.status = "warn"
                hc.message = f"PG latency {latency:.0f}ms > {self.thresholds['pg_latency_ms']}ms"
            else:
                hc.status = "ok"
                hc.message = f"PG responsive ({latency:.0f}ms)"
        except Exception as e:
            hc.status = "crit"
            hc.message = f"PG query failed: {e}"
            self._pg_conn = None
        return hc
    
    def check_pg_dead_tuples(self) -> HealthCheck:
        """Check dead tuple accumulation."""
        hc = HealthCheck(name="pg_dead_tuples", timestamp=self._now())
        conn = self._get_pg()
        if conn is None:
            hc.status = "unknown"
            hc.message = "No PG connection"
            return hc
        
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT COALESCE(SUM(n_dead_tup), 0) 
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public'
            """)
            dead = int(cur.fetchone()[0])
            cur.close()
            hc.value = dead
            if dead > self.thresholds["dead_tuples"]:
                hc.status = "warn"
                hc.message = f"Dead tuples {dead} > {self.thresholds['dead_tuples']}"
            else:
                hc.status = "ok"
                hc.message = f"Dead tuples: {dead}"
        except Exception as e:
            hc.status = "unknown"
            hc.message = f"Query failed: {e}"
        return hc
    
    def check_pg_cache_hit_ratio(self) -> HealthCheck:
        """Check buffer cache hit ratio."""
        hc = HealthCheck(name="pg_cache_hit", timestamp=self._now())
        conn = self._get_pg()
        if conn is None:
            hc.status = "unknown"
            hc.message = "No PG connection"
            return hc
        
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT COALESCE(
                    SUM(heap_blks_hit)::float / NULLIF(SUM(heap_blks_hit) + SUM(heap_blks_read), 0) * 100,
                    100
                ) FROM pg_statio_user_tables
            """)
            ratio = float(cur.fetchone()[0])
            cur.close()
            hc.value = round(ratio, 2)
            if ratio < self.thresholds["cache_hit_ratio_pct"]:
                hc.status = "warn"
                hc.message = f"Cache hit ratio {ratio:.1f}% < {self.thresholds['cache_hit_ratio_pct']}%"
            else:
                hc.status = "ok"
                hc.message = f"Cache hit ratio: {ratio:.1f}%"
        except Exception as e:
            hc.status = "unknown"
            hc.message = f"Query failed: {e}"
        return hc
    
    def check_active_nodes(self) -> HealthCheck:
        """Check active node count hasn't dropped unexpectedly."""
        hc = HealthCheck(name="active_nodes", timestamp=self._now())
        conn = self._get_pg()
        if conn is None:
            hc.status = "unknown"
            hc.message = "No PG connection"
            return hc
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM cortex_nodes WHERE is_active = true")
            count = int(cur.fetchone()[0])
            cur.close()
            hc.value = count
            if count < self.thresholds["active_nodes_min"]:
                hc.status = "crit"
                hc.message = f"Active nodes {count} < {self.thresholds['active_nodes_min']} (data loss?)"
            else:
                hc.status = "ok"
                hc.message = f"Active nodes: {count:,}"
        except Exception as e:
            hc.status = "unknown"
            hc.message = f"Query failed: {e}"
        return hc
    
    def check_embedding_coverage(self) -> HealthCheck:
        """Check embedding coverage percentage."""
        hc = HealthCheck(name="embedding_coverage", timestamp=self._now())
        conn = self._get_pg()
        if conn is None:
            hc.status = "unknown"
            hc.message = "No PG connection"
            return hc
        
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*), COUNT(embedding) 
                FROM cortex_nodes WHERE is_active = true
            """)
            row = cur.fetchone()
            total, with_emb = int(row[0]), int(row[1])
            pct = (with_emb / total * 100) if total > 0 else 0
            cur.close()
            hc.value = round(pct, 1)
            if pct < self.thresholds["embedding_coverage_pct"]:
                hc.status = "warn"
                hc.message = f"Embedding coverage {pct:.1f}% < {self.thresholds['embedding_coverage_pct']}%"
            else:
                hc.status = "ok"
                hc.message = f"Embedding coverage: {pct:.1f}% ({with_emb:,}/{total:,})"
        except Exception as e:
            hc.status = "unknown"
            hc.message = f"Query failed: {e}"
        return hc
    
    def check_embedding_server(self) -> HealthCheck:
        """Check embedding server at port 8083."""
        hc = HealthCheck(name="embedding_server", timestamp=self._now())
        try:
            import urllib.request
            t0 = time.time()
            req = urllib.request.Request(
                'http://127.0.0.1:8083/v1/models',
                headers={'Accept': 'application/json'}
            )
            resp = urllib.request.urlopen(req, timeout=5)
            latency = (time.time() - t0) * 1000
            data = json.loads(resp.read())
            hc.value = round(latency, 1)
            if latency > self.thresholds["embedding_server_latency_ms"]:
                hc.status = "warn"
                hc.message = f"Embedding server slow ({latency:.0f}ms)"
            else:
                hc.status = "ok"
                hc.message = f"Embedding server OK ({latency:.0f}ms)"
        except Exception as e:
            hc.status = "crit"
            hc.message = f"Embedding server unreachable: {e}"
        return hc
    
    def check_pg_locks(self) -> HealthCheck:
        """Check for lock contention."""
        hc = HealthCheck(name="pg_locks", timestamp=self._now())
        conn = self._get_pg()
        if conn is None:
            hc.status = "unknown"
            return hc
        
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM pg_locks l
                JOIN pg_stat_activity a ON l.pid = a.pid
                WHERE NOT l.granted AND a.datname = 'cortex'
            """)
            waiting = int(cur.fetchone()[0])
            cur.close()
            hc.value = waiting
            if waiting > self.thresholds["lock_wait_count"]:
                hc.status = "warn"
                hc.message = f"{waiting} lock waits > {self.thresholds['lock_wait_count']}"
            else:
                hc.status = "ok"
                hc.message = f"Lock waits: {waiting}"
        except Exception as e:
            hc.status = "unknown"
            hc.message = f"Query failed: {e}"
        return hc
    
    def check_disk_space(self) -> HealthCheck:
        """Check disk space on data volume."""
        hc = HealthCheck(name="disk_space", timestamp=self._now())
        try:
            stat = os.statvfs(os.path.expanduser("~"))
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            pct = (free / total * 100) if total > 0 else 0
            hc.value = round(pct, 1)
            if pct < self.thresholds["disk_free_pct"]:
                hc.status = "crit"
                hc.message = f"Disk free {pct:.1f}% < {self.thresholds['disk_free_pct']}%"
            else:
                hc.status = "ok"
                hc.message = f"Disk free: {pct:.1f}% ({free // (1024**3)}GB/{total // (1024**3)}GB)"
        except Exception as e:
            hc.status = "unknown"
            hc.message = f"Stat failed: {e}"
        return hc
    
    def check_memory(self) -> HealthCheck:
        """Check available memory (macOS-aware: free + inactive = available)."""
        hc = HealthCheck(name="memory", timestamp=self._now())
        try:
            # macOS: use vm_stat — free + inactive = truly available
            result = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                page_size = 4096
                free_pages = 0
                inactive_pages = 0
                active_pages = 0
                wired_pages = 0
                for line in lines:
                    val = line.split(':')[1].strip().rstrip('.') if ':' in line else '0'
                    if 'Pages free' in line:
                        free_pages = int(val)
                    elif 'Pages inactive' in line:
                        inactive_pages = int(val)
                    elif 'Pages active' in line:
                        active_pages = int(val)
                    elif 'Pages wired down' in line:
                        wired_pages = int(val)
                
                # On macOS, "inactive" pages are available for immediate use
                available_gb = (free_pages + inactive_pages) * page_size / (1024**3)
                total_gb = (free_pages + inactive_pages + active_pages + wired_pages) * page_size / (1024**3)
                pct = (available_gb / total_gb * 100) if total_gb > 0 else 0
                hc.value = round(pct, 1)
                if pct < self.thresholds["memory_free_pct"]:
                    hc.status = "warn"
                    hc.message = f"Memory available {pct:.1f}% ({available_gb:.1f}GB/{total_gb:.1f}GB)"
                else:
                    hc.status = "ok"
                    hc.message = f"Memory available: {pct:.1f}% ({available_gb:.1f}GB/{total_gb:.1f}GB)"
            else:
                hc.status = "unknown"
                hc.message = "vm_stat unavailable"
        except Exception as e:
            hc.status = "unknown"
            hc.message = f"Check failed: {e}"
        return hc
    
    def check_cpu_load(self) -> HealthCheck:
        """Check system load average."""
        hc = HealthCheck(name="cpu_load", timestamp=self._now())
        try:
            load1, load5, load15 = os.getloadavg()
            hc.value = round(load1, 2)
            # On macOS, 100% = 1.0 per core. Use cpu_count for threshold.
            cpu_count = os.cpu_count() or 1
            load_pct = (load1 / cpu_count) * 100
            if load_pct > self.thresholds["cpu_load_pct"]:
                hc.status = "warn"
                hc.message = f"CPU load {load_pct:.0f}% (1m avg: {load1:.2f})"
            else:
                hc.status = "ok"
                hc.message = f"CPU load: {load_pct:.0f}% (1m: {load1:.2f}, 5m: {load5:.2f})"
        except Exception as e:
            hc.status = "unknown"
            hc.message = f"Check failed: {e}"
        return hc
    
    def check_watched_processes(self) -> List[HealthCheck]:
        """Check that watched processes are alive."""
        checks = []
        for proc_cfg in self.config.get("watched_processes", []):
            hc = HealthCheck(name=f"process_{proc_cfg['name']}", timestamp=self._now())
            
            if "port" in proc_cfg:
                # Check by port
                try:
                    import urllib.request
                    urllib.request.urlopen(f"http://127.0.0.1:{proc_cfg['port']}/v1/models", timeout=3)
                    hc.status = "ok"
                    hc.message = f"{proc_cfg['name']} alive (port {proc_cfg['port']})"
                except:
                    hc.status = "warn"
                    hc.message = f"{proc_cfg['name']} not responding on port {proc_cfg['port']}"
            elif "pattern" in proc_cfg:
                # Check by process name
                try:
                    result = subprocess.run(
                        ['pgrep', '-f', proc_cfg['pattern']],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        pids = result.stdout.strip().split('\n')
                        hc.status = "ok"
                        hc.message = f"{proc_cfg['name']} alive (PID {','.join(pids)})"
                    else:
                        hc.status = "warn"
                        hc.message = f"{proc_cfg['name']} NOT running"
                except Exception as e:
                    hc.status = "unknown"
                    hc.message = f"Check failed: {e}"
            
            checks.append(hc)
        return checks
    
    def check_pg_connections(self) -> HealthCheck:
        """Check PG connection count."""
        hc = HealthCheck(name="pg_connections", timestamp=self._now())
        conn = self._get_pg()
        if conn is None:
            hc.status = "unknown"
            return hc
        
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE datname = 'cortex' AND state != 'idle'
            """)
            active = int(cur.fetchone()[0])
            
            cur.execute("SELECT setting::int FROM pg_settings WHERE name = 'max_connections'")
            max_conn = int(cur.fetchone()[0])
            cur.close()
            
            pct = (active / max_conn * 100) if max_conn > 0 else 0
            hc.value = active
            if pct > 80:
                hc.status = "warn"
                hc.message = f"PG connections {active}/{max_conn} ({pct:.0f}%)"
            else:
                hc.status = "ok"
                hc.message = f"PG connections: {active}/{max_conn} ({pct:.0f}%)"
        except Exception as e:
            hc.status = "unknown"
            hc.message = f"Query failed: {e}"
        return hc
    
    def check_pg_replication_lag(self) -> HealthCheck:
        """Check if PG is in recovery / replication lag (not applicable for single-node, but future-proof)."""
        hc = HealthCheck(name="pg_replication", timestamp=self._now())
        conn = self._get_pg()
        if conn is None:
            hc.status = "unknown"
            return hc
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT pg_is_in_recovery()")
            in_recovery = cur.fetchone()[0]
            cur.close()
            hc.value = in_recovery
            if in_recovery:
                hc.status = "warn"
                hc.message = "PG is in recovery mode (replica)"
            else:
                hc.status = "ok"
                hc.message = "PG primary mode"
        except Exception as e:
            hc.status = "unknown"
            hc.message = f"Query failed: {e}"
        return hc
    
    # ── Check Cycle ────────────────────────────────────────────────────────
    
    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
    
    def run_cycle(self, deep: bool = False) -> CheckResult:
        """Run one full check cycle."""
        result = CheckResult(timestamp=self._now())
        self._cycle_count += 1
        
        # Always-run checks (lightweight)
        checks = [
            self.check_pg_connectivity(),
            self.check_embedding_server(),
            self.check_disk_space(),
            self.check_memory(),
            self.check_cpu_load(),
            self.check_active_nodes(),
        ]
        
        # Deep metrics (every 5 min or on demand)
        if deep or (time.time() - self._last_deep_metrics > self.config.get("metrics_interval_sec", 300)):
            checks.extend([
                self.check_pg_dead_tuples(),
                self.check_pg_cache_hit_ratio(),
                self.check_embedding_coverage(),
                self.check_pg_locks(),
                self.check_pg_connections(),
                self.check_pg_replication_lag(),
            ])
            self._last_deep_metrics = time.time()
        
        # Process checks
        checks.extend(self.check_watched_processes())
        
        result.checks = checks
        
        # Determine overall status
        statuses = [c.status for c in checks]
        if "crit" in statuses:
            result.overall = "crit"
        elif "warn" in statuses:
            result.overall = "warn"
        else:
            result.overall = "ok"
        
        result.alert_count = result.critical_count + result.warning_count
        
        # Record metric sample
        self._record_sample(result)
        
        return result
    
    def _record_sample(self, result: CheckResult):
        """Record a metric sample from check results."""
        sample = MetricSample(timestamp=time.time())
        for c in result.checks:
            if c.name == "pg_connectivity" and c.value:
                sample.pg_latency_ms = c.value
            elif c.name == "pg_dead_tuples":
                sample.dead_tuples = c.value or 0
            elif c.name == "pg_cache_hit":
                sample.cache_hit_ratio = c.value or 100
            elif c.name == "active_nodes":
                sample.active_nodes = c.value or 0
            elif c.name == "embedding_coverage":
                sample.embedding_coverage = c.value or 100
            elif c.name == "disk_space":
                sample.disk_free_pct = c.value or 100
            elif c.name == "memory":
                sample.memory_free_pct = c.value or 100
            elif c.name == "cpu_load":
                sample.cpu_load_1m = c.value or 0
            elif c.name == "pg_locks":
                sample.lock_waits = c.value or 0
            elif c.name == "pg_connections":
                sample.connection_count = c.value or 0
        self.history.append(sample)
    
    # ── Alerting ───────────────────────────────────────────────────────────
    
    def _should_alert(self, key: str) -> bool:
        """Check if enough time has passed since last alert for this key."""
        cooldown = self.config.get("alert_cooldown_sec", 300)
        last = self.alert_history.get(key, 0)
        if time.time() - last > cooldown:
            self.alert_history[key] = time.time()
            return True
        return False
    
    def format_report(self, result: CheckResult) -> str:
        """Format a check result as a human-readable report."""
        lines = [
            f"=== Cortex Sentinel Report [{result.timestamp}] ===",
            f"Overall: {result.overall.upper()} ({result.alert_count} alerts)",
            ""
        ]
        for c in result.checks:
            icon = {"ok": "✓", "warn": "⚠", "crit": "✗", "unknown": "?"}.get(c.status, "?")
            lines.append(f"  {icon} {c.name}: {c.message}")
        return "\n".join(lines)
    
    def save_state(self):
        """Save current state to JSON file."""
        state_path = os.path.expanduser(self.config.get("state_file", "~/.hermes/sentinel_state.json"))
        state = {
            "last_check": self._now(),
            "cycle_count": self._cycle_count,
            "overall": "running",
            "history_size": len(self.history),
            "recent_samples": [
                {k: v for k, v in asdict(s).items() if k != 'timestamp'}
                for s in list(self.history)[-10:]
            ],
            "last_timestamps": [s.timestamp for s in list(self.history)[-10:]],
        }
        try:
            with open(state_path, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    def load_state(self) -> Optional[Dict]:
        """Load previous state."""
        state_path = os.path.expanduser(self.config.get("state_file", "~/.hermes/sentinel_state.json"))
        try:
            if os.path.exists(state_path):
                with open(state_path) as f:
                    return json.load(f)
        except:
            pass
        return None
    
    # ── Main Loop ──────────────────────────────────────────────────────────
    
    def run(self, once: bool = False, verbose: bool = False):
        """Main monitoring loop."""
        self.logger.info("Cortex Sentinel starting...")
        
        # Load previous state
        prev = self.load_state()
        if prev:
            self._cycle_count = prev.get("cycle_count", 0)
            self.logger.info(f"Resumed from cycle {self._cycle_count}")
        
        self.running = True
        
        def handle_signal(signum, frame):
            self.logger.info(f"Signal {signum} received, shutting down...")
            self.running = False
        
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)
        
        while self.running:
            try:
                is_deep = (self._cycle_count % 5 == 0)  # Deep every 5th cycle
                result = self.run_cycle(deep=is_deep)
                
                # Log report
                if result.overall != "ok" or verbose:
                    report = self.format_report(result)
                    self.logger.info(report)
                
                # Alert on critical/warning
                for c in result.checks:
                    if c.status in ("crit", "warn"):
                        alert_key = f"{c.name}:{c.status}"
                        if self._should_alert(alert_key):
                            level = logging.CRITICAL if c.status == "crit" else logging.WARNING
                            self.logger.log(level, f"ALERT: {c.name} — {c.message}")
                
                # Save state
                self.save_state()
                
                if once:
                    break
                
                interval = self.config.get("check_interval_sec", 60)
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Cycle error: {e}\n{traceback.format_exc()}")
                if once:
                    raise
                time.sleep(10)
        
        self.logger.info(f"Cortex Sentinel stopped after {self._cycle_count} cycles")
        
        # Save final state
        self.save_state()
    
    def get_status(self) -> Dict:
        """Get current status summary (for external consumption)."""
        result = self.run_cycle(deep=True)
        report = self.format_report(result)
        
        # Build summary
        checks_dict = {}
        for c in result.checks:
            checks_dict[c.name] = {
                "status": c.status,
                "message": c.message,
                "value": c.value,
            }
        
        # Trend from history
        trend = {}
        if len(self.history) >= 2:
            recent = list(self.history)[-5:]
            oldest = recent[0]
            newest = recent[-1]
            trend = {
                "pg_latency_delta_ms": round(newest.pg_latency_ms - oldest.pg_latency_ms, 1),
                "dead_tuples_delta": newest.dead_tuples - oldest.dead_tuples,
                "nodes_delta": newest.active_nodes - oldest.active_nodes,
            }
        
        return {
            "overall": result.overall,
            "checks": checks_dict,
            "trend": trend,
            "cycle": self._cycle_count,
            "history_size": len(self.history),
            "report": report,
        }


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cortex Sentinel — Continuous Diagnostic Apparatus")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print all metrics")
    parser.add_argument("--status", action="store_true", help="Print status JSON and exit")
    parser.add_argument("--config", default=None, help="Config file path")
    args = parser.parse_args()
    
    # Load config
    config = DEFAULT_CONFIG.copy()
    if args.config:
        try:
            import yaml
            with open(args.config) as f:
                user_cfg = yaml.safe_load(f)
                if user_cfg:
                    config.update(user_cfg)
        except ImportError:
            print("Warning: PyYAML not installed, using defaults")
        except Exception as e:
            print(f"Warning: Config load failed: {e}")
    
    # Load env vars
    env_file = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_file):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            # Manual .env loading
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, val = line.split('=', 1)
                        os.environ.setdefault(key.strip(), val.strip())
    
    sentinel = CortexSentinel(config=config)
    
    if args.status:
        status = sentinel.get_status()
        print(json.dumps(status, indent=2, default=str))
        return
    
    sentinel.run(once=args.once, verbose=args.verbose)


if __name__ == "__main__":
    main()
