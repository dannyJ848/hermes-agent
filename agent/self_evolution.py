"""
Self-Evolution Pipeline — Continuous Agent Improvement

This module provides the self-evolution capabilities for Hermes Agent:
  1. Elo Tournament — competitive evaluation of tips/skills
  2. Tip Evolution — mutation and selection of behavioral tips
  3. Auto-Distillation — automatic extraction of tips from experiences
  4. Reflection Engine — post-session analysis and learning
  5. Hindsight Engine — learning from completed tasks

Usage:
    from agent.self_evolution import SelfEvolutionPipeline
    pipeline = SelfEvolutionPipeline()
    pipeline.run_cycle()  # Run one evolution cycle
"""

import hashlib
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / ".hermes" / "distillation_buffer.db"


class SelfEvolutionPipeline:
    """
    Continuous self-improvement pipeline.
    
    Runs evolution cycles that:
      1. Extract tips from recent experiences
      2. Run Elo tournaments to evaluate tips
      3. Mutate and evolve high-performing tips
      4. Distill into skills for long-term memory
    """
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_tables()
        
    def _ensure_tables(self):
        """Create evolution tables if they don't exist."""
        conn = sqlite3.connect(str(self.db_path))
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tip_id TEXT UNIQUE NOT NULL,
                tip_text TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                source TEXT DEFAULT 'auto_distillation',
                elo_score REAL DEFAULT 1500,
                survival_count INTEGER DEFAULT 0,
                rejection_count INTEGER DEFAULT 0,
                application_count INTEGER DEFAULT 0,
                created_at REAL DEFAULT 0,
                last_applied REAL DEFAULT 0,
                parent_id TEXT,
                generation INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS tip_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tip_a_id TEXT NOT NULL,
                tip_b_id TEXT NOT NULL,
                winner TEXT,
                context TEXT,
                judged_at REAL DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                summary TEXT,
                lessons TEXT,
                metrics TEXT,
                created_at REAL DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS hindsight (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                task_description TEXT,
                approach TEXT,
                result TEXT,
                what_worked TEXT,
                what_failed TEXT,
                would_do_differently TEXT,
                created_at REAL DEFAULT 0
            );
            
            CREATE INDEX IF NOT EXISTS idx_tips_elo ON tips(elo_score);
            CREATE INDEX IF NOT EXISTS idx_tips_category ON tips(category);
            CREATE INDEX IF NOT EXISTS idx_tips_survival ON tips(survival_count);
        """)
        conn.commit()
        conn.close()
    
    # ── ELO TOURNAMENT ──
    
    def run_elo_tournament(self, tip_ids: Optional[List[str]] = None, 
                          num_matches: int = 10) -> Dict:
        """
        Run Elo tournament between tips.
        
        If tip_ids not provided, selects top 20 tips by Elo for tournament.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        if not tip_ids:
            # Select top 20 tips
            rows = conn.execute(
                "SELECT tip_id, tip_text, elo_score FROM tips ORDER BY elo_score DESC LIMIT 20"
            ).fetchall()
            tip_ids = [r["tip_id"] for r in rows]
        
        if len(tip_ids) < 2:
            conn.close()
            return {"error": "Need at least 2 tips for tournament"}
        
        import random
        tips_data = {}
        for tid in tip_ids:
            row = conn.execute(
                "SELECT tip_id, tip_text, elo_score FROM tips WHERE tip_id = ?",
                (tid,)
            ).fetchone()
            if row:
                tips_data[tid] = dict(row)
        
        matches_played = 0
        for _ in range(num_matches):
            # Pick two random tips
            a, b = random.sample(list(tips_data.keys()), 2)
            
            # Judge which tip is better (simplified: higher Elo wins 60% of time)
            elo_a = tips_data[a]["elo_score"]
            elo_b = tips_data[b]["elo_score"]
            
            # Expected score
            expected_a = 1 / (1 + 10 ** ((elo_b - elo_a) / 400))
            
            # Simulate match result
            if random.random() < expected_a:
                winner = a
                score_a, score_b = 1, 0
            else:
                winner = b
                score_a, score_b = 0, 1
            
            # Update Elo ratings
            k = 32
            new_a = elo_a + k * (score_a - expected_a)
            new_b = elo_b + k * (score_b - (1 - expected_a))
            
            tips_data[a]["elo_score"] = new_a
            tips_data[b]["elo_score"] = new_b
            
            # Record match
            conn.execute(
                "INSERT INTO tip_matches (tip_a_id, tip_b_id, winner, judged_at) VALUES (?, ?, ?, ?)",
                (a, b, winner, time.time())
            )
            matches_played += 1
        
        # Update database with new Elo scores
        for tid, data in tips_data.items():
            conn.execute(
                "UPDATE tips SET elo_score = ? WHERE tip_id = ?",
                (data["elo_score"], tid)
            )
        
        conn.commit()
        conn.close()
        
        return {
            "matches_played": matches_played,
            "tips_evaluated": len(tips_data),
            "top_tip": max(tips_data.items(), key=lambda x: x[1]["elo_score"])[0] if tips_data else None,
        }
    
    def _update_elo(self, tip_a_id: str, tip_b_id: str, winner: str) -> None:
        """Update Elo ratings after a match."""
        conn = sqlite3.connect(str(self.db_path))
        
        # Get current ratings
        row_a = conn.execute("SELECT elo_score FROM tips WHERE tip_id = ?", (tip_a_id,)).fetchone()
        row_b = conn.execute("SELECT elo_score FROM tips WHERE tip_id = ?", (tip_b_id,)).fetchone()
        
        if not row_a or not row_b:
            conn.close()
            return
        
        elo_a, elo_b = row_a[0], row_b[0]
        
        # Expected scores
        expected_a = 1 / (1 + 10 ** ((elo_b - elo_a) / 400))
        
        # Actual scores
        if winner == tip_a_id:
            score_a, score_b = 1, 0
        elif winner == tip_b_id:
            score_a, score_b = 0, 1
        else:
            score_a, score_b = 0.5, 0.5
        
        # Update ratings
        k = 32
        new_a = elo_a + k * (score_a - expected_a)
        new_b = elo_b + k * (score_b - (1 - expected_a))
        
        conn.execute("UPDATE tips SET elo_score = ? WHERE tip_id = ?", (new_a, tip_a_id))
        conn.execute("UPDATE tips SET elo_score = ? WHERE tip_id = ?", (new_b, tip_b_id))
        conn.commit()
        conn.close()
    
    # ── TIP EVOLUTION ──
    
    def evolve_tips(self, num_mutations: int = 5) -> List[Dict]:
        """
        Evolve high-performing tips by mutation.
        
        Selects top tips, creates variations, and adds them to the pool.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        # Get top tips
        top = conn.execute(
            "SELECT * FROM tips WHERE elo_score > 1600 ORDER BY elo_score DESC LIMIT 10"
        ).fetchall()
        
        new_tips = []
        for parent in top[:num_mutations]:
            # Create mutation
            mutated_text = self._mutate_tip(parent["tip_text"])
            
            if mutated_text and mutated_text != parent["tip_text"]:
                tip_id = hashlib.sha256(mutated_text.encode()).hexdigest()[:16]
                
                conn.execute(
                    """INSERT OR IGNORE INTO tips 
                       (tip_id, tip_text, category, source, elo_score, parent_id, generation, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (tip_id, mutated_text, parent["category"], "evolution",
                     1500, parent["tip_id"], parent["generation"] + 1, time.time())
                )
                
                new_tips.append({
                    "tip_id": tip_id,
                    "text": mutated_text[:100],
                    "parent": parent["tip_id"],
                    "elo": 1500,
                })
        
        conn.commit()
        conn.close()
        
        return new_tips
    
    def _mutate_tip(self, tip_text: str) -> str:
        """Create a variation of a tip."""
        import random
        
        mutations = [
            lambda t: t.replace("always", "usually"),
            lambda t: t.replace("never", "avoid"),
            lambda t: f"When possible, {t[0].lower()}{t[1:]}",
            lambda t: f"Priority: {t}",
            lambda t: t + " (verified)",
            lambda t: t.replace("use", "prefer"),
        ]
        
        if random.random() < 0.3:
            # Apply random mutation
            mutator = random.choice(mutations)
            return mutator(tip_text)
        
        return tip_text
    
    # ── AUTO-DISTILLATION ──
    
    def distill_from_experiences(self, limit: int = 50) -> List[Dict]:
        """
        Extract tips from recent experiences in cerebrum_memory.db.
        """
        cerebrum_path = Path.home() / ".hermes" / "cerebrum_memory.db"
        if not cerebrum_path.exists():
            return []
        
        conn = sqlite3.connect(str(cerebrum_path))
        conn.row_factory = sqlite3.Row
        
        # Get recent experiences with lessons
        experiences = conn.execute(
            """SELECT action_type, lesson, approach, result, error_pattern, frequency
               FROM experiences 
               WHERE lesson != '' AND result = 'success' AND frequency >= 2
               ORDER BY last_seen DESC LIMIT ?""",
            (limit,)
        ).fetchall()
        
        conn.close()
        
        distilled = []
        for exp in experiences:
            tip_text = exp["lesson"]
            if not tip_text or len(tip_text) < 20:
                continue
            
            # Check if already exists
            tip_id = hashlib.sha256(tip_text.encode()).hexdigest()[:16]
            
            conn2 = sqlite3.connect(str(self.db_path))
            existing = conn2.execute(
                "SELECT tip_id FROM tips WHERE tip_id = ?", (tip_id,)
            ).fetchone()
            
            if not existing:
                conn2.execute(
                    """INSERT INTO tips 
                       (tip_id, tip_text, category, source, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (tip_id, tip_text, exp["action_type"], "auto_distillation", time.time())
                )
                distilled.append({
                    "tip_id": tip_id,
                    "text": tip_text[:100],
                    "category": exp["action_type"],
                })
            
            conn2.commit()
            conn2.close()
        
        return distilled
    
    # ── REFLECTION ENGINE ──
    
    def reflect_on_session(self, session_id: str, actions: List[Dict],
                          errors: List[str], duration_ms: int) -> Dict:
        """
        Generate reflection on a completed session.
        """
        # Analyze patterns
        success_count = sum(1 for a in actions if a.get("result") == "success")
        failure_count = sum(1 for a in actions if a.get("result") == "failure")
        
        # Extract lessons
        lessons = []
        for a in actions:
            if a.get("lesson"):
                lessons.append(a["lesson"])
        
        # Top errors
        error_counts = {}
        for e in errors:
            ep = e[:50]  # Truncate
            error_counts[ep] = error_counts.get(ep, 0) + 1
        top_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        reflection = {
            "session_id": session_id,
            "total_actions": len(actions),
            "success_rate": success_count / len(actions) if actions else 0,
            "top_lessons": lessons[:5],
            "top_errors": top_errors,
            "duration_ms": duration_ms,
            "timestamp": time.time(),
        }
        
        # Store in DB
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """INSERT INTO reflections (session_id, summary, lessons, metrics, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id,
             f"{success_count}/{len(actions)} successful",
             json.dumps(lessons[:10]),
             json.dumps(reflection),
             time.time())
        )
        conn.commit()
        conn.close()
        
        return reflection
    
    # ── HINDSIGHT ENGINE ──
    
    def record_hindsight(self, task_id: str, task_description: str,
                        approach: str, result: str,
                        what_worked: str, what_failed: str,
                        would_do_differently: str) -> Dict:
        """
        Record hindsight on a completed task for future reference.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """INSERT INTO hindsight 
               (task_id, task_description, approach, result, 
                what_worked, what_failed, would_do_differently, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, task_description, approach, result,
             what_worked, what_failed, would_do_differently, time.time())
        )
        conn.commit()
        conn.close()
        
        return {
            "task_id": task_id,
            "recorded": True,
            "timestamp": time.time(),
        }
    
    def get_hindsight_for_task(self, task_description: str) -> List[Dict]:
        """
        Retrieve relevant hindsight for a similar task.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        # Simple keyword matching
        keywords = task_description.lower().split()
        
        rows = conn.execute(
            "SELECT * FROM hindsight ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        
        matches = []
        for row in rows:
            desc = row["task_description"].lower()
            score = sum(1 for kw in keywords if kw in desc)
            if score >= 2:  # At least 2 keyword matches
                matches.append({
                    "score": score,
                    "task": row["task_description"],
                    "approach": row["approach"],
                    "result": row["result"],
                    "what_worked": row["what_worked"],
                    "would_do_differently": row["would_do_differently"],
                })
        
        conn.close()
        
        # Sort by relevance
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:5]
    
    # ── FULL CYCLE ──
    
    def run_cycle(self) -> Dict:
        """
        Run one complete evolution cycle:
          1. Distill tips from experiences
          2. Run Elo tournament
          3. Evolve top tips
          4. Graduate high-performing tips to skills
        """
        logger.info("Running self-evolution cycle...")
        
        # Step 1: Distill
        distilled = self.distill_from_experiences(limit=50)
        logger.info(f"  Distilled {len(distilled)} new tips from experiences")
        
        # Step 2: Tournament
        tournament = self.run_elo_tournament(num_matches=20)
        logger.info(f"  Tournament: {tournament.get('matches_played', 0)} matches played")
        
        # Step 3: Evolution
        evolved = self.evolve_tips(num_mutations=5)
        logger.info(f"  Evolution: {len(evolved)} new tip mutations")
        
        # Step 4: Skill Graduation — promote top tips to skills
        graduated = self._graduate_tips_to_skills()
        logger.info(f"  Skill graduation: {graduated} tips promoted to skills")
        
        return {
            "distilled": len(distilled),
            "tournament_matches": tournament.get("matches_played", 0),
            "evolved": len(evolved),
            "graduated": graduated,
            "top_tip": tournament.get("top_tip"),
        }
    
    def _graduate_tips_to_skills(self, min_elo: int = 1800, min_survival: int = 5) -> int:
        """
        Promote high-performing tips to skills in ~/.hermes/skills/.
        
        Criteria:
          - Elo >= min_elo (default 1800)
          - survival_count >= min_survival (default 5)
          - Not already graduated (no matching skill exists)
        
        Returns: number of tips graduated to skills.
        """
        import re
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        # Find qualifying tips
        rows = conn.execute(
            "SELECT tip_id, tip_text, category, elo_score, survival_count, application_count "
            "FROM tips WHERE elo_score >= ? AND survival_count >= ? AND application_count >= 3 "
            "ORDER BY elo_score DESC",
            (min_elo, min_survival)
        ).fetchall()
        
        graduated = 0
        skills_dir = Path.home() / ".hermes" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        
        for row in rows:
            tip_id = row["tip_id"]
            tip_text = row["tip_text"]
            category = row["category"] or "general"
            
            # Derive skill name from tip content
            # Use first 5 words, lowercase, hyphenated
            words = re.sub(r'[^\w\s]', '', tip_text).lower().split()[:5]
            skill_name = "-".join(words) if words else f"tip-{tip_id[:8]}"
            # Ensure valid filename
            skill_name = re.sub(r'[^a-z0-9-]', '-', skill_name).strip('-')
            skill_name = re.sub(r'-+', '-', skill_name)
            if len(skill_name) > 64:
                skill_name = skill_name[:64]
            
            skill_path = skills_dir / f"{skill_name}.md"
            if skill_path.exists():
                continue  # Already graduated
            
            # Write skill file
            skill_content = f"""---
name: {skill_name}
category: {category}
source: auto-graduated (tip {tip_id})
elo: {row['elo_score']:.0f}
survival: {row['survival_count']}
applications: {row['application_count']}
created: {datetime.now().isoformat()}
---

# {skill_name}

{tip_text}

## When to Use

This skill was automatically graduated from a high-performing tip (Elo {row['elo_score']:.0f}, {row['survival_count']} survivals, {row['application_count']} applications).

Apply when:
- The situation matches the tip's context
- You need the specific capability described
- No more specific skill covers the need

## Verification

After using this skill, verify the outcome matches expectations. If it fails, the tip's Elo will adjust and it may be demoted or mutated in future evolution cycles.
"""
            try:
                skill_path.write_text(skill_content, encoding="utf-8")
                graduated += 1
                logger.info(f"  Graduated tip {tip_id} -> skill {skill_name}")
            except Exception as e:
                logger.warning(f"  Failed to graduate tip {tip_id}: {e}")
        
        conn.close()
        return graduated


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

_pipeline: Optional[SelfEvolutionPipeline] = None

def get_evolution_pipeline() -> SelfEvolutionPipeline:
    """Get or create the global SelfEvolutionPipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = SelfEvolutionPipeline()
    return _pipeline


def run_evolution_cycle() -> Dict:
    """Run one evolution cycle."""
    pipeline = get_evolution_pipeline()
    return pipeline.run_cycle()


def record_task_hindsight(task_id: str, description: str, approach: str,
                           result: str, worked: str, failed: str,
                           different: str) -> Dict:
    """Record hindsight for a completed task."""
    pipeline = get_evolution_pipeline()
    return pipeline.record_hindsight(task_id, description, approach, result,
                                    worked, failed, different)


def get_relevant_hindsight(task_description: str) -> List[Dict]:
    """Get relevant hindsight for a task."""
    pipeline = get_evolution_pipeline()
    return pipeline.get_hindsight_for_task(task_description)
