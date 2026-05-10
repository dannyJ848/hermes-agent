#!/usr/bin/env python3
"""
Step Reward Scorer — PRM-style per-step evaluation for agent reasoning.

Based on: Process Reward Models (PRM), o1-style chain-of-thought scoring,
2025-2026 research on per-step reward signals.

Evaluates each tool call / reasoning step with a reward score and backtracks
if the score drops below threshold.

DB: ~/.hermes/cerebrum_memory.db (tables: step_rewards, reasoning_chains)

Usage:
  python3 step_reward.py start <task_description>
  python3 step_reward.py score <chain_id> <step_num> <reward_0_1> [--tool <name>] [--notes <text>]
  python3 step_reward.py check <chain_id>
  python3 step_reward.py chains [--limit <n>]
"""

import os
import sys
import json
import sqlite3
import time
import hashlib
from collections import defaultdict

DB_PATH = os.path.expanduser("~/.hermes/cerebrum_memory.db")

# Reward thresholds
BACKTRACK_THRESHOLD = 0.3
WARNING_THRESHOLD = 0.5
GOOD_THRESHOLD = 0.7

# Reward heuristics per tool
TOOL_REWARD_HINTS = {
    "terminal": {"success": 0.8, "failure": 0.2, "timeout": 0.1},
    "execute_code": {"success": 0.85, "failure": 0.15, "timeout": 0.1},
    "web_research": {"success": 0.9, "failure": 0.3, "timeout": 0.2},
    "web_extract": {"success": 0.85, "failure": 0.25, "timeout": 0.2},
    "patch": {"success": 0.9, "failure": 0.15, "timeout": 0.3},
    "write_file": {"success": 0.85, "failure": 0.2, "timeout": 0.3},
    "read_file": {"success": 0.95, "failure": 0.4, "timeout": 0.5},
    "search_files": {"success": 0.9, "failure": 0.5, "timeout": 0.4},
    "delegate_with_model": {"success": 0.8, "failure": 0.2, "timeout": 0.3},
    "memory": {"success": 0.9, "failure": 0.3, "timeout": 0.5},
    "autonomous_decide": {"success": 0.7, "failure": 0.3, "timeout": 0.4},
}


def get_db():
    return sqlite3.connect(DB_PATH)


def make_id(*args):
    raw = ":".join(str(a) for a in args) + str(time.time())
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def ensure_tables(db):
    db.execute("CREATE TABLE IF NOT EXISTS reasoning_chains ("
               "chain_id TEXT PRIMARY KEY, "
               "task_description TEXT, "
               "started_at REAL, "
               "ended_at REAL, "
               "total_steps INTEGER DEFAULT 0, "
               "total_reward REAL DEFAULT 0, "
               "avg_reward REAL DEFAULT 0, "
               "status TEXT DEFAULT 'active', "
               "backtrack_count INTEGER DEFAULT 0)")
    db.execute("CREATE TABLE IF NOT EXISTS step_rewards ("
               "step_id TEXT PRIMARY KEY, "
               "chain_id TEXT, "
               "step_num INTEGER, "
               "tool_name TEXT, "
               "reward REAL, "
               "notes TEXT, "
               "timestamp REAL, "
               "is_backtrack INTEGER DEFAULT 0, "
               " FOREIGN KEY (chain_id) REFERENCES reasoning_chains(chain_id))")
    db.execute("CREATE INDEX IF NOT EXISTS idx_rewards_chain ON step_rewards(chain_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_chains_status ON reasoning_chains(status)")
    db.commit()


def start_chain(task_description: str, db=None) -> dict:
    """Start a new reasoning chain."""
    if db is None:
        db = get_db()
    ensure_tables(db)
    
    chain_id = make_id("chain", task_description[:50])
    now = time.time()
    
    db.execute("INSERT INTO reasoning_chains VALUES (?, ?, ?, ?, 0, 0, 0, 'active', 0)",
              (chain_id, task_description, now, 0))
    db.commit()
    
    return {"chain_id": chain_id, "task": task_description, "status": "active"}


def score_step(chain_id: str, step_num: int, reward: float, tool_name: str = None, notes: str = None, db=None) -> dict:
    """Score a reasoning step and check for backtrack signals."""
    if db is None:
        db = get_db()
    ensure_tables(db)
    
    now = time.time()
    step_id = make_id(chain_id, step_num)
    
    # Determine if this is a backtrack step
    is_backtrack = 0
    action = "continue"
    
    if reward < BACKTRACK_THRESHOLD:
        is_backtrack = 1
        action = "BACKTRACK"
        db.execute("UPDATE reasoning_chains SET backtrack_count = backtrack_count + 1 WHERE chain_id=?",
                  (chain_id,))
    elif reward < WARNING_THRESHOLD:
        action = "caution"
    elif reward >= GOOD_THRESHOLD:
        action = "proceed"
    
    # Record the step
    db.execute("INSERT INTO step_rewards VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (step_id, chain_id, step_num, tool_name or "", reward, notes or "", now, is_backtrack))
    
    # Update chain totals
    chain = db.execute("SELECT total_steps, total_reward FROM reasoning_chains WHERE chain_id=?",
                      (chain_id,)).fetchone()
    if chain:
        total_steps, total_reward = chain
        new_steps = total_steps + 1
        new_reward = total_reward + reward
        avg_reward = new_reward / new_steps
        
        status = "active"
        if avg_reward < BACKTRACK_THRESHOLD and new_steps >= 3:
            status = "failing"
        
        db.execute("UPDATE reasoning_chains SET total_steps=?, total_reward=?, avg_reward=?, status=? WHERE chain_id=?",
                  (new_steps, new_reward, avg_reward, status, chain_id))
    
    db.commit()
    
    return {
        "chain_id": chain_id,
        "step": step_num,
        "reward": reward,
        "tool": tool_name,
        "action": action,
        "is_backtrack": bool(is_backtrack),
    }


def check_chain(chain_id: str, db=None) -> dict:
    """Check the status of a reasoning chain."""
    if db is None:
        db = get_db()
    ensure_tables(db)
    
    chain = db.execute("SELECT * FROM reasoning_chains WHERE chain_id=?", (chain_id,)).fetchone()
    if not chain:
        return {"error": "Chain not found"}
    
    steps = db.execute("SELECT step_num, tool_name, reward, notes, is_backtrack FROM step_rewards WHERE chain_id=? ORDER BY step_num",
                      (chain_id,)).fetchall()
    
    # Compute trajectory
    trajectory = []
    cumulative_reward = 0
    for s in steps:
        cumulative_reward += s[2]
        trajectory.append({
            "step": s[0],
            "tool": s[1],
            "reward": round(s[2], 3),
            "notes": s[3][:50] if s[3] else "",
            "backtrack": bool(s[4]),
            "cumulative_avg": round(cumulative_reward / s[0], 3),
        })
    
    # Trend analysis
    if len(trajectory) >= 3:
        recent_3 = [t["reward"] for t in trajectory[-3:]]
        trend = "improving" if recent_3[-1] > recent_3[0] else "declining"
    else:
        trend = "insufficient_data"
    
    return {
        "chain_id": chain[0],
        "task": chain[1],
        "total_steps": chain[4],
        "avg_reward": round(chain[6], 3),
        "status": chain[7],
        "backtracks": chain[8],
        "trend": trend,
        "trajectory": trajectory,
    }


def get_recent_chains(limit: int = 10, db=None) -> list:
    """Get recent reasoning chains."""
    if db is None:
        db = get_db()
    ensure_tables(db)
    
    chains = db.execute(
        "SELECT chain_id, task_description, total_steps, avg_reward, status, backtrack_count, started_at "
        "FROM reasoning_chains ORDER BY started_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    
    return [{
        "chain_id": c[0],
        "task": c[1][:60],
        "steps": c[2],
        "avg_reward": round(c[3], 3),
        "status": c[4],
        "backtracks": c[5],
        "started": c[6],
    } for c in chains]


def get_reward_stats(db=None) -> dict:
    """Get aggregate reward statistics."""
    if db is None:
        db = get_db()
    ensure_tables(db)
    
    total_chains = db.execute("SELECT COUNT(*) FROM reasoning_chains").fetchone()[0]
    active_chains = db.execute("SELECT COUNT(*) FROM reasoning_chains WHERE status='active'").fetchone()[0]
    failing_chains = db.execute("SELECT COUNT(*) FROM reasoning_chains WHERE status='failing'").fetchone()[0]
    completed_chains = db.execute("SELECT COUNT(*) FROM reasoning_chains WHERE status='complete'").fetchone()[0]
    
    total_steps = db.execute("SELECT COUNT(*) FROM step_rewards").fetchone()[0]
    backtrack_steps = db.execute("SELECT COUNT(*) FROM step_rewards WHERE is_backtrack=1").fetchone()[0]
    
    # Per-tool average rewards
    tool_rewards = db.execute(
        "SELECT tool_name, AVG(reward), COUNT(*) FROM step_rewards GROUP BY tool_name ORDER BY AVG(reward) DESC"
    ).fetchall()
    
    return {
        "total_chains": total_chains,
        "active": active_chains,
        "failing": failing_chains,
        "completed": completed_chains,
        "total_steps": total_steps,
        "backtrack_rate": round(backtrack_steps / max(total_steps, 1), 3),
        "tool_performance": [{
            "tool": t[0] or "unknown",
            "avg_reward": round(t[1], 3),
            "count": t[2],
        } for t in tool_rewards],
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: step_reward.py <command> [args]'}))
        sys.exit(1)
    
    cmd = sys.argv[1]
    db = get_db()
    ensure_tables(db)
    
    if cmd == 'start':
        desc = ' '.join(sys.argv[2:])
        result = start_chain(desc, db)
        print(json.dumps(result, indent=2))
    
    elif cmd == 'score':
        chain_id = sys.argv[2]
        step_num = int(sys.argv[3])
        reward = float(sys.argv[4])
        tool_name = None
        notes = None
        if '--tool' in sys.argv:
            tool_name = sys.argv[sys.argv.index('--tool') + 1]
        if '--notes' in sys.argv:
            notes = sys.argv[sys.argv.index('--notes') + 1]
        result = score_step(chain_id, step_num, reward, tool_name, notes, db)
        print(json.dumps(result, indent=2))
    
    elif cmd == 'check':
        chain_id = sys.argv[2]
        result = check_chain(chain_id, db)
        print(json.dumps(result, indent=2))
    
    elif cmd == 'chains':
        limit = 10
        if '--limit' in sys.argv:
            limit = int(sys.argv[sys.argv.index('--limit') + 1])
        result = get_recent_chains(limit, db)
        print(json.dumps(result, indent=2))
    
    elif cmd == 'stats':
        result = get_reward_stats(db)
        print(json.dumps(result, indent=2))
    
    else:
        print(json.dumps({'error': f'Unknown command: {cmd}'}))
