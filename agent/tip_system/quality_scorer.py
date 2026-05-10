#!/usr/bin/env python3
"""
R86: Tip Quality Scorer — rate tip quality on 3 axes.

Axes:
1. Actionability (0-10): Can the agent ACT on this tip immediately?
   "Use X pattern" → 8. "Be careful" → 2.
2. Specificity (0-10): How specific is the trigger?
   "WHEN debugging psycopg2" → 9. "WHEN coding" → 3.
3. Evidence (0-10): How well validated?
   "Validated: +1.1 improvement" → 9. "Should help" → 2.

Composite = (A * 0.4 + S * 0.3 + E * 0.3). Tips < 4.0 = prune candidate.
"""
import os, re, json, threading
from typing import Dict, Tuple

_INSTANCES: Dict[str, "TipQualityScorer"] = {}
_LOCK = threading.Lock()

def get_instance(session_id: str = "default") -> "TipQualityScorer":
    with _LOCK:
        if session_id not in _INSTANCES:
            _INSTANCES[session_id] = TipQualityScorer(session_id)
        return _INSTANCES[session_id]


class TipQualityScorer:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._scores: Dict[str, Dict] = {}

    def score(self, tip_text: str) -> Dict:
        # Actionability: has concrete action verb?
        action_verbs = ["use", "write", "run", "add", "check", "verify",
                        "fix", "replace", "compress", "limit", "route"]
        has_action = any(f" {v} " in tip_text.lower() for v in action_verbs)
        has_pattern = bool(re.search(r"\[.*?\]", tip_text))
        has_specific_cmd = bool(re.search(r"(?:def |import |pip |git )", tip_text))
        actionability = 3 + (3 if has_action else 0) + (2 if has_pattern else 0) + (2 if has_specific_cmd else 0)

        # Specificity: how narrow is the WHEN clause?
        has_when = "WHEN" in tip_text
        has_specific_trigger = bool(re.search(r"(?:psycopg2|docker|python|bash|regex|git)", tip_text.lower()))
        has_domain = any(d in tip_text.lower() for d in ["coding", "search", "tool", "reasoning", "debugging"])
        specificity = 2 + (3 if has_when else 0) + (3 if has_specific_trigger else 0) + (2 if has_domain else 0)

        # Evidence: mentions validation?
        has_validation = any(w in tip_text.lower() for w in ["validated", "proven", "confirmed", "measured", "+1.1", "73%"])
        has_source = bool(re.search(r"arxiv|iclr|neurips", tip_text.lower()))
        evidence = 2 + (5 if has_validation else 0) + (3 if has_source else 0)

        composite = round(actionability * 0.4 + specificity * 0.3 + evidence * 0.3, 1)
        return {"actionability": min(actionability, 10), "specificity": min(specificity, 10),
                "evidence": min(evidence, 10), "composite": composite}

    def build_injection(self, context: str = "") -> str:
        return ""  # Background evaluation module

    def get_status(self) -> Dict:
        return {"session": self.session_id, "scored": len(self._scores)}


if __name__ == "__main__":
    tqs = TipQualityScorer("test")
    s = tqs.score("WHEN debugging psycopg2, DO use rollback() after failed INSERT. Validated: prevents DB abort.")
    print(f"Tip Quality Scorer — OK ({s})")
