#!/usr/bin/env python3
"""
R53: Tip Deduplicator — merge similar tips, remove exact/near duplicates.

4,561 tips but many are variations of the same advice. This module
identifies and merges duplicates using prefix matching + content hashing.
"""
import os, json, threading, re, hashlib
from typing import Dict, List, Tuple
from collections import defaultdict

_INSTANCES: Dict[str, "TipDedup"] = {}
_LOCK = threading.Lock()

def get_instance(session_id: str = "default") -> "TipDedup":
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = TipDedup(session_id)
        return _INSTANCES[session_id]


class TipDedup:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._hashes_seen: Dict[str, str] = {}  # hash → tip_id
        self._prefixes_seen: Dict[str, str] = {}  # prefix(50) → tip_id
        self._duplicates_found = 0
        self._merges = 0

    def content_hash(self, text: str) -> str:
        """MD5 hash of normalized tip text."""
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()

    def is_duplicate(self, text: str, tip_id: str = "") -> Tuple[bool, str]:
        """Check if text is a duplicate of an existing tip."""
        h = self.content_hash(text)
        prefix = text[:50].lower().strip()

        # Exact content hash match
        if h in self._hashes_seen:
            self._duplicates_found += 1
            return True, self._hashes_seen[h]

        # Near-duplicate prefix match (same opening)
        if prefix in self._prefixes_seen:
            self._duplicates_found += 1
            return True, self._prefixes_seen[prefix]

        # Register
        self._hashes_seen[h] = tip_id
        self._prefixes_seen[prefix] = tip_id
        return False, ""

    def merge_tips(self, keep_id: str, remove_id: str, keep_text: str, remove_text: str) -> str:
        """Merge two duplicate tips: keep the longer/more detailed one."""
        self._merges += 1
        if len(remove_text) > len(keep_text):
            return remove_text
        return keep_text

    def get_status(self) -> Dict:
        return {
            "session": self.session_id,
            "known_hashes": len(self._hashes_seen),
            "known_prefixes": len(self._prefixes_seen),
            "duplicates_found": self._duplicates_found,
            "merges": self._merges,
        }


if __name__ == "__main__":
    td = TipDedup("test")
    print("Tip Deduplicator")
    print("=" * 40)

    # Test dedup
    t1 = "WHEN debugging, DO use print statements to trace"
    t2 = "WHEN debugging, DO use print statements to trace variable values"
    t3 = "WHEN writing code, DO add type hints"

    d1, _ = td.is_duplicate(t1, "tip_1")
    d2, _ = td.is_duplicate(t2, "tip_2")  # Prefix match with t1
    d3, _ = td.is_duplicate(t3, "tip_3")

    print(f"  t1 dup={d1}, t2 dup={d2} (prefix match), t3 dup={d3}")
    print(f"  Status: {json.dumps(td.get_status())}")
    print("OK")
