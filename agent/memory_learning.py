"""
Self-Improving Memory System — Kimi Harness v2.0

This module adds learning and prediction to the adaptive injection system.
After each session, it analyzes which injected memory entries and skills were
actually used, updates relevance weights, and predicts what will be needed
in future sessions.

Architecture:
- Usage tracker: Logs which memory entries/skills were loaded/used per session
- Weight updater: Adjusts relevance scores based on actual usage
- Predictor: Anticipates which entries/skills will be needed next
- Feedback loop: Closes the loop between injection → usage → learning

Author: Kimi
Date: 2026-04-26
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class MemoryUsageRecord:
    """Record of how a memory entry was used in a session."""
    entry_hash: str  # Hash of the entry content (for identification)
    entry_preview: str  # First 100 chars for human readability
    session_id: str
    was_injected: bool  # Was it in the system prompt?
    was_referenced: bool  # Did the model reference it in output?
    was_useful: Optional[bool] = None  # User feedback: was it helpful?
    timestamp: float = field(default_factory=time.time)
    query_context: str = ""  # What was the user asking about?


@dataclass
class SkillUsageRecord:
    """Record of how a skill was used in a session."""
    skill_name: str
    session_id: str
    was_shown: bool  # Was it in the skills list?
    was_loaded: bool  # Did the model call skill_view()?
    was_followed: bool  # Did the model follow the skill's instructions?
    was_useful: Optional[bool] = None
    timestamp: float = field(default_factory=time.time)
    query_context: str = ""


@dataclass
class LearnedWeight:
    """Learned relevance weight for a memory entry or skill."""
    id: str  # entry_hash or skill_name
    base_score: float = 0.5  # From TF-IDF scoring
    learned_multiplier: float = 1.0  # Learned from usage
    usage_count: int = 0
    success_count: int = 0  # Times it was actually useful
    failure_count: int = 0  # Times it was injected but not useful
    last_used: float = 0.0
    context_tags: Set[str] = field(default_factory=set)
    
    @property
    def effective_score(self) -> float:
        """Combined score for ranking."""
        # Bayesian-ish update: success rate affects multiplier
        if self.usage_count > 0:
            success_rate = self.success_count / self.usage_count
            # Smooth with prior (0.5)
            smoothed = (self.success_count + 1) / (self.usage_count + 2)
            self.learned_multiplier = 0.5 + smoothed
        
        return self.base_score * self.learned_multiplier


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

class MemoryLearningStore:
    """Persistent store for learned memory weights."""
    
    def __init__(self, store_dir: Optional[Path] = None):
        if store_dir is None:
            from hermes_constants import get_hermes_home
            store_dir = Path(get_hermes_home()) / "memory_learning"
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)
        
        self.weights_file = self.store_dir / "learned_weights.json"
        self.usage_file = self.store_dir / "usage_history.jsonl"
        
        self._weights: Dict[str, LearnedWeight] = {}
        self._load_weights()
    
    def _load_weights(self):
        """Load learned weights from disk."""
        if not self.weights_file.exists():
            return
        try:
            data = json.loads(self.weights_file.read_text())
            for id_str, w_data in data.items():
                self._weights[id_str] = LearnedWeight(
                    id=id_str,
                    base_score=w_data.get("base_score", 0.5),
                    learned_multiplier=w_data.get("learned_multiplier", 1.0),
                    usage_count=w_data.get("usage_count", 0),
                    success_count=w_data.get("success_count", 0),
                    failure_count=w_data.get("failure_count", 0),
                    last_used=w_data.get("last_used", 0.0),
                    context_tags=set(w_data.get("context_tags", [])),
                )
        except Exception as e:
            logger.warning("Failed to load learned weights: %s", e)
    
    def _save_weights(self):
        """Save learned weights to disk."""
        data = {}
        for id_str, weight in self._weights.items():
            data[id_str] = {
                "base_score": weight.base_score,
                "learned_multiplier": weight.learned_multiplier,
                "usage_count": weight.usage_count,
                "success_count": weight.success_count,
                "failure_count": weight.failure_count,
                "last_used": weight.last_used,
                "context_tags": list(weight.context_tags),
            }
        try:
            self.weights_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning("Failed to save learned weights: %s", e)
    
    def get_weight(self, id_str: str) -> Optional[LearnedWeight]:
        return self._weights.get(id_str)
    
    def update_weight(self, weight: LearnedWeight):
        self._weights[weight.id] = weight
        self._save_weights()
    
    def record_usage(self, record: MemoryUsageRecord):
        """Append usage record to history."""
        try:
            with open(self.usage_file, "a") as f:
                f.write(json.dumps({
                    "type": "memory",
                    "entry_hash": record.entry_hash,
                    "entry_preview": record.entry_preview,
                    "session_id": record.session_id,
                    "was_injected": record.was_injected,
                    "was_referenced": record.was_referenced,
                    "was_useful": record.was_useful,
                    "timestamp": record.timestamp,
                    "query_context": record.query_context,
                }) + "\n")
        except Exception as e:
            logger.warning("Failed to record usage: %s", e)
    
    def record_skill_usage(self, record: SkillUsageRecord):
        """Append skill usage record to history."""
        try:
            with open(self.usage_file, "a") as f:
                f.write(json.dumps({
                    "type": "skill",
                    "skill_name": record.skill_name,
                    "session_id": record.session_id,
                    "was_shown": record.was_shown,
                    "was_loaded": record.was_loaded,
                    "was_followed": record.was_followed,
                    "was_useful": record.was_useful,
                    "timestamp": record.timestamp,
                    "query_context": record.query_context,
                }) + "\n")
        except Exception as e:
            logger.warning("Failed to record skill usage: %s", e)
    
    def get_usage_stats(self, id_str: str) -> Dict[str, Any]:
        """Get usage statistics for an entry or skill."""
        weight = self._weights.get(id_str)
        if not weight:
            return {"found": False}
        return {
            "found": True,
            "usage_count": weight.usage_count,
            "success_count": weight.success_count,
            "failure_count": weight.failure_count,
            "success_rate": weight.success_count / weight.usage_count if weight.usage_count > 0 else 0,
            "effective_score": weight.effective_score,
            "last_used": weight.last_used,
            "context_tags": list(weight.context_tags),
        }


# ---------------------------------------------------------------------------
# Learning engine
# ---------------------------------------------------------------------------

class MemoryLearningEngine:
    """Analyzes usage patterns and updates learned weights."""
    
    def __init__(self, store: Optional[MemoryLearningStore] = None):
        self.store = store or MemoryLearningStore()
    
    def process_session_results(
        self,
        session_id: str,
        injected_memory: List[str],
        referenced_memory: List[str],
        loaded_skills: List[str],
        followed_skills: List[str],
        query_context: str = "",
    ):
        """
        Process a completed session to update learned weights.
        
        Args:
            injected_memory: List of memory entries that were injected
            referenced_memory: List of entries the model actually referenced
            loaded_skills: List of skills the model loaded
            followed_skills: List of skills the model followed
            query_context: Summary of what the session was about
        """
        # Process memory entries
        for entry in injected_memory:
            entry_hash = str(hash(entry) % 10000000)
            was_referenced = entry in referenced_memory
            
            weight = self.store.get_weight(entry_hash)
            if weight is None:
                weight = LearnedWeight(id=entry_hash, base_score=0.5)
            
            weight.usage_count += 1
            weight.last_used = time.time()
            
            if was_referenced:
                weight.success_count += 1
                # Extract context tags from query
                weight.context_tags.update(self._extract_tags(query_context))
            else:
                weight.failure_count += 1
            
            self.store.update_weight(weight)
            
            # Record usage
            self.store.record_usage(MemoryUsageRecord(
                entry_hash=entry_hash,
                entry_preview=entry[:100],
                session_id=session_id,
                was_injected=True,
                was_referenced=was_referenced,
                query_context=query_context,
            ))
        
        # Process skills
        for skill in loaded_skills:
            was_followed = skill in followed_skills
            
            weight = self.store.get_weight(f"skill:{skill}")
            if weight is None:
                weight = LearnedWeight(id=f"skill:{skill}", base_score=0.5)
            
            weight.usage_count += 1
            weight.last_used = time.time()
            
            if was_followed:
                weight.success_count += 1
                weight.context_tags.update(self._extract_tags(query_context))
            else:
                weight.failure_count += 1
            
            self.store.update_weight(weight)
            
            self.store.record_skill_usage(SkillUsageRecord(
                skill_name=skill,
                session_id=session_id,
                was_shown=True,
                was_loaded=True,
                was_followed=was_followed,
                query_context=query_context,
            ))
        
        logger.info(
            "Learning engine processed session %s: %d memory entries, %d skills",
            session_id, len(injected_memory), len(loaded_skills)
        )
    
    def _extract_tags(self, text: str) -> Set[str]:
        """Extract topic tags from text."""
        from agent.adaptive_injection import _tokenize
        tokens = _tokenize(text)
        # Return top tokens as tags
        return set(tokens[:10])
    
    def predict_relevant_entries(
        self,
        query: str,
        available_entries: List[str],
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        Predict which entries will be relevant to a query.
        Returns list of (entry, predicted_score) sorted by score.
        """
        from agent.adaptive_injection import score_relevance
        
        query_tags = self._extract_tags(query)
        scored = []
        
        for entry in available_entries:
            entry_hash = str(hash(entry) % 10000000)
            
            # Base relevance score
            base_score = score_relevance(query, entry)
            
            # Learned weight adjustment
            weight = self.store.get_weight(entry_hash)
            if weight:
                # Boost if context tags overlap
                tag_overlap = len(query_tags & weight.context_tags)
                tag_boost = 1.0 + (tag_overlap * 0.1)
                
                learned_score = weight.effective_score * tag_boost
                combined = 0.7 * base_score + 0.3 * learned_score
            else:
                combined = base_score
            
            scored.append((entry, combined))
        
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]
    
    def predict_relevant_skills(
        self,
        query: str,
        available_skills: List[str],
        top_k: int = 5,
    ) -> List[Tuple[str, float]]:
        """Predict which skills will be relevant to a query."""
        from agent.adaptive_injection import score_relevance
        
        query_tags = self._extract_tags(query)
        scored = []
        
        for skill in available_skills:
            # Base relevance
            base_score = score_relevance(query, skill)
            
            # Learned adjustment
            weight = self.store.get_weight(f"skill:{skill}")
            if weight:
                tag_overlap = len(query_tags & weight.context_tags)
                tag_boost = 1.0 + (tag_overlap * 0.1)
                learned_score = weight.effective_score * tag_boost
                combined = 0.7 * base_score + 0.3 * learned_score
            else:
                combined = base_score
            
            scored.append((skill, combined))
        
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]
    
    def get_learning_report(self) -> Dict[str, Any]:
        """Generate report on what the system has learned."""
        total_weights = len(self.store._weights)
        memory_weights = [w for w in self.store._weights.values() if not w.id.startswith("skill:")]
        skill_weights = [w for w in self.store._weights.values() if w.id.startswith("skill:")]
        
        avg_success_rate = 0.0
        if memory_weights:
            avg_success_rate = sum(w.success_count / max(1, w.usage_count) for w in memory_weights) / len(memory_weights)
        
        top_memory = sorted(memory_weights, key=lambda w: -w.effective_score)[:5]
        top_skills = sorted(skill_weights, key=lambda w: -w.effective_score)[:5]
        
        return {
            "total_tracked_items": total_weights,
            "memory_items": len(memory_weights),
            "skill_items": len(skill_weights),
            "average_success_rate": round(avg_success_rate, 3),
            "top_memory_entries": [(w.id, w.effective_score) for w in top_memory],
            "top_skills": [(w.id, w.effective_score) for w in top_skills],
            "store_path": str(self.store.store_dir),
        }


# ---------------------------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------------------------

_learning_engine: Optional[MemoryLearningEngine] = None

def get_learning_engine() -> MemoryLearningEngine:
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = MemoryLearningEngine()
    return _learning_engine
