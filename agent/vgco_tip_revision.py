"""VGCO Tip Revision — LLM-as-Editor for downvoted tips.

When a tip gets downvoted 5+ times, its condition/recommendation are likely wrong.
This module rewrites tips based on accumulated failure signals.

Inspired by VGCO (AAAI 2026) — LLMs auto-refine tool docs from failure cases.
"""

import sqlite3
import os
from pathlib import Path


def revise_downvoted_tips(downvote_threshold=5, max_revisions=3):
    """Find tips with high downvotes and revise their conditions.
    
    Returns list of (tip_id, old_condition, new_condition) tuples.
    """
    cer_path = str(Path.home() / ".hermes" / "cerebrum_memory.db")
    db = sqlite3.connect(cer_path, timeout=5)
    
    candidates = db.execute(
        "SELECT id, tool_name, condition, recommendation, confidence, upvotes, downvotes, tip_type "
        "FROM distilled_tips WHERE downvotes >= ? AND confidence > 0.5 ORDER BY downvotes DESC LIMIT ?",
        (downvote_threshold, max_revisions)
    ).fetchall()
    
    revisions = []
    
    for tid, tool, cond, rec, conf, up, down, ttype in candidates:
        # Heuristic rewriting rules (no LLM needed)
        if down > up / 2:
            new_cond = cond.replace("When ", "ONLY When ").replace("when ", "ONLY when ")
            if "ONLY" not in new_cond:
                new_cond = "SPECIFICALLY " + new_cond
            new_rec = rec + f" [REVISED: was downvoted {down} times — likely too broad or wrong context]"
        else:
            new_cond = cond
            new_rec = rec + f" [CAUTION: {down} failures recorded — verify applicability]"
        
        db.execute(
            "UPDATE distilled_tips SET condition = ?, recommendation = ?, confidence = ? WHERE id = ?",
            (new_cond, new_rec, max(conf * 0.9, 0.4), tid)
        )
        revisions.append((tid, cond[:60], new_cond[:60]))
    
    db.commit()
    db.close()
    return revisions


def get_revision_candidates():
    """Preview which tips would be revised."""
    cer_path = str(Path.home() / ".hermes" / "cerebrum_memory.db")
    db = sqlite3.connect(cer_path, timeout=5)
    candidates = db.execute(
        "SELECT id, tool_name, condition, downvotes, upvotes, confidence "
        "FROM distilled_tips WHERE downvotes >= 3 ORDER BY downvotes DESC LIMIT 10"
    ).fetchall()
    db.close()
    return candidates
