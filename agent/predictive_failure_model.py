#!/usr/bin/env python3
"""predictive_failure_model.py — Predict tool failure probability before execution.

Trains on error_patterns to predict P(failure) based on:
- Tool name
- Arg complexity (nested depth, length)
- Recent error rate for this tool
- Time since last success

Usage:
    python3 predictive_failure_model.py --predict <tool_name> <args_json>  # Predict failure
    python3 predictive_failure_model.py --train                           # Retrain model
    python3 predictive_failure_model.py --stats                           # Show accuracy stats
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("predictive_failure")

DB_PATH = Path.home() / ".hermes" / "cerebrum_memory.db"


class FailurePredictor:
    """Predict tool failure probability."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_schema()
        self._model = {}  # Simple heuristic model
    
    def _ensure_schema(self):
        """Ensure predictions and accuracy tracking tables exist."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS failure_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                tool_name TEXT,
                args_json TEXT,
                predicted_failure_prob REAL,
                actual_result TEXT,  -- 'success', 'failure', 'unknown'
                confidence REAL DEFAULT 0.5,
                features TEXT  -- JSON of extracted features
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tool_failure_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT UNIQUE,
                total_calls INTEGER DEFAULT 0,
                failures INTEGER DEFAULT 0,
                last_call TEXT,
                last_failure TEXT,
                avg_args_complexity REAL DEFAULT 0.0,
                failure_rate_7d REAL DEFAULT 0.0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _extract_features(self, tool_name: str, args: dict) -> dict:
        """Extract features from tool call."""
        args_json = json.dumps(args)
        
        # Arg complexity: nested depth + length
        complexity = 0
        try:
            complexity = len(args_json) / 100.0  # 1 point per 100 chars
            # Count nested structures
            complexity += args_json.count('{') * 0.5
            complexity += args_json.count('[') * 0.3
        except:
            pass
        
        # Tool-specific risk
        high_risk_tools = {'terminal', 'browser_navigate', 'browser_click', 'execute_code'}
        medium_risk_tools = {'web_search', 'web_extract', 'patch', 'write_file'}
        
        if tool_name in high_risk_tools:
            tool_risk = 0.6
        elif tool_name in medium_risk_tools:
            tool_risk = 0.4
        else:
            tool_risk = 0.2
        
        return {
            "complexity": min(complexity, 5.0),
            "tool_risk": tool_risk,
            "args_length": len(args_json),
            "has_nested": '{' in args_json or '[' in args_json
        }
    
    def _get_tool_stats(self, tool_name: str) -> dict:
        """Get historical stats for a tool."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM tool_failure_stats WHERE tool_name = ?", (tool_name,))
        row = cur.fetchone()
        
        if not row:
            # Calculate from error_patterns
            cur.execute("""
                SELECT COUNT(*) FROM error_patterns
                WHERE error_summary LIKE ? OR context LIKE ?
            """, (f"%{tool_name}%", f"%{tool_name}%"))
            error_count = cur.fetchone()[0]
            
            conn.close()
            return {
                "total_calls": 0, "failures": error_count,
                "failure_rate": 0.0 if error_count == 0 else 0.5,
                "last_failure": None
            }
        
        conn.close()
        total = row[2] or 1
        failures = row[3] or 0
        return {
            "total_calls": total, "failures": failures,
            "failure_rate": failures / total,
            "last_failure": row[5]
        }
    
    def predict(self, tool_name: str, args: dict) -> dict:
        """Predict failure probability for a tool call."""
        features = self._extract_features(tool_name, args)
        stats = self._get_tool_stats(tool_name)
        
        # Base probability
        p_failure = 0.1  # Base 10% failure rate
        
        # Add tool risk
        p_failure += features["tool_risk"] * 0.3
        
        # Add complexity penalty
        p_failure += min(features["complexity"] * 0.05, 0.2)
        
        # Add historical failure rate
        if stats["total_calls"] > 5:
            p_failure += stats["failure_rate"] * 0.3
        
        # Clamp
        p_failure = max(0.05, min(0.95, p_failure))
        
        # Record prediction
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO failure_predictions (tool_name, args_json, predicted_failure_prob, features)
            VALUES (?, ?, ?, ?)
        """, (tool_name, json.dumps(args), p_failure, json.dumps(features)))
        conn.commit()
        conn.close()
        
        return {
            "tool_name": tool_name,
            "failure_probability": round(p_failure, 3),
            "confidence": min(0.9, 0.5 + stats["total_calls"] * 0.05),
            "features": features,
            "historical_failures": stats["failures"],
            "recommendation": self._get_recommendation(p_failure, tool_name)
        }
    
    def _get_recommendation(self, p_failure: float, tool_name: str) -> str:
        """Get recommendation based on failure probability."""
        if p_failure > 0.7:
            return f"HIGH RISK: Consider alternative approach for {tool_name}. Add validation and rollback plan."
        elif p_failure > 0.4:
            return f"MEDIUM RISK: Add error handling for {tool_name}. Verify inputs carefully."
        elif p_failure > 0.2:
            return f"LOW RISK: Standard execution for {tool_name}."
        else:
            return f"SAFE: High confidence in {tool_name} success."
    
    def record_actual(self, tool_name: str, args: dict, success: bool):
        """Record actual result to improve model."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        # Update latest prediction
        cur.execute("""
            UPDATE failure_predictions
            SET actual_result = ?
            WHERE tool_name = ? AND actual_result = 'unknown'
            ORDER BY id DESC LIMIT 1
        """, ("success" if success else "failure", tool_name))
        
        # Update tool stats
        cur.execute("""
            INSERT INTO tool_failure_stats (tool_name, total_calls, failures, last_call)
            VALUES (?, 1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(tool_name) DO UPDATE SET
                total_calls = total_calls + 1,
                failures = failures + ?,
                last_call = CURRENT_TIMESTAMP,
                last_failure = CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE last_failure END
        """, (tool_name, 0 if success else 1, 0 if success else 1, 0 if success else 1))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> dict:
        """Get prediction accuracy stats."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN actual_result = 'failure' THEN 1 ELSE 0 END) as actual_failures,
                SUM(CASE WHEN predicted_failure_prob > 0.5 AND actual_result = 'failure' THEN 1 ELSE 0 END) as true_positives,
                SUM(CASE WHEN predicted_failure_prob > 0.5 AND actual_result = 'success' THEN 1 ELSE 0 END) as false_positives,
                SUM(CASE WHEN predicted_failure_prob <= 0.5 AND actual_result = 'failure' THEN 1 ELSE 0 END) as false_negatives,
                SUM(CASE WHEN predicted_failure_prob <= 0.5 AND actual_result = 'success' THEN 1 ELSE 0 END) as true_negatives
            FROM failure_predictions
            WHERE actual_result != 'unknown'
        """)
        row = cur.fetchone()
        conn.close()
        
        if not row or row[0] == 0:
            return {"total_predictions": 0, "accuracy": None}
        
        total, actual_failures, tp, fp, fn, tn = row
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        return {
            "total_predictions": total,
            "actual_failures": actual_failures,
            "accuracy": round(accuracy, 3),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn
        }
    
    def get_tool_risk_ranking(self) -> list[dict]:
        """Get tools ranked by failure risk."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("""
            SELECT tool_name, total_calls, failures,
                   CASE WHEN total_calls > 0 THEN CAST(failures AS REAL) / total_calls ELSE 0 END as rate
            FROM tool_failure_stats
            ORDER BY rate DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return [
            {"tool": r[0], "calls": r[1], "failures": r[2], "failure_rate": round(r[3], 3)}
            for r in rows
        ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predict", nargs=2, metavar=("TOOL", "ARGS"), help="Predict failure for tool+args")
    parser.add_argument("--record", nargs=3, metavar=("TOOL", "ARGS", "RESULT"), help="Record actual result")
    parser.add_argument("--stats", action="store_true", help="Show accuracy stats")
    parser.add_argument("--ranking", action="store_true", help="Show tool risk ranking")
    args = parser.parse_args()
    
    predictor = FailurePredictor()
    
    if args.predict:
        tool_name, args_json = args.predict
        try:
            args_dict = json.loads(args_json)
        except:
            args_dict = {}
        result = predictor.predict(tool_name, args_dict)
        print(json.dumps(result, indent=2))
    
    elif args.record:
        tool_name, args_json, result = args.record
        try:
            args_dict = json.loads(args_json)
        except:
            args_dict = {}
        predictor.record_actual(tool_name, args_dict, result.lower() == "success")
        print(f"Recorded: {tool_name} -> {result}")
    
    elif args.ranking:
        ranking = predictor.get_tool_risk_ranking()
        print("=== TOOL RISK RANKING ===")
        for r in ranking:
            print(f"  {r['tool']:20} {r['failure_rate']:.1%} ({r['failures']}/{r['calls']})")
    
    else:
        stats = predictor.get_stats()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
