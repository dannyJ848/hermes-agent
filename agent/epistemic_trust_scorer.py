#!/usr/bin/env python3
"""
Epistemic Trust Scorer — v1.0
═══════════════════════════════════════════════════════════════════════════════
Scores every memory, fact, and learned pattern by its trustworthiness.

PROBLEM: Agents accumulate "facts" that are wrong, outdated, or hallucinated.
Without trust scoring, bad information poisons future reasoning.

SOLUTION: Apply the F-G-R Trust Tuple to every piece of knowledge:
  • Formation (F): How was this fact created? (direct observation, inference,
    hearsay, hallucination)
  • Grounding (G): How well is it supported by evidence? (verified, plausible,
    speculative, contradicted)
  • Recency (R): How stale is it? (fresh, aging, stale, fossil)

TRUST SCORE = weighted combination of F, G, R
  • 0.9-1.0: Gold — directly verified, recent, multiple sources
  • 0.7-0.9: Silver — plausible, single source, recent
  • 0.4-0.7: Bronze — inferred, unverified, aging
  • 0.1-0.4: Rust — speculative, old, or contradicted
  • 0.0-0.1: Toxic — hallucinated or proven false

ACTIONS:
  • Gold facts: Prioritize in context injection
  • Silver facts: Include with confidence annotation
  • Bronze facts: Include only if space permits
  • Rust facts: Suppress unless explicitly asked
  • Toxic facts: Flag for review, don't inject

INTEGRATION: Hooks into memory retrieval, skill loading, and tip injection.
Every piece of knowledge gets scored before entering the context window.

Author: Hermes Agent (self-improving)
Date: 2026-05-13
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


@dataclass
class TrustTuple:
    """The F-G-R trust tuple for a piece of knowledge."""
    formation: str   # "direct", "inferred", "hearsay", "hallucinated"
    grounding: str   # "verified", "plausible", "speculative", "contradicted"
    recency: str     # "fresh", "aging", "stale", "fossil"
    
    # Numeric scores (0.0-1.0)
    formation_score: float = 0.5
    grounding_score: float = 0.5
    recency_score: float = 0.5
    
    # Metadata
    source_count: int = 1
    verification_count: int = 0
    contradiction_count: int = 0
    last_verified: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    
    @property
    def overall_trust(self) -> float:
        """Calculate overall trust score."""
        # Weights: Grounding matters most, then formation, then recency
        weights = {
            "formation": 0.25,
            "grounding": 0.45,
            "recency": 0.30,
        }
        
        score = (
            weights["formation"] * self.formation_score +
            weights["grounding"] * self.grounding_score +
            weights["recency"] * self.recency_score
        )
        
        # Boost for multiple verifications
        if self.verification_count > 0:
            score += min(self.verification_count * 0.05, 0.15)
        
        # Penalty for contradictions
        if self.contradiction_count > 0:
            score -= min(self.contradiction_count * 0.15, 0.4)
        
        return max(0.0, min(1.0, score))
    
    @property
    def trust_tier(self) -> str:
        """Classify into trust tier."""
        score = self.overall_trust
        if score >= 0.9:
            return "gold"
        elif score >= 0.7:
            return "silver"
        elif score >= 0.4:
            return "bronze"
        elif score >= 0.1:
            return "rust"
        else:
            return "toxic"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "formation": self.formation,
            "grounding": self.grounding,
            "recency": self.recency,
            "formation_score": self.formation_score,
            "grounding_score": self.grounding_score,
            "recency_score": self.recency_score,
            "source_count": self.source_count,
            "verification_count": self.verification_count,
            "contradiction_count": self.contradiction_count,
            "last_verified": self.last_verified,
            "created_at": self.created_at,
            "overall_trust": self.overall_trust,
            "trust_tier": self.trust_tier,
        }


class EpistemicTrustScorer:
    """
    Scores knowledge by trustworthiness.
    
    Usage:
        scorer = EpistemicTrustScorer()
        
        # Score a new fact
        trust = scorer.score_fact(
            content="Python 3.12 supports PEP 695 type parameter syntax",
            formation="direct",  # I observed this directly
            sources=["python.org", "pep695"],
        )
        
        # Retrieve with trust filtering
        facts = scorer.retrieve_trusted(
            query="Python type syntax",
            min_trust=0.7,
            max_age_days=365,
        )
    """
    
    # Formation quality scores
    FORMATION_SCORES = {
        "direct": 0.95,      # I directly observed/verified this
        "inferred": 0.60,    # I reasoned to this conclusion
        "hearsay": 0.35,     # Someone told me this
        "hallucinated": 0.05, # I made this up (should be rare)
    }
    
    # Grounding quality scores
    GROUNDING_SCORES = {
        "verified": 0.95,      # Multiple independent sources confirm
        "plausible": 0.70,     # Consistent with known facts
        "speculative": 0.35,   # Possible but unconfirmed
        "contradicted": 0.05,  # Evidence against this
    }
    
    # Recency decay function
    RECENCY_HALFLIFE_DAYS = {
        "technical": 180,    # Tech facts decay in 6 months
        "factual": 365,      # General facts decay in 1 year
        "personal": 90,      # Personal prefs decay in 3 months
        "procedural": 730,   # Procedures decay in 2 years
    }
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create trust scoring tables."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS epistemic_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_hash TEXT UNIQUE,
                    content TEXT,
                    formation TEXT,
                    grounding TEXT,
                    formation_score REAL,
                    grounding_score REAL,
                    recency_score REAL,
                    source_count INTEGER,
                    verification_count INTEGER,
                    contradiction_count INTEGER,
                    last_verified REAL,
                    created_at REAL,
                    overall_trust REAL,
                    trust_tier TEXT,
                    category TEXT DEFAULT 'general',
                    sources TEXT,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_epistemic_trust 
                ON epistemic_facts(overall_trust DESC);
                CREATE INDEX IF NOT EXISTS idx_epistemic_tier 
                ON epistemic_facts(trust_tier);
                CREATE INDEX IF NOT EXISTS idx_epistemic_category 
                ON epistemic_facts(category);
                CREATE INDEX IF NOT EXISTS idx_epistemic_hash 
                ON epistemic_facts(content_hash);
                
                CREATE TABLE IF NOT EXISTS epistemic_verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact_hash TEXT,
                    verifier TEXT,
                    verification_type TEXT,
                    result TEXT,
                    confidence REAL,
                    created_at REAL,
                    FOREIGN KEY (fact_hash) REFERENCES epistemic_facts(content_hash)
                );
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("Epistemic schema init failed: %s", e)
    
    def score_fact(self, content: str, 
                   formation: str = "inferred",
                   grounding: str = "plausible",
                   sources: List[str] = None,
                   category: str = "general",
                   metadata: Dict[str, Any] = None) -> TrustTuple:
        """
        Score a fact and store it.
        
        Args:
            content: The fact content
            formation: How it was formed (direct, inferred, hearsay, hallucinated)
            grounding: How well supported (verified, plausible, speculative, contradicted)
            sources: List of source identifiers
            category: Fact category (technical, factual, personal, procedural)
            metadata: Additional metadata
            
        Returns:
            TrustTuple with full scoring
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:32]
        
        # Calculate scores
        formation_score = self.FORMATION_SCORES.get(formation, 0.5)
        grounding_score = self.GROUNDING_SCORES.get(grounding, 0.5)
        
        # Calculate recency (new facts start fresh)
        recency_score = 1.0
        
        # Adjust for source count
        source_count = len(sources) if sources else 1
        if source_count > 1:
            grounding_score += min((source_count - 1) * 0.05, 0.15)
        
        trust = TrustTuple(
            formation=formation,
            grounding=grounding,
            recency="fresh",
            formation_score=formation_score,
            grounding_score=min(grounding_score, 1.0),
            recency_score=recency_score,
            source_count=source_count,
        )
        
        # Store
        self._store_fact(content_hash, content, trust, sources, category, metadata)
        
        return trust
    
    def _store_fact(self, content_hash: str, content: str, 
                    trust: TrustTuple, sources: List[str],
                    category: str, metadata: Dict[str, Any]):
        """Store fact in database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute(
                """INSERT OR REPLACE INTO epistemic_facts
                   (content_hash, content, formation, grounding,
                    formation_score, grounding_score, recency_score,
                    source_count, verification_count, contradiction_count,
                    last_verified, created_at, overall_trust, trust_tier,
                    category, sources, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    content_hash,
                    content[:2000],
                    trust.formation,
                    trust.grounding,
                    trust.formation_score,
                    trust.grounding_score,
                    trust.recency_score,
                    trust.source_count,
                    trust.verification_count,
                    trust.contradiction_count,
                    trust.last_verified,
                    trust.created_at,
                    trust.overall_trust,
                    trust.trust_tier,
                    category,
                    json.dumps(sources or []),
                    json.dumps(metadata or {}),
                )
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug("Failed to store fact: %s", e)
    
    def verify_fact(self, content_hash: str, 
                    verifier: str = "self",
                    verification_type: str = "cross_reference",
                    result: str = "confirmed",
                    confidence: float = 0.8):
        """Record a verification event for a fact."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            
            # Record verification
            conn.execute(
                "INSERT INTO epistemic_verifications (fact_hash, verifier, verification_type, result, confidence, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (content_hash, verifier, verification_type, result, confidence, time.time())
            )
            
            # Update fact scores
            if result == "confirmed":
                conn.execute(
                    "UPDATE epistemic_facts SET verification_count = verification_count + 1, "
                    "last_verified = ?, overall_trust = MIN(overall_trust + 0.05, 1.0) "
                    "WHERE content_hash = ?",
                    (time.time(), content_hash)
                )
            elif result == "contradicted":
                conn.execute(
                    "UPDATE epistemic_facts SET contradiction_count = contradiction_count + 1, "
                    "overall_trust = MAX(overall_trust - 0.15, 0.0), trust_tier = 'rust' "
                    "WHERE content_hash = ?",
                    (content_hash,)
                )
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug("Verification failed: %s", e)
    
    def retrieve_trusted(self, query: str = "",
                         min_trust: float = 0.4,
                         max_age_days: int = 365,
                         category: str = None,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve facts filtered by trust score.
        
        Args:
            query: Optional text search
            min_trust: Minimum trust score (0.0-1.0)
            max_age_days: Maximum age in days
            category: Filter by category
            limit: Max results
            
        Returns:
            List of facts with trust metadata
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            
            cutoff_time = time.time() - (max_age_days * 86400)
            
            sql = """
                SELECT * FROM epistemic_facts
                WHERE overall_trust >= ?
                AND created_at >= ?
            """
            params = [min_trust, cutoff_time]
            
            if category:
                sql += " AND category = ?"
                params.append(category)
            
            if query:
                sql += " AND content LIKE ?"
                params.append(f"%{query}%")
            
            sql += " ORDER BY overall_trust DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return results
        except Exception as e:
            logger.debug("Retrieve failed: %s", e)
            return []
    
    def decay_old_facts(self):
        """Apply recency decay to all facts."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute("SELECT content_hash, created_at, category FROM epistemic_facts")
            
            now = time.time()
            updates = []
            
            for row in cursor.fetchall():
                age_days = (now - row["created_at"]) / 86400
                halflife = self.RECENCY_HALFLIFE_DAYS.get(row["category"], 365)
                
                # Exponential decay
                decay = 0.5 ** (age_days / halflife)
                
                # Update recency score
                updates.append((decay, row["content_hash"]))
            
            # Batch update
            conn.executemany(
                "UPDATE epistemic_facts SET recency_score = ?, overall_trust = overall_trust * 0.9 + ? * 0.1 "
                "WHERE content_hash = ?",
                [(d, d, h) for d, h in updates]
            )
            
            # Update tiers
            conn.execute("""
                UPDATE epistemic_facts SET trust_tier = CASE
                    WHEN overall_trust >= 0.9 THEN 'gold'
                    WHEN overall_trust >= 0.7 THEN 'silver'
                    WHEN overall_trust >= 0.4 THEN 'bronze'
                    WHEN overall_trust >= 0.1 THEN 'rust'
                    ELSE 'toxic'
                END
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug("Decay failed: %s", e)
    
    def get_trust_report(self) -> Dict[str, Any]:
        """Get summary statistics of trust distribution."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT trust_tier, COUNT(*) as count, AVG(overall_trust) as avg_trust
                FROM epistemic_facts GROUP BY trust_tier
            """)
            
            tiers = {}
            for row in cursor.fetchall():
                tiers[row["trust_tier"]] = {
                    "count": row["count"],
                    "avg_trust": row["avg_trust"],
                }
            
            cursor = conn.execute("SELECT COUNT(*) as total FROM epistemic_facts")
            total = cursor.fetchone()["total"]
            
            conn.close()
            
            return {
                "total_facts": total,
                "tiers": tiers,
                "healthy_ratio": sum(tiers.get(t, {}).get("count", 0) for t in ["gold", "silver"]) / max(total, 1),
            }
        except Exception as e:
            return {"error": str(e)}


# Singleton accessor
_scorer: Optional[EpistemicTrustScorer] = None


def get_trust_scorer() -> EpistemicTrustScorer:
    """Get the singleton trust scorer."""
    global _scorer
    if _scorer is None:
        _scorer = EpistemicTrustScorer()
    return _scorer
