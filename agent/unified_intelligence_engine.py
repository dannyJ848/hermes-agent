"""
unified_intelligence_engine.py — Cross-system analytics and unified querying.

Queries across ALL cognitive databases to answer questions like:
- "What errors correlate with low success rates?"
- "Which tips are validated by actual outcomes?"
- "What's my learning velocity per tool?"
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import time


@dataclass
class CrossSystemInsight:
    query: str
    sources: List[str]
    confidence: float
    data: Dict[str, Any]
    recommendation: str


# ── UPSTREAM PATTERN: Iteration Budget Tracking (adapted from iteration_budget.py) ──
# Thread-safe budget tracking for cognitive subsystem operations.
# Prevents runaway subsystems from consuming all iterations.

import threading


class CognitiveIterationBudget:
    """Thread-safe iteration counter per cognitive subsystem.
    
    Adapted from upstream IterationBudget:
    - Each subsystem gets its own budget cap
    - Parent (orchestrator) has total budget
    - execute_code iterations are refunded (don't eat budget)
    """
    
    def __init__(self, max_total=100):
        self.max_total = max_total
        self._used = 0
        self._lock = threading.Lock()
        self._subsystem_usage = {}  # Track per-subsystem
    
    def consume(self, subsystem_name="general"):
        """Try to consume one iteration. Returns True if allowed."""
        with self._lock:
            if self._used >= self.max_total:
                return False
            self._used += 1
            self._subsystem_usage[subsystem_name] = self._subsystem_usage.get(subsystem_name, 0) + 1
            return True
    
    def refund(self, subsystem_name="general"):
        """Give back one iteration (e.g. for execute_code turns)."""
        with self._lock:
            if self._used > 0:
                self._used -= 1
                if subsystem_name in self._subsystem_usage:
                    self._subsystem_usage[subsystem_name] -= 1
    
    @property
    def used(self):
        with self._lock:
            return self._used
    
    @property
    def remaining(self):
        with self._lock:
            return max(0, self.max_total - self._used)
    
    def get_subsystem_report(self):
        """Get per-subsystem usage breakdown."""
        with self._lock:
            return dict(self._subsystem_usage)


class UnifiedIntelligenceEngine:
    """Cross-system query engine for the cognitive apparatus."""

    def __init__(self):
        self._db_paths = {
            'cerebrum': Path.home() / ".hermes" / "cerebrum_memory.db",
            'cortex': Path.home() / "hermes-agent" / "cerebrum_memory.db",
            'training': Path.home() / ".hermes" / "training_gym.db",
            'errors': Path.home() / ".hermes" / "error_patterns.db",
        }
        self._connections = {}
        # Initialize iteration budget tracking (upstream pattern)
        self._budget = CognitiveIterationBudget(max_total=100)
        self._budget_enabled = True

    def track_subsystem_call(self, subsystem_name, action_type):
        """Track a subsystem call against the iteration budget."""
        if not getattr(self, '_budget_enabled', False):
            return {"allowed": True, "budget_remaining": -1}
        
        allowed = self._budget.consume(subsystem_name)
        if not allowed:
            logger.warning("Budget exhausted for %s — skipping %s", subsystem_name, action_type)
        
        return {
            "allowed": allowed,
            "budget_remaining": self._budget.remaining,
            "subsystem_usage": self._budget.get_subsystem_report()
        }

    def get_budget_report(self):
        """Get full budget status report."""
        if not getattr(self, '_budget_enabled', False):
            return {"error": "Budget tracking not initialized"}
        
        return {
            "total_budget": self._budget.max_total,
            "used": self._budget.used,
            "remaining": self._budget.remaining,
            "per_subsystem": self._budget.get_subsystem_report(),
            "exhausted": self._budget.remaining <= 0
        }

    def _get_db(self, name: str) -> Optional[sqlite3.Connection]:
        if name not in self._connections:
            path = self._db_paths.get(name)
            if path and path.exists():
                self._connections[name] = sqlite3.connect(str(path))
                self._connections[name].row_factory = sqlite3.Row
        return self._connections.get(name)

    def query_error_success_correlation(self, tool_name: Optional[str] = None) -> CrossSystemInsight:
        """Which errors happen most often before failed actions?"""
        cerebrum = self._get_db('cerebrum')
        if not cerebrum:
            return CrossSystemInsight("error_success_correlation", [], 0.0, {}, "No cerebrum DB")

        # Join error_patterns with experiences
        query = """
            SELECT 
                ep.error_signature,
                ep.occurrence_count,
                ep.recovery_success_rate,
                COUNT(DISTINCT e.id) as associated_failures
            FROM error_patterns ep
            LEFT JOIN experiences e ON e.metadata LIKE '%' || ep.error_signature || '%'
            WHERE e.success = 0 OR e.success IS NULL
            GROUP BY ep.error_signature
            ORDER BY associated_failures DESC, ep.occurrence_count DESC
            LIMIT 10
        """
        try:
            rows = cerebrum.execute(query).fetchall()
        except Exception:
            # Fallback: query separately with correct schema
            errors = cerebrum.execute("""
                SELECT fingerprint as error_signature, occurrence_count, 
                       resolution_success_rate as recovery_success_rate
                FROM error_patterns 
                ORDER BY occurrence_count DESC LIMIT 10
            """).fetchall()
            rows = errors

        data = {
            'top_errors': [
                {
                    'signature': r['error_signature'][:80],
                    'occurrences': r['occurrence_count'],
                    'recovery_rate': r.get('recovery_success_rate', 0),
                }
                for r in rows
            ]
        }

        # Calculate correlation strength
        total_errors = sum(r['occurrence_count'] for r in rows) if rows else 0
        avg_recovery = sum(r.get('recovery_success_rate', 0) for r in rows) / len(rows) if rows else 0

        confidence = min(0.9, max(0.3, len(rows) / 20))

        recommendation = (
            f"Top {len(rows)} error patterns account for {total_errors} occurrences. "
            f"Average recovery rate: {avg_recovery:.1%}. "
            f"Focus on: {rows[0]['error_signature'][:60] if rows else 'N/A'}"
        )

        return CrossSystemInsight(
            query="error_success_correlation",
            sources=['error_patterns', 'experiences'],
            confidence=confidence,
            data=data,
            recommendation=recommendation
        )

    def query_tip_validation(self) -> CrossSystemInsight:
        """Which tips have been validated by actual outcomes?"""
        cerebrum = self._get_db('cerebrum')
        if not cerebrum:
            return CrossSystemInsight("tip_validation", [], 0.0, {}, "No cerebrum DB")

        # Check staging_tips vs experiences
        try:
            tips = cerebrum.execute("""
                SELECT content, confidence, category, metadata 
                FROM staging_tips 
                WHERE confidence > 0.7 
                ORDER BY confidence DESC LIMIT 20
            """).fetchall()
        except Exception:
            tips = []

        try:
            validated = cerebrum.execute("""
                SELECT s.content, COUNT(e.id) as usage_count, AVG(e.success) as success_rate
                FROM staging_tips s
                LEFT JOIN experiences e ON e.task_type LIKE '%' || s.category || '%'
                WHERE s.confidence > 0.6
                GROUP BY s.id
                HAVING usage_count > 0
                ORDER BY success_rate DESC
                LIMIT 10
            """).fetchall()
        except Exception:
            validated = []

        data = {
            'high_confidence_tips': len(tips),
            'validated_tips': len(validated),
            'top_validated': [
                {'tip': v['content'][:60], 'uses': v['usage_count'], 'success': v['success_rate']}
                for v in validated[:5]
            ]
        }

        confidence = min(0.85, max(0.3, len(validated) / 10))

        return CrossSystemInsight(
            query="tip_validation",
            sources=['staging_tips', 'experiences'],
            confidence=confidence,
            data=data,
            recommendation=f"{len(validated)} tips validated by experience. {len(tips)} high-confidence tips awaiting validation."
        )

    def query_learning_velocity(self, tool_name: Optional[str] = None) -> CrossSystemInsight:
        """How fast am I improving per tool?"""
        cerebrum = self._get_db('cerebrum')
        training = self._get_db('training')

        data = {'tools': {}}

        if cerebrum:
            try:
                # Success rate trend over time
                rows = cerebrum.execute("""
                    SELECT 
                        task_type,
                        COUNT(*) as total,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                        AVG(duration_ms) as avg_duration
                    FROM experiences
                    WHERE created_at > ?
                    GROUP BY task_type
                    ORDER BY total DESC
                """, (time.time() - 7*24*3600,)).fetchall()

                for row in rows:
                    if tool_name and row['task_type'] != tool_name:
                        continue
                    data['tools'][row['task_type']] = {
                        'total': row['total'],
                        'success_rate': row['successes'] / row['total'] if row['total'] > 0 else 0,
                        'avg_duration_ms': row['avg_duration'] or 0,
                    }
            except Exception:
                pass

        if training:
            try:
                rows = training.execute("""
                    SELECT tier_at_attempt, COUNT(*) as attempts, AVG(score * 1.0 / max_score) as avg_score
                    FROM attempts
                    GROUP BY tier_at_attempt
                """).fetchall()
                data['training'] = {
                    row['tier_at_attempt']: {
                        'attempts': row['attempts'],
                        'avg_score': row['avg_score']
                    }
                    for row in rows
                }
            except Exception:
                pass

        total_tools = len(data['tools'])
        avg_success = sum(t['success_rate'] for t in data['tools'].values()) / total_tools if total_tools > 0 else 0

        return CrossSystemInsight(
            query="learning_velocity",
            sources=['experiences', 'training_gym'],
            confidence=0.7 if total_tools > 0 else 0.3,
            data=data,
            recommendation=f"Active on {total_tools} tools. Average success rate: {avg_success:.1%}."
        )

    def query_weaknesses(self) -> CrossSystemInsight:
        """What are my current weakest areas?"""
        cerebrum = self._get_db('cerebrum')
        if not cerebrum:
            return CrossSystemInsight("weaknesses", [], 0.0, {}, "No cerebrum DB")

        weaknesses = []

        # Low success rate tools
        try:
            rows = cerebrum.execute("""
                SELECT task_type, COUNT(*) as total, 
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
                FROM experiences
                GROUP BY task_type
                HAVING total >= 3
                ORDER BY (successes * 1.0 / total) ASC
                LIMIT 5
            """).fetchall()
            weaknesses.extend([
                {'type': 'tool', 'name': r['task_type'], 'success_rate': r['successes']/r['total']}
                for r in rows
            ])
        except Exception:
            pass

        # Frequent errors
        try:
            rows = cerebrum.execute("""
                SELECT error_signature, occurrence_count, recovery_success_rate
                FROM error_patterns
                ORDER BY occurrence_count DESC
                LIMIT 5
            """).fetchall()
            weaknesses.extend([
                {'type': 'error', 'name': r['error_signature'][:50], 'occurrences': r['occurrence_count']}
                for r in rows
            ])
        except Exception:
            pass

        return CrossSystemInsight(
            query="weaknesses",
            sources=['experiences', 'error_patterns'],
            confidence=0.75,
            data={'weaknesses': weaknesses},
            recommendation=f"Found {len(weaknesses)} weakness areas. Top: {weaknesses[0]['name'] if weaknesses else 'N/A'}"
        )

    def generate_daily_briefing(self) -> Dict[str, Any]:
        """Generate a comprehensive daily intelligence briefing."""
        return {
            'errors': self.query_error_success_correlation(),
            'tips': self.query_tip_validation(),
            'velocity': self.query_learning_velocity(),
            'weaknesses': self.query_weaknesses(),
            'timestamp': time.time(),
        }

    def close(self):
        for conn in self._connections.values():
            conn.close()
        self._connections.clear()
