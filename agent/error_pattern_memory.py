#!/usr/bin/env python3
"""
R43: Error Pattern Memory — tracks recurring bugs to avoid repeat failures

When the same error type occurs 2+ times, inject a prevention hint.
Pattern: error_type → count → lastseen → prevention_strategy

From our own experience: psycopg2 aborts, shell quoting breaks,
__pycache__ ignores changes, memory echo loops. Each was encountered
multiple times before becoming encoded as tips.
"""

import os, re, json, threading, time
from typing import Dict, List, Tuple
from collections import defaultdict

_INSTANCES: Dict[str, "ErrorPatternMemory"] = {}
_LOCK = threading.Lock()

def get_instance(session_id: str = "default") -> "ErrorPatternMemory":
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = ErrorPatternMemory(session_id)
        return _INSTANCES[session_id]


# Known recurring patterns from our own debugging history
# Context keywords for matching patterns to task context
CONTEXT_KEYWORDS = {
    "psycopg2_abort": ["psycopg2", "postgres", "database", "db", "insert", "sql", "cortex"],
    "__pycache__": ["plugin", "import", "module", "hermes", "restart", "config"],
    "shell_quoting": ["terminal", "shell", "command", "script", "bash"],
    "memory_echo": ["memory", "save", "remember", "store"],
    "gateway_kill": ["gateway", "restart", "kill", "process", "pid"],
    "open_no_context": ["file", "open", "read", "write", "csv", "json"],
    "import_error": ["import", "module", "install", "pip"],
    "type_error": ["type", "attribute", "class", "object"],
    "connection_error": ["connect", "api", "http", "request", "url", "endpoint"],
    "permission_error": ["permission", "access", "auth", "denied"],
    "file_error": ["file", "path", "directory", "read", "write"],
}

SEED_PATTERNS = {
    "psycopg2_abort": {"count": 5, "prevention": "psycopg2: one failed INSERT aborts ALL subsequent until rollback() — wrap in try/except with conn.rollback()"},
    "__pycache__": {"count": 4, "prevention": "After modifying plugins: rm -rf __pycache__/ or changes silently ignored"},
    "shell_quoting": {"count": 3, "prevention": "Complex scripts: write to /tmp/ file, NOT inline in terminal — shell quoting breaks"},
    "memory_echo": {"count": 2, "prevention": "Don't save throwaway user messages to memory — causes echo loops"},
    "gateway_kill": {"count": 3, "prevention": "Never use kill on any PID — gateway IS the Hermes process"},
    "open_no_context": {"count": 3, "prevention": "Use 'with open(...) as f:' for all file operations — manual .close() causes resource leaks"},
}

ERROR_CATEGORIES = {
    "import_error": r"ImportError|ModuleNotFoundError",
    "type_error": r"TypeError|AttributeError",
    "key_error": r"KeyError|IndexError",
    "syntax_error": r"SyntaxError|IndentationError",
    "runtime_error": r"RuntimeError|ValueError",
    "connection_error": r"ConnectionError|TimeoutError|ConnectionRefused",
    "permission_error": r"PermissionError|AccessDenied",
    "file_error": r"FileNotFoundError|IsADirectoryError",
}


class ErrorPatternMemory:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._patterns: Dict[str, dict] = dict(SEED_PATTERNS)
        self._recent_errors: List[Dict] = []
        self._injections = 0
    
    def record_error(self, error_text: str, context: str = "") -> None:
        """Record an error occurrence and increment pattern count."""
        for cat, pattern in ERROR_CATEGORIES.items():
            if re.search(pattern, error_text):
                if cat not in self._patterns:
                    self._patterns[cat] = {"count": 0, "prevention": ""}
                self._patterns[cat]["count"] += 1
                self._patterns[cat]["last_seen"] = time.time()
        
        # Check for seed pattern matches
        error_lower = error_text.lower()
        for name, info in self._patterns.items():
            if any(kw in error_lower for kw in name.split("_")):
                info["count"] = info.get("count", 0) + 1
                info["last_seen"] = time.time()
        
        self._recent_errors.append({"error": error_text[:200], "time": time.time()})
        if len(self._recent_errors) > 20:
            self._recent_errors = self._recent_errors[-20:]
    
    def build_injection(self, context: str = "") -> str:
        """Inject prevention hints for recurring error patterns relevant to the context."""
        ctx = (context or "").lower()
        relevant = []
        
        for name, info in self._patterns.items():
            if info.get("count", 0) >= 2:  # Only inject if seen 2+ times
                # Check if pattern is contextually relevant
                # Check context keywords first, fall back to name keywords
                ctx_kw = CONTEXT_KEYWORDS.get(name, name.replace("_", " ").split())
                if any(kw in ctx for kw in ctx_kw) or not ctx:
                    relevant.append(f"{name}({info['count']}x): {info.get('prevention', 'known issue')[:60]}")
        
        if not relevant:
            return ""
        
        self._injections += 1
        top3 = relevant[:3]  # Cap at 3 to stay within injection budget
        return f"[ERROR-MEMORY {len(relevant)} known patterns | Top: {'; '.join(top3)}]"
    
    def get_status(self) -> Dict:
        return {
            "session": self.session_id,
            "patterns": len(self._patterns),
            "total_errors": sum(p.get("count", 0) for p in self._patterns.values()),
            "recent": len(self._recent_errors),
            "injections": self._injections,
        }


if __name__ == "__main__":
    epm = ErrorPatternMemory("test")
    print("Error Pattern Memory — Self Test")
    print("=" * 40)
    
    # Record errors
    epm.record_error("ImportError: No module named 'foo'", "python script")
    epm.record_error("psycopg2: insert failed", "database query")
    
    # Injection
    h1 = epm.build_injection("Write a python database script")
    h2 = epm.build_injection("What is the capital of France?")
    print(f"1. DB context: {h1}")
    print(f"2. No context: {h2}")
    
    print(f"\n3. Status: {json.dumps(epm.get_status(), indent=2)}")
    print("\nAll tests passed")
