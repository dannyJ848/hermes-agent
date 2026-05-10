#!/usr/bin/env python3
"""
cortex_flywheel_v2.py — Enhanced Elo tournament with prompt fragment battles.

Runs Elo tournaments for:
1. Tips (existing)
2. Prompt fragments (new — A/B test system prompt components)

Usage: python3 cortex_flywheel_v2.py [--mode tips|prompts|both] [--batch 50]
"""

import sqlite3
import time
import json
import os
from typing import List, Tuple, Optional

# Import existing judge
import sys
# sys.path removed — modules now in hermes-agent
from agent.llm_judge import LLMJudge

CEREBRUM_DB = os.path.expanduser("~/.hermes/cerebrum_memory.db")

def run_prompt_fragment_tournament(batch_size: int = 20) -> int:
    """Run Elo tournament on prompt fragments."""
    conn = sqlite3.connect(CEREBRUM_DB)
    c = conn.cursor()
    
    # Get prompt fragments with enough matches for meaningful comparison
    c.execute('''
        SELECT id, fragment, fragment_type, elo, matches
        FROM prompt_fragments
        WHERE matches >= 0
        ORDER BY RANDOM()
        LIMIT ?
    ''', (batch_size,))
    
    fragments = c.fetchall()
    if len(fragments) < 2:
        print("Not enough prompt fragments for tournament (need 2+, have %d)" % len(fragments))
        conn.close()
        return 0
    
    judge = LLMJudge()
    battles = 0
    
    # Pair fragments of same type for fair comparison
    for i in range(0, len(fragments)-1, 2):
        if i+1 >= len(fragments):
            break
        f1_id, f1_text, f1_type, f1_elo, f1_matches = fragments[i]
        f2_id, f2_text, f2_type, f2_elo, f2_matches = fragments[i+1]
        
        # Skip if different types
        if f1_type != f2_type:
            continue
        
        # Battle: which fragment produces better reasoning?
        winner = judge.compare_prompt_fragments(f1_text, f2_text, f1_type)
        
        # Update Elo
        if winner == 1:
            new_f1_elo = f1_elo + 32 * (1 - 1/(1 + 10**((f2_elo - f1_elo)/400)))
            new_f2_elo = f2_elo + 32 * (0 - 1/(1 + 10**((f1_elo - f2_elo)/400)))
        else:
            new_f1_elo = f1_elo + 32 * (0 - 1/(1 + 10**((f2_elo - f1_elo)/400)))
            new_f2_elo = f2_elo + 32 * (1 - 1/(1 + 10**((f1_elo - f2_elo)/400)))
        
        c.execute("UPDATE prompt_fragments SET elo=?, matches=matches+1 WHERE id=?", (new_f1_elo, f1_id))
        c.execute("UPDATE prompt_fragments SET elo=?, matches=matches+1 WHERE id=?", (new_f2_elo, f2_id))
        
        battles += 1
    
    conn.commit()
    conn.close()
    
    print(f"Prompt fragment tournament: {battles} battles")
    return battles

def get_top_prompt_fragments(fragment_type: str = None, limit: int = 5) -> List[Tuple]:
    """Get highest-rated prompt fragments."""
    conn = sqlite3.connect(CEREBRUM_DB)
    c = conn.cursor()
    
    if fragment_type:
        c.execute("""
            SELECT fragment, elo, matches, fragment_type
            FROM prompt_fragments
            WHERE fragment_type = ? AND matches >= 5
            ORDER BY elo DESC
            LIMIT ?
        """, (fragment_type, limit))
    else:
        c.execute("""
            SELECT fragment, elo, matches, fragment_type
            FROM prompt_fragments
            WHERE matches >= 5
            ORDER BY elo DESC
            LIMIT ?
        """, (limit,))
    
    results = c.fetchall()
    conn.close()
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["tips", "prompts", "both"], default="both")
    parser.add_argument("--batch", type=int, default=50)
    args = parser.parse_args()
    
    if args.mode in ("prompts", "both"):
        battles = run_prompt_fragment_tournament(args.batch)
        print(f"Prompt fragment battles: {battles}")
        
        # Show top fragments
        print("\n=== TOP PROMPT FRAGMENTS ===")
        for fragment, elo, matches, ftype in get_top_prompt_fragments(limit=5):
            print(f"[{ftype}] Elo={elo:.0f} ({matches} matches)")
            print(f"  {fragment[:100]}...")
            print()
