#!/usr/bin/env python3
"""
Self-Critic Reflection Module (Self-RAG + Reflexion inspired)
=============================================================
Evaluates tool call outcomes with multi-axis self-critique.
Produces structured reflections that feed back into future tool calls.

Born from: R1 research round — Self-RAG (Asai et al., 2024) + Reflexion (Shinn et al., 2024)

Architecture:
- post_tool_call: Record outcome + generate reflection
- pre_llm_call: Inject relevant past reflections as context hints

Reflection axes (inspired by Self-RAG reflection tokens):
  [IsRel] - Was the retrieved/captured information relevant?
  [IsSup] - Was the tool output sufficient for the task?
  [IsUse] - Was using this tool useful vs alternative approaches?
  [IsEff] - Was this efficient (minimal redundant calls)?

Thread-safe via instance registry (same pattern as trajectory_intel.py).
"""

import os
import re
import json
import time
import hashlib
import threading
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Thread-safe instance registry
_instances = {}
_instance_lock = threading.Lock()

def get_instance(session_id: str = "default") -> "SelfCritic":
    with _instance_lock:
        if session_id not in _instances:
            _instances[session_id] = SelfCritic(session_id)
        return _instances[session_id]

def _cleanup_instance(session_id: str):
    with _instance_lock:
        _instances.pop(session_id, None)


class Reflection:
    """A single self-critique reflection."""
    __slots__ = ['id', 'timestamp', 'tool_name', 'task_summary', 'axes', 
                 'verdict', 'lesson', 'frequency']
    
    def __init__(self, tool_name, task_summary, axes, verdict, lesson):
        self.id = hashlib.md5(f"{tool_name}:{task_summary}:{time.time()}".encode()).hexdigest()[:12]
        self.timestamp = time.time()
        self.tool_name = tool_name
        self.task_summary = task_summary[:200]
        self.axes = axes  # dict: {IsRel: bool, IsSup: bool, IsUse: bool, IsEff: bool}
        self.verdict = verdict  # 'success', 'partial', 'failure', 'silent_failure'
        self.lesson = lesson[:500]
        self.frequency = 1
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'tool_name': self.tool_name,
            'task_summary': self.task_summary,
            'axes': self.axes,
            'verdict': self.verdict,
            'lesson': self.lesson,
            'frequency': self.frequency
        }


class SelfCritic:
    """
    Self-critique engine that evaluates tool call quality on 4 axes
    and generates actionable reflections for future improvement.
    """
    
    # Verdict heuristics — maps tool result patterns to verdicts
    SILENT_FAILURE_PATTERNS = [
        (r'0 (?:results?|matches?|found|cards?|items?)', 'zero_results'),
        (r'empty|no output|none|null', 'empty_output'),
        (r'error|fail|exception', 'error'),
    ]
    
    PARTIAL_SUCCESS_PATTERNS = [
        (r'\d+ (?:results?|matches?|cards?|items?)\b', 'has_results'),
    ]
    
    # Tool-specific quality heuristics
    TOOL_QUALITY_RULES = {
        'web_extract': {
            'min_output_chars': 100,
            'max_output_chars': 50000,
            'expected_patterns': [r'[a-zA-Z]{20,}'],  # Real content, not just URLs
        },
        'web_search': {
            'min_results': 1,
            'expected_fields': ['url', 'title'],
        },
        'execute_code': {
            'failure_indicators': ['Error', 'Traceback', 'Exception', 'FAIL'],
            'success_indicators': ['OK', 'PASS', 'success'],
        },
        'terminal': {
            'failure_indicators': ['command not found', 'permission denied', 'No such file'],
            'success_indicators': ['exit_code: 0', 'OK'],
        },
        'browser_navigate': {
            'failure_indicators': ['timeout', 'ERR_', '403', '404', '500'],
        },
    }
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.reflections: Dict[str, Reflection] = {}  # id -> Reflection
        self.tool_stats: Dict[str, Dict] = defaultdict(lambda: {
            'total': 0, 'success': 0, 'partial': 0, 'failure': 0, 'silent_failure': 0,
            'avg_relevance': 0, 'avg_sufficiency': 0, 'avg_usefulness': 0, 'avg_efficiency': 0
        })
        self.recent_verdicts: List[Tuple[str, str, float]] = []  # (tool, verdict, time)
        self._lock = threading.Lock()
        
        # Pattern memory: tool_name -> common failure lessons
        self.failure_lessons: Dict[str, List[str]] = defaultdict(list)
        
        # Session context
        self._call_count = 0
        self._last_critique_time = 0
    
    def _detect_silent_failure(self, tool_name: str, result_text: str) -> bool:
        """Detect silent failures — the most dangerous bug class."""
        if not result_text:
            return True
        
        result_lower = result_text.lower()
        
        # Check tool-specific rules
        rules = self.TOOL_QUALITY_RULES.get(tool_name, {})
        
        # Check minimum output length
        min_chars = rules.get('min_output_chars', 0)
        if min_chars and len(result_text.strip()) < min_chars:
            return True
        
        # Check for zero results in data tools
        for pattern, label in self.SILENT_FAILURE_PATTERNS:
            if re.search(pattern, result_lower):
                return True
        
        return False
    
    def _detect_partial_success(self, tool_name: str, result_text: str) -> bool:
        """Detect partial success — tool ran but results may be incomplete."""
        result_lower = result_text.lower()
        
        rules = self.TOOL_QUALITY_RULES.get(tool_name, {})
        
        # Check for failure indicators mixed with success
        has_failure = any(ind in result_lower for ind in rules.get('failure_indicators', []))
        has_success = any(ind in result_lower for ind in rules.get('success_indicators', []))
        
        if has_failure and has_success:
            return True
        
        return False
    
    def _score_relevance(self, tool_name: str, result_text: str, task_context: str = "") -> bool:
        """[IsRel] Was the tool output relevant to the task?"""
        if not result_text or len(result_text.strip()) < 10:
            return False
        
        # Check for error messages masquerading as results
        error_indicators = ['error', 'forbidden', 'not found', 'timeout', 'access denied']
        result_lower = result_text.lower()
        if any(ind in result_lower for ind in error_indicators):
            # If the ENTIRE output is just an error, not relevant
            non_error_chars = sum(1 for c in result_text if c.isalnum())
            if non_error_chars < 50:
                return False
        
        return True
    
    def _score_sufficiency(self, tool_name: str, result_text: str) -> bool:
        """[IsSup] Was the output sufficient for the task?"""
        rules = self.TOOL_QUALITY_RULES.get(tool_name, {})
        min_chars = rules.get('min_output_chars', 50)
        return len(result_text.strip()) >= min_chars
    
    def _score_usefulness(self, tool_name: str, result_text: str, verdict: str) -> bool:
        """[IsUse] Was using this tool useful vs alternatives?"""
        if verdict == 'silent_failure':
            return False
        if verdict == 'failure':
            return False
        
        # Check tool stats — if this tool fails >50% of the time, question usefulness
        stats = self.tool_stats.get(tool_name, {})
        if stats.get('total', 0) > 5:
            success_rate = (stats.get('success', 0) + stats.get('partial', 0)) / stats['total']
            if success_rate < 0.3:
                return False
        
        return True
    
    def _score_efficiency(self, tool_name: str) -> bool:
        """[IsEff] Was this efficient? Checks for redundant calls."""
        recent = [v for t, v, _ in self.recent_verdicts[-10:] if t == tool_name]
        if len(recent) >= 3:
            # If last 3 calls to same tool all failed, this is inefficient
            if all(v in ('failure', 'silent_failure') for v in recent[-3:]):
                return False
        return True
    
    def _generate_lesson(self, tool_name: str, verdict: str, axes: dict, 
                          result_text: str, task_context: str = "") -> str:
        """Generate an actionable lesson from this critique."""
        lessons = []
        
        if not axes.get('IsRel'):
            lessons.append(f"Output from {tool_name} was not relevant — consider different tool or query")
        
        if not axes.get('IsSup'):
            if len(result_text.strip()) < 50:
                lessons.append(f"{tool_name} returned insufficient output — verify input parameters")
            else:
                lessons.append(f"{tool_name} output incomplete — may need follow-up call")
        
        if not axes.get('IsUse'):
            # Suggest alternatives based on tool
            alternatives = {
                'web_extract': 'web_search (find different source)',
                'browser_navigate': 'web_extract or web_search (faster)',
                'cached_delegate': 'delegate_with_model or web_research',
                'delegate_parallel': 'web_research directly (avoid free model failures)',
            }
            alt = alternatives.get(tool_name, 'a different approach')
            lessons.append(f"{tool_name} has low success rate — try {alt}")
        
        if not axes.get('IsEff'):
            lessons.append(f"Multiple failed {tool_name} calls detected — change strategy instead of retrying")
        
        if verdict == 'silent_failure':
            lessons.append(f"SILENT FAILURE detected in {tool_name} — verify output quantity independently")
        
        return "; ".join(lessons) if lessons else "Tool call effective"
    
    def critique(self, tool_name: str, result_text: str, is_error: bool = False,
                 task_context: str = "") -> Optional[Reflection]:
        """
        Main entry point: Critique a tool call result.
        Returns a Reflection or None if no critique needed.
        """
        with self._lock:
            self._call_count += 1
            
            # Determine verdict
            if is_error:
                verdict = 'failure'
            elif self._detect_silent_failure(tool_name, result_text):
                verdict = 'silent_failure'
            elif self._detect_partial_success(tool_name, result_text):
                verdict = 'partial'
            else:
                verdict = 'success'
            
            # Score all 4 axes
            axes = {
                'IsRel': self._score_relevance(tool_name, result_text, task_context),
                'IsSup': self._score_sufficiency(tool_name, result_text),
                'IsUse': self._score_usefulness(tool_name, result_text, verdict),
                'IsEff': self._score_efficiency(tool_name),
            }
            
            # Update tool stats
            stats = self.tool_stats[tool_name]
            stats['total'] += 1
            stats[verdict] = stats.get(verdict, 0) + 1
            
            # Track rolling averages
            for i, axis in enumerate(['IsRel', 'IsSup', 'IsUse', 'IsEff']):
                key = ['avg_relevance', 'avg_sufficiency', 'avg_usefulness', 'avg_efficiency'][i]
                n = stats['total']
                stats[key] = stats[key] * (n - 1) / n + (1.0 if axes[axis] else 0.0) / n
            
            # Record recent verdict
            self.recent_verdicts.append((tool_name, verdict, time.time()))
            
            # Only generate reflection for non-success or every 10th success
            all_pass = all(axes.values())
            
            if verdict != 'success' or self._call_count % 10 == 0:
                lesson = self._generate_lesson(tool_name, verdict, axes, result_text, task_context)
                
                reflection = Reflection(
                    tool_name=tool_name,
                    task_summary=task_context[:200] if task_context else f"{tool_name} call #{self._call_count}",
                    axes=axes,
                    verdict=verdict,
                    lesson=lesson
                )
                
                self.reflections[reflection.id] = reflection
                
                # Track failure lessons per tool
                if verdict in ('failure', 'silent_failure'):
                    self.failure_lessons[tool_name].append(lesson)
                    # Keep only last 20 per tool
                    self.failure_lessons[tool_name] = self.failure_lessons[tool_name][-20:]
                
                return reflection
            
            return None
    
    def build_injection(self, current_task: str = "") -> Optional[str]:
        """
        Build a context injection hint for pre_llm_call.
        Injects relevant past reflections and tool health warnings.
        """
        with self._lock:
            hints = []
            
            # 1. Tool health warnings — tools with <50% success rate
            for tool_name, stats in self.tool_stats.items():
                if stats['total'] >= 5:
                    success_rate = (stats['success'] + stats.get('partial', 0)) / stats['total']
                    if success_rate < 0.5:
                        hints.append(
                            f"[SELF-CRITIC] {tool_name} has {success_rate:.0%} success rate "
                            f"({stats['total']} calls). Consider alternatives."
                        )
            
            # 2. Recent failure patterns — if last 3 calls failed
            if len(self.recent_verdicts) >= 3:
                recent = self.recent_verdicts[-3:]
                if all(v in ('failure', 'silent_failure') for _, v, _ in recent):
                    tools = set(t for t, _, _ in recent)
                    hints.append(
                        f"[SELF-CRITIC] Last 3 calls failed: {', '.join(tools)}. "
                        f"Change strategy — don't repeat the same approach."
                    )
            
            # 3. Silent failure detection reminder
            silent_count = sum(1 for r in self.reflections.values() if r.verdict == 'silent_failure')
            if silent_count > 3:
                hints.append(
                    f"[SELF-CRITIC] {silent_count} silent failures detected this session. "
                    f"Verify output quantities independently before proceeding."
                )
            
            # 4. Task-relevant reflections
            if current_task:
                task_lower = current_task.lower()
                relevant = []
                for ref in self.reflections.values():
                    if any(word in ref.task_summary.lower() for word in task_lower.split()[:5]):
                        relevant.append(ref)
                
                if relevant:
                    # Get most recent relevant reflection
                    latest = max(relevant, key=lambda r: r.timestamp)
                    if time.time() - latest.timestamp < 3600:  # Last hour
                        hints.append(
                            f"[SELF-CRITIC] Recent reflection on similar task: {latest.lesson}"
                        )
            
            if hints:
                return "\n".join(hints)
            return None
    
    def get_stats(self) -> dict:
        """Get current self-critique statistics."""
        with self._lock:
            total_reflections = len(self.reflections)
            verdicts = defaultdict(int)
            for r in self.reflections.values():
                verdicts[r.verdict] += 1
            
            return {
                'session_id': self.session_id,
                'total_calls': self._call_count,
                'total_reflections': total_reflections,
                'verdicts': dict(verdicts),
                'tools_tracked': len(self.tool_stats),
                'tool_health': {
                    tool: {
                        'total': stats['total'],
                        'success_rate': (stats['success'] + stats.get('partial', 0)) / max(1, stats['total']),
                        'avg_relevance': round(stats['avg_relevance'], 2),
                        'avg_sufficiency': round(stats['avg_sufficiency'], 2),
                    }
                    for tool, stats in self.tool_stats.items()
                    if stats['total'] >= 3
                },
                'tools_with_failures': list(self.failure_lessons.keys()),
            }
    
    def get_recent_lessons(self, limit: int = 10) -> List[dict]:
        """Get most recent reflection lessons."""
        with self._lock:
            sorted_refs = sorted(self.reflections.values(), key=lambda r: r.timestamp, reverse=True)
            return [r.to_dict() for r in sorted_refs[:limit]]


# ==================== STANDALONE TEST ====================
if __name__ == "__main__":
    print("=== Self-Critic Module Test ===\n")
    
    critic = get_instance("test")
    
    # Test 1: Successful tool call
    r1 = critic.critique("web_search", "Found 5 results about AI agents\n1. Paper A\n2. Paper B", 
                          task_context="Search for AI agent papers")
    print(f"Test 1 (success): {r1.verdict if r1 else 'no reflection (expected for success)'}")
    
    # Test 2: Silent failure (zero results)
    r2 = critic.critique("web_search", "0 results found", task_context="Search for AI agents")
    print(f"Test 2 (silent failure): {r2.verdict if r2 else 'none'}")
    if r2:
        print(f"  Axes: {r2.axes}")
        print(f"  Lesson: {r2.lesson}")
    
    # Test 3: Error
    r3 = critic.critique("browser_navigate", "HTTP Error 403: Forbidden", is_error=True,
                          task_context="Navigate to API docs")
    print(f"Test 3 (error): {r3.verdict if r3 else 'none'}")
    
    # Test 4: Multiple failures to trigger efficiency warning
    for i in range(3):
        critic.critique("cached_delegate", "glm-N-turbo returned empty after retries", 
                        is_error=True, task_context="Delegate research task")
    r4 = critic.critique("cached_delegate", "glm-N-turbo returned empty after retries", 
                          is_error=True, task_context="Delegate research task")
    print(f"Test 4 (repeated failure): {r4.verdict if r4 else 'none'}")
    if r4:
        print(f"  Efficiency: {r4.axes['IsEff']}")
    
    # Test 5: Build injection
    injection = critic.build_injection("Search for AI agent papers")
    print(f"\nTest 5 (injection):")
    if injection:
        for line in injection.split('\n'):
            print(f"  {line}")
    
    # Stats
    stats = critic.get_stats()
    print(f"\nStats: {json.dumps(stats, indent=2)}")
    
    print("\n=== All tests passed ===")
    _cleanup_instance("test")
