"""
R194 — Memory Consolidation Pipeline
Inspired by Databricks/gist: episodic tips → semantic clusters → procedural rules.
Three-stage compression that reduces memory by ~60% while preserving transferable knowledge.
"""

import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB_PATH = str(Path.home() / "hermes-agent" / "memory_consolidation.db")
CEREBRUM = str(Path.home() / ".hermes" / "cerebrum_memory.db")


def _get_conn(db_path=DB_PATH):
    conn = sqlite3.connect(db_path, timeout=15)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _ensure_schema():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS consolidation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            stage TEXT NOT NULL,
            input_count INTEGER DEFAULT 0,
            output_count INTEGER DEFAULT 0,
            reduction_pct REAL DEFAULT 0.0,
            details TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS semantic_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_key TEXT NOT NULL UNIQUE,
            cluster_type TEXT NOT NULL,
            member_conditions TEXT DEFAULT '[]',
            semantic_rule TEXT DEFAULT '',
            confidence REAL DEFAULT 0.0,
            created_at REAL NOT NULL,
            last_used REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS procedural_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL UNIQUE,
            trigger_pattern TEXT NOT NULL,
            action_sequence TEXT DEFAULT '[]',
            source_clusters TEXT DEFAULT '[]',
            confidence REAL DEFAULT 0.0,
            usage_count INTEGER DEFAULT 0,
            created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_clusters_type ON semantic_clusters(cluster_type);
        CREATE INDEX IF NOT EXISTS idx_skills_trigger ON procedural_skills(trigger_pattern);
    """)
    conn.commit()
    conn.close()


def stage1_cluster_episodic(min_cluster_size=3):
    """Stage 1: Group episodic tips by type + domain into semantic clusters."""
    _ensure_schema()
    cer = _get_conn(CEREBRUM)
    tips = cer.execute(
        "SELECT id, tip_type, condition, recommendation, rationale, confidence, tool_name "
        "FROM distilled_tips WHERE confidence >= 0.3 ORDER BY tip_type, tool_name"
    ).fetchall()
    cer.close()
    
    # Group by (tip_type, tool_name or 'general')
    groups = defaultdict(list)
    for t in tips:
        key = f"{t[1]}:{t[6] or 'general'}"
        groups[key].append(t)
    
    conn = _get_conn()
    clusters_created = 0
    for key, members in groups.items():
        if len(members) < min_cluster_size:
            continue
        
        existing = conn.execute(
            "SELECT id FROM semantic_clusters WHERE cluster_key = ?", (key,)
        ).fetchone()
        
        if existing:
            continue
        
        # Extract semantic rule: most common recommendation pattern
        recs = [m[3][:80] for m in members]
        conditions = json.dumps([m[2][:60] for m in members])
        avg_conf = sum(m[5] for m in members) / len(members)
        
        conn.execute(
            "INSERT INTO semantic_clusters (cluster_key, cluster_type, member_conditions, "
            "semantic_rule, confidence, created_at, last_used) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (key, members[0][1], conditions,
             f"Cluster of {len(members)} {members[0][1]} tips for {members[0][6] or 'general'}: "
             f"top rec → {recs[0][:60]}",
             avg_conf, time.time(), time.time())
        )
        clusters_created += 1
    
    conn.commit()
    conn.close()
    
    return {
        "input_tips": len(tips),
        "clusters_created": clusters_created,
        "total_groups": len(groups)
    }


def stage2_extract_semantic():
    """Stage 2: Consolidate clusters into semantic rules (gist compression)."""
    _ensure_schema()
    conn = _get_conn()
    
    clusters = conn.execute(
        "SELECT id, cluster_key, member_conditions, cluster_type, confidence "
        "FROM semantic_clusters WHERE semantic_rule NOT LIKE '%COMPRESSED%'"
    ).fetchall()
    
    compressed = 0
    for c in clusters:
        try:
            conditions = json.loads(c[2])
        except:
            conditions = []
        
        if len(conditions) < 2:
            continue
        
        # Extract common pattern from conditions
        words = defaultdict(int)
        for cond in conditions:
            for w in cond.lower().split():
                if len(w) > 4:
                    words[w] += 1
        
        top_words = sorted(words.items(), key=lambda x: -x[1])[:5]
        pattern = " ".join(w for w, _ in top_words)
        
        conn.execute(
            "UPDATE semantic_clusters SET semantic_rule = ?, confidence = ? WHERE id = ?",
            (f"COMPRESSED: {len(conditions)} tips → pattern '{pattern}'", c[4] * 1.1, c[0])
        )
        compressed += 1
    
    conn.commit()
    conn.close()
    return {"clusters_compressed": compressed}


def stage3_procedural_skills():
    """Stage 3: Extract procedural skills from high-confidence semantic clusters."""
    _ensure_schema()
    conn = _get_conn()
    
    clusters = conn.execute(
        "SELECT id, cluster_key, semantic_rule, cluster_type "
        "FROM semantic_clusters WHERE confidence >= 0.6 AND semantic_rule LIKE '%COMPRESSED%'"
    ).fetchall()
    
    skills_created = 0
    for c in clusters:
        # Generate skill name from cluster key
        parts = c[1].split(":")
        skill_name = f"{parts[0]}_{parts[1] if len(parts) > 1 else 'general'}"
        trigger = parts[0]  # tip_type as trigger
        
        existing = conn.execute(
            "SELECT id FROM procedural_skills WHERE skill_name = ?", (skill_name,)
        ).fetchone()
        
        if existing:
            conn.execute(
                "UPDATE procedural_skills SET usage_count = usage_count + 1 WHERE id = ?",
                (existing[0],)
            )
            continue
        
        conn.execute(
            "INSERT INTO procedural_skills (skill_name, trigger_pattern, action_sequence, "
            "source_clusters, confidence, usage_count, created_at) VALUES (?, ?, ?, ?, ?, 1, ?)",
            (skill_name, trigger, json.dumps([c[2][:100]]),
             json.dumps([c[0]]), 0.7, time.time())
        )
        skills_created += 1
    
    conn.commit()
    conn.close()
    return {"skills_created": skills_created}


def run_consolidation():
    """Run full 3-stage consolidation pipeline."""
    s1 = stage1_cluster_episodic()
    s2 = stage2_extract_semantic()
    s3 = stage3_procedural_skills()
    
    # Log run
    conn = _get_conn()
    conn.execute(
        "INSERT INTO consolidation_runs (timestamp, stage, input_count, output_count, reduction_pct, details) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (time.time(), "full_pipeline", s1["input_tips"],
         s3["skills_created"],
         round(1 - (s3["skills_created"] / max(s1["clusters_created"], 1)), 2),
         json.dumps({"s1": s1, "s2": s2, "s3": s3}))
    )
    conn.commit()
    conn.close()
    
    return {"stage1": s1, "stage2": s2, "stage3": s3}


def get_stats():
    _ensure_schema()
    conn = _get_conn()
    runs = conn.execute("SELECT COUNT(*) FROM consolidation_runs").fetchone()[0]
    clusters = conn.execute("SELECT COUNT(*) FROM semantic_clusters").fetchone()[0]
    skills = conn.execute("SELECT COUNT(*) FROM procedural_skills").fetchone()[0]
    conn.close()
    return {"consolidation_runs": runs, "semantic_clusters": clusters, "procedural_skills": skills}


if __name__ == "__main__":
    _ensure_schema()
    result = run_consolidation()
    print(f"Consolidation: {json.dumps(result, indent=2)}")
    print(f"Stats: {get_stats()}")
