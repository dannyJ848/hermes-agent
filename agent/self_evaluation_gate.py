"""Self-Evaluation Gate — forces quality review before delivering output.

Wired into the conversation loop to:
1. Evaluate every response before delivery
2. Gate-check: block low-quality output
3. Force self-review on complex tasks
4. Track quality metrics over time
"""

import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = Path.home() / ".hermes" / "evaluation_gate.db"


@dataclass
class QualityScore:
    """Quality dimensions for a response."""
    overall: float = 0.0
    accuracy: float = 0.0
    completeness: float = 0.0
    clarity: float = 0.0
    safety: float = 1.0
    reasoning: float = 0.0
    
    @property
    def passed(self) -> bool:
        return self.overall >= 0.6 and self.accuracy >= 0.5 and self.safety >= 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall,
            "accuracy": self.accuracy,
            "completeness": self.completeness,
            "clarity": self.clarity,
            "safety": self.safety,
            "reasoning": self.reasoning,
            "passed": self.passed,
        }


@dataclass
class EvaluationResult:
    """Full evaluation result with feedback."""
    score: QualityScore
    feedback: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    should_redo: bool = False
    confidence: float = 0.0


class SelfEvaluationGate:
    """Quality gate that evaluates responses before delivery.
    
    Uses heuristic scoring + optional LLM-based review.
    Tracks quality trends in SQLite.
    """
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_db()
        self._session_scores: List[QualityScore] = []
        self._total_evaluations = 0
        self._passed_count = 0
    
    def _ensure_db(self):
        """Create evaluation tracking tables."""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT,
                    timestamp REAL,
                    overall REAL,
                    accuracy REAL,
                    completeness REAL,
                    clarity REAL,
                    safety REAL,
                    reasoning REAL,
                    passed INTEGER,
                    feedback TEXT,
                    response_preview TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_trends (
                    date TEXT PRIMARY KEY,
                    avg_overall REAL,
                    avg_accuracy REAL,
                    pass_rate REAL,
                    total_evals INTEGER
                )
            """)
    
    def evaluate(
        self,
        response: str,
        task_type: str = "general",
        complexity: str = "medium",
        session_id: str = "",
        tool_calls_used: int = 0,
        iteration_count: int = 0,
    ) -> EvaluationResult:
        """Evaluate a response across multiple quality dimensions.
        
        Returns EvaluationResult with score, feedback, and redo recommendation.
        """
        score = QualityScore()
        feedback = []
        improvements = []
        
        # ── Heuristic scoring ──
        
        # 1. Accuracy: check for common error patterns
        error_patterns = [
            "I apologize", "I'm sorry", "I cannot", "I can't",
            "error occurred", "failed to", "unable to",
        ]
        error_hits = sum(1 for p in error_patterns if p.lower() in response.lower())
        score.accuracy = max(0.0, 1.0 - (error_hits * 0.15))
        if error_hits > 0:
            feedback.append(f"Detected {error_hits} potential error indicators")
            improvements.append("Verify all claims and fix any errors before delivery")
        
        # 2. Completeness: response length + structure
        word_count = len(response.split())
        has_structure = any(marker in response for marker in ["===", "---", "##", "**", "1.", "2."])
        has_code = "```" in response
        
        if complexity == "high":
            score.completeness = min(1.0, word_count / 200)
        elif complexity == "medium":
            score.completeness = min(1.0, word_count / 100)
        else:
            score.completeness = min(1.0, word_count / 50)
        
        if has_structure:
            score.completeness = min(1.0, score.completeness + 0.2)
        if has_code and task_type in ("coding", "debugging", "devops"):
            score.completeness = min(1.0, score.completeness + 0.15)
        
        if score.completeness < 0.5:
            feedback.append("Response may be incomplete")
            improvements.append("Expand explanation with more detail")
        
        # 3. Clarity: readability markers
        has_examples = "example" in response.lower() or "e.g." in response.lower()
        has_steps = any(marker in response for marker in ["Step", "step", "First", "Then", "Finally"])
        
        score.clarity = 0.5
        if has_structure:
            score.clarity += 0.2
        if has_examples:
            score.clarity += 0.15
        if has_steps:
            score.clarity += 0.15
        
        # 4. Safety: check for dangerous content
        dangerous = [
            "rm -rf /", "DROP TABLE", "DELETE FROM", "format c:",
            "sudo rm", ":(){ :|:& };:", "> /dev/sda",
        ]
        danger_hits = sum(1 for d in dangerous if d in response)
        score.safety = 1.0 if danger_hits == 0 else max(0.0, 1.0 - (danger_hits * 0.3))
        if danger_hits > 0:
            feedback.append(f"WARNING: {danger_hits} potentially dangerous patterns detected")
            improvements.append("Remove dangerous commands or add safety warnings")
        
        # 5. Reasoning: check for reasoning depth
        reasoning_markers = [
            "because", "therefore", "however", "although", "since",
            "reason", "analysis", "evaluate", "compare", "consider",
        ]
        reasoning_hits = sum(1 for r in reasoning_markers if r in response.lower())
        score.reasoning = min(1.0, reasoning_hits / 5)
        
        if score.reasoning < 0.3 and complexity == "high":
            feedback.append("Limited reasoning depth for complex task")
            improvements.append("Add explicit reasoning steps")
        
        # Overall: weighted average
        score.overall = (
            score.accuracy * 0.25 +
            score.completeness * 0.20 +
            score.clarity * 0.20 +
            score.safety * 0.20 +
            score.reasoning * 0.15
        )
        
        # ── Determine if redo needed ──
        should_redo = not score.passed
        
        # High-complexity tasks need higher bar
        if complexity == "high" and score.overall < 0.7:
            should_redo = True
            improvements.append("Complex task requires more thorough response")
        
        # Many tool calls but low completeness = likely rushed
        if tool_calls_used > 5 and score.completeness < 0.6:
            should_redo = True
            improvements.append("Many tools used but explanation is thin — consolidate findings")
        
        # ── Persist ──
        self._persist_evaluation(score, feedback, response[:500], session_id)
        self._session_scores.append(score)
        self._total_evaluations += 1
        if score.passed:
            self._passed_count += 1
        
        return EvaluationResult(
            score=score,
            feedback=feedback,
            improvements=improvements,
            should_redo=should_redo,
            confidence=min(1.0, 0.5 + len(feedback) * 0.1),
        )
    
    def gate_check(self, evaluation: EvaluationResult) -> Tuple[bool, str]:
        """Check if response passes the gate.
        
        Returns: (passed, message)
        """
        if evaluation.should_redo:
            msg = f"GATE BLOCKED: Quality score {evaluation.score.overall:.0%} below threshold. Issues: {', '.join(evaluation.improvements[:3])}"
            return False, msg
        
        if not evaluation.score.passed:
            msg = f"GATE WARNING: Quality score {evaluation.score.overall:.0%}. {len(evaluation.feedback)} issues found."
            return True, msg  # Allow through with warning
        
        return True, f"GATE PASSED: Quality score {evaluation.score.overall:.0%}"
    
    def should_proceed(self, task_complexity: str = "medium", current_iteration: int = 0) -> bool:
        """Determine if we should proceed or pause for review.
        
        Called before starting work on a task.
        """
        # Always proceed for simple tasks
        if task_complexity == "low":
            return True
        
        # For high complexity, check if we've been struggling
        if task_complexity == "high" and current_iteration > 10:
            # If we've done many iterations, force a review
            return False
        
        return True
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get quality summary for current session."""
        if not self._session_scores:
            return {"evaluations": 0, "avg_score": 0, "pass_rate": 0}
        
        avg = sum(s.overall for s in self._session_scores) / len(self._session_scores)
        passed = sum(1 for s in self._session_scores if s.passed)
        
        return {
            "evaluations": len(self._session_scores),
            "avg_score": round(avg, 2),
            "pass_rate": round(passed / len(self._session_scores), 2),
            "last_score": self._session_scores[-1].overall if self._session_scores else 0,
        }
    
    def _persist_evaluation(self, score: QualityScore, feedback: List[str], preview: str, session_id: str):
        """Save evaluation to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO evaluations 
                    (session_id, timestamp, overall, accuracy, completeness, clarity, safety, reasoning, passed, feedback, response_preview)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, time.time(),
                    score.overall, score.accuracy, score.completeness,
                    score.clarity, score.safety, score.reasoning,
                    int(score.passed), json.dumps(feedback), preview
                ))
        except Exception:
            pass  # Non-critical
    
    def get_quality_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get quality trend over last N days."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT date, avg_overall, avg_accuracy, pass_rate, total_evals
                    FROM quality_trends
                    WHERE date >= date('now', '-{} days')
                    ORDER BY date
                """.format(days))
                return [
                    {"date": row[0], "avg_overall": row[1], "avg_accuracy": row[2],
                     "pass_rate": row[3], "total_evals": row[4]}
                    for row in cursor.fetchall()
                ]
        except Exception:
            return []
