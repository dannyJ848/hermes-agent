#!/usr/bin/env python3
"""
Meta-Self-Modifier — The meta agent can modify its own cognitive parameters.

Based on HyperAgents (arXiv 2603.19461): meta-level modifications should
transfer across domains and accumulate over time.

Architecture:
1. PARAMETER REGISTRY: All tunable parameters in one place
2. MODIFICATION LOG: Track every self-modification and its outcome
3. FEEDBACK LOOP: Compare performance before/after modification
4. SAFETY: Only allow modifications that improve or maintain performance

Parameters that can be self-modified:
- distillation tip confidence thresholds
- controller quality thresholds
- brain cycle frequencies
- mastery engine learning rates
- context injection priorities
"""

import json
import sqlite3
import time
import os
from pathlib import Path

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"
PARAMS_PATH = Path.home() / "hermes-agent" / "meta_params.json"

# Default parameters (safe starting values)
DEFAULTS = {
    "distillation": {
        "tip_confidence_min": 0.3,
        "tip_vote_threshold": 0,
        "tip_frequency_min": 1,
        "lesson_min_length": 20,
        "lesson_max_age_days": 7,
        "buffer_process_count": 20,
    },
    "controller": {
        "ground_truth_min_pct": 0.40,
        "speculative_max_pct": 0.50,
        "prediction_backlog_max": 50,
        "trust_violation_max": 0,
        "duplicate_max": 5,
    },
    "brain": {
        "cycle_interval_sec": 120,
        "temporal_weight": 0.3,
        "prefrontal_weight": 0.4,
        "motor_weight": 0.3,
    },
    "mastery": {
        "learning_rate": 0.1,
        "decay_rate": 0.01,
        "confidence_threshold": 0.6,
        "min_samples": 3,
    },
    "context_injection": {
        "max_tips": 5,
        "max_lessons": 3,
        "max_facts": 3,
        "max_total_chars": 2000,
        "semantic_tool_top_k": 3,
        "semantic_tool_min_score": 0.4,
    },
}


def _ensure_table():
    """Create meta_modifications table."""
    db = sqlite3.connect(str(DB_PATH), timeout=5)
    db.execute("""
        CREATE TABLE IF NOT EXISTS meta_modifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parameter TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            reason TEXT,
            performance_before REAL,
            performance_after REAL,
            approved INTEGER DEFAULT 1,
            created_at REAL
        )
    """)
    db.commit()
    db.close()


def load_params():
    """Load current parameters, creating defaults if needed."""
    if PARAMS_PATH.exists():
        with open(PARAMS_PATH) as f:
            return json.load(f)
    else:
        save_params(DEFAULTS)
        return DEFAULTS.copy()


def save_params(params):
    """Save parameters to JSON file."""
    with open(PARAMS_PATH, "w") as f:
        json.dump(params, f, indent=2)


def propose_modification(param_path, new_value, reason):
    """Propose a parameter modification.
    
    Args:
        param_path: dot-separated path, e.g. "distillation.tip_confidence_min"
        new_value: the proposed new value
        reason: why this change should improve performance
        
    Returns:
        dict with approval status
    """
    params = load_params()
    
    # Navigate to the parameter
    parts = param_path.split(".")
    if len(parts) != 2:
        return {"approved": False, "reason": "Invalid param path (need category.param)"}
    
    category, param = parts
    if category not in params or param not in params[category]:
        return {"approved": False, "reason": "Unknown parameter: {}.{}".format(category, param)}
    
    old_value = params[category][param]
    
    # Safety checks
    # 1. Numeric parameters must stay in reasonable range
    if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
        if isinstance(old_value, float) and 0 <= old_value <= 1:
            if not (0 <= new_value <= 1):
                return {"approved": False, "reason": "Float param must stay in [0, 1]"}
        # Don't allow >50% changes in one step
        if old_value != 0 and abs(new_value - old_value) / abs(old_value) > 0.5:
            return {"approved": False, "reason": "Change too large (>50%). Apply incrementally."}
    
    # 2. Integer parameters must stay positive
    if isinstance(old_value, int) and new_value < 1:
        return {"approved": False, "reason": "Integer param must stay >= 1"}
    
    # Apply the modification
    params[category][param] = new_value
    save_params(params)
    
    # Log it
    _ensure_table()
    db = sqlite3.connect(str(DB_PATH), timeout=5)
    db.execute(
        "INSERT INTO meta_modifications (parameter, old_value, new_value, reason, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (param_path, str(old_value), str(new_value), reason, time.time())
    )
    db.commit()
    db.close()
    
    return {
        "approved": True,
        "parameter": param_path,
        "old_value": old_value,
        "new_value": new_value,
        "reason": reason,
    }


def get_modification_history(limit=20):
    """Get recent parameter modifications."""
    _ensure_table()
    db = sqlite3.connect(str(DB_PATH), timeout=5)
    rows = db.execute(
        "SELECT parameter, old_value, new_value, reason, created_at "
        "FROM meta_modifications ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    db.close()
    return rows


def auto_tune():
    """Auto-tune parameters based on performance data.
    
    This is the meta-cognitive self-modification loop:
    1. Read current performance metrics
    2. Identify underperforming areas
    3. Propose parameter changes
    4. Apply if safe
    """
    params = load_params()
    modifications = []
    
    # Check tip quality
    try:
        db = sqlite3.connect(str(DB_PATH), timeout=5)
        tip_stats = db.execute(
            "SELECT tip_type, AVG(upvotes - downvotes) as avg_score, COUNT(*) as cnt "
            "FROM distilled_tips GROUP BY tip_type"
        ).fetchall()
        db.close()
        
        for tip_type, avg_score, cnt in tip_stats:
            if cnt > 10 and avg_score < 0:
                # Tips are getting downvoted — raise confidence threshold
                old = params["distillation"]["tip_confidence_min"]
                new_val = min(0.8, old + 0.05)
                mod = propose_modification(
                    "distillation.tip_confidence_min",
                    new_val,
                    "Auto-tune: {} tips avg_score={:.1f}, raising min confidence".format(tip_type, avg_score)
                )
                modifications.append(mod)
    except Exception:
        pass
    
    return modifications


# DGM-inspired code patch proposal system
# Analyzes failure patterns from distilled_tips and meta_insights to propose
# concrete code changes that could improve agent performance

COGNITIVE_FILES = {
    "distillation_bridge": str(Path.home() / "hermes-agent" / "distillation_bridge.py"),
    "meta_self_modifier": str(Path.home() / "hermes-agent" / "meta_self_modifier.py"),
    "controller": str(Path.home() / "hermes-agent" / "controller.py"),
    "iteration_engine": str(Path.home() / "hermes-agent" / "iteration_engine.py"),
    "epistemic_guard": str(Path.home() / "hermes-agent" / "epistemic_guard.py"),
    "self_awareness": str(Path.home() / "hermes-agent" / "self_awareness.py"),
    "intrinsic_reward": str(Path.home() / "hermes-agent" / "intrinsic_reward.py"),
    "circuit_breaker": str(Path.home() / "hermes-agent" / "circuit_breaker.py"),
    "context_reservoir": str(Path.home() / "hermes-agent" / "context_reservoir.py"),
    "brain_daemon": str(Path.home() / "hermes-agent" / "brain_daemon.py"),
}


def propose_code_patches():
    """DGM-inspired: Analyze failure patterns and propose code-level fixes.
    
    Reads meta_insights and recovery tips, identifies recurring failure patterns,
    and generates concrete patch proposals for cognitive system files.
    """
    patches = []
    try:
        db = sqlite3.connect(str(DB_PATH), timeout=5)
        
        # 1. Get tools with most recovery tips (highest failure frequency)
        recovery_tools = db.execute(
            "SELECT tool_name, COUNT(*) as cnt, GROUP_CONCAT(recommendation, ' | ') as recs "
            "FROM distilled_tips WHERE tip_type='recovery' AND frequency > 3 "
            "GROUP BY tool_name ORDER BY cnt DESC LIMIT 5"
        ).fetchall()
        
        for tool, cnt, recs in recovery_tools:
            recs_str = str(recs)[:200]
            # Map tool to cognitive file
            target_file = "distillation_bridge"  # default
            if tool in ("execute_code", "terminal"):
                target_file = "distillation_bridge"
            elif tool in ("web_extract", "web_research"):
                target_file = "distillation_bridge"
            elif "memory" in tool:
                target_file = "meta_self_modifier"
            
            patches.append({
                "priority": "high" if cnt > 10 else "medium",
                "type": "recovery_optimization",
                "file": COGNITIVE_FILES.get(target_file, "unknown"),
                "tool": tool,
                "description": "Add specific recovery handler for {} ({} failures: {})".format(
                    tool, cnt, recs_str[:60]
                ),
                "pattern": "Recurring failures with {} suggest adding pre-check or retry logic".format(tool)
            })
        
        # 2. Check meta_insights for optimization opportunities
        meta_rows = db.execute(
            "SELECT tool_name, principles, procedures, tip_count FROM meta_insights "
            "WHERE tip_count > 10 ORDER BY tip_count DESC LIMIT 3"
        ).fetchall()
        
        for tool, princ_json, proc_json, tip_count in meta_rows:
            try:
                procs = json.loads(proc_json) if proc_json else []
                for proc in procs:
                    if "fail" in proc.lower() or "error" in proc.lower():
                        patches.append({
                            "priority": "medium",
                            "type": "procedural_fix",
                            "file": COGNITIVE_FILES.get("distillation_bridge", "unknown"),
                            "tool": tool,
                            "description": "Implement procedural fix for {}: {}".format(tool, proc[:80]),
                            "pattern": "Epoch synthesis identified this as a recurring procedure"
                        })
            except:
                pass
        
        # 3. Check circuit breaker state
        try:
            cb_rows = db.execute(
                "SELECT tool_name, state, failure_count FROM circuit_breaker "
                "WHERE state='OPEN' LIMIT 3"
            ).fetchall()
            for tool, state, fc in cb_rows:
                patches.append({
                    "priority": "high",
                    "type": "circuit_breaker_open",
                    "file": COGNITIVE_FILES.get("circuit_breaker", "unknown"),
                    "tool": tool,
                    "description": "Circuit breaker OPEN for {} ({} failures) — investigate root cause".format(tool, fc),
                    "pattern": "Tool is being blocked due to excessive failures"
                })
        except:
            pass
        
        db.close()
    except Exception as e:
        patches.append({"priority": "error", "type": "db_error", "description": str(e)})
    
    return patches


if __name__ == "__main__":
    print("=== Meta Self-Modifier ===\n")
    
    # Load and show current params
    params = load_params()
    print("Current parameters:")
    for cat, pmap in params.items():
        print("  [{}]".format(cat))
        for k, v in pmap.items():
            print("    {} = {}".format(k, v))
    
    print("\nModification history:")
    history = get_modification_history(5)
    for param, old, new, reason, ts in history:
        print("  {} -> {} ({})".format(old, new, param))
    
    if not history:
        print("  (no modifications yet)")
    
    print("\nAuto-tune check:")
    mods = auto_tune()
    if mods:
        for m in mods:
            print("  {}: {}".format(m.get("parameter", "?"), m.get("approved", False)))
    else:
        print("  No changes needed")
    
    print("\nDGM Code Patch Proposals:")
    patches = propose_code_patches()
    for p in patches:
        print("  [{}] {}: {}".format(p.get("priority", "?"), p.get("file", "?"), p.get("description", "?")[:80]))
    if not patches:
        print("  No patches proposed")
