"""Multi-Agent Blackboard — Collaborative worker coordination for Hermes Agent.

Extracted and refined from llm_orchestrator.py v4.
Provides thread-safe shared state, worker messaging, artifact tracking,
and tool result caching for multi-agent workflows.

Usage:
    from agent.multi_agent_blackboard import get_blackboard, ToolCache
    bb = get_blackboard()
    bb.post_message("worker1", "worker2", "Found the bug in line 42")
    bb.register_artifact("worker1", "/tmp/fix.py", "Patch for null pointer")
"""
import json, hashlib, threading, time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

# ── Tool Result Cache ─────────────────────────────────────────────────
class ToolCache:
    """Thread-safe cache for tool results to avoid redundant calls."""
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.cache: Dict[str, tuple] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def _key(self, tool_name: str, args: dict) -> str:
        return hashlib.sha256(
            f"{tool_name}:{json.dumps(args, sort_keys=True)}".encode()
        ).hexdigest()[:16]

    def get(self, tool_name: str, args: dict) -> Optional[Any]:
        with self.lock:
            k = self._key(tool_name, args)
            if k in self.cache:
                result, ts = self.cache[k]
                if time.time() - ts < self.ttl:
                    self.hits += 1
                    return result
                del self.cache[k]
            self.misses += 1
            return None

    def put(self, tool_name: str, args: dict, result: Any):
        with self.lock:
            k = self._key(tool_name, args)
            self.cache[k] = (result, time.time())
            if len(self.cache) > self.max_size:
                oldest = min(self.cache.items(), key=lambda x: x[1][1])
                del self.cache[oldest[0]]

    def stats(self) -> dict:
        with self.lock:
            total = self.hits + self.misses
            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(self.hits / total, 3) if total > 0 else 0,
                "entries": len(self.cache),
            }

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

# ── Rate Limiter ──────────────────────────────────────────────────────
class RateLimiter:
    """Thread-safe rate limiter for API calls."""
    def __init__(self, calls_per_min: int = 60):
        self.calls_per_min = calls_per_min
        self.timestamps: List[float] = []
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            now = time.time()
            self.timestamps = [t for t in self.timestamps if now - t < 60]
            if len(self.timestamps) >= self.calls_per_min:
                sleep_time = 60 - (now - self.timestamps[0]) + 0.1
                if sleep_time > 0:
                    time.sleep(sleep_time)
            self.timestamps.append(time.time())

# ── Blackboard ────────────────────────────────────────────────────────
class Blackboard:
    """Thread-safe shared state for multi-agent collaboration.

    Workers post messages, register artifacts, share findings, and
    report status/blockers. The coordinator (or any worker) can read
    the full state for replanning.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.messages: List[dict] = []
        self.artifacts: Dict[str, dict] = {}
        self.findings: List[dict] = []
        self.status: Dict[str, dict] = {}
        self.blockers: List[dict] = []
        self.plan_updates: List[dict] = []
        self.tool_results_shared: Dict[str, dict] = {}
        self._message_counter = 0

    def post_message(self, from_worker: str, to_worker: str, message: str,
                     msg_type: str = "info") -> int:
        """Post a message to another worker or 'all'. Returns msg id."""
        with self.lock:
            self._message_counter += 1
            entry = {
                "id": self._message_counter,
                "from": from_worker,
                "to": to_worker,
                "message": message,
                "type": msg_type,
                "time": datetime.now().isoformat(),
            }
            self.messages.append(entry)
            return self._message_counter

    def get_messages(self, worker_name: str, since_id: int = 0,
                     msg_type: Optional[str] = None) -> List[dict]:
        """Get messages for a worker since a given message id."""
        with self.lock:
            msgs = [m for m in self.messages if m["id"] > since_id
                    and (m["to"] == worker_name or m["to"] == "all")]
            if msg_type:
                msgs = [m for m in msgs if m["type"] == msg_type]
            return msgs

    def register_artifact(self, worker: str, path: str, description: str = ""):
        with self.lock:
            self.artifacts[path] = {
                "worker": worker,
                "description": description,
                "time": datetime.now().isoformat(),
            }

    def add_finding(self, worker: str, finding: str, priority: str = "normal"):
        with self.lock:
            self.findings.append({
                "worker": worker,
                "finding": finding,
                "priority": priority,
                "time": datetime.now().isoformat(),
            })

    def set_status(self, worker: str, status: str, detail: str = ""):
        with self.lock:
            self.status[worker] = {
                "status": status,
                "detail": detail,
                "time": datetime.now().isoformat(),
            }

    def add_blocker(self, worker: str, blocker: str, severity: str = "medium"):
        with self.lock:
            self.blockers.append({
                "worker": worker,
                "blocker": blocker,
                "severity": severity,
                "time": datetime.now().isoformat(),
            })

    def add_plan_update(self, instruction: str, source: str = "coordinator"):
        with self.lock:
            self.plan_updates.append({
                "instruction": instruction,
                "source": source,
                "time": datetime.now().isoformat(),
            })

    def share_tool_result(self, worker: str, tool_name: str, args: dict, result: Any):
        with self.lock:
            args_hash = hashlib.sha256(
                json.dumps(args, sort_keys=True).encode()
            ).hexdigest()[:16]
            key = f"{tool_name}:{args_hash}"
            self.tool_results_shared[key] = {
                "worker": worker,
                "result": result,
                "time": datetime.now().isoformat(),
            }

    def get_shared_tool_result(self, tool_name: str, args: dict) -> Optional[Any]:
        with self.lock:
            args_hash = hashlib.sha256(
                json.dumps(args, sort_keys=True).encode()
            ).hexdigest()[:16]
            key = f"{tool_name}:{args_hash}"
            if key in self.tool_results_shared:
                return self.tool_results_shared[key]["result"]
            return None

    def get_state_summary(self) -> dict:
        with self.lock:
            return {
                "messages_count": len(self.messages),
                "artifacts_count": len(self.artifacts),
                "findings_count": len(self.findings),
                "worker_status": dict(self.status),
                "blockers_count": len(self.blockers),
                "plan_updates_count": len(self.plan_updates),
            }

    def get_context_for_worker(self, worker_name: str) -> dict:
        """Get relevant context for a specific worker."""
        with self.lock:
            msgs = [m for m in self.messages
                    if m["to"] == worker_name or m["to"] == "all"]
            recent_msgs = msgs[-10:]
            artifacts_summary = "\n".join(
                f"  {p}: {a['description']} (by {a['worker']})"
                for p, a in list(self.artifacts.items())[-10:]
            )
            findings_text = "\n".join(
                f"  [{f['worker']}] {f['finding']}"
                for f in self.findings[-10:]
            )
            blockers_text = "\n".join(
                f"  [{b['worker']}] {b['blocker']}"
                for b in self.blockers[-5:]
            )
            plan_text = "\n".join(
                f"  {p['instruction']}"
                for p in self.plan_updates[-5:]
            )
            return {
                "messages": recent_msgs,
                "artifacts": artifacts_summary,
                "findings": findings_text,
                "blockers": blockers_text,
                "plan_updates": plan_text,
                "worker_status": dict(self.status),
            }

    def clear(self):
        with self.lock:
            self.messages.clear()
            self.artifacts.clear()
            self.findings.clear()
            self.status.clear()
            self.blockers.clear()
            self.plan_updates.clear()
            self.tool_results_shared.clear()
            self._message_counter = 0

# ── Global instances ──────────────────────────────────────────────────
_blackboard = None
_tool_cache = None

def get_blackboard() -> Blackboard:
    global _blackboard
    if _blackboard is None:
        _blackboard = Blackboard()
    return _blackboard

def get_tool_cache() -> ToolCache:
    global _tool_cache
    if _tool_cache is None:
        _tool_cache = ToolCache()
    return _tool_cache

def reset_blackboard():
    global _blackboard
    _blackboard = Blackboard()

def reset_tool_cache():
    global _tool_cache
    _tool_cache = ToolCache()
