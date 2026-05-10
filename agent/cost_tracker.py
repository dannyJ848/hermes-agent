#!/usr/bin/env python3
"""
R94: Cost Tracker — track per-module and per-turn cost attribution.

Since modules inject tokens into every LLM call, track:
- Chars injected per module per turn
- Modules that inject most (budget consumers)
- Modules that never inject (candidates for removal)
- Injection efficiency (chars injected vs domain score improvement)

Runs as diagnostic, not injection.
"""
import os, json, threading
from typing import Dict, List
from collections import defaultdict

_INSTANCES: Dict[str, "CostTracker"] = {}
_LOCK = threading.Lock()

def get_instance(session_id: str = "default") -> "CostTracker":
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = CostTracker(session_id)
        return _INSTANCES[session_id]


class CostTracker:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._chars_by_module: Dict[str, int] = defaultdict(int)
        self._turns_by_module: Dict[str, int] = defaultdict(int)
        self._total_turns = 0

    def record_injection(self, module_name: str, chars: int):
        self._chars_by_module[module_name] += chars
        self._turns_by_module[module_name] += 1
        self._total_turns += 1

    def get_injection_report(self) -> Dict:
        total_chars = sum(self._chars_by_module.values())
        by_module = {}
        for mod, chars in sorted(self._chars_by_module.items(), key=lambda x: -x[1]):
            by_module[mod] = {"chars": chars, "turns": self._turns_by_module[mod],
                              "pct": round(chars / max(1, total_chars) * 100, 1)}
        return {"total_chars": total_chars, "total_turns": self._total_turns,
                "by_module": by_module}

    def build_injection(self, context: str = "") -> str:
        return ""  # Diagnostic module

    def get_status(self) -> Dict:
        return {"session": self.session_id, "total_turns": self._total_turns}


if __name__ == "__main__":
    ct = CostTracker("test")
    print("Cost Tracker — OK")
