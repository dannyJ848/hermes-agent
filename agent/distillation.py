#!/usr/bin/env python3
"""
Distillation Pipeline — Raw experiences → actionable behavioral tips.

Stages:
  1. Experience Collection (from cerebrum + cortex)
  2. Pattern Extraction (grouping, frequency analysis)
  3. Tip Generation (structured tip creation)
  4. Deduplication (semantic similarity)
  5. Prioritization (impact × frequency × recency × confidence)
  6. Verification (track application outcomes)
"""

import sqlite3
import json
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

HERMES_HOME = Path.home() / ".hermes"


def _safe(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"[distillation] {fn.__name__} failed: {e}")
            if fn.__name__.startswith("get_") or fn.__name__.startswith("query_"):
                return []
            if fn.__name__.startswith("count_"):
                return 0
            return None
    return wrapper


class DistillationPipeline:
    """Transform raw experiences into structured, actionable tips."""

    def __init__(self):
        self.cerebrum = None
        self.cortex = None
        self._init_connections()

    def _init_connections(self):
        try:
            from agent.cerebrum import get_cerebrum
            self.cerebrum = get_cerebrum()
        except Exception:
            pass
        try:
            from agent.cortex_flywheel import get_cortex
            self.cortex = get_cortex()
        except Exception:
            pass

    @_safe
    def distill_last_24h(self) -> List[Dict]:
        """Run full distillation on last 24h of experiences."""
        experiences = self._collect_experiences(hours=24)
        if len(experiences) < 2:
            return []
        patterns = self._extract_patterns(experiences)
        tips = []
        for pattern in patterns:
            tip = self._generate_tip(pattern)
            if tip:
                deduped = self._deduplicate_tip(tip)
                if deduped:
                    prioritized = self._prioritize_tip(deduped)
                    self._store_tip(prioritized)
                    tips.append(prioritized)
        return tips

    @_safe
    def _collect_experiences(self, hours: int = 24) -> List[Dict]:
        """Gather experiences from all sources."""
        all_exps = []
        # From cortex (if available and has method)
        if self.cortex and hasattr(self.cortex, 'get_recent_experiences'):
            try:
                all_exps.extend(self.cortex.get_recent_experiences(hours=hours))
            except Exception:
                pass
        # From cerebrum episodic
        if self.cerebrum and hasattr(self.cerebrum, 'get_episodes'):
            try:
                eps = self.cerebrum.get_episodes(min_importance=0.4, limit=200)
                for ep in eps:
                    all_exps.append({
                        "session_id": ep.get("session_id", "unknown"),
                        "capture_type": ep.get("event_type", "unknown"),
                        "description": ep.get("content", ""),
                        "outcome": None,
                        "lessons": None,
                        "importance": ep.get("importance_score", 0.5)
                    })
            except Exception:
                pass
        # Fallback: read from SQLite experiences table directly
        if not all_exps:
            try:
                conn = sqlite3.connect(str(HERMES_HOME / "cerebrum_memory.db"))
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, action_type, action_detail, result, lesson, error_pattern, 
                           context_tags, last_seen, created_at
                    FROM experiences
                    WHERE lesson != '' AND lesson IS NOT NULL
                      AND last_seen > datetime('now', '-{} hours')
                    ORDER BY frequency DESC, last_seen DESC
                    LIMIT 200
                """.format(hours))
                for row in cur.fetchall():
                    all_exps.append({
                        "session_id": str(row["id"]),
                        "capture_type": row["action_type"] or "unknown",
                        "description": row["action_detail"] or "",
                        "outcome": row["result"] or "unknown",
                        "lessons": row["lesson"] or "",
                        "error_pattern": row["error_pattern"] or "",
                        "importance": 0.6 if row["result"] == "regression" else 0.4
                    })
                conn.close()
            except Exception:
                pass
        return all_exps

    @_safe
    def _extract_patterns(self, experiences: List[Dict]) -> List[Dict]:
        """Group similar experiences into patterns."""
        from collections import defaultdict, Counter
        # Group by normalized description keywords
        groups = defaultdict(list)
        for exp in experiences:
            # Extract key terms
            desc = exp.get("description", "")
            terms = re.findall(r"\b[a-z]{4,}\b", desc.lower())
            # Use top 2 most common meaningful words as key
            stopwords = {"this", "that", "with", "from", "have", "been", "were", "when", "where", "what", "error", "failed"}
            filtered = [t for t in terms if t not in stopwords]
            if len(filtered) >= 2:
                key = tuple(sorted(filtered[:2]))
            else:
                key = (exp.get("capture_type", "unknown"),)
            groups[key].append(exp)

        patterns = []
        for key, exps in groups.items():
            if len(exps) >= 2:
                outcomes = [e.get("outcome") for e in exps if e.get("outcome")]
                lessons = [e.get("lessons") for e in exps if e.get("lessons")]
                descriptions = [e.get("description", "") for e in exps]
                # Calculate success rate from outcomes
                success_count = sum(1 for o in outcomes if o and o.lower() in ["success", "fixed", "resolved", "passed"])
                success_rate = success_count / len(outcomes) if outcomes else 0.5
                patterns.append({
                    "key": key,
                    "frequency": len(exps),
                    "descriptions": descriptions,
                    "outcomes": outcomes,
                    "lessons": lessons,
                    "success_rate": success_rate,
                    "session_ids": list(set(e.get("session_id", "unknown") for e in exps))
                })
        # Sort by frequency × success_rate
        patterns.sort(key=lambda p: p["frequency"] * p["success_rate"], reverse=True)
        return patterns[:20]  # Top 20 patterns

    @_safe
    def _generate_tip(self, pattern: Dict) -> Optional[Dict]:
        """Generate a structured tip from a pattern."""
        lessons = [l for l in pattern["lessons"] if l and len(l) > 10]
        if not lessons:
            # Generate from descriptions if no explicit lessons
            descs = pattern["descriptions"]
            common_words = self._find_common_phrases(descs)
            if not common_words:
                return None
            lesson = f"When dealing with {' '.join(pattern['key'])}, {common_words}"
        else:
            lesson = max(lessons, key=len)

        topic = " ".join(pattern["key"]) if isinstance(pattern["key"], tuple) else str(pattern["key"])
        # Clean up topic
        topic = re.sub(r"[^a-z0-9 ]", "", topic.lower())[:50]

        confidence = min(0.5 + (pattern["frequency"] * 0.1) + (pattern["success_rate"] * 0.3), 0.95)

        return {
            "topic": topic,
            "text": lesson,
            "confidence": confidence,
            "frequency": pattern["frequency"],
            "success_rate": pattern["success_rate"],
            "sessions": pattern["session_ids"]
        }

    def _find_common_phrases(self, descriptions: List[str]) -> str:
        """Find common substrings across descriptions."""
        if not descriptions:
            return ""
        words = []
        for d in descriptions:
            words.extend(re.findall(r"\b[a-z]{4,}\b", d.lower()))
        from collections import Counter
        common = Counter(words).most_common(5)
        return " ".join([w for w, c in common])

    @_safe
    def _deduplicate_tip(self, tip: Dict) -> Optional[Dict]:
        """Check semantic similarity against existing tips."""
        tip_hash = hashlib.sha256(tip["text"].encode()).hexdigest()[:16]
        
        # Try cerebrum first
        existing = []
        if self.cerebrum and hasattr(self.cerebrum, 'get_all_tips'):
            try:
                existing = self.cerebrum.get_all_tips(limit=200)
            except Exception:
                pass
        
        # Fallback: read from SQLite
        if not existing:
            try:
                conn = sqlite3.connect(str(HERMES_HOME / "cerebrum_memory.db"))
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT tip_hash, tip_text FROM distilled_tips LIMIT 200")
                existing = [dict(row) for row in cur.fetchall()]
                conn.close()
            except Exception:
                pass
        
        # Exact hash check
        for ex in existing:
            if ex.get("tip_hash") == tip_hash:
                return None  # Exact duplicate
        # Simple text similarity: shared word ratio
        tip_words = set(re.findall(r"\b[a-z]{4,}\b", tip["text"].lower()))
        for ex in existing:
            ex_words = set(re.findall(r"\b[a-z]{4,}\b", ex.get("tip_text", ex.get("text", "")).lower()))
            if tip_words and ex_words:
                overlap = len(tip_words & ex_words) / len(tip_words | ex_words)
                if overlap > 0.85:
                    return None
        return tip

    @_safe
    def _prioritize_tip(self, tip: Dict) -> Dict:
        """Calculate priority score."""
        # Score = impact × frequency × recency × confidence
        # Simplified: use frequency + success_rate + confidence
        score = (tip.get("frequency", 1) * 2) + (tip.get("success_rate", 0.5) * 3) + (tip.get("confidence", 0.5) * 2)
        priority = min(int(score), 10)
        tip["priority"] = max(priority, 1)
        return tip

    @_safe
    def _store_tip(self, tip: Dict) -> bool:
        """Store tip in cerebrum."""
        if not self.cerebrum:
            return False
        return self.cerebrum.store_tip(
            tip["topic"], tip["text"], priority=tip.get("priority", 5),
            source_sessions=tip.get("sessions", [])
        )

    @_safe
    def get_distillation_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        if not self.cerebrum:
            return {"status": "no_cerebrum"}
        return {
            "cerebrum_tips": self.cerebrum.get_stats().get("distilled_tips", 0),
            "status": "active"
        }


# Singleton
_pipeline_instance = None

def get_pipeline() -> DistillationPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = DistillationPipeline()
    return _pipeline_instance
