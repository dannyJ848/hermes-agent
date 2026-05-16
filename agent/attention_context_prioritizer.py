"""
attention_context_prioritizer.py — Relevance-based memory injection.

Scores every memory unit by relevance to current task and injects only
the top-N most relevant tips/facts into context. Prevents context bloat.
"""

import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ScoredMemory:
    memory_id: str
    content: str
    relevance_score: float
    memory_type: str
    source: str
    age_hours: float


class AttentionContextPrioritizer:
    """Attention-based memory relevance scoring."""

    def __init__(self, max_memories: int = 5, recency_halflife_hours: float = 24.0):
        self.max_memories = max_memories
        self.recency_halflife = recency_halflife_hours
        self._memory_cache: List[Dict] = []
        self._last_refresh = 0

    def _tokenize(self, text: str) -> set:
        """Simple tokenization for overlap scoring."""
        return set(w.lower() for w in text.split() if len(w) > 2)

    def _compute_overlap(self, text_a: str, text_b: str) -> float:
        """Compute Jaccard similarity between two texts."""
        tokens_a = self._tokenize(text_a)
        tokens_b = self._tokenize(text_b)
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)
        return intersection / union if union > 0 else 0.0

    def _score_relevance(self, memory: Dict, current_task: str, current_context: str) -> float:
        """Score a memory's relevance to current task."""
        content = memory.get('content', memory.get('text', ''))

        # Semantic overlap with task
        task_overlap = self._compute_overlap(content, current_task)

        # Semantic overlap with context
        context_overlap = self._compute_overlap(content, current_context)

        # Recency decay
        created_at = memory.get('created_at', memory.get('timestamp', 0))
        if isinstance(created_at, str):
            try:
                created_at = float(created_at)
            except:
                created_at = time.time()
        age_hours = (time.time() - created_at) / 3600
        recency_factor = 0.5 ** (age_hours / self.recency_halflife)

        # Type boost
        type_boost = {
            'error_pattern': 1.2,
            'tip': 1.1,
            'skill': 1.0,
            'fact': 0.9,
            'trace': 0.7,
        }.get(memory.get('type', memory.get('node_type', '')), 0.8)

        # Confidence/trust boost
        confidence = memory.get('confidence', memory.get('trust_score', 0.5))

        # Composite score
        relevance = (
            task_overlap * 0.35 +
            context_overlap * 0.25 +
            recency_factor * 0.20 +
            type_boost * 0.10 +
            confidence * 0.10
        )

        return min(1.0, relevance)

    def _fetch_all_memories(self) -> List[Dict]:
        """Fetch memories from all cognitive databases."""
        memories = []

        # From cerebrum
        try:
            import sqlite3
            from pathlib import Path
            db = sqlite3.connect(str(Path.home() / ".hermes" / "cerebrum_memory.db"))
            db.row_factory = sqlite3.Row

            # Error patterns
            try:
                rows = db.execute("SELECT error_signature as content, occurrence_count, 'error_pattern' as type, last_seen as created_at FROM error_patterns").fetchall()
                memories.extend([dict(r) for r in rows])
            except:
                pass

            # Staging tips
            try:
                rows = db.execute("SELECT content, confidence, category as type, created_at FROM staging_tips").fetchall()
                memories.extend([dict(r) for r in rows])
            except:
                pass

            # Epistemic facts
            try:
                rows = db.execute("SELECT content, overall_trust as confidence, category as type, created_at FROM epistemic_facts WHERE overall_trust > 0.7").fetchall()
                memories.extend([dict(r) for r in rows])
            except:
                pass

            db.close()
        except Exception:
            pass

        # From cortex
        try:
            from agent.cortex_access import CortexDB
            cortex = CortexDB()
            nodes = cortex.query_nodes(domain="general", limit=50)
            for node in nodes:
                memories.append({
                    'content': node.get('text', ''),
                    'confidence': node.get('confidence', 0.5),
                    'type': node.get('node_type', 'tip'),
                    'created_at': node.get('created_at', time.time()),
                })
        except Exception:
            pass

        return memories

    def prioritize(self, current_task: str, current_context: str = "") -> List[ScoredMemory]:
        """Return top-N most relevant memories for current task."""
        # Refresh cache if stale
        if time.time() - self._last_refresh > 300:  # 5 minutes
            self._memory_cache = self._fetch_all_memories()
            self._last_refresh = time.time()

        scored = []
        for memory in self._memory_cache:
            score = self._score_relevance(memory, current_task, current_context)
            if score > 0.2:  # Minimum relevance threshold
                scored.append(ScoredMemory(
                    memory_id=str(hash(memory.get('content', ''))),
                    content=memory.get('content', '')[:300],
                    relevance_score=score,
                    memory_type=memory.get('type', memory.get('node_type', 'unknown')),
                    source=memory.get('source', 'cerebrum'),
                    age_hours=(time.time() - memory.get('created_at', time.time())) / 3600
                ))

        scored.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored[:self.max_memories]

    def format_for_injection(self, memories: List[ScoredMemory]) -> str:
        """Format prioritized memories for context injection."""
        if not memories:
            return ""

        lines = ["\n[RELEVANT MEMORY CONTEXT]"]
        for i, mem in enumerate(memories, 1):
            lines.append(f"{i}. [{mem.memory_type.upper()}] {mem.content}")
            lines.append(f"   (relevance: {mem.relevance_score:.2f}, age: {mem.age_hours:.1f}h)")
        lines.append("[END MEMORY CONTEXT]\n")

        return "\n".join(lines)

    def get_injection(self, current_task: str, current_context: str = "") -> str:
        """Get formatted memory injection for current task."""
        memories = self.prioritize(current_task, current_context)
        return self.format_for_injection(memories)
