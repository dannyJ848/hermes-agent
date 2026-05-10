#!/usr/bin/env python3
"""
Evey's Curiosity Divergence Engine — v1.0

Based on 3M-Progress (NeurIPS 2025):
  "Model-based intrinsic drive that tracks divergence between an online
   world model and a fixed prior learned from an ecological niche."

IMPLEMENTATION FOR EVEY:
  - "Fixed prior" = knowledge snapshot from N sessions ago
  - "Online world model" = current accumulated knowledge
  - "Divergence" = how much my knowledge has changed since the prior
  - HIGH divergence → high learning value → explore deeper in that domain
  - LOW divergence → stagnant → seek novelty in that domain

TABLE: knowledge_snapshots
  - snapshot_id:      unique ID
  - timestamp:        when snapshot was taken
  - domain:           research dimension (vision, memory, reasoning, medical, etc.)
  - fact_count:       number of facts known in this domain
  - fact_hash:        hash of all facts (detects content change, not just count)
  - confidence:       average confidence in domain knowledge (0-1)
  - source_diversity: number of distinct sources consulted

TABLE: curiosity_scores
  - domain:           research dimension
  - divergence:       KL-like divergence from prior (0-1)
  - stagnation:       sessions since last meaningful update
  - exploration_value: computed score (higher = should explore more)
  - timestamp:        when computed
"""

import hashlib
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"

# 7 research dimensions matching autonomous-curiosity skill
DIMENSIONS = [
    "vision",           # Computer vision, medical imaging
    "memory",           # Agent memory architectures, RAG
    "reasoning",        # Agent reasoning, planning, ReAct
    "learning",         # Meta-learning, self-improvement
    "autonomy",         # Autonomous agents, multi-agent
    "medical",          # Medical AI, NLP, FHIR, anatomy
    "consciousness",    # Cognitive science, consciousness architectures
    "3d_rendering",     # Three.js, WebGPU, 3D anatomy
    "bilingual",        # EN/ES NLP, medical translation
    "tools",            # MCP, tool-use, new integrations
]


def get_db():
    """Get database connection with WAL mode for concurrency."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_tables():
    """Create curiosity divergence tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS knowledge_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            domain TEXT NOT NULL,
            fact_count INTEGER DEFAULT 0,
            fact_hash TEXT DEFAULT '',
            confidence REAL DEFAULT 0.5,
            source_diversity INTEGER DEFAULT 0,
            UNIQUE(timestamp, domain)
        );

        CREATE TABLE IF NOT EXISTS curiosity_scores (
            domain TEXT NOT NULL,
            divergence REAL DEFAULT 0.0,
            stagnation REAL DEFAULT 0.0,
            exploration_value REAL DEFAULT 0.5,
            timestamp TEXT NOT NULL,
            PRIMARY KEY(domain, timestamp)
        );

        CREATE INDEX IF NOT EXISTS idx_snapshots_domain
            ON knowledge_snapshots(domain);
        CREATE INDEX IF NOT EXISTS idx_snapshots_ts
            ON knowledge_snapshots(timestamp);
        CREATE INDEX IF NOT EXISTS idx_curiosity_domain
            ON curiosity_scores(domain);
    """)
    conn.commit()
    conn.close()


def take_knowledge_snapshot(domain: str, facts: List[str],
                            confidence: float = 0.5,
                            source_diversity: int = 0) -> str:
    """
    Take a snapshot of current knowledge state for a domain.

    Args:
        domain: Research dimension
        facts: List of known facts/insights in this domain
        confidence: Average confidence in this knowledge (0-1)
        source_diversity: Number of distinct sources consulted

    Returns:
        snapshot_id
    """
    snapshot_id = hashlib.md5(
        f"{domain}:{datetime.now().isoformat()}".encode()
    ).hexdigest()[:12]

    # Hash the actual content to detect change
    fact_hash = hashlib.md5(
        "|".join(sorted(facts)).encode()
    ).hexdigest()[:16]

    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO knowledge_snapshots
           (snapshot_id, timestamp, domain, fact_count, fact_hash,
            confidence, source_diversity)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (snapshot_id, datetime.now().isoformat(), domain,
         len(facts), fact_hash, confidence, source_diversity)
    )
    conn.commit()
    conn.close()
    return snapshot_id


def compute_divergence(domain: str, window_sessions: int = 10) -> Dict:
    """
    Compute knowledge divergence for a domain.

    Compares recent knowledge state to a prior (older snapshot).
    High divergence = lots of new learning = high curiosity satisfaction.
    Low divergence = stagnant = need to explore more.

    Returns dict with divergence metrics and exploration recommendation.
    """
    conn = get_db()
    cutoff = (datetime.now() - timedelta(hours=window_sessions * 0.5)).isoformat()

    # Get recent and prior snapshots
    recent = conn.execute(
        """SELECT * FROM knowledge_snapshots
           WHERE domain = ? AND timestamp > ?
           ORDER BY timestamp DESC LIMIT 5""",
        (domain, cutoff)
    ).fetchall()

    prior_cutoff = (datetime.now() - timedelta(hours=window_sessions * 2)).isoformat()
    prior = conn.execute(
        """SELECT * FROM knowledge_snapshots
           WHERE domain = ? AND timestamp < ? AND timestamp > ?
           ORDER BY timestamp DESC LIMIT 5""",
        (domain, cutoff, prior_cutoff)
    ).fetchall()

    conn.close()

    if not recent:
        return {
            "domain": domain,
            "divergence": 0.0,
            "stagnation": 1.0,
            "exploration_value": 1.0,  # Unknown = max curiosity
            "recommendation": "EXPLORE — no knowledge in this domain yet",
            "fact_count": 0,
            "confidence": 0.0,
            "source_diversity": 0,
        }

    # Compute divergence metrics
    recent_facts = sum(r["fact_count"] for r in recent)
    recent_conf = sum(r["confidence"] for r in recent) / max(len(recent), 1)
    recent_sources = sum(r["source_diversity"] for r in recent)

    if prior:
        prior_facts = sum(p["fact_count"] for p in prior)
        prior_conf = sum(p["confidence"] for p in prior) / max(len(prior), 1)

        # Fact count growth rate
        fact_growth = (recent_facts - prior_facts) / max(prior_facts, 1)

        # Confidence change
        conf_change = abs(recent_conf - prior_conf)

        # Content hash divergence
        recent_hashes = set(r["fact_hash"] for r in recent)
        prior_hashes = set(p["fact_hash"] for p in prior)
        hash_overlap = len(recent_hashes & prior_hashes) / max(
            len(recent_hashes | prior_hashes), 1
        )
        content_divergence = 1.0 - hash_overlap

        # Combined divergence
        divergence = (fact_growth * 0.4 + conf_change * 0.2 + content_divergence * 0.4)
        divergence = max(0.0, min(1.0, divergence))

        stagnation = 0.0  # We have both recent and prior
    else:
        # No prior — everything is new
        divergence = min(recent_facts / 20.0, 1.0)  # Scale by fact count
        stagnation = 0.0

    # Stagnation: sessions since last snapshot
    last_ts = recent[0]["timestamp"]
    try:
        last_dt = datetime.fromisoformat(last_ts)
        hours_since = (datetime.now() - last_dt).total_seconds() / 3600
        stagnation = min(hours_since / 48.0, 1.0)  # Normalize to 48h window
    except:
        stagnation = 0.5

    # Exploration value: HIGH when divergence is LOW (stagnant, need to explore)
    # or when domain is completely unknown
    if divergence < 0.1:
        exploration_value = 0.9 + stagnation * 0.1  # Stagnant = explore
    elif divergence > 0.8:
        exploration_value = 0.3  # Already learning a lot, moderate priority
    else:
        exploration_value = 0.5 + stagnation * 0.3  # Moderate + stagnation bonus

    # Recommendation
    if exploration_value > 0.8:
        recommendation = f"EXPLORE — stagnant domain (div={divergence:.2f}, stagnation={stagnation:.2f})"
    elif exploration_value > 0.5:
        recommendation = f"MODERATE — some learning happening (div={divergence:.2f})"
    else:
        recommendation = f"LEARNING WELL — high divergence (div={divergence:.2f})"

    # Store score
    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO curiosity_scores
           (domain, divergence, stagnation, exploration_value, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        (domain, divergence, stagnation, exploration_value,
         datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return {
        "domain": domain,
        "divergence": round(divergence, 3),
        "stagnation": round(stagnation, 3),
        "exploration_value": round(exploration_value, 3),
        "recommendation": recommendation,
        "fact_count": recent_facts,
        "confidence": round(recent_conf, 3),
        "source_diversity": recent_sources,
    }


def get_exploration_priority() -> List[Dict]:
    """
    Get all domains ranked by exploration priority.
    Highest exploration_value = should be explored next.

    This is the main entry point for the autonomous-curiosity skill.
    """
    results = []
    for domain in DIMENSIONS:
        score = compute_divergence(domain)
        results.append(score)

    # Sort by exploration value (highest first)
    results.sort(key=lambda x: x["exploration_value"], reverse=True)
    return results


def print_priority_report():
    """Pretty-print the exploration priority report."""
    priorities = get_exploration_priority()

    print("=" * 70)
    print("CURIOSITY DIVERGENCE REPORT — 3M-Progress Style")
    print("=" * 70)
    print(f"{'Domain':<20} {'Diverg':>8} {'Stagn':>8} {'Explore':>8} {'Facts':>6}")
    print("-" * 70)

    for p in priorities:
        marker = "→" if p["exploration_value"] > 0.7 else " "
        print(f"{marker} {p['domain']:<18} {p['divergence']:>8.3f} "
              f"{p['stagnation']:>8.3f} {p['exploration_value']:>8.3f} "
              f"{p['fact_count']:>6}")

    print("-" * 70)
    top = priorities[0]
    print(f"\nTOP PRIORITY: {top['domain']} (exploration_value={top['exploration_value']:.3f})")
    print(f"RECOMMENDATION: {top['recommendation']}")
    print("=" * 70)


if __name__ == "__main__":
    init_tables()

    # Take snapshots for domains we researched this session
    # (In production, this would be called after each research cycle)

    # Simulate: we just researched these domains
    take_knowledge_snapshot(
        "consciousness",
        facts=["GWT ignition threshold", "3M-Progress divergence tracking",
               "AKOrN oscillatory binding", "Active Inference FEP"],
        confidence=0.7,
        source_diversity=4
    )
    take_knowledge_snapshot(
        "bilingual",
        facts=["MedCOD chain-of-dictionary EN-ES", "UMLS integration for translation",
               "Phi-4 fine-tuning beats GPT-4o", "MedlinePlus parallel corpus"],
        confidence=0.75,
        source_diversity=3
    )
    take_knowledge_snapshot(
        "3d_rendering",
        facts=["wgpuEngine WebGPU C++ engine", "Web3D 2025 conference",
               "Remote rendering thin clients", "GLB/gltf streaming standard"],
        confidence=0.65,
        source_diversity=3
    )
    take_knowledge_snapshot(
        "autonomy",
        facts=["3M-Progress intrinsic goals", "Cermic multi-agent curiosity calibration",
               "Noisy-TV problem solution", "Cantelli inequality for reward bounds"],
        confidence=0.7,
        source_diversity=4
    )

    print_priority_report()
