#!/usr/bin/env python3
"""Evaluation-Driven Flywheel — Tournament-Based Tip Evolution.

Inspired by:
  - Autoreason (NousResearch): A/B/AB three-way tournament, Borda aggregation,
    CoT judges, convergence detection via margin
  - A-Evolve (Orchestra): File-based evolvable state, fitness-gated progression,
    verify-fix loops, hypothesis-first exploration
  - Self-Evolving Agents Survey (2507.21046): 5-goal evaluation framework

Architecture:
  1. CHALLENGE: Sample 2 tips for same domain → create tournament pair
  2. EVALUATE: Judge panel (local models) scores each tip on 3 axes:
     - Answer quality: Would following this tip produce correct results?
     - Format quality: Is the condition/recommendation well-structured?
     - Execution quality: Is the tip practical and actionable?
  3. AGGREGATE: Borda count across judges → rank tips
  4. EVOLVE: Winner survives, loser gets flagged for revision or retirement
  5. SYNTHESIZE: When both tips have merit, create AB synthesis
  6. RECORD: All outcomes tracked for meta-evaluation (convergence detection)

Usage:
    from eval_flywheel import EvalFlywheel
    fw = EvalFlywheel()
    results = fw.run_tournament(domain="debugging", n_rounds=5)
    report = fw.meta_report()
"""

import json
import sqlite3
import time
import urllib.request
import hashlib
import logging
from collections import defaultdict
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

CEREBRUM_DB = str(Path.home() / ".hermes" / "cerebrum_memory.db")
PHI3_URL = "http://localhost:8081/v1/chat/completions"
LLAMA8B_URL = "http://localhost:8082/v1/chat/completions"
HINDSIGHT_URL = "http://localhost:8890/v1/default/banks/hermes-cerebrum/memories"

# Tier 3: Cloud judges (Featherless Premium — unlimited tokens)
FEATHERLESS_URL = "https://api.featherless.ai/v1/chat/completions"
FEATHERLESS_KEY = "rc_a4f9154eaf34d7ac8bdceeeb4a656df8de249edd79174d64f48099b7207980b7"
FEATHERLESS_MODEL = "deepseek-ai/DeepSeek-V3.1"  # Strong CoT judge
FEATHERLESS_MODEL_FAST = "deepseek-ai/DeepSeek-V3.1"  # Same model — no thinking overhead

# Borda scoring: 1st place = N points, 2nd = N-1, etc.
# For 2-item tournament: winner gets 2, loser gets 1
BORDA_FIRST = 2
BORDA_SECOND = 1

# Convergence threshold from Autoreason: margin >= 2 consecutive wins
CONVERGENCE_WINDOW = 3  # consecutive wins to declare dominance
RETIREMENT_THRESHOLD = 0.3  # conf below this → flag for removal
SYNTHESIS_MIN_SCORE = 6.0  # both tips must score >= this for synthesis

# ── Elo Rating System (replaces pure Borda) ──
# K=40 for first 20 matchups, K=20 after (from eval research)
ELO_INITIAL = 1200
ELO_K_EARLY = 40
ELO_K_LATE = 20
ELO_TRANSITION = 20  # matchups before switching to K_LATE
ELO_SCALE = 400  # standard Elo scaling factor


class EloTracker:
    """Elo rating system for tips with Bayesian uncertainty tracking.
    
    Key improvement over Borda: beating a strong tip moves rating more
    than beating a weak tip. Ratings have continuous variance instead of
    binary win/loss. Enables Thompson sampling for matchup allocation.
    """
    
    def __init__(self):
        self._ensure_schema()
    
    def _ensure_schema(self):
        try:
            conn = sqlite3.connect(CEREBRUM_DB, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tip_elo (
                    tip_id INTEGER PRIMARY KEY,
                    elo REAL DEFAULT 1200,
                    matches INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    last_match REAL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_elo_rating ON tip_elo(elo DESC);
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Elo schema creation failed: {e}")
    
    def get_rating(self, tip_id):
        """Get current Elo rating for a tip."""
        try:
            conn = sqlite3.connect(CEREBRUM_DB, timeout=5)
            row = conn.execute(
                "SELECT elo, matches FROM tip_elo WHERE tip_id=?", (tip_id,)
            ).fetchone()
            conn.close()
            if row:
                return {"elo": row[0], "matches": row[1]}
            return {"elo": ELO_INITIAL, "matches": 0}
        except Exception:
            return {"elo": ELO_INITIAL, "matches": 0}
    
    def update(self, winner_id, loser_id, margin=1.0):
        """Update Elo ratings after a matchup.
        
        Args:
            winner_id: ID of winning tip
            loser_id: ID of losing tip  
            margin: 1.0 for decisive, 0.67 for 2-1 split, 0.33 for close
        """
        try:
            conn = sqlite3.connect(CEREBRUM_DB, timeout=10)
            conn.execute("PRAGMA busy_timeout=5000")
            
            # Get current ratings
            w = conn.execute("SELECT elo, matches FROM tip_elo WHERE tip_id=?", (winner_id,)).fetchone()
            l = conn.execute("SELECT elo, matches FROM tip_elo WHERE tip_id=?", (loser_id,)).fetchone()
            
            w_elo = w[0] if w else ELO_INITIAL
            w_matches = w[1] if w else 0
            l_elo = l[0] if l else ELO_INITIAL
            l_matches = l[1] if l else 0
            
            # Expected scores (standard Elo formula)
            exp_w = 1.0 / (1.0 + 10 ** ((l_elo - w_elo) / ELO_SCALE))
            exp_l = 1.0 - exp_w
            
            # K-factor: early = aggressive, late = conservative
            k_w = ELO_K_EARLY if w_matches < ELO_TRANSITION else ELO_K_LATE
            k_l = ELO_K_EARLY if l_matches < ELO_TRANSITION else ELO_K_LATE
            
            # Apply margin as multiplier on K
            k_w *= max(0.5, margin)
            k_l *= max(0.5, margin)
            
            # New ratings
            new_w_elo = w_elo + k_w * (1.0 - exp_w)
            new_l_elo = l_elo + k_l * (0.0 - exp_l)
            
            # Upsert
            for tip_id, new_elo, is_win, old_matches in [
                (winner_id, new_w_elo, True, w_matches),
                (loser_id, new_l_elo, False, l_matches)
            ]:
                if old_matches == 0:
                    conn.execute(
                        "INSERT INTO tip_elo (tip_id, elo, matches, wins, losses, last_match) VALUES (?,?,?,?,?,?)",
                        (tip_id, new_elo, 1, 1 if is_win else 0, 0 if is_win else 1, time.time())
                    )
                else:
                    conn.execute(
                        "UPDATE tip_elo SET elo=?, matches=matches+1, wins=wins+?, losses=losses+?, last_match=? WHERE tip_id=?",
                        (new_elo, 1 if is_win else 0, 1 if is_win else 0, time.time(), tip_id)
                    )
            
            conn.commit()
            conn.close()
            return {"winner_elo": round(new_w_elo, 1), "loser_elo": round(new_l_elo, 1)}
        except Exception as e:
            logger.warning(f"Elo update failed: {e}")
            return {}
    
    def get_ranking(self, limit=20, min_matches=0):
        """Get tips ranked by Elo rating."""
        try:
            conn = sqlite3.connect(CEREBRUM_DB, timeout=5)
            rows = conn.execute("""
                SELECT te.tip_id, te.elo, te.matches, te.wins, te.losses,
                       dt.condition, dt.domain
                FROM tip_elo te
                JOIN distilled_tips dt ON te.tip_id = dt.id
                WHERE te.matches >= ?
                ORDER BY te.elo DESC
                LIMIT ?
            """, (min_matches, limit)).fetchall()
            conn.close()
            return [
                {
                    "tip_id": r[0], "elo": round(r[1], 1), "matches": r[2],
                    "wins": r[3], "losses": r[4],
                    "condition": r[5][:60] if r[5] else "", "domain": r[6]
                }
                for r in rows
            ]
        except Exception:
            return []
    
    def thompson_sample(self, tip_ids):
        """Select next matchup using Thompson sampling.
        
        Returns pair of tip IDs with highest uncertainty overlap.
        Each tip's win rate modeled as Beta(wins+1, losses+1).
        """
        import random
        if len(tip_ids) < 2:
            return None
        
        try:
            conn = sqlite3.connect(CEREBRUM_DB, timeout=5)
            ratings = {}
            for tid in tip_ids:
                row = conn.execute(
                    "SELECT wins, losses FROM tip_elo WHERE tip_id=?", (tid,)
                ).fetchone()
                if row:
                    ratings[tid] = {"wins": row[0], "losses": row[1]}
                else:
                    ratings[tid] = {"wins": 0, "losses": 0}
            conn.close()
            
            # Sample from Beta posteriors
            samples = {}
            for tid, r in ratings.items():
                alpha = r["wins"] + 1
                beta = r["losses"] + 1
                samples[tid] = random.betavariate(alpha, beta)
            
            # Find pair with closest sampled values (highest uncertainty about ordering)
            best_pair = None
            min_gap = float('inf')
            ids = list(tip_ids)
            for i in range(len(ids)):
                for j in range(i+1, len(ids)):
                    gap = abs(samples[ids[i]] - samples[ids[j]])
                    if gap < min_gap:
                        min_gap = gap
                        best_pair = (ids[i], ids[j])
            
            return best_pair
        except Exception:
            return (tip_ids[0], tip_ids[1]) if len(tip_ids) >= 2 else None


def _local_inference(url, prompt, max_tokens=150, timeout=15):
    """Call local inference server with error handling."""
    payload = json.dumps({
        "model": "local",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.05,
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"Local inference failed: {e}")
        return ""


def _phi3_judge(tip_a, tip_b, task_context="general agent operations", focus="standard"):
    """Phi-3 judge: fast winner selection (3s per call).
    
    Args:
        focus: "standard", "accuracy", "efficiency", or "completeness"
               Varies the rubric emphasis for multi-judge panels.
    """
    cond_a = tip_a['condition'][:80]
    rec_a = tip_a['recommendation'][:100]
    cond_b = tip_b['condition'][:80]
    rec_b = tip_b['recommendation'][:100]
    
    focus_prompts = {
        "standard": "",
        "accuracy": "Focus: which tip would produce MORE CORRECT results?",
        "efficiency": "Focus: which tip leads to FEWER tool calls and LESS waste?",
        "completeness": "Focus: which tip handles MORE edge cases and failure modes?",
    }
    focus_text = focus_prompts.get(focus, "")
    
    prompt = f"""Which tip is better? Context: {task_context}
A: IF {cond_a} THEN {rec_a}
B: IF {cond_b} THEN {rec_b}
{focus_text}
Pick winner. JSON: {{"winner":"A","reason":"brief"}}"""

    response = _local_inference(PHI3_URL, prompt, max_tokens=30, timeout=8)
    return _parse_judge_response(response, f"Phi3-{focus}")


def _run_3judge_panel(tip_a, tip_b, task_context="general agent operations"):
    """Run 5-judge panel: 3 local Phi-3 + 1 Llama-8B + 1 cloud (Featherless).
    
    Returns list of 5 judgments. Local judges handle bulk scoring,
    cloud judge provides strong tiebreaking when local judges disagree.
    Total cost: ~12s per matchup (3x3s Phi-3 + 3s Llama-8B + 3s cloud Qwen3-8B).
    """
    judges = []
    # Tier 1: 3x Phi-3 with varied focus (fast, local)
    for focus in ["accuracy", "efficiency", "completeness"]:
        j = _phi3_judge(tip_a, tip_b, task_context=task_context, focus=focus)
        judges.append(j)
    # Tier 2: Llama 8B CoT judge (local)
    judges.append(_llama8b_judge(tip_a, tip_b, task_context=task_context))
    # Tier 3: Cloud judge (Featherless — unlimited tokens)
    judges.append(_featherless_judge(tip_a, tip_b, task_context=task_context, model=FEATHERLESS_MODEL_FAST))
    return judges


def _llama8b_judge(tip_a, tip_b, task_context="general agent operations"):
    """Llama 8B CoT judge: second opinion for Borda aggregation."""
    cond_a = tip_a['condition'][:60]
    rec_a = tip_a['recommendation'][:80]
    cond_b = tip_b['condition'][:60]
    rec_b = tip_b['recommendation'][:80]
    
    prompt = f"""Judge tips. Think step by step. Context: {task_context}

A: IF {cond_a} THEN {rec_a}
B: IF {cond_b} THEN {rec_b}

Score 1-10: answer, format, execution. Pick winner. JSON only:
{{"A":{{"a":N,"f":N,"e":N}},"B":{{"a":N,"f":N,"e":N}},"winner":"A","reason":"brief"}}"""

    response = _local_inference(LLAMA8B_URL, prompt, max_tokens=200, timeout=25)
    return _parse_judge_response(response, "Llama8B")


def _cloud_inference(url, prompt, model, max_tokens=150, timeout=30):
    """Call cloud inference (Featherless) with auth header."""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.05,
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {FEATHERLESS_KEY}",
            "User-Agent": "hermes-eval-flywheel/1.0",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"Cloud inference failed: {e}")
        return ""


def _featherless_judge(tip_a, tip_b, task_context="general agent operations", model=None):
    """Featherless cloud judge — strong CoT evaluation.
    
    Uses DeepSeek V3.1 for deep analysis or Qwen3-8B for fast bulk judging.
    Tier 3 judge — breaks ties when local judges disagree.
    """
    if model is None:
        model = FEATHERLESS_MODEL
    cond_a = tip_a['condition'][:80]
    rec_a = tip_a['recommendation'][:100]
    cond_b = tip_b['condition'][:80]
    rec_b = tip_b['recommendation'][:100]
    
    prompt = f"""You are an expert AI agent evaluator. Compare these two behavioral tips.

Context: {task_context}

Tip A: IF {cond_a} THEN {rec_a}
Tip B: IF {cond_b} THEN {rec_b}

Evaluate on 3 axes (1-10):
- Answer quality: Would following this tip produce correct results?
- Format quality: Is the condition/recommendation well-structured?
- Execution quality: Is the tip practical and actionable?

Pick winner. JSON only:
{{"A":{{"a":N,"f":N,"e":N}},"B":{{"a":N,"f":N,"e":N}},"winner":"A","reason":"brief"}}"""

    response = _cloud_inference(FEATHERLESS_URL, prompt, model, max_tokens=200, timeout=45)
    return _parse_judge_response(response, f"Cloud-{model.split('/')[-1]}")


def _parse_judge_response(text, judge_name):
    """Parse judge response into structured scores."""
    if not text:
        return {"scores": {}, "winner": None, "reason": "no response", "judge": judge_name}

    # Try to find JSON in response
    try:
        # Find JSON block
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
            return {
                "scores": data.get("A", {}),  # Will be restructured below
                "scores_b": data.get("B", {}),
                "winner": data.get("winner", "A").strip().upper()[:1],
                "reason": data.get("reason", ""),
                "judge": judge_name,
                "raw": data,
            }
    except json.JSONDecodeError:
        pass

    # Fallback: simple winner extraction
    if "A" in text.upper() and "B" not in text.upper().split("WINNER")[0][-5:]:
        winner = "A"
    elif "B" in text.upper():
        winner = "B"
    else:
        winner = "A"  # default to incumbent

    return {"scores": {}, "winner": winner, "reason": text[:100], "judge": judge_name}


def _borda_aggregate(judgments):
    """Aggregate multiple judge rankings via Borda count.
    
    From Autoreason: Borda score = sum of (N - rank_i) across all judges.
    More judges = faster convergence (7 judges 3x faster than 3).
    """
    scores = defaultdict(int)
    for j in judgments:
        winner = j.get("winner", "A")
        if winner == "A":
            scores["A"] += BORDA_FIRST
            scores["B"] += BORDA_SECOND
        else:
            scores["B"] += BORDA_FIRST
            scores["A"] += BORDA_SECOND
    
    return dict(scores)


class EvalFlywheel:
    """Tournament-based evaluation flywheel for tip evolution.
    
    Inspired by Autoreason's three-way tournament and A-Evolve's fitness gating.
    """

    def __init__(self):
        self.tournament_history = []
        self.win_streaks = defaultdict(int)  # tip_id → consecutive wins
        self.evolution_log = []
        self.elo = EloTracker()  # Elo rating system

    def _get_tips_by_domain(self, domain, limit=10):
        """Get tips from cerebrum for a specific domain."""
        try:
            conn = sqlite3.connect(CEREBRUM_DB, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            rows = conn.execute("""
                SELECT id, tip_type, condition, recommendation, rationale,
                       tool_name, domain, confidence, frequency, upvotes, downvotes
                FROM distilled_tips
                WHERE (domain = ? OR tip_type = ?) AND confidence >= 0.5
                ORDER BY RANDOM()
                LIMIT ?
            """, (domain, domain, limit)).fetchall()
            conn.close()

            return [
                {
                    "id": r[0], "tip_type": r[1], "condition": r[2],
                    "recommendation": r[3], "rationale": r[4],
                    "tool_name": r[5], "domain": r[6], "confidence": r[7],
                    "frequency": r[8], "upvotes": r[9], "downvotes": r[10],
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Failed to get tips: {e}")
            return []

    def _get_all_domains(self):
        """Get all domains with tip counts."""
        try:
            conn = sqlite3.connect(CEREBRUM_DB, timeout=30)
            domains = conn.execute("""
                SELECT domain, COUNT(*) as cnt
                FROM distilled_tips
                WHERE confidence >= 0.5 AND domain IS NOT NULL AND domain != ''
                GROUP BY domain
                HAVING cnt >= 2
                ORDER BY cnt DESC
            """).fetchall()
            conn.close()
            return [(d, c) for d, c in domains]
        except Exception as e:
            logger.error(f"Failed to get domains: {e}")
            return []

    def _record_outcome(self, tip_id, outcome, scores=None, opponent_id=None):
        """Record tournament outcome in cerebrum."""
        try:
            conn = sqlite3.connect(CEREBRUM_DB, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")

            if outcome == "win":
                conn.execute(
                    "UPDATE distilled_tips SET upvotes = upvotes + 1, last_seen = ? WHERE id = ?",
                    (time.time(), tip_id)
                )
            elif outcome == "loss":
                conn.execute(
                    "UPDATE distilled_tips SET downvotes = downvotes + 1 WHERE id = ?",
                    (tip_id,)
                )
                # Check if should be flagged
                row = conn.execute(
                    "SELECT confidence, downvotes, upvotes FROM distilled_tips WHERE id = ?",
                    (tip_id,)
                ).fetchone()
                if row:
                    total = row[1] + row[2]
                    if total > 3 and (row[1] / total) > 0.7:
                        # 70%+ loss rate → reduce confidence
                        new_conf = max(0.3, row[0] - 0.05)
                        conn.execute(
                            "UPDATE distilled_tips SET confidence = ? WHERE id = ?",
                            (new_conf, tip_id)
                        )
                        logger.info(f"Tip {tip_id} confidence reduced to {new_conf}")
            elif outcome == "synthesis":
                conn.execute(
                    "UPDATE distilled_tips SET upvotes = upvotes + 1, last_seen = ? WHERE id = ?",
                    (time.time(), tip_id)
                )

            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to record outcome: {e}")

    def run_tournament(self, domain=None, n_rounds=5):
        """Run tournament rounds for a domain.
        
        Each round:
          1. Sample 2 tips from domain
          2. Both judges evaluate (Phi-3 + Llama 8B)
          3. Borda aggregation determines winner
          4. Record outcome (upvotes/downvotes)
          5. Check for synthesis opportunity
          
        Returns list of round results.
        """
        if domain is None:
            domains = self._get_all_domains()
            if not domains:
                return []
            domain = domains[0][0]

        tips = self._get_tips_by_domain(domain, limit=max(n_rounds * 3, 10))
        if len(tips) < 2:
            logger.warning(f"Domain '{domain}' has < 2 tips, skipping tournament")
            return []

        results = []
        for round_num in range(min(n_rounds, len(tips) // 2)):
            # Pick pair (non-overlapping)
            idx_a = round_num * 2
            idx_b = round_num * 2 + 1
            if idx_b >= len(tips):
                break

            tip_a = tips[idx_a]
            tip_b = tips[idx_b]

            # 3-judge panel with varied rubric emphasis (~9s total)
            # Produces margins of 1.0, 0.67, or 0.33 instead of always 1.0
            judgments = _run_3judge_panel(tip_a, tip_b, task_context=domain)
            borda = _borda_aggregate(judgments)

            # Calculate margin from 3-judge panel
            a_votes = sum(1 for j in judgments if j.get("winner") == "A")
            b_votes = len(judgments) - a_votes
            margin = max(a_votes, b_votes) / max(len(judgments), 1)  # 1.0, 0.67, or 0.33

            winner_id = tip_a["id"] if borda.get("A", 0) >= borda.get("B", 0) else tip_b["id"]
            loser_id = tip_b["id"] if winner_id == tip_a["id"] else tip_a["id"]

            # Record outcomes
            self._record_outcome(winner_id, "win")
            self._record_outcome(loser_id, "loss")

            # Update Elo ratings with margin
            elo_result = self.elo.update(winner_id, loser_id, margin=margin)

            # Track win streaks for convergence detection
            self.win_streaks[winner_id] += 1
            self.win_streaks[loser_id] = 0

            round_result = {
                "round": round_num + 1,
                "domain": domain,
                "tip_a_id": tip_a["id"],
                "tip_b_id": tip_b["id"],
                "borda": borda,
                "winner_id": winner_id,
                "loser_id": loser_id,
                "judges": [
                    {"judge": j.get("judge"), "winner": j.get("winner"), "reason": j.get("reason", "")[:100]}
                    for j in judgments
                ],
                "margin": margin,
                "margin_type": f"{a_votes}-{b_votes}",
                "elo": elo_result,
                "timestamp": time.time(),
            }
            results.append(round_result)
            self.tournament_history.append(round_result)

            # Convergence check (Autoreason: margin >= 2, k consecutive wins)
            if self.win_streaks[winner_id] >= CONVERGENCE_WINDOW:
                round_result["converged"] = True
                round_result["convergent_tip"] = winner_id

            time.sleep(0.2)  # Rate limit

        return results

    def run_full_evaluation(self, n_rounds_per_domain=2, max_domains=15):
        """Run tournaments across ALL domains with sufficient tips.
        
        Returns comprehensive evaluation report.
        """
        domains = self._get_all_domains()
        all_results = {}

        for domain, count in domains[:max_domains]:
            if count < 2:
                continue

            results = self.run_tournament(domain=domain, n_rounds=n_rounds_per_domain)
            all_results[domain] = {
                "tip_count": count,
                "rounds_played": len(results),
                "convergent_tips": [r.get("convergent_tip") for r in results if r.get("converged")],
                "avg_margin": sum(r["margin"] for r in results) / max(len(results), 1),
                "dominant_tip": max(
                    set(r["winner_id"] for r in results),
                    key=lambda x: sum(1 for r in results if r["winner_id"] == x),
                ) if results else None,
            }

        return all_results

    def meta_report(self):
        """Generate meta-evaluation report.
        
        Tracks: convergence rates, dominant tips per domain, evaluation quality.
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tournaments": len(self.tournament_history),
            "domains_evaluated": len(set(r["domain"] for r in self.tournament_history)),
            "total_judgments": len(self.tournament_history) * 2,
        }

        if not self.tournament_history:
            report["status"] = "no_data"
            return report

        # Convergence analysis (Autoreason metric)
        converged = [r for r in self.tournament_history if r.get("converged")]
        report["convergence_rate"] = round(len(converged) / len(self.tournament_history), 3)

        # Margin distribution
        margins = [r["margin"] for r in self.tournament_history]
        report["avg_margin"] = round(sum(margins) / len(margins), 2)
        report["max_margin"] = max(margins)
        report["close_matches"] = sum(1 for m in margins if m <= 1)

        # Domain breakdown
        domain_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "rounds": 0})
        for r in self.tournament_history:
            d = r["domain"]
            domain_stats[d]["rounds"] += 1

        report["domain_breakdown"] = dict(domain_stats)

        # Judge agreement rate
        judge_agreements = 0
        for r in self.tournament_history:
            judges = r.get("judges", [])
            if len(judges) >= 2:
                if judges[0].get("winner") == judges[1].get("winner"):
                    judge_agreements += 1
        report["judge_agreement_rate"] = round(
            judge_agreements / max(len(self.tournament_history), 1), 3
        )

        # Cerebrum health
        try:
            conn = sqlite3.connect(CEREBRUM_DB, timeout=10)
            report["cerebrum"] = {
                "total_tips": conn.execute("SELECT COUNT(*) FROM distilled_tips").fetchone()[0],
                "avg_confidence": conn.execute("SELECT ROUND(AVG(confidence),2) FROM distilled_tips").fetchone()[0],
                "flagged_low": conn.execute("SELECT COUNT(*) FROM distilled_tips WHERE confidence < 0.5").fetchone()[0],
                "high_upvote": conn.execute("SELECT COUNT(*) FROM distilled_tips WHERE upvotes > downvotes + 2").fetchone()[0],
            }
            conn.close()
        except Exception:
            report["cerebrum"] = {"error": "unavailable"}

        report["status"] = "active"
        return report

    def get_dominant_tips(self, domain=None, top_n=5):
        """Get tips with highest tournament win rates."""
        try:
            conn = sqlite3.connect(CEREBRUM_DB, timeout=10)
            query = """
                SELECT id, condition, recommendation, domain, confidence, upvotes, downvotes,
                       ROUND(CAST(upvotes AS FLOAT) / MAX(1, upvotes + downvotes), 3) as win_rate
                FROM distilled_tips
                WHERE upvotes + downvotes >= 2
            """
            params = []
            if domain:
                query += " AND domain = ?"
                params.append(domain)
            query += " ORDER BY win_rate DESC, upvotes DESC LIMIT ?"
            params.append(top_n)

            rows = conn.execute(query, params).fetchall()
            conn.close()

            return [
                {
                    "id": r[0], "condition": r[1][:80],
                    "domain": r[3], "confidence": r[4],
                    "win_rate": r[7], "upvotes": r[5], "downvotes": r[6],
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Failed to get dominant tips: {e}")
            return []


# Singleton for plugin integration
_instance = None

def get_instance(session_id: str = "default"):
    global _instance
    if _instance is None:
        _instance = EvalFlywheel()
    return _instance


if __name__ == "__main__":
    # Standalone test
    print("=== Eval Flywheel Self-Test ===\n")
    
    fw = EvalFlywheel()
    
    # Get domains
    domains = fw._get_all_domains()
    print(f"Domains with 2+ tips: {len(domains)}")
    for d, c in domains[:5]:
        print(f"  {d}: {c} tips")
    
    print(f"\nRunning tournament (3 rounds)...")
    results = fw.run_tournament(n_rounds=3)
    
    for r in results:
        print(f"\n  Round {r['round']} ({r['domain']}):")
        print(f"    Borda: A={r['borda'].get('A',0)} B={r['borda'].get('B',0)}")
        print(f"    Winner: tip #{r['winner_id']}, Margin: {r['margin']}")
        for j in r.get("judges", []):
            print(f"    Judge {j['judge']}: {j['winner']} — {j['reason'][:60]}")
    
    print(f"\n=== Meta Report ===")
    report = fw.meta_report()
    for k, v in report.items():
        if k != "domain_breakdown":
            print(f"  {k}: {v}")
    
    print("\nDONE — flywheel operational!")

    def build_injection(self, context="") -> str:
        """Utility module — no context injection"""
        return ""
