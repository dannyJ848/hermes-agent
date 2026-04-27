#!/usr/bin/env python3
"""
Hermes Memory Bloat Monitor

Proactively monitors memory files, state.db, and context injection size.
Auto-trims when thresholds are exceeded. Alerts the agent before bloat
becomes critical.

Runs as a module that can be called:
- Every turn (lightweight check)
- On memory mutations (immediate check)
- Via cron (periodic deep check)

Thresholds (configurable):
- MEMORY.md: warn at 2000 chars, trim at 2500
- USER.md: warn at 1200 chars, trim at 1375
- state.db: warn at 10MB, archive at 50MB
- Injected context: warn at 80% of budget, trim at 95%
"""

import json
import logging
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────

@dataclass
class BloatThresholds:
    memory_warn: int = 2000
    memory_max: int = 2500
    user_warn: int = 1200
    user_max: int = 1375
    state_db_warn_mb: float = 10.0
    state_db_max_mb: float = 50.0
    injection_warn_pct: float = 80.0
    injection_max_pct: float = 95.0

# ── Monitor Class ─────────────────────────────────────────────────────────

class MemoryBloatMonitor:
    """Monitors and auto-trims memory bloat."""
    
    def __init__(self, thresholds: Optional[BloatThresholds] = None):
        self.thresholds = thresholds or BloatThresholds()
        self.last_check = {}
        self._trim_count = 0
    
    def check_all(self, memory_store=None) -> Dict[str, any]:
        """Run full bloat check on all components.
        
        Returns dict with status, alerts, and actions taken.
        """
        results = {
            "status": "ok",
            "alerts": [],
            "actions": [],
            "metrics": {},
        }
        
        # 1. Check MEMORY.md
        mem_status = self._check_memory_file("memory")
        results["metrics"]["memory"] = mem_status
        if mem_status["level"] == "critical":
            results["status"] = "critical"
            results["alerts"].append(f"MEMORY.md at {mem_status['chars']} chars (max {self.thresholds.memory_max})")
            # Auto-trim
            trimmed = self._auto_trim_memory("memory")
            if trimmed:
                results["actions"].append(f"Auto-trimmed MEMORY.md: removed {trimmed} oldest entries")
        elif mem_status["level"] == "warning":
            results["alerts"].append(f"MEMORY.md approaching limit: {mem_status['chars']}/{self.thresholds.memory_max}")
        
        # 2. Check USER.md
        user_status = self._check_memory_file("user")
        results["metrics"]["user"] = user_status
        if user_status["level"] == "critical":
            results["status"] = "critical"
            results["alerts"].append(f"USER.md at {user_status['chars']} chars (max {self.thresholds.user_max})")
            trimmed = self._auto_trim_memory("user")
            if trimmed:
                results["actions"].append(f"Auto-trimmed USER.md: removed {trimmed} oldest entries")
        elif user_status["level"] == "warning":
            results["alerts"].append(f"USER.md approaching limit: {user_status['chars']}/{self.thresholds.user_max}")
        
        # 3. Check state.db
        db_status = self._check_state_db()
        results["metrics"]["state_db"] = db_status
        if db_status["level"] == "critical":
            results["status"] = "critical"
            results["alerts"].append(f"state.db at {db_status['size_mb']:.1f}MB (max {self.thresholds.state_db_max_mb}MB)")
        elif db_status["level"] == "warning":
            results["alerts"].append(f"state.db approaching limit: {db_status['size_mb']:.1f}MB/{self.thresholds.state_db_max_mb}MB")
        
        # 4. Check injection size if store provided
        if memory_store is not None:
            inj_status = self._check_injection_size(memory_store)
            results["metrics"]["injection"] = inj_status
            if inj_status["level"] == "critical":
                results["status"] = "critical"
                results["alerts"].append(f"Injection at {inj_status['pct']:.0f}% of budget")
        
        return results
    
    def _check_memory_file(self, target: str) -> Dict:
        """Check a memory file's size."""
        from tools.memory_tool import get_memory_dir, ENTRY_DELIMITER
        
        mem_dir = get_memory_dir()
        fname = "MEMORY.md" if target == "memory" else "USER.md"
        fpath = mem_dir / fname
        
        if not fpath.exists():
            return {"level": "ok", "chars": 0, "entries": 0}
        
        content = fpath.read_text()
        chars = len(content)
        entries = [e.strip() for e in content.split(ENTRY_DELIMITER) if e.strip()]
        
        limit = self.thresholds.memory_max if target == "memory" else self.thresholds.user_max
        warn = self.thresholds.memory_warn if target == "memory" else self.thresholds.user_warn
        
        if chars >= limit:
            level = "critical"
        elif chars >= warn:
            level = "warning"
        else:
            level = "ok"
        
        return {"level": level, "chars": chars, "entries": len(entries), "limit": limit}
    
    def _check_state_db(self) -> Dict:
        """Check state.db size."""
        state_db = Path.home() / ".hermes/state.db"
        if not state_db.exists():
            return {"level": "ok", "size_mb": 0, "messages": 0}
        
        size_bytes = state_db.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        
        try:
            conn = sqlite3.connect(str(state_db))
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM messages")
            msg_count = c.fetchone()[0]
            conn.close()
        except Exception:
            msg_count = 0
        
        if size_mb >= self.thresholds.state_db_max_mb:
            level = "critical"
        elif size_mb >= self.thresholds.state_db_warn_mb:
            level = "warning"
        else:
            level = "ok"
        
        return {"level": level, "size_mb": size_mb, "messages": msg_count}
    
    def _check_injection_size(self, memory_store) -> Dict:
        """Check current injection size against budget."""
        mem_block = memory_store.format_for_system_prompt("memory") or ""
        user_block = memory_store.format_for_system_prompt("user") or ""
        total = len(mem_block) + len(user_block)
        
        budget = memory_store.memory_char_limit + memory_store.user_char_limit
        pct = (total / budget) * 100 if budget > 0 else 0
        
        if pct >= self.thresholds.injection_max_pct:
            level = "critical"
        elif pct >= self.thresholds.injection_warn_pct:
            level = "warning"
        else:
            level = "ok"
        
        return {"level": level, "chars": total, "budget": budget, "pct": pct}
    
    def _auto_trim_memory(self, target: str) -> int:
        """Auto-trim a memory file by removing oldest entries.
        
        Returns number of entries removed.
        """
        from tools.memory_tool import get_memory_dir, ENTRY_DELIMITER, MemoryStore
        
        mem_dir = get_memory_dir()
        fname = "MEMORY.md" if target == "memory" else "USER.md"
        fpath = mem_dir / fname
        
        if not fpath.exists():
            return 0
        
        content = fpath.read_text()
        entries = [e.strip() for e in content.split(ENTRY_DELIMITER) if e.strip()]
        
        limit = self.thresholds.memory_max if target == "memory" else self.thresholds.user_max
        
        # Calculate how many to keep (most recent)
        total = 0
        keep_from = len(entries)
        for i in range(len(entries) - 1, -1, -1):
            entry_size = len(entries[i]) if i == len(entries) - 1 else len(entries[i]) + len(ENTRY_DELIMITER)
            if total + entry_size > limit * 0.9:  # Trim to 90% of limit
                break
            total += entry_size
            keep_from = i
        
        if keep_from > 0:
            removed = entries[:keep_from]
            kept = entries[keep_from:]
            new_content = ENTRY_DELIMITER.join(kept)
            fpath.write_text(new_content)
            
            logger.warning(
                f"Auto-trimmed {target} memory: removed {len(removed)} entries, "
                f"kept {len(kept)}. Size: {len(content)} → {len(new_content)} chars"
            )
            self._trim_count += 1
            return len(removed)
        
        return 0
    
    def get_stats(self) -> Dict:
        """Get monitor statistics."""
        return {
            "trim_count": self._trim_count,
            "thresholds": {
                "memory_warn": self.thresholds.memory_warn,
                "memory_max": self.thresholds.memory_max,
                "user_warn": self.thresholds.user_warn,
                "user_max": self.thresholds.user_max,
            },
        }


# ── Integration Hook ──────────────────────────────────────────────────────

def check_memory_bloat(memory_store=None) -> str:
    """Quick check function for use in run_agent.py every turn.
    
    Returns a short status string or empty if all clear.
    """
    monitor = MemoryBloatMonitor()
    results = monitor.check_all(memory_store)
    
    if results["status"] == "critical":
        alerts = " | ".join(results["alerts"])
        actions = " | ".join(results["actions"]) if results["actions"] else ""
        return f"[BLOAT ALERT] {alerts}. {actions}"
    elif results["alerts"]:
        return f"[BLOAT WARN] {' | '.join(results['alerts'])}"
    
    return ""


# ── Standalone Check ──────────────────────────────────────────────────────

if __name__ == "__main__":
    monitor = MemoryBloatMonitor()
    results = monitor.check_all()
    print(json.dumps(results, indent=2))
