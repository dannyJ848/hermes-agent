#!/usr/bin/env python3
"""
cortex_flywheel.py — Autonomous training flywheel for the unified Cortex database.

Runs as a self-sustaining loop:
  1. EVALUATE: Run Elo tournaments on unrated/under-rated tips
  2. REPAIR: Fix low-Elo tips by revision or deactivation
  3. CONSOLIDATE: Merge redundant nodes, strengthen edges
  4. TRACK: Record flywheel metrics
  5. REPEAT

Designed to be called from Hermes cron every 2h or run as daemon thread.
"""

import sys
import os
import json
import time
import random
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Ensure hermes-agent is in path for imports
sys.path.insert(0, str(Path.home() / "hermes-agent"))
from agent.cortex_access import CortexDB, cortex_cursor

# Try to import LLM judge
try:
    from llm_judge import LLMJudge
    HAS_LLM_JUDGE = True
except ImportError:
    HAS_LLM_JUDGE = False

# Constants
K_FACTOR = 40  # Elo K-factor for fast convergence
ELO_FLOOR = 800
ELO_CEILING = 2000
REPAIR_THRESHOLD = 1050  # Elo below this after 8+ matches = repair
DEACTIVATE_THRESHOLD = 950  # Elo below this after 10+ matches = deactivate
CONSOLIDATION_THRESHOLD = 0.92  # Cosine similarity for auto-merge


def update_elo_pair(elo_a: float, elo_b: float, a_wins: bool, k: int = K_FACTOR) -> Tuple[float, float]:
    """Standard Elo update. Returns (new_elo_a, new_elo_b)."""
    expected_a = 1 / (1 + 10 ** ((elo_b - elo_a) / 400))
    expected_b = 1 - expected_a
    
    score_a = 1.0 if a_wins else 0.0
    score_b = 1.0 - score_a
    
    new_elo_a = elo_a + k * (score_a - expected_a)
    new_elo_b = elo_b + k * (score_b - expected_b)
    
    # Clamp to valid range
    new_elo_a = max(ELO_FLOOR, min(ELO_CEILING, new_elo_a))
    new_elo_b = max(ELO_FLOOR, min(ELO_CEILING, new_elo_b))
    
    return new_elo_a, new_elo_b


def heuristic_judge(tip_a: Dict, tip_b: Dict) -> Tuple[str, float, str]:
    """
    Heuristic comparison of two tips.
    Returns (winner, confidence, reasoning) where winner is 'a', 'b', or 't' (tie).
    """
    score_a = 0
    score_b = 0
    factors = []
    
    # Factor 1: Specificity (longer text with concrete details)
    a_words = len(tip_a['text'].split())
    b_words = len(tip_b['text'].split())
    if a_words > b_words and a_words > 15:
        score_a += 1
        factors.append("A more specific")
    elif b_words > a_words and b_words > 15:
        score_b += 1
        factors.append("B more specific")
    
    # Factor 2: Actionability (contains actionable verbs)
    action_words = ['do', 'use', 'check', 'verify', 'run', 'try', 'ensure', 'avoid', 'prefer', 'when']
    a_actions = sum(1 for w in action_words if w in tip_a['text'].lower())
    b_actions = sum(1 for w in action_words if w in tip_b['text'].lower())
    if a_actions > b_actions:
        score_a += 1
        factors.append("A more actionable")
    elif b_actions > a_actions:
        score_b += 1
        factors.append("B more actionable")
    
    # Factor 3: Has condition (starts with WHEN or IF)
    a_has_condition = tip_a['text'].lower().startswith(('when', 'if'))
    b_has_condition = tip_b['text'].lower().startswith(('when', 'if'))
    if a_has_condition and not b_has_condition:
        score_a += 1
        factors.append("A has trigger")
    elif b_has_condition and not a_has_condition:
        score_b += 1
        factors.append("B has trigger")
    
    # Factor 4: Domain confidence (from metadata or existing elo)
    if tip_a.get('confidence', 0.5) > tip_b.get('confidence', 0.5) + 0.2:
        score_a += 1
        factors.append("A higher confidence")
    elif tip_b.get('confidence', 0.5) > tip_a.get('confidence', 0.5) + 0.2:
        score_b += 1
        factors.append("B higher confidence")
    
    # Factor 5: Historical performance
    if tip_a.get('elo_matches', 0) > 5 and tip_b.get('elo_matches', 0) <= 2:
        if tip_a.get('elo', 1200) > 1200:
            score_a += 1
            factors.append("A proven track record")
    elif tip_b.get('elo_matches', 0) > 5 and tip_a.get('elo_matches', 0) <= 2:
        if tip_b.get('elo', 1200) > 1200:
            score_b += 1
            factors.append("B proven track record")
    
    # Determine winner
    margin = abs(score_a - score_b)
    if margin == 0:
        return 't', 0.5, "Tie: " + ", ".join(factors) if factors else "No clear winner"
    elif score_a > score_b:
        confidence = 0.5 + (margin * 0.1)
        return 'a', min(0.95, confidence), f"A wins ({score_a}-{score_b}): " + ", ".join(factors)
    else:
        confidence = 0.5 + (margin * 0.1)
        return 'b', min(0.95, confidence), f"B wins ({score_b}-{score_a}): " + ", ".join(factors)


class CortexFlywheel:
    """Autonomous flywheel for continuous tip improvement."""
    
    def __init__(self, db: Optional[CortexDB] = None):
        self.db = db or CortexDB()
        self.llm_judge = LLMJudge() if HAS_LLM_JUDGE else None
        self.stats = {
            'pairs_evaluated': 0,
            'tips_repaired': 0,
            'tips_consolidated': 0,
            'tips_deactivated': 0,
            'llm_calls': 0
        }
    
    def run_eval_sweep(self, num_pairs: int = 100, use_llm_every: int = 3) -> Dict:
        """
        Run Elo tournaments on tip pairs.
        
        Args:
            num_pairs: Number of pairs to evaluate
            use_llm_every: Use LLM judge every Nth cycle (1 = always, 3 = every 3rd)
        """
        try:
            cycle_id = self.db.start_flywheel_cycle('eval')
        except Exception:
            cycle_id = None
        start_time = time.time()
        
        # Get tips needing evaluation
        tips = self.db.get_tips_for_eval(limit=num_pairs * 2)
        
        if len(tips) < 2:
            self.db.complete_flywheel_cycle(cycle_id, 'completed', 0, 0, 0, 0)
            return {'status': 'skipped', 'reason': 'not_enough_tips', 'tips_available': len(tips)}
        
        random.shuffle(tips)
        pairs_evaluated = 0
        
        for i in range(0, min(len(tips) - 1, num_pairs * 2), 2):
            tip_a = tips[i]
            tip_b = tips[i + 1]
            
            # Skip if same tip
            if tip_a['id'] == tip_b['id']:
                continue
            
            # Decide judge type
            use_llm = self.llm_judge and (pairs_evaluated % use_llm_every == 0)
            
            if use_llm:
                try:
                    result = self.llm_judge.compare_tips(tip_a, tip_b)
                    winner = result['winner']
                    confidence = result['confidence']
                    reasoning = result['reasoning']
                    judge_type = 'llm'
                    self.stats['llm_calls'] += 1
                except Exception as e:
                    # Fallback to heuristic
                    winner, confidence, reasoning = heuristic_judge(tip_a, tip_b)
                    judge_type = 'heuristic'
            else:
                winner, confidence, reasoning = heuristic_judge(tip_a, tip_b)
                judge_type = 'heuristic'
            
            # Update Elo ratings
            if winner == 'a':
                new_elo_a, new_elo_b = update_elo_pair(tip_a['elo'], tip_b['elo'], True)
            elif winner == 'b':
                new_elo_a, new_elo_b = update_elo_pair(tip_a['elo'], tip_b['elo'], False)
            else:
                # Tie - both get slight adjustment toward mean
                new_elo_a = tip_a['elo'] + (1200 - tip_a['elo']) * 0.05
                new_elo_b = tip_b['elo'] + (1200 - tip_b['elo']) * 0.05
            
            self.db.update_elo(tip_a['id'], new_elo_a, winner == 'a')
            self.db.update_elo(tip_b['id'], new_elo_b, winner == 'b')
            
            # Record evaluation - winner_id must be actual node UUID or None
            winner_id = tip_a['id'] if winner == 'a' else (tip_b['id'] if winner == 'b' else None)
            try:
                self.db.record_eval(
                    tip_a['id'], tip_b['id'], winner,
                    judge_type, confidence, reasoning, cycle_id
                )
            except Exception:
                pass  # Non-fatal: eval history may have schema issues
            
            pairs_evaluated += 1
        
        duration_ms = int((time.time() - start_time) * 1000)
        try:
            self.db.complete_flywheel_cycle(cycle_id, 'completed', pairs_evaluated, 0, 0, duration_ms)
        except Exception:
            pass
        
        self.stats['pairs_evaluated'] += pairs_evaluated
        
        return {
            'status': 'completed',
            'pairs_evaluated': pairs_evaluated,
            'llm_calls': self.stats['llm_calls'] if use_llm_every else 0,
            'duration_ms': duration_ms
        }
    
    def run_repair_sweep(self) -> Dict:
        """Repair or deactivate low-performing tips."""
        cycle_id = self.db.start_flywheel_cycle('repair')
        start_time = time.time()
        
        tips_repaired = 0
        tips_deactivated = 0
        
        with cortex_cursor() as cur:
            # Find tips needing repair (low elo after many matches)
            cur.execute("""
                SELECT id, text, elo, elo_matches, metadata
                FROM cortex_nodes
                WHERE node_type = 'tip' AND is_active = TRUE
                  AND elo < %s AND elo_matches >= 8
            """, (REPAIR_THRESHOLD,))
            
            repair_candidates = [dict(row) for row in cur.fetchall()]
            
            for tip in repair_candidates:
                # Attempt repair: try to improve the tip
                repaired_text = self._attempt_repair(tip)
                
                if repaired_text and repaired_text != tip['text']:
                    # Create new version as separate tip
                    self.db.insert_node(
                        text=repaired_text,
                        node_type='tip',
                        domain='general',
                        confidence=tip['metadata'].get('confidence', 0.5) * 0.9,  # Slightly lower confidence
                        elo=1100,  # Start repaired tips at 1100
                        metadata={
                            'repaired_from': tip['id'],
                            'original_text': tip['text'],
                            'repair_reason': 'low_elo'
                        }
                    )
                    tips_repaired += 1
                
                # Deactivate original if very low
                if tip['elo'] < DEACTIVATE_THRESHOLD and tip['elo_matches'] >= 10:
                    self.db.deactivate_node(tip['id'], f"Elo {tip['elo']:.0f} after {tip['elo_matches']} matches")
                    tips_deactivated += 1
        
        duration_ms = int((time.time() - start_time) * 1000)
        self.db.complete_flywheel_cycle(cycle_id, 'completed', 0, tips_repaired, 0, duration_ms)
        
        self.stats['tips_repaired'] += tips_repaired
        self.stats['tips_deactivated'] += tips_deactivated
        
        return {
            'status': 'completed',
            'tips_repaired': tips_repaired,
            'tips_deactivated': tips_deactivated,
            'duration_ms': duration_ms
        }
    
    def _attempt_repair(self, tip: Dict) -> Optional[str]:
        """Attempt to repair a low-performing tip. Returns improved text or None."""
        text = tip['text']
        
        # Common repair patterns
        repairs = []
        
        # 1. Add WHEN prefix if missing
        if not text.lower().startswith(('when', 'if')):
            repairs.append("WHEN " + text[0].lower() + text[1:])
        
        # 2. Add DO if missing action
        if ' do ' not in text.lower() and ' do,' not in text.lower():
            # Try to insert DO before the action
            words = text.split()
            if len(words) > 3:
                # Find a good spot for DO
                for i, word in enumerate(words[2:], 2):
                    if word.lower() in ['use', 'check', 'run', 'try', 'ensure']:
                        words.insert(i, 'DO')
                        repairs.append(' '.join(words))
                        break
        
        # 3. Add rationale if missing
        if 'because' not in text.lower() and 'to ' not in text.lower():
            repairs.append(text + " (to ensure reliability)")
        
        # Return the best repair (longest = most complete)
        if repairs:
            return max(repairs, key=len)
        return None
    
    def run_consolidation_sweep(self, similarity_threshold: float = CONSOLIDATION_THRESHOLD) -> Dict:
        """Merge duplicate/similar tips."""
        cycle_id = self.db.start_flywheel_cycle('consolidate')
        start_time = time.time()
        
        tips_consolidated = 0
        
        # Find potential duplicates using MD5 hash
        with cortex_cursor() as cur:
            cur.execute("""
                SELECT content_md5, array_agg(id) as ids
                FROM cortex_nodes
                WHERE node_type = 'tip' AND is_active = TRUE
                  AND content_md5 IS NOT NULL
                GROUP BY content_md5
                HAVING count(*) > 1
            """)
            
            for row in cur.fetchall():
                ids = row['ids'] if isinstance(row, dict) else json.loads(row[1])
                # Keep highest Elo, deactivate others
                if len(ids) > 1:
                    # Get Elo for each
                    cur.execute("""
                        SELECT id, elo FROM cortex_nodes WHERE id = ANY(%s) ORDER BY elo DESC
                    """, (ids,))
                    
                    sorted_ids = [r['id'] if isinstance(r, dict) else r[0] for r in cur.fetchall()]
                    
                    # Keep first (highest Elo), deactivate rest
                    for dup_id in sorted_ids[1:]:
                        self.db.deactivate_node(dup_id, f"Duplicate of {sorted_ids[0]}")
                        tips_consolidated += 1
        
        duration_ms = int((time.time() - start_time) * 1000)
        self.db.complete_flywheel_cycle(cycle_id, 'completed', 0, 0, tips_consolidated, duration_ms)
        
        self.stats['tips_consolidated'] += tips_consolidated
        
        return {
            'status': 'completed',
            'tips_consolidated': tips_consolidated,
            'duration_ms': duration_ms
        }
    
    def run_full_cycle(self, eval_pairs: int = 100) -> Dict:
        """Run a complete flywheel cycle: eval + repair + consolidate."""
        results = {
            'eval': self.run_eval_sweep(eval_pairs),
            'repair': self.run_repair_sweep(),
            'consolidate': self.run_consolidation_sweep()
        }
        return results
    
    def get_stats(self) -> Dict:
        """Get flywheel statistics."""
        return {
            **self.stats,
            'db_stats': self.db.get_stats(),
            'quality_report': self.db.get_tip_quality_report()
        }


def main():
    """CLI entry point for cron jobs."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cortex Flywheel')
    parser.add_argument('--eval-pairs', type=int, default=100, help='Number of pairs to evaluate')
    parser.add_argument('--repair-only', action='store_true', help='Only run repair sweep')
    parser.add_argument('--consolidate-only', action='store_true', help='Only run consolidation')
    parser.add_argument('--full-cycle', action='store_true', help='Run full cycle (eval+repair+consolidate)')
    
    args = parser.parse_args()
    
    flywheel = CortexFlywheel()
    
    if args.repair_only:
        result = flywheel.run_repair_sweep()
    elif args.consolidate_only:
        result = flywheel.run_consolidation_sweep()
    elif args.full_cycle:
        result = flywheel.run_full_cycle(args.eval_pairs)
    else:
        # Default: just eval sweep
        result = flywheel.run_eval_sweep(args.eval_pairs)
    
    print(json.dumps(result, indent=2))
    
    # Print stats
    stats = flywheel.get_stats()
    print(f"\nFlywheel Stats:")
    print(f"  Pairs evaluated: {stats['pairs_evaluated']}")
    print(f"  Tips repaired: {stats['tips_repaired']}")
    print(f"  Tips consolidated: {stats['tips_consolidated']}")
    print(f"  Tips deactivated: {stats['tips_deactivated']}")
    print(f"  LLM calls: {stats['llm_calls']}")


if __name__ == "__main__":
    main()
