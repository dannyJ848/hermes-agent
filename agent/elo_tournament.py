#!/usr/bin/env python3
"""elo_tournament.py — Competitive tip ranking via Elo tournaments.

Every N tool calls, pit recent tips against each other. Winners get promoted,
losers flagged for re-distillation. Produces a living, competitive knowledge base.

Usage:
    python3 elo_tournament.py --run           # Run tournament
    python3 elo_tournament.py --stats         # Show rankings
    python3 elo_tournament.py --reset         # Reset all Elo scores
"""

import argparse
import json
import logging
import os
import random
import sqlite3
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("elo_tournament")

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"
K_FACTOR = 32  # Elo K-factor
TOURNAMENT_SIZE = 10  # Tips per tournament
PROMOTION_THRESHOLD = 1600  # Elo score for auto-promotion
DEMOTION_THRESHOLD = 1200  # Elo score for flagging


class EloTournament:
    """Elo-based tip ranking engine."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Ensure elo_scores and tournament_history tables exist."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS elo_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tip_id INTEGER NOT NULL,
                tip_hash TEXT,
                elo REAL DEFAULT 1500.0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                tournaments INTEGER DEFAULT 0,
                last_tournament TEXT,
                promoted INTEGER DEFAULT 0,
                flagged INTEGER DEFAULT 0,
                UNIQUE(tip_id)
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tournament_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                tip_a_id INTEGER,
                tip_b_id INTEGER,
                winner INTEGER,  -- 1=tip_a, 2=tip_b, 0=draw
                tip_a_elo_before REAL,
                tip_b_elo_before REAL,
                tip_a_elo_after REAL,
                tip_b_elo_after REAL,
                reason TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_tips(self, limit: int = 100) -> list[dict]:
        """Get tips from distilled_tips."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("""
            SELECT id, tip_hash, topic, tip_text, priority, confidence, category
            FROM distilled_tips
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "id": r[0], "tip_hash": r[1], "topic": r[2],
                "tip_text": r[3], "priority": r[4], "confidence": r[5], "category": r[6]
            }
            for r in rows
        ]
    
    def _get_or_create_elo(self, tip_id: int, tip_hash: str) -> dict:
        """Get Elo record for a tip, creating if needed."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM elo_scores WHERE tip_id = ?", (tip_id,))
        row = cur.fetchone()
        
        if not row:
            cur.execute("""
                INSERT INTO elo_scores (tip_id, tip_hash, elo, wins, losses, draws, tournaments)
                VALUES (?, ?, 1500.0, 0, 0, 0, 0)
            """, (tip_id, tip_hash))
            conn.commit()
            cur.execute("SELECT * FROM elo_scores WHERE tip_id = ?", (tip_id,))
            row = cur.fetchone()
        
        conn.close()
        return {
            "id": row[0], "tip_id": row[1], "tip_hash": row[2], "elo": row[3],
            "wins": row[4], "losses": row[5], "draws": row[6], "tournaments": row[7],
            "last_tournament": row[8], "promoted": row[9], "flagged": row[10]
        }
    
    def _expected_score(self, elo_a: float, elo_b: float) -> float:
        """Calculate expected score for A vs B."""
        return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))
    
    def _update_elo(self, elo: float, expected: float, actual: float) -> float:
        """Update Elo rating."""
        return elo + K_FACTOR * (actual - expected)
    
    def _judge_match(self, tip_a: dict, tip_b: dict) -> int:
        """Judge a match between two tips. Returns 1=A wins, 2=B wins, 0=draw.
        
        Uses heuristics:
        - Higher confidence wins
        - Higher priority wins
        - More specific (longer text) wins over vague
        - Category diversity bonus
        """
        score_a = 0
        score_b = 0
        
        # Confidence
        if tip_a.get("confidence", 0.5) > tip_b.get("confidence", 0.5):
            score_a += 1
        elif tip_b.get("confidence", 0.5) > tip_a.get("confidence", 0.5):
            score_b += 1
        
        # Priority
        if tip_a.get("priority", 0.5) > tip_b.get("priority", 0.5):
            score_a += 1
        elif tip_b.get("priority", 0.5) > tip_a.get("priority", 0.5):
            score_b += 1
        
        # Specificity (length as proxy)
        len_a = len(tip_a.get("tip_text", ""))
        len_b = len(tip_b.get("tip_text", ""))
        if len_a > len_b * 1.2:  # A is significantly longer
            score_a += 1
        elif len_b > len_a * 1.2:
            score_b += 1
        
        # Random jitter to prevent stagnation
        score_a += random.uniform(-0.3, 0.3)
        score_b += random.uniform(-0.3, 0.3)
        
        if score_a > score_b + 0.5:
            return 1
        elif score_b > score_a + 0.5:
            return 2
        else:
            return 0
    
    def run_tournament(self, num_matches: int = 5) -> dict:
        """Run a tournament with random tip pairings."""
        tips = self._get_tips(limit=50)
        if len(tips) < 2:
            logger.warning("Not enough tips for tournament (need 2+, got %d)", len(tips))
            return {"matches": 0, "tips_competed": 0}
        
        matches_played = 0
        tips_competed = set()
        
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        for _ in range(num_matches):
            # Pick two random tips
            tip_a, tip_b = random.sample(tips, 2)
            tips_competed.add(tip_a["id"])
            tips_competed.add(tip_b["id"])
            
            # Get current Elo
            elo_a = self._get_or_create_elo(tip_a["id"], tip_a["tip_hash"])
            elo_b = self._get_or_create_elo(tip_b["id"], tip_b["tip_hash"])
            
            # Judge match
            winner = self._judge_match(tip_a, tip_b)
            
            # Calculate expected scores
            exp_a = self._expected_score(elo_a["elo"], elo_b["elo"])
            exp_b = self._expected_score(elo_b["elo"], elo_a["elo"])
            
            # Actual scores
            if winner == 1:
                actual_a, actual_b = 1.0, 0.0
            elif winner == 2:
                actual_a, actual_b = 0.0, 1.0
            else:
                actual_a, actual_b = 0.5, 0.5
            
            # Update Elo
            new_elo_a = self._update_elo(elo_a["elo"], exp_a, actual_a)
            new_elo_b = self._update_elo(elo_b["elo"], exp_b, actual_b)
            
            # Update records
            now = datetime.now().isoformat()
            cur.execute("""
                UPDATE elo_scores SET elo = ?, tournaments = tournaments + 1,
                wins = wins + ?, losses = losses + ?, draws = draws + ?,
                last_tournament = ?
                WHERE tip_id = ?
            """, (new_elo_a, 1 if winner == 1 else 0, 1 if winner == 2 else 0,
                  1 if winner == 0 else 0, now, tip_a["id"]))
            
            cur.execute("""
                UPDATE elo_scores SET elo = ?, tournaments = tournaments + 1,
                wins = wins + ?, losses = losses + ?, draws = draws + ?,
                last_tournament = ?
                WHERE tip_id = ?
            """, (new_elo_b, 1 if winner == 2 else 0, 1 if winner == 1 else 0,
                  1 if winner == 0 else 0, now, tip_b["id"]))
            
            # Record match
            cur.execute("""
                INSERT INTO tournament_history
                (tip_a_id, tip_b_id, winner, tip_a_elo_before, tip_b_elo_before,
                 tip_a_elo_after, tip_b_elo_after, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (tip_a["id"], tip_b["id"], winner, elo_a["elo"], elo_b["elo"],
                  new_elo_a, new_elo_b, "auto_judged"))
            
            matches_played += 1
        
        conn.commit()
        conn.close()
        
        # Check promotions/demotions
        self._process_promotions()
        
        logger.info("Tournament complete: %d matches, %d tips competed", matches_played, len(tips_competed))
        return {"matches": matches_played, "tips_competed": len(tips_competed)}
    
    def _process_promotions(self):
        """Auto-promote high Elo tips, flag low Elo tips."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        # Promote
        cur.execute("""
            UPDATE elo_scores SET promoted = 1, flagged = 0
            WHERE elo >= ? AND promoted = 0
        """, (PROMOTION_THRESHOLD,))
        promoted = cur.rowcount
        
        # Flag for re-distillation
        cur.execute("""
            UPDATE elo_scores SET flagged = 1, promoted = 0
            WHERE elo <= ? AND flagged = 0
        """, (DEMOTION_THRESHOLD,))
        flagged = cur.rowcount
        
        conn.commit()
        conn.close()
        
        if promoted:
            logger.info("Promoted %d tips to high-priority", promoted)
        if flagged:
            logger.info("Flagged %d tips for re-distillation", flagged)
    
    def get_rankings(self, limit: int = 20) -> list[dict]:
        """Get top tips by Elo rating."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("""
            SELECT e.tip_id, e.tip_hash, e.elo, e.wins, e.losses, e.draws,
                   e.tournaments, e.promoted, e.flagged,
                   d.topic, d.tip_text, d.priority, d.confidence
            FROM elo_scores e
            JOIN distilled_tips d ON e.tip_id = d.id
            ORDER BY e.elo DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "tip_id": r[0], "tip_hash": r[1], "elo": r[2],
                "wins": r[3], "losses": r[4], "draws": r[5], "tournaments": r[6],
                "promoted": r[7], "flagged": r[8],
                "topic": r[9], "tip_text": r[10][:100], "priority": r[11], "confidence": r[12]
            }
            for r in rows
        ]
    
    def get_stats(self) -> dict:
        """Get tournament statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM elo_scores")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM elo_scores WHERE promoted = 1")
        promoted = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM elo_scores WHERE flagged = 1")
        flagged = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM tournament_history")
        matches = cur.fetchone()[0]
        
        cur.execute("SELECT AVG(elo) FROM elo_scores")
        avg_elo = cur.fetchone()[0] or 1500
        
        conn.close()
        return {
            "total_tips_ranked": total,
            "promoted": promoted,
            "flagged": flagged,
            "total_matches": matches,
            "average_elo": round(avg_elo, 1)
        }
    
    def reset(self):
        """Reset all Elo scores."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("DELETE FROM elo_scores")
        cur.execute("DELETE FROM tournament_history")
        conn.commit()
        conn.close()
        logger.info("Elo scores reset")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="Run tournament")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    parser.add_argument("--rankings", action="store_true", help="Show rankings")
    parser.add_argument("--reset", action="store_true", help="Reset scores")
    parser.add_argument("--matches", type=int, default=5, help="Matches per tournament")
    args = parser.parse_args()
    
    tourney = EloTournament()
    
    if args.reset:
        tourney.reset()
        return
    
    if args.run:
        result = tourney.run_tournament(num_matches=args.matches)
        print(f"Tournament: {result['matches']} matches, {result['tips_competed']} tips")
    
    if args.rankings:
        rankings = tourney.get_rankings(limit=20)
        print("\n=== TOP TIPS BY ELO ===")
        for i, r in enumerate(rankings, 1):
            status = "⭐" if r["promoted"] else "🚩" if r["flagged"] else "  "
            print(f"{i:2}. {status} Elo:{r['elo']:.0f} W{r['wins']}/L{r['losses']}/D{r['draws']} | {r['topic']}: {r['tip_text'][:60]}...")
    
    if args.stats or not any([args.run, args.rankings, args.reset]):
        stats = tourney.get_stats()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
