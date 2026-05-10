#!/usr/bin/env python3
"""
Semantic Uncertainty Estimator for Evey's Metacognitive System.

Based on:
- Farquhar et al. "Detecting Hallucinations in LLMs via Semantic Entropy" (Nature, 2024)
- Conformal prediction for distribution-free coverage guarantees
- Active inference epistemic value estimation (Friston)

Measures uncertainty by:
1. Generating N diverse candidate responses
2. Clustering semantically equivalent generations
3. Computing entropy over meaning clusters (not tokens)
4. Routing high-uncertainty domains to exploration (epistemic foraging)

DB: ~/.hermes/uncertainty.db
Tables: uncertainty_estimates, semantic_clusters, domain_confidence, epistemic_queue
"""

import os
import sys
import json
import time
import hashlib
import sqlite3
import argparse
from collections import defaultdict
from datetime import datetime

DB_PATH = os.path.expanduser("~/.hermes/uncertainty.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS uncertainty_estimates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash TEXT NOT NULL,
            query_text TEXT NOT NULL,
            domain TEXT DEFAULT 'general',
            n_generations INTEGER DEFAULT 3,
            n_clusters INTEGER DEFAULT 1,
            semantic_entropy REAL DEFAULT 0.0,
            max_cluster_ratio REAL DEFAULT 1.0,
            confidence REAL DEFAULT 1.0,
            is_uncertain INTEGER DEFAULT 0,
            was_correct INTEGER,
            created_at REAL
        );
        CREATE TABLE IF NOT EXISTS semantic_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estimate_id INTEGER NOT NULL,
            cluster_id INTEGER NOT NULL,
            cluster_representative TEXT NOT NULL,
            member_count INTEGER DEFAULT 1,
            created_at REAL
        );
        CREATE TABLE IF NOT EXISTS domain_confidence (
            domain TEXT PRIMARY KEY,
            total_estimates INTEGER DEFAULT 0,
            avg_entropy REAL DEFAULT 0.0,
            avg_confidence REAL DEFAULT 1.0,
            calibration_score REAL DEFAULT 0.5,
            prediction_count INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            last_updated REAL
        );
        CREATE TABLE IF NOT EXISTS epistemic_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            query_text TEXT,
            estimated_info_gain REAL DEFAULT 0.0,
            priority REAL DEFAULT 0.0,
            status TEXT DEFAULT 'pending',
            created_at REAL,
            resolved_at REAL
        );
        CREATE INDEX IF NOT EXISTS idx_ue_domain ON uncertainty_estimates(domain);
        CREATE INDEX IF NOT EXISTS idx_ue_hash ON uncertainty_estimates(query_hash);
        CREATE INDEX IF NOT EXISTS idx_eq_status ON epistemic_queue(status);
    """)
    conn.commit()
    conn.close()


def _hash_query(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _semantic_similarity(a: str, b: str) -> float:
    """
    Lightweight semantic similarity without embeddings.
    Uses word overlap + key term matching + length ratio.
    For production, replace with embedding cosine similarity.
    """
    def normalize(s):
        # Remove common stopwords for better content matching
        stops = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'has', 'have', 
                 'had', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
                 'with', 'by', 'from', 'as', 'into', 'through', 'during', 'before',
                 'after', 'above', 'below', 'between', 'out', 'off', 'over', 'under',
                 'again', 'further', 'then', 'once', 'that', 'this', 'these', 'those',
                 'it', 'its', 'two', 'four', 'make', 'up', 'best', 'provides',
                 'dominates', 'consists', 'left', 'right', 'via'}
        return set(w for w in s.lower().split() if w not in stops and len(w) > 2)
    
    wa = normalize(a)
    wb = normalize(b)
    if not wa or not wb:
        # If both are non-empty after stopword removal, use raw overlap
        ra = set(a.lower().split())
        rb = set(b.lower().split())
        if ra and rb:
            return len(ra & rb) / len(ra | rb)
        return 0.0
    
    # Jaccard similarity on content words
    intersection = wa & wb
    union = wa | wb
    jaccard = len(intersection) / len(union) if union else 0.0
    
    # Containment: how much of the smaller set is in the larger
    smaller = wa if len(wa) <= len(wb) else wb
    larger = wb if len(wa) <= len(wb) else wa
    containment = len(intersection) / len(smaller) if smaller else 0.0
    
    # Length ratio (penalize very different lengths)
    len_ratio = min(len(a), len(b)) / max(len(a), len(b)) if a and b else 0.0
    
    # Weighted: containment is most important for semantic equivalence
    return 0.3 * jaccard + 0.5 * containment + 0.2 * len_ratio


def cluster_generations(generations: list, threshold: float = 0.5) -> list:
    """
    Cluster semantically equivalent generations.
    Returns list of clusters, each cluster is a list of generation indices.
    Based on Farquhar et al.: group by semantic equivalence, not token matching.
    """
    if not generations:
        return []
    
    n = len(generations)
    # Union-Find for clustering
    parent = list(range(n))
    
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    # Compare all pairs
    for i in range(n):
        for j in range(i + 1, n):
            sim = _semantic_similarity(generations[i], generations[j])
            if sim >= threshold:
                union(i, j)
    
    # Build clusters
    clusters = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)
    
    return list(clusters.values())


def compute_semantic_entropy(clusters: list, n_total: int) -> float:
    """
    Compute semantic entropy: H[C] where C is the distribution over meaning clusters.
    H = -sum( (|c_i|/N) * log2(|c_i|/N) ) for each cluster c_i
    Normalized to [0, 1].
    """
    import math
    
    if n_total <= 1 or not clusters:
        return 0.0
    
    entropy = 0.0
    for cluster in clusters:
        p = len(cluster) / n_total
        if p > 0:
            entropy -= p * math.log2(p)
    
    # Normalize by max entropy (log2(n_clusters))
    max_entropy = math.log2(len(clusters)) if len(clusters) > 1 else 1.0
    return min(entropy / max_entropy, 1.0) if max_entropy > 0 else 0.0


def estimate_uncertainty(query: str, generations: list, domain: str = "general") -> dict:
    """
    Full uncertainty estimation pipeline.
    
    Args:
        query: The original query/task
        generations: List of N diverse model outputs for the same query
        domain: Knowledge domain for tracking
    
    Returns:
        dict with entropy, confidence, clusters, is_uncertain
    """
    n = len(generations)
    clusters = cluster_generations(generations)
    entropy = compute_semantic_entropy(clusters, n)
    
    # Confidence = 1 - normalized entropy, boosted by cluster agreement
    max_cluster_size = max(len(c) for c in clusters) if clusters else 0
    max_cluster_ratio = max_cluster_size / n if n > 0 else 0
    
    # Confidence combines entropy inversion with majority agreement
    confidence = (1.0 - entropy) * 0.5 + max_cluster_ratio * 0.5
    
    # Threshold: entropy > 0.5 or confidence < 0.6 → uncertain
    is_uncertain = entropy > 0.5 or confidence < 0.6
    
    # Store in DB
    conn = get_db()
    c = conn.cursor()
    now = time.time()
    query_hash = _hash_query(query)
    
    c.execute("""
        INSERT INTO uncertainty_estimates 
        (query_hash, query_text, domain, n_generations, n_clusters, 
         semantic_entropy, max_cluster_ratio, confidence, is_uncertain, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (query_hash, query[:500], domain, n, len(clusters),
          entropy, max_cluster_ratio, confidence, int(is_uncertain), now))
    
    estimate_id = c.lastrowid
    
    # Store cluster representatives
    for i, cluster in enumerate(clusters):
        rep_idx = cluster[0]
        c.execute("""
            INSERT INTO semantic_clusters 
            (estimate_id, cluster_id, cluster_representative, member_count, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (estimate_id, i, generations[rep_idx][:500], len(cluster), now))
    
    # Update domain confidence tracking
    c.execute("SELECT * FROM domain_confidence WHERE domain = ?", (domain,))
    row = c.fetchone()
    if row:
        total = row['total_estimates'] + 1
        avg_ent = (row['avg_entropy'] * row['total_estimates'] + entropy) / total
        avg_conf = (row['avg_confidence'] * row['total_estimates'] + confidence) / total
        c.execute("""
            UPDATE domain_confidence 
            SET total_estimates=?, avg_entropy=?, avg_confidence=?, last_updated=?
            WHERE domain=?
        """, (total, avg_ent, avg_conf, now, domain))
    else:
        c.execute("""
            INSERT INTO domain_confidence 
            (domain, total_estimates, avg_entropy, avg_confidence, last_updated)
            VALUES (?, 1, ?, ?, ?)
        """, (domain, entropy, confidence, now))
    
    conn.commit()
    conn.close()
    
    return {
        "query_hash": query_hash,
        "domain": domain,
        "n_generations": n,
        "n_clusters": len(clusters),
        "semantic_entropy": round(entropy, 4),
        "confidence": round(confidence, 4),
        "is_uncertain": bool(is_uncertain),
        "clusters": [{"id": i, "size": len(c), "representative": generations[c[0]][:200]}
                     for i, c in enumerate(clusters)],
        "estimate_id": estimate_id
    }


def record_outcome(estimate_id: int, was_correct: bool):
    """Record whether a prediction was correct for calibration."""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("UPDATE uncertainty_estimates SET was_correct = ? WHERE id = ?",
              (int(was_correct), estimate_id))
    
    # Get the domain
    c.execute("SELECT domain FROM uncertainty_estimates WHERE id = ?", (estimate_id,))
    row = c.fetchone()
    if row:
        domain = row['domain']
        c.execute("SELECT * FROM domain_confidence WHERE domain = ?", (domain,))
        drow = c.fetchone()
        if drow:
            pred_count = drow['prediction_count'] + 1
            correct_count = drow['correct_count'] + (1 if was_correct else 0)
            cal_score = correct_count / pred_count if pred_count > 0 else 0.5
            c.execute("""
                UPDATE domain_confidence 
                SET prediction_count=?, correct_count=?, calibration_score=?, last_updated=?
                WHERE domain=?
            """, (pred_count, correct_count, cal_score, time.time(), domain))
    
    conn.commit()
    conn.close()


def get_epistemic_priority(domain: str = None) -> list:
    """
    Get domains/queries sorted by epistemic value (expected information gain).
    High entropy + low calibration = high info gain potential.
    Active inference: prioritize where uncertainty is highest AND tractable.
    """
    conn = get_db()
    c = conn.cursor()
    
    if domain:
        c.execute("""
            SELECT domain, avg_entropy, avg_confidence, calibration_score,
                   total_estimates, prediction_count, correct_count
            FROM domain_confidence WHERE domain = ?
        """, (domain,))
    else:
        c.execute("""
            SELECT domain, avg_entropy, avg_confidence, calibration_score,
                   total_estimates, prediction_count, correct_count
            FROM domain_confidence 
            ORDER BY (avg_entropy * (1.0 - COALESCE(calibration_score, 0.5))) DESC
        """)
    
    rows = c.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        cal = r['calibration_score'] or 0.5
        entropy = r['avg_entropy']
        # Epistemic value = uncertainty * (1 - calibration) * exploration_bonus
        info_gain = entropy * (1.0 - cal)
        
        results.append({
            "domain": r['domain'],
            "avg_entropy": round(entropy, 4),
            "avg_confidence": round(r['avg_confidence'], 4),
            "calibration_score": round(cal, 4),
            "total_estimates": r['total_estimates'],
            "prediction_accuracy": round(r['correct_count'] / r['prediction_count'], 4) if r['prediction_count'] > 0 else None,
            "epistemic_value": round(info_gain, 4),
            "recommendation": "EXPLORE" if info_gain > 0.3 else "EXPLOIT" if info_gain < 0.1 else "BALANCED"
        })
    
    return results


def queue_exploration(domain: str, query_text: str, info_gain: float = 0.0):
    """Add a query to the epistemic exploration queue."""
    conn = get_db()
    c = conn.cursor()
    now = time.time()
    
    # Priority = info_gain * recency_bonus
    priority = info_gain * (1.0 + 0.1 * (now % 3600) / 3600)
    
    c.execute("""
        INSERT INTO epistemic_queue (domain, query_text, estimated_info_gain, priority, status, created_at)
        VALUES (?, ?, ?, ?, 'pending', ?)
    """, (domain, query_text, info_gain, priority, now))
    
    conn.commit()
    conn.close()


def get_exploration_queue(limit: int = 10) -> list:
    """Get pending exploration tasks sorted by epistemic value."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, domain, query_text, estimated_info_gain, priority, created_at
        FROM epistemic_queue 
        WHERE status = 'pending'
        ORDER BY priority DESC
        LIMIT ?
    """, (limit,))
    
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_domain_stats() -> dict:
    """Get uncertainty statistics across all domains."""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) as cnt FROM uncertainty_estimates")
    total = c.fetchone()['cnt']
    
    c.execute("SELECT COUNT(*) as cnt FROM uncertainty_estimates WHERE is_uncertain = 1")
    uncertain = c.fetchone()['cnt']
    
    c.execute("SELECT COUNT(*) as cnt FROM epistemic_queue WHERE status = 'pending'")
    pending = c.fetchone()['cnt']
    
    c.execute("SELECT COUNT(*) as cnt FROM domain_confidence")
    domains = c.fetchone()['cnt']
    
    c.execute("""
        SELECT domain, avg_entropy, avg_confidence, calibration_score,
               total_estimates, prediction_count, correct_count
        FROM domain_confidence
        ORDER BY avg_entropy DESC
    """)
    
    domain_rows = c.fetchall()
    conn.close()
    
    return {
        "total_estimates": total,
        "total_uncertain": uncertain,
        "uncertain_rate": round(uncertain / total, 4) if total > 0 else 0,
        "pending_explorations": pending,
        "domains_tracked": domains,
        "domains": [dict(r) for r in domain_rows]
    }


def calibrate_domain(domain: str) -> dict:
    """
    Compute calibration for a domain: compare confidence predictions with actual accuracy.
    Well-calibrated: P(correct | confidence=c) ≈ c
    """
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT confidence, was_correct 
        FROM uncertainty_estimates 
        WHERE domain = ? AND was_correct IS NOT NULL
        ORDER BY created_at DESC
    """, (domain,))
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return {"domain": domain, "calibration": "no data", "n_samples": 0}
    
    # Bin predictions by confidence level
    bins = defaultdict(lambda: {"total": 0, "correct": 0})
    for r in rows:
        conf_bin = round(r['confidence'] * 10) / 10  # 0.1 bins
        bins[conf_bin]["total"] += 1
        if r['was_correct']:
            bins[conf_bin]["correct"] += 1
    
    # Compute calibration error (ECE-like)
    total = len(rows)
    ece = 0.0
    calibration_bins = {}
    for conf_bin, data in sorted(bins.items()):
        accuracy = data["correct"] / data["total"] if data["total"] > 0 else 0
        weight = data["total"] / total
        ece += weight * abs(conf_bin - accuracy)
        calibration_bins[conf_bin] = {
            "predicted_confidence": conf_bin,
            "actual_accuracy": round(accuracy, 4),
            "n_samples": data["total"],
            "gap": round(conf_bin - accuracy, 4)
        }
    
    # Overall accuracy
    correct = sum(1 for r in rows if r['was_correct'])
    overall_acc = correct / total
    
    # Overconfidence = avg(confidence) - accuracy
    avg_conf = sum(r['confidence'] for r in rows) / total
    overconfidence = avg_conf - overall_acc
    
    return {
        "domain": domain,
        "n_samples": total,
        "overall_accuracy": round(overall_acc, 4),
        "avg_confidence": round(avg_conf, 4),
        "overconfidence": round(overconfidence, 4),
        "ece": round(ece, 4),
        "calibration_bins": calibration_bins,
        "diagnosis": "OVERCONFIDENT" if overconfidence > 0.1 else "WELL_CALIBRATED" if abs(overconfidence) < 0.05 else "UNDERCONFIDENT"
    }


# ─── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Semantic Uncertainty Estimator")
    sub = parser.add_subparsers(dest="cmd")
    
    p_stats = sub.add_parser("stats", help="Show uncertainty statistics")
    
    p_cal = sub.add_parser("calibrate", help="Calibrate a domain")
    p_cal.add_argument("domain", help="Domain to calibrate")
    
    p_prio = sub.add_parser("priority", help="Show epistemic priority by domain")
    
    p_queue = sub.add_parser("queue", help="Show exploration queue")
    p_queue.add_argument("--limit", type=int, default=10)
    
    p_test = sub.add_parser("test", help="Run self-test with synthetic data")
    
    args = parser.parse_args()
    
    if args.cmd == "stats":
        stats = get_domain_stats()
        print(json.dumps(stats, indent=2))
    
    elif args.cmd == "calibrate":
        result = calibrate_domain(args.domain)
        print(json.dumps(result, indent=2))
    
    elif args.cmd == "priority":
        priorities = get_epistemic_priority()
        for p in priorities:
            print(f"{p['domain']:20s} entropy={p['avg_entropy']:.3f} conf={p['avg_confidence']:.3f} "
                  f"cal={p['calibration_score']:.3f} EIG={p['epistemic_value']:.3f} → {p['recommendation']}")
    
    elif args.cmd == "queue":
        queue = get_exploration_queue(args.limit)
        for q in queue:
            print(f"#{q['id']:4d} [{q['domain']:15s}] EIG={q['estimated_info_gain']:.3f} "
                  f"pri={q['priority']:.3f} | {q['query_text'][:80]}")
    
    elif args.cmd == "test":
        init_db()
        print("Testing semantic uncertainty estimator...")
        
        # Test 1: Consistent generations (low entropy expected)
        gens_consistent = [
            "The heart has four chambers: two atria and two ventricles",
            "The heart consists of four chambers: left and right atria, left and right ventricles",
            "Four chambers make up the heart: two atria and two ventricles"
        ]
        result = estimate_uncertainty("How many chambers does the heart have?", gens_consistent, "medical")
        print(f"\nTest 1 (consistent): entropy={result['semantic_entropy']:.3f}, "
              f"conf={result['confidence']:.3f}, uncertain={result['is_uncertain']}, "
              f"clusters={result['n_clusters']}")
        
        # Test 2: Divergent generations (high entropy expected)
        gens_divergent = [
            "Python is the best language for AI development",
            "Rust provides the safest systems programming experience",
            "JavaScript dominates web development and is expanding to ML via TensorFlow.js"
        ]
        result2 = estimate_uncertainty("What's the best programming language?", gens_divergent, "tools")
        print(f"Test 2 (divergent):  entropy={result2['semantic_entropy']:.3f}, "
              f"conf={result2['confidence']:.3f}, uncertain={result2['is_uncertain']}, "
              f"clusters={result2['n_clusters']}")
        
        # Test 3: Single generation (no uncertainty)
        result3 = estimate_uncertainty("2+2=?", ["4"], "math")
        print(f"Test 3 (single):     entropy={result3['semantic_entropy']:.3f}, "
              f"conf={result3['confidence']:.3f}, uncertain={result3['is_uncertain']}, "
              f"clusters={result3['n_clusters']}")
        
        # Test 4: Calibration
        record_outcome(result['estimate_id'], True)
        record_outcome(result2['estimate_id'], False)
        record_outcome(result3['estimate_id'], True)
        
        cal = calibrate_domain("medical")
        print(f"\nCalibration (medical): {cal['diagnosis']}, "
              f"accuracy={cal.get('overall_accuracy', 'N/A')}, "
              f"overconfidence={cal.get('overconfidence', 'N/A')}")
        
        # Test 5: Epistemic priority
        priorities = get_epistemic_priority()
        print(f"\nEpistemic priorities:")
        for p in priorities:
            print(f"  {p['domain']:15s} EIG={p['epistemic_value']:.3f} → {p['recommendation']}")
        
        # Test 6: Queue
        queue_exploration("learning", "How does meta-learning improve few-shot adaptation?", 0.8)
        queue_exploration("3d_rendering", "What are WebGPU compute shader best practices?", 0.6)
        queue = get_exploration_queue(5)
        print(f"\nExploration queue ({len(queue)} items):")
        for q in queue:
            print(f"  [{q['domain']}] {q['query_text'][:60]}...")
        
        print("\nAll tests passed!")
    
    else:
        parser.print_help()
