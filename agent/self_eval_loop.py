#!/usr/bin/env python3
"""R116 BUILD: Self-Evaluation Loop — trajectory-level quality scoring.

Based on research: AgentEval (Salehi 2024), LLM-as-Judge (Zheng 2023),
trajectory-level scoring vs outcome-only, 4-axis rubric.

Features:
- Per-step trajectory scoring on 4 axes
- Sliding-window quality tracking per session
- Calibration: compares self-eval vs actual outcomes
- Injects quality warnings when recent performance drops
- Auto-detects repetition loops and brute-force patterns
"""

import sqlite3, time, json, os
from pathlib import Path
from collections import defaultdict

DB_PATH = str(Path.home() / "hermes-agent" / "self_eval.db")

# 4-axis rubric from AgentEval research
AXES = {
    "correctness": {"weight": 0.40, "desc": "Is the output factually and logically correct?"},
    "completeness": {"weight": 0.25, "desc": "Does it fully address the task requirements?"},
    "reasoning": {"weight": 0.20, "desc": "Is the reasoning chain sound and efficient?"},
    "efficiency": {"weight": 0.15, "desc": "Were tool calls minimal and well-chosen?"},
}

# Quality thresholds
QUALITY_HIGH = 0.8
QUALITY_LOW = 0.4
REPETITION_THRESHOLD = 3  # same tool+error 3+ times = brute force


def _ensure_eval_db():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS trajectory_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            step_number INTEGER NOT NULL,
            tool_name TEXT NOT NULL,
            status TEXT NOT NULL,
            correctness REAL DEFAULT 0.5,
            completeness REAL DEFAULT 0.5,
            reasoning REAL DEFAULT 0.5,
            efficiency REAL DEFAULT 0.5,
            composite_score REAL DEFAULT 0.5,
            is_repetition BOOLEAN DEFAULT 0,
            error_signature TEXT DEFAULT '',
            created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_traj_session ON trajectory_scores(session_id);
        CREATE INDEX IF NOT EXISTS idx_traj_tool ON trajectory_scores(tool_name);

        CREATE TABLE IF NOT EXISTS calibration_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            self_score REAL NOT NULL,
            actual_outcome REAL NOT NULL,
            calibration_error REAL NOT NULL,
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS session_quality (
            session_id TEXT PRIMARY KEY,
            total_steps INTEGER DEFAULT 0,
            avg_score REAL DEFAULT 0.5,
            score_window TEXT DEFAULT '[]',
            repetition_count INTEGER DEFAULT 0,
            brute_force_detected BOOLEAN DEFAULT 0,
            last_updated REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS eval_stats (
            id INTEGER PRIMARY KEY CHECK(id=1),
            total_evaluations INTEGER DEFAULT 0,
            avg_composite REAL DEFAULT 0.5,
            avg_calibration_error REAL DEFAULT 0,
            brute_force_events INTEGER DEFAULT 0
        );
    """)
    count = db.execute("SELECT COUNT(*) FROM eval_stats").fetchone()[0]
    if count == 0:
        db.execute("INSERT INTO eval_stats VALUES (1, 0, 0.5, 0, 0)")
    db.commit()
    db.close()


class SelfEvaluator:
    """Track and evaluate agent trajectory quality."""

    WINDOW_SIZE = 20  # sliding window for quality tracking

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._repetition_tracker = defaultdict(int)  # (tool, error_sig) -> count
        _ensure_eval_db()

    def score_step(self, tool_name: str, status: str, error: str = "",
                   tool_count_this_turn: int = 1) -> dict:
        """Score a single step on 4 axes using heuristic signals."""
        is_error = status == "error"
        error_sig = error[:60] if error else ""

        # Heuristic scoring based on observable signals
        if is_error:
            correctness = 0.2
            completeness = 0.1
            reasoning = 0.3
            efficiency = 0.2
        else:
            correctness = 0.85
            completeness = 0.8
            reasoning = 0.75
            efficiency = max(0.3, 1.0 - (tool_count_this_turn * 0.1))

        # Check for repetition (brute force detection)
        key = (tool_name, error_sig)
        self._repetition_tracker[key] += 1
        is_repetition = self._repetition_tracker[key] >= REPETITION_THRESHOLD
        if is_repetition:
            efficiency *= 0.5  # Heavy penalty for repetition

        composite = sum(
            AXES[axis]["weight"] * score
            for axis, score in [
                ("correctness", correctness),
                ("completeness", completeness),
                ("reasoning", reasoning),
                ("efficiency", efficiency),
            ]
        )

        result = {
            "tool": tool_name,
            "status": status,
            "correctness": round(correctness, 3),
            "completeness": round(completeness, 3),
            "reasoning": round(reasoning, 3),
            "efficiency": round(efficiency, 3),
            "composite": round(composite, 3),
            "is_repetition": is_repetition,
        }

        # Persist
        try:
            db = sqlite3.connect(DB_PATH, timeout=5)
            db.execute(
                "INSERT INTO trajectory_scores "
                "(session_id, step_number, tool_name, status, "
                "correctness, completeness, reasoning, efficiency, composite_score, "
                "is_repetition, error_signature, created_at) "
                "VALUES (?, (SELECT COALESCE(MAX(step_number),0)+1 FROM trajectory_scores WHERE session_id=?), "
                "?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.session_id, self.session_id,
                 tool_name, status,
                 correctness, completeness, reasoning, efficiency, composite,
                 1 if is_repetition else 0, error_sig, time.time())
            )
            # Update session quality
            self._update_session_quality(db, composite, is_repetition)
            # Update global stats (increment FIRST to avoid div-by-zero)
            db.execute(
                "UPDATE eval_stats SET total_evaluations=total_evaluations+1, "
                "avg_composite = (avg_composite * total_evaluations + ?) / (total_evaluations + 1)",
                (composite,)
            )
            if is_repetition:
                db.execute(
                    "UPDATE eval_stats SET brute_force_events=brute_force_events+1"
                )
            db.commit()
            db.close()
        except Exception:
            pass

        return result

    def _update_session_quality(self, db, new_score, is_repetition):
        """Update rolling session quality stats."""
        row = db.execute(
            "SELECT total_steps, score_window FROM session_quality WHERE session_id=?",
            (self.session_id,)
        ).fetchone()

        if row:
            total, window_json = row
            window = json.loads(window_json)
        else:
            total, window = 0, []

        window.append(new_score)
        if len(window) > self.WINDOW_SIZE:
            window = window[-self.WINDOW_SIZE:]

        avg = sum(window) / len(window) if window else 0.5
        rep_count = self._count_repetitions()

        db.execute(
            "INSERT OR REPLACE INTO session_quality "
            "(session_id, total_steps, avg_score, score_window, "
            "repetition_count, brute_force_detected, last_updated) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.session_id, total + 1, round(avg, 3), json.dumps(window),
             rep_count, 1 if rep_count > 3 else 0, time.time())
        )

    def _count_repetitions(self) -> int:
        return sum(1 for v in self._repetition_tracker.values() if v >= REPETITION_THRESHOLD)

    def get_quality_summary(self) -> str:
        """Build injection text for pre_llm_call."""
        try:
            db = sqlite3.connect(DB_PATH, timeout=3)
            row = db.execute(
                "SELECT avg_score, total_steps, repetition_count, brute_force_detected "
                "FROM session_quality WHERE session_id=?",
                (self.session_id,)
            ).fetchone()
            db.close()

            if not row or row[1] < 3:
                return ""

            avg, steps, reps, bf = row
            parts = [f"QUALITY: avg={avg:.2f} over {steps} steps"]

            if avg < QUALITY_LOW:
                parts.append("WARNING: low quality — reconsider approach")
            elif avg > QUALITY_HIGH:
                parts.append("performing well")

            if bf:
                parts.append(f"BRUTE_FORCE detected ({reps} repetition patterns) — switch strategy")

            return "[" + " | ".join(parts) + "]"
        except Exception:
            return ""

    def record_calibration(self, self_score: float, actual_outcome: float):
        """Record calibration data: did self-eval match reality?"""
        try:
            db = sqlite3.connect(DB_PATH, timeout=3)
            error = abs(self_score - actual_outcome)
            db.execute(
                "INSERT INTO calibration_log (session_id, self_score, actual_outcome, "
                "calibration_error, created_at) VALUES (?, ?, ?, ?, ?)",
                (self.session_id, self_score, actual_outcome, error, time.time())
            )
            db.execute(
                "UPDATE eval_stats SET avg_calibration_error = "
                "(SELECT AVG(calibration_error) FROM calibration_log)"
            )
            db.commit()
            db.close()
        except Exception:
            pass

    def get_stats(self) -> dict:
        try:
            db = sqlite3.connect(DB_PATH, timeout=3)
            row = db.execute(
                "SELECT total_evaluations, avg_composite, avg_calibration_error, "
                "brute_force_events FROM eval_stats WHERE id=1"
            ).fetchone()
            db.close()
            if row:
                return {
                    "total_evaluations": row[0],
                    "avg_composite": round(row[1] or 0.5, 3),
                    "calibration_error": round(row[2] if row[2] is not None else 0, 3),
                    "brute_force_events": row[3] or 0,
                }
            return {"total_evaluations": 0}
        except Exception:
            return {"total_evaluations": 0}


# Singleton per session
_instances = {}

def get_evaluator(session_id: str = None) -> SelfEvaluator:
    sid = session_id or os.environ.get("HERMES_SESSION_ID", "default")
    if sid not in _instances:
        _instances[sid] = SelfEvaluator(sid)
    return _instances[sid]
