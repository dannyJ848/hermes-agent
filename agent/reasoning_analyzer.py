#!/usr/bin/env python3
"""
reasoning_analyzer.py — Analyze my reasoning quality and extract lessons.

Monitors:
  1. Planning errors (wrong approach, missing steps)
  2. Goal drift (getting sidetracked)
  3. Over-complication (unnecessary complexity)
  4. Under-analysis (missing edge cases)
  5. Confirmation bias (ignoring contradictory evidence)
  6. Premature optimization (optimizing before understanding)

Usage:
    from reasoning_analyzer import ReasoningAnalyzer
    ra = ReasoningAnalyzer()
    
    # After a complex task
    analysis = ra.analyze_task(reasoning_trace, outcomes)
    print(analysis['lessons'])
"""

import sys
import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

sys.path.insert(0, str(Path.home() / "hermes-agent"))
from agent.cortex_access import CortexDB, cortex_cursor


class ReasoningAnalyzer:
    """Analyzes reasoning quality and extracts meta-lessons."""
    
    # Pattern definitions for reasoning flaws
    REASONING_PATTERNS = {
        'missing_verification': {
            'patterns': [
                r'(?i)(?:assume|assuming|probably|likely|should work|might be)',
                r'(?i)(?:without checking|skip verification|no need to verify)',
            ],
            'severity': 'high',
            'lesson': 'WHEN making assumptions, DO verify with data or test before proceeding',
        },
        'premature_action': {
            'patterns': [
                r'(?i)(?:just (?:run|do|try)|quickly|fast|hurry|rush)',
                r'(?i)(?:skip|bypass|ignore|don\'t bother with)',
            ],
            'severity': 'medium',
            'lesson': 'WHEN tempted to skip steps, DO follow the full verification process',
        },
        'over_complication': {
            'patterns': [
                r'(?i)(?:complex solution|overengineer|too complicated|unnecessary)',
                r'(?i)(?:(?:could|should) also|additionally|furthermore|moreover)',
            ],
            'severity': 'low',
            'lesson': 'WHEN solution seems complex, DO check if a simpler approach exists',
        },
        'goal_drift': {
            'patterns': [
                r'(?i)(?:by the way|also|while we\'re at it|might as well)',
                r'(?i)(?:sidenote|tangentially|related topic)',
            ],
            'severity': 'medium',
            'lesson': 'WHEN getting sidetracked, DO refocus on the original goal',
        },
        'missing_alternative': {
            'patterns': [
                r'(?i)(?:only way|must|have to|no choice|only option)',
                r'(?i)(?:obviously|clearly|definitely|certainly)',
            ],
            'severity': 'medium',
            'lesson': 'WHEN claiming something is the only way, DO consider at least 2 alternatives',
        },
        'insufficient_research': {
            'patterns': [
                r'(?i)(?:don\'t know|not sure|unclear|confusing|guess)',
                r'(?i)(?:maybe try|perhaps|possibly|could be)',
            ],
            'severity': 'high',
            'lesson': 'WHEN uncertain about approach, DO research before implementing',
        },
    }
    
    def __init__(self, db: Optional[CortexDB] = None):
        self.db = db or CortexDB()
        self._session_patterns = defaultdict(int)
        self._lessons_extracted = []
    
    def analyze_reasoning(self, reasoning_text: str, 
                         task_outcome: str = "success",
                         tools_used: List[str] = None) -> Dict:
        """
        Analyze a reasoning trace for patterns.
        
        Returns:
            {
                'flaws_found': [{'type': 'missing_verification', 'severity': 'high', 'evidence': '...'}],
                'lessons': ['WHEN ... DO ...'],
                'quality_score': 0.85,
                'recommendations': ['...']
            }
        """
        flaws = []
        lessons = []
        
        # Check each pattern
        for flaw_type, config in self.REASONING_PATTERNS.items():
            matches = []
            for pattern in config['patterns']:
                found = re.findall(pattern, reasoning_text)
                matches.extend(found)
            
            if matches:
                flaws.append({
                    'type': flaw_type,
                    'severity': config['severity'],
                    'evidence': matches[:3],
                    'count': len(matches)
                })
                self._session_patterns[flaw_type] += len(matches)
                
                # Extract lesson if outcome was poor
                if task_outcome != "success" or config['severity'] == 'high':
                    lessons.append(config['lesson'])
        
        # Calculate quality score
        quality_score = self._calculate_quality(reasoning_text, flaws, task_outcome)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(flaws, tools_used or [])
        
        result = {
            'flaws_found': flaws,
            'lessons': list(set(lessons)),
            'quality_score': quality_score,
            'recommendations': recommendations,
            'reasoning_length': len(reasoning_text),
            'analysis_time': len(reasoning_text) / 100  # proxy
        }
        
        # Store in database
        self._store_analysis(result, reasoning_text[:500])
        
        return result
    
    def _calculate_quality(self, reasoning: str, flaws: List[Dict], 
                          outcome: str) -> float:
        """Calculate a quality score for reasoning."""
        score = 1.0
        
        # Deduct for flaws
        for flaw in flaws:
            if flaw['severity'] == 'high':
                score -= 0.15 * flaw['count']
            elif flaw['severity'] == 'medium':
                score -= 0.08 * flaw['count']
            else:
                score -= 0.03 * flaw['count']
        
        # Deduct for outcome
        if outcome == "failure":
            score -= 0.2
        elif outcome == "partial":
            score -= 0.1
        
        # Bonus for thoroughness
        if len(reasoning) > 500:
            score += 0.05
        if 'verify' in reasoning.lower() or 'check' in reasoning.lower():
            score += 0.05
        if 'alternative' in reasoning.lower() or 'option' in reasoning.lower():
            score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def _generate_recommendations(self, flaws: List[Dict], 
                                   tools_used: List[str]) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        
        flaw_types = [f['type'] for f in flaws]
        
        if 'missing_verification' in flaw_types:
            recs.append("Add explicit verification steps after each major action")
        
        if 'premature_action' in flaw_types:
            recs.append("Pause and review the plan before executing")
        
        if 'over_complication' in flaw_types:
            recs.append("Start with the simplest solution that could work")
        
        if 'goal_drift' in flaw_types:
            recs.append("Write down the goal and check against it periodically")
        
        if 'missing_alternative' in flaw_types:
            recs.append("Always list at least 2 approaches before choosing")
        
        if 'insufficient_research' in flaw_types:
            recs.append("Spend 2 minutes researching before implementing")
        
        # Tool-specific recommendations
        if 'terminal' in tools_used and 'execute_code' not in tools_used:
            recs.append("Consider using execute_code for complex multi-step operations")
        
        if len(tools_used) > 5:
            recs.append("High tool count - consider if the approach is too complex")
        
        return recs
    
    def _store_analysis(self, analysis: Dict, reasoning_preview: str):
        """Store analysis results in database."""
        try:
            with cortex_cursor() as cur:
                # Store as a meta-tip
                if analysis['lessons']:
                    for lesson in analysis['lessons']:
                        cur.execute("""
                            INSERT INTO cortex_nodes 
                            (text, node_type, domain, confidence, tip_type, provenance, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            lesson,
                            'tip',
                            'reasoning',
                            analysis['quality_score'],
                            'reasoning_lesson',
                            'reasoning_analyzer',
                            json.dumps({
                                'quality_score': analysis['quality_score'],
                                'flaws': [f['type'] for f in analysis['flaws_found']],
                                'reasoning_preview': reasoning_preview[:200]
                            })
                        ))
        except Exception:
            pass
    
    def get_session_summary(self) -> Dict:
        """Get summary of reasoning patterns this session."""
        total_flaws = sum(self._session_patterns.values())
        
        if total_flaws == 0:
            return {
                'total_flaws': 0,
                'quality': 'excellent',
                'top_pattern': None,
                'improvement_areas': []
            }
        
        top_pattern = max(self._session_patterns.items(), key=lambda x: x[1])
        
        quality = 'good' if total_flaws < 5 else 'needs_work' if total_flaws < 10 else 'poor'
        
        improvement_areas = [
            p.replace('_', ' ') for p, c in 
            sorted(self._session_patterns.items(), key=lambda x: -x[1])[:3]
        ]
        
        return {
            'total_flaws': total_flaws,
            'quality': quality,
            'top_pattern': top_pattern[0],
            'top_pattern_count': top_pattern[1],
            'improvement_areas': improvement_areas,
            'all_patterns': dict(self._session_patterns)
        }
    
    def build_injection(self) -> str:
        """Build injection based on reasoning analysis."""
        summary = self.get_session_summary()
        
        if summary['total_flaws'] == 0:
            return ""
        
        parts = ["🧠 REASONING ANALYSIS:"]
        
        if summary['top_pattern']:
            parts.append(f"  Watch for: {summary['top_pattern'].replace('_', ' ')} "
                        f"({summary['top_pattern_count']} times this session)")
        
        if summary['improvement_areas']:
            parts.append(f"  Focus: {', '.join(summary['improvement_areas'][:2])}")
        
        return "\n".join(parts)


# Singleton
_analyzer_instance = None

def get_analyzer() -> ReasoningAnalyzer:
    """Get singleton."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ReasoningAnalyzer()
    return _analyzer_instance


if __name__ == "__main__":
    print("="*70)
    print("REASONING ANALYZER TEST")
    print("="*70)
    
    ra = ReasoningAnalyzer()
    
    # Test 1: Good reasoning
    good_reasoning = """
    I need to find all Python files. Let me:
    1. First check what directory I'm in
    2. Use search_files to find .py files
    3. Verify the results
    4. Alternative: could use terminal with find command
    I'll go with search_files for reliability.
    """
    
    result = ra.analyze_reasoning(good_reasoning, "success", ["search_files"])
    print(f"\n[1] Good reasoning:")
    print(f"    Quality: {result['quality_score']:.0%}")
    print(f"    Flaws: {len(result['flaws_found'])}")
    print(f"    Lessons: {result['lessons']}")
    
    # Test 2: Flawed reasoning
    bad_reasoning = """
    I need to fix this bug. I'll just quickly run a command to patch it.
    Probably this will work. No need to verify, I'm sure it's right.
    This is the only way to do it. Let's just hurry and get it done.
    """
    
    result2 = ra.analyze_reasoning(bad_reasoning, "failure", ["patch"])
    print(f"\n[2] Flawed reasoning:")
    print(f"    Quality: {result2['quality_score']:.0%}")
    print(f"    Flaws: {len(result2['flaws_found'])}")
    for flaw in result2['flaws_found']:
        print(f"      - {flaw['type']} ({flaw['severity']}): {flaw['evidence'][:50]}...")
    print(f"    Lessons: {result2['lessons']}")
    print(f"    Recommendations: {result2['recommendations']}")
    
    # Test 3: Session summary
    print(f"\n[3] Session summary:")
    summary = ra.get_session_summary()
    print(f"    {summary}")
    
    print("\n" + "="*70)
    print("REASONING ANALYZER READY")
    print("="*70)
