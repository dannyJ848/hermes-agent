#!/usr/bin/env python3
"""
Agent Scorecard — ICLR 5-level autonomy evaluation framework.

Evaluates the agent across 5 dimensions:
1. SELF_IMPROVEMENT — Does the agent learn from its actions?
2. ERROR_RECOVERY — Can it diagnose and fix its own failures?
3. TASK_SELECTION — Does it choose high-value work autonomously?
4. CONTEXT_MANAGEMENT — How well does it handle context limits?
5. TOOL_MASTERY — How many tools has it mastered?

Levels: L1 (Script) → L2 (Reactive) → L3 (Proactive) → L4 (High Autonomy) → L5 (Full Autonomy)

Usage:
  python3 agent_scorecard.py score
  python3 agent_scorecard.py detail
  python3 agent_scorecard.py history
"""

import os
import sys
import json
import sqlite3
import time
import math

DB_PATH = os.path.expanduser("~/.hermes/cerebrum_memory.db")

LEVEL_NAMES = {
    1: "Script — follows fixed procedures",
    2: "Reactive — responds to errors",
    3: "Proactive — anticipates needs",
    4: "High Autonomy — self-directed",
    5: "Full Autonomy — self-improving",
}

DIMENSION_WEIGHTS = {
    "SELF_IMPROVEMENT": 0.25,
    "ERROR_RECOVERY": 0.20,
    "TASK_SELECTION": 0.20,
    "CONTEXT_MANAGEMENT": 0.15,
    "TOOL_MASTERY": 0.20,
}


def get_db():
    return sqlite3.connect(DB_PATH)


def count_rows(db, table):
    try:
        return db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except:
        return 0


def score_self_improvement(db) -> dict:
    """Score based on: tips distilled, meta-insights, strategy patterns, self-corrections."""
    tips = count_rows(db, "distilled_tips")
    meta_insights = count_rows(db, "meta_insights")
    
    try:
        patterns = db.execute("SELECT COUNT(DISTINCT strategy_type) FROM cognitive_patterns").fetchone()[0]
    except:
        patterns = 0
    
    try:
        lessons = count_rows(db, "iteration_lessons")
    except:
        lessons = 0
    
    # Score 1-5
    score = 1
    evidence = []
    
    if tips > 50 or lessons > 30:
        score = 5
        evidence.append(f"{tips} distilled tips, {lessons} lessons (extensive learning)")
    elif tips > 20 or lessons > 10:
        score = 4
        evidence.append(f"{tips} tips, {lessons} lessons (strong learning)")
    elif tips > 5 or lessons > 3:
        score = 3
        evidence.append(f"{tips} tips, {lessons} lessons (moderate learning)")
    elif tips > 0 or lessons > 0:
        score = 2
        evidence.append(f"{tips} tips, {lessons} lessons (basic learning)")
    else:
        evidence.append("No tips or lessons recorded")
    
    if meta_insights > 10:
        evidence.append(f"{meta_insights} meta-insights (deep reflection)")
    
    if patterns >= 5:
        evidence.append(f"{patterns} strategy types tracked")
    
    return {"score": score, "evidence": evidence}


def score_error_recovery(db) -> dict:
    """Score based on: recovery tips, circuit breaker state, tool failure handling.
    Uses tool_capability.db for real success rates (cerebrum tool_stats has wrong schema)."""
    try:
        recovery_tips = db.execute("SELECT COUNT(*) FROM distilled_tips WHERE tip_type='recovery'").fetchone()[0]
    except:
        recovery_tips = 0
    
    try:
        cb_state = db.execute("SELECT COUNT(*) FROM circuit_breaker WHERE state='OPEN'").fetchone()[0]
    except:
        cb_state = 0
    
    # Read from tool_capability.db (the REAL tool stats)
    try:
        cap_db_path = os.path.expanduser("~/.hermes/tool_capability.db")
        if os.path.exists(cap_db_path):
            cap_db = sqlite3.connect(cap_db_path, timeout=5)
            total_calls = cap_db.execute("SELECT SUM(total_calls) FROM tool_stats").fetchone()[0] or 0
            success_calls = cap_db.execute("SELECT SUM(successes) FROM tool_stats").fetchone()[0] or 0
            cap_db.close()
            success_rate = success_calls / total_calls if total_calls else 0
        else:
            raise Exception("no tool_capability.db")
    except:
        # Fallback to cerebrum (may be wrong)
        try:
            total_calls = db.execute("SELECT SUM(total_calls) FROM tool_stats").fetchone()[0] or 0
            success_calls = db.execute("SELECT SUM(successes) FROM tool_stats").fetchone()[0] or 0
            success_rate = success_calls / total_calls if total_calls else 0
        except:
            success_rate = 0
            total_calls = 0
    
    score = 1
    evidence = []
    
    if recovery_tips > 50 and success_rate > 0.7:
        score = 5
    elif recovery_tips > 20 and success_rate > 0.6:
        score = 4
    elif recovery_tips > 5 and success_rate > 0.5:
        score = 3
    elif recovery_tips > 0:
        score = 2
    
    evidence.append(f"{recovery_tips} recovery tips")
    evidence.append(f"Overall success rate: {success_rate:.1%} ({total_calls} calls)")
    
    if cb_state > 0:
        evidence.append(f"{cb_state} circuit breakers OPEN (protecting)")
    
    return {"score": score, "evidence": evidence}


def score_task_selection(db) -> dict:
    """Score based on: active inference, cycle progress, goal management."""
    try:
        agi_cycle = 0
        roadmap_path = os.path.expanduser("~/hermes-agent/agent/agi_roadmap.json")
        if os.path.exists(roadmap_path):
            roadmap = json.load(open(roadmap_path))
            agi_cycle = roadmap.get("current_cycle", 0)
    except:
        agi_cycle = 0
    
    try:
        domains = db.execute("SELECT COUNT(DISTINCT domain) FROM domain_calibration WHERE prediction_count > 0").fetchone()[0]
    except:
        domains = 0
    
    try:
        pending_tasks = count_rows(db, "exploration_tasks")
    except:
        pending_tasks = 0
    
    score = 1
    evidence = []
    
    if agi_cycle > 100 and domains >= 5:
        score = 5
    elif agi_cycle > 30 and domains >= 3:
        score = 4
    elif agi_cycle > 10 and domains >= 2:
        score = 3
    elif agi_cycle > 0:
        score = 2
    
    evidence.append(f"AGI cycle {agi_cycle}/1000")
    evidence.append(f"{domains} domains calibrated")
    evidence.append(f"{pending_tasks} exploration tasks pending")
    
    return {"score": score, "evidence": evidence}


def score_context_management(db) -> dict:
    """Score based on: facts stored, compression config, reservoir usage."""
    try:
        facts = db.execute("SELECT COUNT(*) FROM semantic_facts").fetchone()[0]
    except:
        facts = 0
    
    try:
        reservoir_pages = count_rows(db, "context_reservoir")
    except:
        reservoir_pages = 0
    
    score = 1
    evidence = []
    
    if facts > 500 and reservoir_pages > 10:
        score = 5
    elif facts > 200 and reservoir_pages > 0:
        score = 4
    elif facts > 50:
        score = 3
    elif facts > 10:
        score = 2
    
    evidence.append(f"{facts} semantic facts stored")
    evidence.append(f"{reservoir_pages} context pages in reservoir")
    
    return {"score": score, "evidence": evidence}


def score_tool_mastery(db) -> dict:
    """Score based on: tools mastered, confidence levels, call distribution."""
    try:
        mastered = db.execute("SELECT COUNT(*) FROM mastery_scores WHERE level='mastered'").fetchone()[0]
    except:
        mastered = 0
    
    try:
        total_tools = db.execute("SELECT COUNT(*) FROM mastery_scores").fetchone()[0]
    except:
        total_tools = 0
    
    try:
        avg_confidence = db.execute("SELECT AVG(confidence) FROM mastery_scores").fetchone()[0] or 0
    except:
        avg_confidence = 0
    
    score = 1
    evidence = []
    
    if mastered >= 10 and avg_confidence > 0.7:
        score = 5
    elif mastered >= 5 and avg_confidence > 0.5:
        score = 4
    elif mastered >= 3:
        score = 3
    elif mastered >= 1:
        score = 2
    
    mastery_pct = (mastered / total_tools * 100) if total_tools else 0
    evidence.append(f"{mastered}/{total_tools} tools mastered ({mastery_pct:.0f}%)")
    evidence.append(f"Average confidence: {avg_confidence:.2f}")
    
    return {"score": score, "evidence": evidence}


def compute_scorecard(db=None) -> dict:
    """Compute the full agent scorecard."""
    if db is None:
        db = get_db()
    
    dimensions = {
        "SELF_IMPROVEMENT": score_self_improvement(db),
        "ERROR_RECOVERY": score_error_recovery(db),
        "TASK_SELECTION": score_task_selection(db),
        "CONTEXT_MANAGEMENT": score_context_management(db),
        "TOOL_MASTERY": score_tool_mastery(db),
    }
    
    # Weighted average
    weighted_sum = sum(dimensions[d]["score"] * DIMENSION_WEIGHTS[d] for d in dimensions)
    
    # Determine level
    if weighted_sum >= 4.5:
        level = 5
    elif weighted_sum >= 3.5:
        level = 4
    elif weighted_sum >= 2.5:
        level = 3
    elif weighted_sum >= 1.5:
        level = 2
    else:
        level = 1
    
    return {
        "overall_score": round(weighted_sum, 2),
        "level": level,
        "level_name": LEVEL_NAMES[level],
        "dimensions": dimensions,
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S'),
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: agent_scorecard.py <score|detail|history>'}))
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'score':
        card = compute_scorecard()
        print(f"Level: L{card['level']} — {card['level_name']}")
        print(f"Overall: {card['overall_score']:.2f}/5.00")
        for dim, data in card['dimensions'].items():
            print(f"  {dim:25s} {data['score']}/5  ({', '.join(data['evidence'][:2])})")
    
    elif cmd == 'detail':
        card = compute_scorecard()
        print(json.dumps(card, indent=2))
    
    else:
        print(json.dumps({'error': f'Unknown command: {cmd}'}))
