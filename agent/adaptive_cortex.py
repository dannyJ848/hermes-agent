#!/usr/bin/env python3
"""
adaptive_cortex.py — Real-time personalized self-improvement system.

Makes me iteratively better with every turn by:
  1. Tracking MY specific error patterns
  2. Detecting when I'm about to repeat a mistake
  3. Interrupting with personalized guidance
  4. Learning immediately, not after 2 hours
  5. Building a model of MY cognitive strengths/weaknesses

Usage:
    from adaptive_cortex import AdaptiveCortex
    ac = AdaptiveCortex()
    
    # Before tool call
    warning = ac.check_before_tool(tool_name, args, reasoning_trace)
    if warning:
        print(f"ADAPTIVE: {warning}")
    
    # After tool call
    ac.learn_from_outcome(tool_name, args, result, error, reasoning_trace)
"""

import sys
import os
import json
import hashlib
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, str(Path.home() / "hermes-agent"))
from agent.cortex_access import CortexDB, cortex_cursor


class AdaptiveCortex:
    """
    Real-time personalized learning engine.
    
    Tracks my patterns, predicts my mistakes, guides my improvement.
    """
    
    def __init__(self, db: Optional[CortexDB] = None):
        self.db = db or CortexDB()
        self._error_patterns: Dict[str, List[Dict]] = defaultdict(list)
        self._tool_stats: Dict[str, Dict] = defaultdict(lambda: {
            'calls': 0, 'successes': 0, 'errors': [],
            'common_args': defaultdict(int),
            'avg_duration': 0
        })
        self._recent_lessons: List[Dict] = []
        self._session_start = time.time()
        self._load_personal_patterns()
    
    def _load_personal_patterns(self):
        """Load my error patterns from database."""
        try:
            with cortex_cursor() as cur:
                cur.execute("""
                    SELECT pattern_type, tool_name, error_signature, 
                           frequency, prevention_tip, contexts
                    FROM my_error_patterns
                    WHERE frequency > 1
                    ORDER BY frequency DESC, last_seen DESC
                """)
                for row in cur.fetchall():
                    key = f"{row['tool_name']}:{row['error_signature'][:50]}"
                    self._error_patterns[row['tool_name']].append({
                        'pattern_type': row['pattern_type'],
                        'signature': row['error_signature'],
                        'frequency': row['frequency'],
                        'prevention_tip': row['prevention_tip'],
                        'contexts': row['contexts'] or {}
                    })
        except Exception as e:
            # Table might not exist yet
            pass
    
    def check_before_tool(self, tool_name: str, args: Dict, 
                          reasoning: str = "") -> Optional[str]:
        """
        Check if I'm about to make a known mistake.
        
        Returns: Warning message if pattern matches, None otherwise.
        """
        warnings = []
        
        # Check 1: Tool-specific error patterns
        if tool_name in self._error_patterns:
            for pattern in self._error_patterns[tool_name][:3]:  # Top 3 patterns
                match_score = self._match_pattern(args, reasoning, pattern)
                if match_score > 0.7:
                    warnings.append(
                        f"Pattern match ({match_score:.0%}): {pattern['prevention_tip']}"
                    )
        
        # Check 2: Argument validation based on my history
        arg_warnings = self._validate_args_for_me(tool_name, args)
        warnings.extend(arg_warnings)
        
        # Check 3: Reasoning trace analysis
        if reasoning:
            reasoning_warning = self._analyze_reasoning(tool_name, reasoning)
            if reasoning_warning:
                warnings.append(reasoning_warning)
        
        if warnings:
            return "ADAPTIVE WARNING:\n" + "\n".join(f"  • {w}" for w in warnings[:2])
        return None
    
    def _match_pattern(self, args: Dict, reasoning: str, 
                       pattern: Dict) -> float:
        """Match current context against error pattern. Return 0-1 score."""
        score = 0.0
        contexts = pattern.get('contexts', {})
        
        # Match argument patterns
        if 'arg_patterns' in contexts:
            for arg_key, arg_pattern in contexts['arg_patterns'].items():
                if arg_key in args:
                    if re.search(arg_pattern, str(args[arg_key]), re.IGNORECASE):
                        score += 0.3
        
        # Match reasoning patterns
        if 'reasoning_keywords' in contexts and reasoning:
            keywords = contexts['reasoning_keywords']
            matches = sum(1 for kw in keywords if kw.lower() in reasoning.lower())
            score += min(0.4, matches * 0.1)
        
        return min(1.0, score)
    
    def _validate_args_for_me(self, tool_name: str, args: Dict) -> List[str]:
        """Validate args based on MY common mistakes with this tool."""
        warnings = []
        stats = self._tool_stats[tool_name]
        
        # Check for missing args I often forget
        if tool_name == 'terminal':
            if 'command' in args:
                cmd = args['command']
                if 'rm -rf' in cmd and 'timeout' not in args:
                    warnings.append("You often forget timeout with dangerous commands. Add timeout=30?")
                if 'cd ' in cmd and 'workdir' not in args:
                    warnings.append("Consider using workdir instead of cd for reliability")
        
        elif tool_name == 'web_search':
            if 'query' in args:
                query = args['query']
                if len(query) < 10:
                    warnings.append("Short queries often return poor results. Add more context?")
        
        elif tool_name == 'read_file':
            if 'path' in args:
                path = args['path']
                if not path.startswith('/') and not path.startswith('~'):
                    warnings.append("Relative paths sometimes fail. Use absolute path?")
        
        return warnings
    
    def _analyze_reasoning(self, tool_name: str, reasoning: str) -> Optional[str]:
        """Analyze my reasoning for red flags."""
        reasoning_lower = reasoning.lower()
        
        # Pattern: I'm uncertain about tool choice
        uncertainty_markers = ['maybe', 'perhaps', 'try', 'guess', 'not sure', 'hopefully']
        if any(m in reasoning_lower for m in uncertainty_markers):
            # Check if there's a better tool based on my history
            better = self._suggest_better_tool(tool_name, reasoning)
            if better:
                return f"You seem uncertain. {better} might be better (based on your success rates)"
        
        # Pattern: I'm repeating a failed approach
        if 'again' in reasoning_lower or 'retry' in reasoning_lower:
            return "Retrying same approach. Consider: what failed last time?"
        
        return None
    
    def _suggest_better_tool(self, current_tool: str, reasoning: str) -> Optional[str]:
        """Suggest a better tool based on my history with similar tasks."""
        # Simple heuristic: check my success rates
        current_stats = self._tool_stats[current_tool]
        if current_stats['calls'] > 5:
            current_rate = current_stats['successes'] / current_stats['calls']
            if current_rate < 0.7:
                # Find better alternatives
                alternatives = []
                for tool, stats in self._tool_stats.items():
                    if stats['calls'] > 5 and stats['successes'] / stats['calls'] > 0.9:
                        alternatives.append((tool, stats['successes'] / stats['calls']))
                if alternatives:
                    best = max(alternatives, key=lambda x: x[1])
                    return f"{best[0]} (your success rate: {best[1]:.0%})"
        return None
    
    def learn_from_outcome(self, tool_name: str, args: Dict, 
                          result: Any, error: str, reasoning: str = ""):
        """
        Learn immediately from tool outcome.
        
        This happens RIGHT AFTER the tool call, not 2 hours later.
        """
        is_success = not error and not (isinstance(result, dict) and result.get('error'))
        
        # Update my tool stats
        stats = self._tool_stats[tool_name]
        stats['calls'] += 1
        if is_success:
            stats['successes'] += 1
        else:
            error_sig = self._extract_error_signature(error, result)
            stats['errors'].append({
                'signature': error_sig,
                'args': {k: str(v)[:100] for k, v in args.items()},
                'reasoning': reasoning[:200],
                'time': time.time()
            })
        
        # Update rolling average duration
        # (would need actual timing, using placeholder)
        
        # If error, extract lesson immediately
        if not is_success:
            lesson = self._extract_lesson(tool_name, args, error, result, reasoning)
            if lesson:
                self._recent_lessons.append({
                    'lesson': lesson,
                    'tool': tool_name,
                    'time': time.time(),
                    'applied': False
                })
                # Store in database for persistence
                self._store_lesson(lesson, tool_name, args, error)
        
        # Update my skill model
        self._update_skill_model(tool_name, is_success)
    
    def _extract_error_signature(self, error: str, result: Any) -> str:
        """Extract normalized error signature for pattern matching."""
        if not error and isinstance(result, dict):
            error = result.get('error', '')
        
        # Normalize: remove specific values, keep structure
        sig = error.lower()
        sig = re.sub(r'\d+', 'N', sig)  # Numbers → N
        sig = re.sub(r"['\"].*?['\"]", '"STR"', sig)  # Strings → STR
        sig = re.sub(r'/[\w/]+', '/PATH', sig)  # Paths → PATH
        return sig[:200]
    
    def _extract_lesson(self, tool_name: str, args: Dict, 
                       error: str, result: Any, reasoning: str) -> Optional[str]:
        """Extract a specific lesson from an error."""
        error_str = (error or str(result.get('error', ''))).lower()
        
        # Tool-specific lesson extraction
        lessons = {
            'terminal': {
                'not found': f"WHEN using {tool_name}, DO verify the command exists first with 'which'",
                'permission denied': f"WHEN {tool_name} fails with permission denied, DO check file permissions with ls -la",
                'no such file': f"WHEN {tool_name} can't find a file, DO verify the path with pwd and ls",
            },
            'web_search': {
                'timeout': f"WHEN {tool_name} times out, DO try a more specific query with fewer results",
                'no results': f"WHEN {tool_name} returns no results, DO try alternative keywords or broader terms",
            },
            'read_file': {
                'not found': f"WHEN {tool_name} fails, DO check if file exists with search_files first",
                'permission': f"WHEN {tool_name} has permission issues, DO try with elevated privileges",
            },
            'browser_navigate': {
                'timeout': f"WHEN browser times out, DO check if URL is accessible with curl first",
                '404': f"WHEN browser gets 404, DO verify URL with web_search for correct link",
            }
        }
        
        if tool_name in lessons:
            for pattern, lesson in lessons[tool_name].items():
                if pattern in error_str:
                    return lesson
        
        # Generic lesson
        return f"WHEN {tool_name} fails with '{error[:50]}', DO verify inputs and try alternative approach"
    
    def _store_lesson(self, lesson: str, tool_name: str, args: Dict, error: str):
        """Store lesson in Cortex for future use."""
        try:
            # Insert as tip with high priority
            self.db.insert_node(
                text=lesson,
                node_type='tip',
                domain=tool_name,
                confidence=0.9,  # High confidence - I just learned this
                tip_type='personal_lesson',
                tool_name=tool_name,
                provenance='adaptive_cortex_realtime',
                metadata={
                    'error': error[:200],
                    'args': {k: str(v)[:50] for k, v in args.items()},
                    'learned_at': datetime.now().isoformat(),
                    'session_id': hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
                }
            )
        except Exception:
            pass  # Don't crash if DB fails
    
    def _update_skill_model(self, tool_name: str, is_success: bool):
        """Update my skill model for this tool."""
        try:
            with cortex_cursor() as cur:
                # Check if skill record exists
                cur.execute("""
                    SELECT id, total_calls, successes FROM my_skills
                    WHERE skill_name = %s
                """, (tool_name,))
                row = cur.fetchone()
                
                if row:
                    # Update existing
                    new_calls = row['total_calls'] + 1
                    new_successes = row['successes'] + (1 if is_success else 0)
                    new_rate = new_successes / new_calls
                    
                    cur.execute("""
                        UPDATE my_skills
                        SET total_calls = %s,
                            successes = %s,
                            success_rate = %s,
                            last_assessed = NOW(),
                            improving = (success_rate < %s)
                        WHERE id = %s
                    """, (new_calls, new_successes, new_rate, new_rate, row['id']))
                else:
                    # Insert new
                    cur.execute("""
                        INSERT INTO my_skills
                        (skill_name, proficiency, total_calls, successes, success_rate, improving, last_assessed)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (tool_name, 0.5 if is_success else 0.3, 1, 1 if is_success else 0,
                          1.0 if is_success else 0.0, True))
        except Exception:
            pass
    
    def get_recent_lessons(self, count: int = 3) -> List[str]:
        """Get recent lessons for injection into context."""
        # Return lessons from this session
        recent = [l for l in self._recent_lessons 
                 if time.time() - l['time'] < 3600]  # Last hour
        return [l['lesson'] for l in recent[-count:]]
    
    def get_my_stats(self) -> Dict:
        """Get my personal performance stats."""
        total_calls = sum(s['calls'] for s in self._tool_stats.values())
        total_successes = sum(s['successes'] for s in self._tool_stats.values())
        
        return {
            'session_duration': time.time() - self._session_start,
            'total_calls': total_calls,
            'success_rate': total_successes / total_calls if total_calls > 0 else 0,
            'tools_used': len(self._tool_stats),
            'recent_lessons': len(self._recent_lessons),
            'tool_breakdown': {
                tool: {
                    'calls': stats['calls'],
                    'success_rate': stats['successes'] / stats['calls'] if stats['calls'] > 0 else 0,
                    'recent_errors': len(stats['errors'])
                }
                for tool, stats in self._tool_stats.items()
            }
        }
    
    def build_injection(self) -> str:
        """Build context injection based on my current state."""
        parts = []
        
        # Recent lessons
        lessons = self.get_recent_lessons(3)
        if lessons:
            parts.append("RECENT LESSONS:")
            for lesson in lessons:
                parts.append(f"  • {lesson}")
        
        # Skill status
        stats = self.get_my_stats()
        if stats['total_calls'] > 10:
            parts.append(f"\nYOUR STATS: {stats['success_rate']:.0%} success rate across {stats['total_calls']} calls")
            
            # Highlight improving/declining skills
            improving = []
            declining = []
            for tool, tool_stats in stats['tool_breakdown'].items():
                if tool_stats['calls'] > 5:
                    if tool_stats['success_rate'] > 0.9:
                        improving.append(tool)
                    elif tool_stats['success_rate'] < 0.5:
                        declining.append(tool)
            
            if improving:
                parts.append(f"Strong skills: {', '.join(improving)}")
            if declining:
                parts.append(f"Needs work: {', '.join(declining)}")
        
        return "\n".join(parts) if parts else ""


# Singleton instance for plugin use
_adaptive_instance = None

def get_adaptive_cortex() -> AdaptiveCortex:
    """Get or create singleton instance."""
    global _adaptive_instance
    if _adaptive_instance is None:
        _adaptive_instance = AdaptiveCortex()
    return _adaptive_instance


def check_before_tool(tool_name: str, args: Dict, reasoning: str = "") -> Optional[str]:
    """Convenience function for plugin hook."""
    return get_adaptive_cortex().check_before_tool(tool_name, args, reasoning)


def learn_from_outcome(tool_name: str, args: Dict, result: Any, 
                       error: str, reasoning: str = ""):
    """Convenience function for plugin hook."""
    return get_adaptive_cortex().learn_from_outcome(tool_name, args, result, error, reasoning)


def build_injection() -> str:
    """Convenience function for plugin hook."""
    return get_adaptive_cortex().build_injection()


if __name__ == "__main__":
    # Test
    ac = AdaptiveCortex()
    
    # Simulate a tool call
    warning = ac.check_before_tool("terminal", {"command": "rm -rf /tmp/*"})
    if warning:
        print(warning)
    
    # Simulate outcome
    ac.learn_from_outcome(
        "terminal", 
        {"command": "rm -rf /tmp/*"},
        {"success": True},
        "",
        "Cleaning temp files"
    )
    
    print("\n" + ac.build_injection())
    print("\nStats:", ac.get_my_stats())
