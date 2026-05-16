"""
predictive_failure_prevention.py — Before-action risk scoring.

Scores each planned action for predicted failure probability BEFORE execution.
Queries error patterns, tool oracle, and context sculptor to compute risk.
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class RiskAssessment:
    action_type: str
    risk_score: float  # 0.0 = safe, 1.0 = certain failure
    risk_level: str    # 'low', 'medium', 'high', 'critical'
    factors: List[Dict[str, Any]]
    mitigation: List[str]
    proceed: bool      # Recommendation


class PredictiveFailurePrevention:
    """Predict and prevent failures before they happen."""

    def __init__(self, error_learning=None, tool_oracle=None, context_sculptor=None):
        self.error_learning = error_learning
        self.tool_oracle = tool_oracle
        self.context_sculptor = context_sculptor
        self._failure_history = {}  # action_type -> {count, failures}

    def assess_risk(self, action_type: str, detail: str, context: str = "") -> RiskAssessment:
        """Assess risk of a planned action."""
        factors = []
        risk_score = 0.0

        # Factor 1: Historical failure rate for this tool
        hist_risk = self._get_historical_risk(action_type)
        if hist_risk > 0:
            factors.append({
                'factor': 'historical_failure_rate',
                'weight': 0.3,
                'score': hist_risk,
                'detail': f"{hist_risk:.1%} historical failure rate for {action_type}"
            })
            risk_score += hist_risk * 0.3

        # Factor 2: Error pattern match
        if self.error_learning:
            try:
                # Check if similar actions recently failed
                patterns = self.error_learning.get_patterns_for_tool(action_type)
                if patterns:
                    recent_failures = sum(1 for p in patterns if p.get('occurrence_count', 0) > 1)
                    pattern_risk = min(0.8, recent_failures / 5)
                    factors.append({
                        'factor': 'error_pattern_match',
                        'weight': 0.25,
                        'score': pattern_risk,
                        'detail': f"{recent_failures} recurring error patterns for {action_type}"
                    })
                    risk_score += pattern_risk * 0.25
            except Exception:
                pass

        # Factor 3: Context complexity
        if self.context_sculptor:
            try:
                # Estimate task complexity from context
                complexity = self._estimate_complexity(detail, context)
                factors.append({
                    'factor': 'task_complexity',
                    'weight': 0.2,
                    'score': complexity,
                    'detail': f"Task complexity: {complexity:.2f}"
                })
                risk_score += complexity * 0.2
            except Exception:
                pass

        # Factor 4: Tool oracle confidence
        if self.tool_oracle:
            try:
                pred = self.tool_oracle.predict_for_query(context, [action_type])
                oracle_conf = pred.get('confidence', 0.5)
                # Low oracle confidence = higher risk
                oracle_risk = 1.0 - oracle_conf
                factors.append({
                    'factor': 'tool_oracle_uncertainty',
                    'weight': 0.15,
                    'score': oracle_risk,
                    'detail': f"Tool oracle confidence: {oracle_conf:.2f}"
                })
                risk_score += oracle_risk * 0.15
            except Exception:
                pass

        # Factor 5: Detail quality (heuristic)
        detail_risk = self._assess_detail_quality(action_type, detail)
        factors.append({
            'factor': 'detail_quality',
            'weight': 0.1,
            'score': detail_risk,
            'detail': f"Detail completeness: {1-detail_risk:.2f}"
        })
        risk_score += detail_risk * 0.1

        # Clamp and classify
        risk_score = min(1.0, max(0.0, risk_score))
        risk_level = self._classify_risk(risk_score)

        # Generate mitigations
        mitigations = self._generate_mitigations(risk_score, factors, action_type)

        return RiskAssessment(
            action_type=action_type,
            risk_score=risk_score,
            risk_level=risk_level,
            factors=factors,
            mitigation=mitigations,
            proceed=risk_score < 0.7
        )

    def _get_historical_risk(self, action_type: str) -> float:
        """Get historical failure rate for a tool."""
        if action_type not in self._failure_history:
            # Try to load from experiences DB
            try:
                import sqlite3
                from pathlib import Path
                db = sqlite3.connect(str(Path.home() / ".hermes" / "cerebrum_memory.db"))
                db.row_factory = sqlite3.Row
                row = db.execute(
                    "SELECT COUNT(*) as total, SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes FROM experiences WHERE task_type = ?",
                    (action_type,)
                ).fetchone()
                db.close()
                if row and row['total'] > 0:
                    failures = row['total'] - row['successes']
                    self._failure_history[action_type] = {
                        'total': row['total'],
                        'failures': failures
                    }
                    return failures / row['total']
            except Exception:
                pass
            return 0.0

        hist = self._failure_history[action_type]
        return hist['failures'] / hist['total'] if hist['total'] > 0 else 0.0

    def _estimate_complexity(self, detail: str, context: str) -> float:
        """Estimate task complexity from detail and context."""
        complexity = 0.3  # Base

        # Longer details = more complex
        detail_len = len(detail)
        if detail_len > 1000:
            complexity += 0.2
        elif detail_len > 500:
            complexity += 0.1

        # Multiple operations in one call
        if isinstance(detail, str):
            if detail.count('&&') > 1 or detail.count('||') > 1:
                complexity += 0.15

        # Context mentions error or failure
        if context and any(w in context.lower() for w in ['error', 'fail', 'bug', 'crash', 'timeout']):
            complexity += 0.15

        return min(1.0, complexity)

    def _assess_detail_quality(self, action_type: str, detail: str) -> float:
        """Assess if detail has enough information. Returns risk (0=good, 1=bad)."""
        risk = 0.0

        if not detail or detail == '{}':
            risk += 0.5

        # Check for required fields per action type
        required_fields = {
            'patch': ['path', 'old_string', 'new_string'],
            'terminal': ['command'],
            'read_file': ['path'],
            'write_file': ['path', 'content'],
            'delegate_task': ['goal'],
            'web_search': ['query'],
        }

        if action_type in required_fields:
            try:
                parsed = json.loads(detail) if isinstance(detail, str) else detail
                if isinstance(parsed, dict):
                    missing = [f for f in required_fields[action_type] if f not in parsed or not parsed[f]]
                    if missing:
                        risk += 0.3 * len(missing) / len(required_fields[action_type])
            except Exception:
                risk += 0.2

        return min(1.0, risk)

    def _classify_risk(self, score: float) -> str:
        if score < 0.2:
            return 'low'
        elif score < 0.4:
            return 'medium'
        elif score < 0.7:
            return 'high'
        return 'critical'

    def _generate_mitigations(self, risk_score: float, factors: List[Dict], action_type: str) -> List[str]:
        mitigations = []

        if risk_score >= 0.7:
            mitigations.append(f"HIGH RISK: Consider breaking {action_type} into smaller steps")

        for factor in factors:
            if factor['score'] > 0.5:
                if factor['factor'] == 'historical_failure_rate':
                    mitigations.append("Review past failures for this tool before proceeding")
                elif factor['factor'] == 'error_pattern_match':
                    mitigations.append("Similar errors have occurred — verify inputs carefully")
                elif factor['factor'] == 'task_complexity':
                    mitigations.append("Complex task — consider delegating to subagent")
                elif factor['factor'] == 'detail_quality':
                    mitigations.append("Incomplete parameters — fill in missing fields")

        if not mitigations:
            mitigations.append("Standard precautions apply")

        return mitigations

    def record_outcome(self, action_type: str, detail: str, success: bool, error: str = ""):
        """Record outcome to improve future risk assessments."""
        if action_type not in self._failure_history:
            self._failure_history[action_type] = {'total': 0, 'failures': 0}
        self._failure_history[action_type]['total'] += 1
        if not success:
            self._failure_history[action_type]['failures'] += 1
