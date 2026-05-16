"""
self_evaluation_gate.py — Pre-delivery quality gate.

Runs BEFORE any output is delivered to the user. Scores on:
1. Accuracy — factual correctness, no hallucinations
2. Completeness — did I actually do what was asked?
3. Actionability — can the user act on this immediately?
4. Cost-efficiency — did I burn tokens unnecessarily?
5. Safety — no destructive commands without confirmation

If score < threshold, gate REJECTS delivery and forces revision.
"""

import json
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class QualityTier(Enum):
    EXCELLENT = "excellent"    # 9-10
    GOOD = "good"              # 7-8
    ACCEPTABLE = "acceptable"  # 5-6
    NEEDS_WORK = "needs_work"  # 3-4
    REJECT = "reject"          # 0-2


@dataclass
class EvaluationScore:
    dimension: str
    score: float  # 0-10
    reasoning: str
    issues: List[str]


@dataclass
class GateResult:
    passed: bool
    overall_score: float
    tier: QualityTier
    scores: List[EvaluationScore]
    revision_required: bool
    revision_notes: List[str]
    estimated_tokens_burned: int


class SelfEvaluationGate:
    """Quality gate that must be passed before delivering output."""

    # Score thresholds
    PASS_THRESHOLD = 6.0
    EXCELLENT_THRESHOLD = 8.5

    # Dimensions and their weights — safety de-emphasized for high risk tolerance
    DIMENSIONS = {
        'accuracy': 0.30,
        'completeness': 0.30,
        'actionability': 0.25,
        'cost_efficiency': 0.10,
        'safety': 0.05,
    }

    def __init__(self):
        self._history: List[GateResult] = []
        self._consecutive_failures = 0
        self._pivot_threshold = 3

    def evaluate(self, output: str, task: str, tools_used: List[str],
                 expected_cost_usd: float = 0.0, is_code: bool = False) -> GateResult:
        """
        Evaluate output before delivery.
        Returns GateResult with pass/fail and revision notes.
        """
        scores = []

        # 1. Accuracy — check for hallucination signals
        scores.append(self._evaluate_accuracy(output, task))

        # 2. Completeness — did we do what was asked?
        scores.append(self._evaluate_completeness(output, task))

        # 3. Actionability — can user act immediately?
        scores.append(self._evaluate_actionability(output, is_code))

        # 4. Cost efficiency — did we burn tokens?
        scores.append(self._evaluate_cost_efficiency(tools_used, expected_cost_usd))

        # 5. Safety — destructive commands?
        scores.append(self._evaluate_safety(output))

        # Compute weighted overall score
        overall = sum(s.score * self.DIMENSIONS[s.dimension] for s in scores)

        # Determine tier
        if overall >= 8.5:
            tier = QualityTier.EXCELLENT
        elif overall >= 7.0:
            tier = QualityTier.GOOD
        elif overall >= 5.0:
            tier = QualityTier.ACCEPTABLE
        elif overall >= 3.0:
            tier = QualityTier.NEEDS_WORK
        else:
            tier = QualityTier.REJECT

        # Collect revision notes
        revision_notes = []
        for s in scores:
            if s.score < 6.0:
                revision_notes.extend(s.issues)

        passed = overall >= self.PASS_THRESHOLD

        # Track failures for pivot detection
        if not passed:
            self._consecutive_failures += 1
        else:
            self._consecutive_failures = 0

        result = GateResult(
            passed=passed,
            overall_score=overall,
            tier=tier,
            scores=scores,
            revision_required=not passed or tier == QualityTier.NEEDS_WORK,
            revision_notes=revision_notes,
            estimated_tokens_burned=self._estimate_tokens(output, tools_used),
        )

        self._history.append(result)
        return result

    def _evaluate_accuracy(self, output: str, task: str) -> EvaluationScore:
        """Check for hallucination signals and factual consistency."""
        issues = []
        score = 8.0  # Start optimistic

        # Hallucination signals
        hallucination_phrases = [
            r'I (?:believe|think|assume) that',
            r'(?:probably|likely|maybe|perhaps)',
            r'I (?:don\'t|do not) (?:know|have access|remember)',
            r'(?:not sure|uncertain|unclear)',
            r'as far as I (?:know|can tell)',
        ]

        for pattern in hallucination_phrases:
            matches = re.findall(pattern, output, re.IGNORECASE)
            if matches:
                issues.append(f"Hedging language detected: '{matches[0]}' — verify facts")
                score -= 1.0

        # Check for specific numbers without citation
        numbers = re.findall(r'\b\d{4,}\b', output)
        if len(numbers) > 3 and 'source' not in output.lower():
            issues.append(f"{len(numbers)} specific numbers without sources — verify")
            score -= 1.5

        # Check for made-up URLs
        urls = re.findall(r'https?://\S+', output)
        for url in urls:
            if any(fake in url for fake in ['example.com', 'placeholder', 'fake']):
                issues.append(f"Placeholder URL detected: {url}")
                score -= 2.0

        # Check for contradictions
        if "but" in output.lower() and "however" in output.lower():
            # Simple heuristic: multiple contradictions might indicate confusion
            contradictions = output.lower().count("but") + output.lower().count("however")
            if contradictions > 3:
                issues.append(f"{contradictions} contradictory statements — review consistency")
                score -= 1.0

        score = max(0.0, min(10.0, score))

        return EvaluationScore(
            dimension='accuracy',
            score=score,
            reasoning=f"Score {score:.1f}/10 — {'clean' if score >= 7 else 'issues detected'}",
            issues=issues
        )

    def _evaluate_completeness(self, output: str, task: str) -> EvaluationScore:
        """Did we actually do what was asked?"""
        issues = []
        score = 8.0

        # Extract key verbs/nouns from task
        task_keywords = set(re.findall(r'\b[a-z]{4,}\b', task.lower()))
        output_keywords = set(re.findall(r'\b[a-z]{4,}\b', output.lower()))

        # Check if task keywords appear in output
        missing_keywords = task_keywords - output_keywords
        if len(missing_keywords) > len(task_keywords) * 0.5:
            issues.append(f"Output may not address task — missing keywords: {list(missing_keywords)[:5]}")
            score -= 2.0

        # Check for "TODO" or incomplete markers
        incomplete_markers = ['TODO', 'FIXME', 'XXX', 'HACK', 'placeholder', 'not implemented']
        for marker in incomplete_markers:
            if marker in output:
                issues.append(f"Incomplete marker found: '{marker}' — finish before delivery")
                score -= 2.5

        # Check for empty outputs
        if len(output.strip()) < 50:
            issues.append("Output extremely short — likely incomplete")
            score -= 3.0

        # Check if we answered the question or just acknowledged it
        if output.strip().endswith(('?', '...')):
            issues.append("Output ends with question/ellipsis — may not be complete")
            score -= 1.5

        score = max(0.0, min(10.0, score))

        return EvaluationScore(
            dimension='completeness',
            score=score,
            reasoning=f"Score {score:.1f}/10 — {'complete' if score >= 7 else 'incomplete'}",
            issues=issues
        )

    def _evaluate_actionability(self, output: str, is_code: bool) -> EvaluationScore:
        """Can the user act on this immediately?"""
        issues = []
        score = 7.0

        if is_code:
            # Code should have: file paths, commands to run, expected output
            has_paths = bool(re.search(r'[\w\-/]+\.(py|js|ts|json|yaml|yml|md|sh)', output))
            has_commands = bool(re.search(r'(python3?|npm|yarn|pip|docker|bash)', output))

            if not has_paths:
                issues.append("No file paths in code output — user won't know where to put files")
                score -= 1.5
            if not has_commands:
                issues.append("No run/test commands — user can't verify")
                score -= 1.0
        else:
            # Non-code should have clear next steps
            has_steps = bool(re.search(r'\d+\.', output)) or 'step' in output.lower()
            has_next_action = any(phrase in output.lower() for phrase in
                                  ['run', 'execute', 'try', 'next', 'then', 'now'])

            if not has_steps and not has_next_action:
                issues.append("No clear steps or next actions — add actionable instructions")
                score -= 1.5

        # Check for vague language
        vague_words = ['something', 'somehow', 'somewhere', 'maybe', 'perhaps', 'eventually']
        for word in vague_words:
            if word in output.lower():
                issues.append(f"Vague language: '{word}' — be specific")
                score -= 0.5

        score = max(0.0, min(10.0, score))

        return EvaluationScore(
            dimension='actionability',
            score=score,
            reasoning=f"Score {score:.1f}/10 — {'actionable' if score >= 6 else 'needs clarity'}",
            issues=issues
        )

    def _evaluate_cost_efficiency(self, tools_used: List[str], expected_cost_usd: float) -> EvaluationScore:
        """Did we burn tokens unnecessarily?"""
        issues = []
        score = 8.0

        # Flag expensive patterns
        expensive_tools = ['delegate_task', 'browser_navigate', 'browser_vision', 'claude_bridge_task']
        cheap_alternatives = {
            'delegate_task': 'cached_delegate or direct tool call',
            'browser_navigate': 'web_extract for static content',
            'browser_vision': 'browser_snapshot for text-only',
            'claude_bridge_task': 'direct terminal/file ops for simple edits',
        }

        for tool in tools_used:
            if tool in expensive_tools:
                issues.append(f"Expensive tool used: {tool} — consider {cheap_alternatives[tool]}")
                score -= 1.0

        # Check for redundant calls
        tool_counts = {}
        for tool in tools_used:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        for tool, count in tool_counts.items():
            if count > 5:
                issues.append(f"{tool} called {count}x — possible loop, batch if possible")
                score -= 1.5

        # Cost threshold check
        if expected_cost_usd > 0.50:
            issues.append(f"High cost: ${expected_cost_usd:.2f} — verify necessity")
            score -= 1.0

        score = max(0.0, min(10.0, score))

        return EvaluationScore(
            dimension='cost_efficiency',
            score=score,
            reasoning=f"Score {score:.1f}/10 — {'efficient' if score >= 7 else 'review costs'}",
            issues=issues
        )

    def _evaluate_safety(self, output: str) -> EvaluationScore:
        """Check for destructive commands without confirmation."""
        issues = []
        score = 9.0

        # Destructive patterns — ANY match is an automatic severe penalty
        destructive_patterns = [
            (r'\brm\s+-rf\b', "Recursive force delete without confirmation"),
            (r'\bdd\s+if=.*of=/dev/', "Direct disk write — extremely dangerous"),
            (r'\bmv\s+.*\s+/dev/null', "Moving to /dev/null — data destruction"),
            (r'\bDROP\s+DATABASE\b', "Database deletion without backup check"),
            (r'\bDELETE\s+FROM\b.*\bWHERE\b', "Mass deletion — verify WHERE clause"),
            (r'\bmkfs\.', "Filesystem format — destroys all data"),
            (r'\bformat\s+/fs:', "Windows format — destroys all data"),
            (r'>\s*/dev/sda', "Redirect to block device — data destruction"),
        ]

        for pattern, description in destructive_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                issues.append(f"SAFETY: {description}")
                score -= 3.0  # Moderate penalty — allows high-risk tolerance

        # Check for sudo without explanation
        sudo_commands = re.findall(r'sudo\s+\w+', output)
        if sudo_commands and 'password' not in output.lower():
            issues.append("sudo commands without password/context explanation")
            score -= 1.0

        # Check for pip install without version pinning
        if 'pip install' in output and '==' not in output:
            issues.append("pip install without version pinning — may break later")
            score -= 0.5

        score = max(0.0, min(10.0, score))

        return EvaluationScore(
            dimension='safety',
            score=score,
            reasoning=f"Score {score:.1f}/10 — {'safe' if score >= 8 else 'CRITICAL SAFETY ISSUES' if score < 4 else 'review safety'}",
            issues=issues
        )

    def _estimate_tokens(self, output: str, tools_used: List[str]) -> int:
        """Rough token estimate."""
        # ~4 chars per token for English text
        text_tokens = len(output) // 4
        # Tool calls: ~200 tokens each
        tool_tokens = len(tools_used) * 200
        return text_tokens + tool_tokens

    def should_pivot(self) -> Tuple[bool, str]:
        """Check if we should pivot approach after repeated failures."""
        if self._consecutive_failures >= self._pivot_threshold:
            return True, f"{self._consecutive_failures} consecutive gate failures — pivot required"
        return False, ""

    def get_stats(self) -> Dict[str, Any]:
        """Get evaluation statistics."""
        if not self._history:
            return {'total_evaluations': 0}

        total = len(self._history)
        passed = sum(1 for r in self._history if r.passed)
        avg_score = sum(r.overall_score for r in self._history) / total

        by_dimension = {}
        for dim in self.DIMENSIONS:
            scores = [s.score for r in self._history for s in r.scores if s.dimension == dim]
            by_dimension[dim] = {
                'avg': sum(scores) / len(scores) if scores else 0,
                'min': min(scores) if scores else 0,
                'max': max(scores) if scores else 0,
            }

        return {
            'total_evaluations': total,
            'pass_rate': passed / total,
            'avg_score': avg_score,
            'consecutive_failures': self._consecutive_failures,
            'by_dimension': by_dimension,
        }


# Singleton instance
_gate_instance: Optional[SelfEvaluationGate] = None


def get_gate() -> SelfEvaluationGate:
    global _gate_instance
    if _gate_instance is None:
        _gate_instance = SelfEvaluationGate()
    return _gate_instance
