"""Automatic memory extraction — distill session experiences into cerebrum tips.

Runs at session end to extract learnable facts from the conversation
and store them in cerebrum_memory.db as distilled tips.

Usage:
    from agent.auto_memory import AutoMemoryExtractor
    extractor = AutoMemoryExtractor()
    tips = extractor.extract_from_session(session_messages)
    extractor.store_tips(tips)

ZERO-FAILURE: Silently returns empty list on any error.
"""

import json
import logging
import sqlite3
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

HERMES_HOME = Path.home() / ".hermes"
CEREBRUM_DB = HERMES_HOME / "cerebrum_memory.db"


import re as _think_re

_THINK_TAG_RE = _think_re.compile(r'<think>.*?</think>', _think_re.DOTALL | _think_re.IGNORECASE)
_THINK_OPEN_RE = _think_re.compile(r'<think>.*', _think_re.DOTALL | _think_re.IGNORECASE)


def _strip_think_tags(text: str) -> str:
    """Remove <think> reasoning blocks from content."""
    if not text or "<think" not in text.lower():
        return text
    text = _THINK_TAG_RE.sub("", text)
    text = _THINK_OPEN_RE.sub("", text)
    return text.strip()


@dataclass
class ExtractedTip:
    """A distilled tip extracted from session content."""
    topic: str
    tip_text: str
    priority: int  # 1-10
    source: str  # session_id or source identifier
    confidence: float  # 0.0-1.0
    category: str  # "procedural", "semantic", "preference", "error"


class AutoMemoryExtractor:
    """Extracts and stores learnable tips from session content."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or CEREBRUM_DB
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Ensure cerebrum tables exist (or use existing schema)."""
        # The cerebrum DB already has tables from agent/cerebrum.py
        # We just need to ensure distilled_tips has the columns we use
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            # Check if distilled_tips exists with our expected schema
            cursor.execute("PRAGMA table_info(distilled_tips)")
            columns = {row[1] for row in cursor.fetchall()}
            # Add missing columns if needed
            if "confidence" not in columns:
                cursor.execute("ALTER TABLE distilled_tips ADD COLUMN confidence REAL DEFAULT 0.5")
            if "category" not in columns:
                cursor.execute("ALTER TABLE distilled_tips ADD COLUMN category TEXT DEFAULT 'procedural'")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug("[AutoMemory] DB ensure (may already exist): %s", e)

    def extract_from_session(self, messages: List[Dict[str, Any]], session_id: str = "unknown") -> List[ExtractedTip]:
        """Extract tips from a session's message history.

        Uses heuristic extraction — no LLM call required for speed.
        For higher quality, use extract_with_llm().
        """
        tips = []
        try:
            # Extract from tool calls and results
            tool_patterns = self._extract_tool_patterns(messages)
            for pattern in tool_patterns:
                tips.append(ExtractedTip(
                    topic=pattern["topic"],
                    tip_text=pattern["tip"],
                    priority=pattern.get("priority", 5),
                    source=session_id,
                    confidence=pattern.get("confidence", 0.6),
                    category=pattern.get("category", "procedural"),
                ))

            # Extract from errors
            error_patterns = self._extract_error_patterns(messages)
            for pattern in error_patterns:
                tips.append(ExtractedTip(
                    topic=pattern["topic"],
                    tip_text=pattern["tip"],
                    priority=8,  # High priority for errors
                    source=session_id,
                    confidence=0.7,
                    category="error",
                ))

            # Extract user preferences
            preference_patterns = self._extract_preferences(messages)
            for pattern in preference_patterns:
                tips.append(ExtractedTip(
                    topic=pattern["topic"],
                    tip_text=pattern["tip"],
                    priority=6,
                    source=session_id,
                    confidence=0.5,
                    category="preference",
                ))

            # Deduplicate by topic+text similarity
            tips = self._deduplicate(tips)

        except Exception as e:
            logger.warning("[AutoMemory] Extraction failed: %s", e)

        return tips

    def _extract_tool_patterns(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract procedural patterns from tool usage."""
        patterns = []
        try:
            tool_calls = []
            tool_results = []

            for msg in messages:
                # Guard against non-dict entries (session telemetry may pass
                # strings or other formats that don't match the message schema).
                if not isinstance(msg, dict):
                    continue
                if msg.get("role") == "assistant" and "tool_calls" in msg:
                    for tc in msg["tool_calls"]:
                        if not isinstance(tc, dict):
                            continue
                        fn = tc.get("function") or {}
                        tool_calls.append({
                            "name": fn.get("name", "") if isinstance(fn, dict) else "",
                            "args": fn.get("arguments", {}) if isinstance(fn, dict) else {},
                        })
                elif msg.get("role") == "tool":
                    tool_results.append({
                        "name": msg.get("name", ""),
                        "content": str(msg.get("content", ""))[:500],
                    })

            # Pattern: successful tool sequences
            if len(tool_calls) >= 2:
                sequence = " -> ".join([tc["name"] for tc in tool_calls[:5]])
                patterns.append({
                    "topic": f"tool_sequence_{tool_calls[0]['name']}",
                    "tip": f"Successful sequence: {sequence}",
                    "priority": 4,
                    "confidence": 0.6,
                    "category": "procedural",
                })

            # Pattern: tool + error -> recovery
            for i, result in enumerate(tool_results):
                if "error" in result["content"].lower() or result["content"].startswith("{") and "error" in result["content"]:
                    if i + 1 < len(tool_calls):
                        recovery_tool = tool_calls[i + 1]["name"]
                        patterns.append({
                            "topic": f"recovery_from_{result['name']}",
                            "tip": f"When {result['name']} fails, try {recovery_tool}",
                            "priority": 7,
                            "confidence": 0.5,
                            "category": "procedural",
                        })

        except Exception as e:
            logger.debug("[AutoMemory] Tool pattern extraction failed: %s", e)

        return patterns

    def _extract_error_patterns(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract error patterns and resolutions."""
        patterns = []
        try:
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                content = str(msg.get("content", ""))
                if "error" in content.lower() or "exception" in content.lower() or "traceback" in content.lower():
                    # Extract error type and context
                    lines = content.split("\n")
                    for line in lines[:3]:
                        if "error" in line.lower() or "exception" in line.lower():
                            patterns.append({
                                "topic": "error_pattern",
                                "tip": f"Observed error: {line[:200]}",
                            })
                            break
        except Exception as e:
            logger.debug("[AutoMemory] Error pattern extraction failed: %s", e)

        return patterns

    def _extract_preferences(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract user preferences from messages."""
        patterns = []
        try:
            preference_keywords = [
                ("prefer", "preference"),
                ("like", "preference"),
                ("want", "preference"),
                ("need", "preference"),
                ("always", "habit"),
                ("never", "habit"),
                ("use", "tool_preference"),
                ("instead of", "alternative"),
            ]

            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                if msg.get("role") == "user":
                    content = str(msg.get("content", "")).lower()
                    for keyword, category in preference_keywords:
                        if keyword in content and len(content) < 500:
                            # Extract sentence containing keyword
                            sentences = content.split(".")
                            for sent in sentences:
                                if keyword in sent:
                                    patterns.append({
                                        "topic": f"user_{category}",
                                        "tip": sent.strip()[:200],
                                    })
                                    break
                            break  # One preference per message

        except Exception as e:
            logger.debug("[AutoMemory] Preference extraction failed: %s", e)

        return patterns

    def _deduplicate(self, tips: List[ExtractedTip]) -> List[ExtractedTip]:
        """Remove near-duplicate tips."""
        seen = set()
        unique = []
        for tip in tips:
            key = f"{tip.topic}:{tip.tip_text[:100]}"
            if key not in seen:
                seen.add(key)
                unique.append(tip)
        return unique

    def store_tips(self, tips: List[ExtractedTip]) -> int:
        """Store extracted tips in cerebrum database."""
        if not tips:
            return 0

        stored = 0
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            for tip in tips:
                import hashlib
                tip_hash = hashlib.sha256(tip.tip_text.encode()).hexdigest()[:16]
                cursor.execute("""
                    INSERT INTO distilled_tips (tip_hash, topic, tip_text, priority, source_sessions, confidence, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (tip_hash, tip.topic, tip.tip_text, tip.priority, tip.source, tip.confidence, tip.category))
                stored += 1

            conn.commit()
            conn.close()
            logger.info("[AutoMemory] Stored %d tips", stored)

        except Exception as e:
            logger.warning("[AutoMemory] Store failed: %s", e)

        return stored

    def extract_with_llm(self, messages: List[Dict[str, Any]], session_id: str = "unknown",
                         llm_call: Optional[Any] = None) -> List[ExtractedTip]:
        """Extract tips using an LLM for higher quality.

        Requires an llm_call function that takes a prompt and returns text.
        """
        if llm_call is None:
            logger.debug("[AutoMemory] No LLM provided, falling back to heuristic extraction")
            return self.extract_from_session(messages, session_id)

        try:
            # Build summary of session
            session_summary = self._summarize_session(messages)

            prompt = f"""Analyze this session summary and extract 3-5 learnable tips.
Each tip should be a concise lesson that would help future sessions.

Session summary:
{session_summary}

Respond with a JSON array of tips:
[
  {{
    "topic": "brief topic name",
    "tip_text": "the specific lesson or pattern",
    "priority": 1-10,
    "category": "procedural|semantic|preference|error"
  }}
]

Tips to extract:
- Successful tool sequences or workflows
- Error patterns and how they were resolved
- User preferences or habits
- Domain-specific facts learned"""

            response = llm_call(prompt)

            # Parse JSON response
            import json
            try:
                data = json.loads(response)
                if isinstance(data, list):
                    tips = []
                    for item in data:
                        tips.append(ExtractedTip(
                            topic=item.get("topic", "unknown"),
                            tip_text=item.get("tip_text", ""),
                            priority=item.get("priority", 5),
                            source=session_id,
                            confidence=0.8,
                            category=item.get("category", "procedural"),
                        ))
                    return tips
            except json.JSONDecodeError:
                pass

        except Exception as e:
            logger.warning("[AutoMemory] LLM extraction failed: %s", e)

        return self.extract_from_session(messages, session_id)

    def _summarize_session(self, messages: List[Dict[str, Any]]) -> str:
        """Create a brief summary of session content."""
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = _strip_think_tags(str(msg.get("content", "")))[:200]
            if role in ("user", "assistant"):
                lines.append(f"{role}: {content}")
            elif role == "tool":
                name = msg.get("name", "tool")
                lines.append(f"tool ({name}): {content[:100]}")
        return "\n".join(lines[:50])  # Limit length

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored tips."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM distilled_tips")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT category, COUNT(*) FROM distilled_tips GROUP BY category")
            rows = cursor.fetchall()
            by_category = {row[0]: row[1] for row in rows if row[0]}

            cursor.execute("SELECT AVG(confidence), AVG(priority) FROM distilled_tips")
            avg_conf, avg_pri = cursor.fetchone()

            conn.close()

            return {
                "total_tips": total,
                "by_category": by_category,
                "avg_confidence": round(avg_conf or 0, 2),
                "avg_priority": round(avg_pri or 0, 2),
            }
        except Exception as e:
            logger.warning("[AutoMemory] Stats failed: %s", e)
            return {"error": str(e)}


# Singleton accessor
_extractor_instance: Optional[AutoMemoryExtractor] = None


def get_auto_memory_extractor() -> AutoMemoryExtractor:
    """Get the singleton auto memory extractor."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = AutoMemoryExtractor()
    return _extractor_instance
