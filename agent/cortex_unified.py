#!/usr/bin/env python3
"""
cortex_unified.py — Single integration point for all Cortex systems.

Combines:
  1. Classic Cortex (tips, Elo, flywheel)
  2. Adaptive Cortex (real-time learning, error patterns)
  3. Tool Oracle (predictive tool selection)

Provides clean API for the distillation plugin:
  - pre_tool_call(task, reasoning) -> warnings + suggestions
  - post_tool_call(tool, args, result, error) -> immediate learning
  - pre_llm_call(user_message) -> personalized injection

Usage:
    from cortex_unified import UnifiedCortex
    uc = UnifiedCortex()
    
    # Before tool call
    guidance = uc.before_tool("terminal", {"command": "rm -rf /"}, "cleaning up")
    
    # After tool call  
    uc.after_tool("terminal", {...}, result, error, "cleaning up")
    
    # For LLM context
    injection = uc.build_context_injection("I need to find a file")
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

sys.path.insert(0, str(Path.home() / "hermes-agent"))

from agent.cortex_access import CortexDB
from agent.adaptive_cortex import AdaptiveCortex
from agent.tool_oracle import ToolOracle
from agent.reasoning_analyzer import ReasoningAnalyzer
from agent.sequence_learner import SequenceLearner
from agent.anomaly_detector import AnomalyDetector


class UnifiedCortex:
    """Unified interface for all self-improvement systems."""
    
    def __init__(self):
        self.db = CortexDB()
        self.adaptive = AdaptiveCortex(self.db)
        self.oracle = ToolOracle(self.db)
        self.reasoning = ReasoningAnalyzer(self.db)
        self.sequences = SequenceLearner(self.db)
        self.anomaly = AnomalyDetector(self.db)
        self._session_stats = {
            'calls': 0,
            'successes': 0,
            'lessons_learned': 0,
            'warnings_given': 0,
            'anomalies_detected': 0,
            'reasoning_flaws': 0,
            'start_time': time.time()
        }
        self._recent_tools = []

    def before_tool(self, tool_name: str, args: Dict, 
                    reasoning: str = "", task_description: str = "") -> Dict:
        """
        Called before every tool call. Returns comprehensive guidance.
        """
        result = {
            'warnings': [],
            'suggestions': {},
            'predicted_success': 0.5,
            'better_tool': None,
            'sequence_suggestion': None,
            'anomaly': None,
            'risk_score': 0.0,
            'injection': ''
        }
        
        # 1. Adaptive Cortex: Check for known error patterns
        warning = self.adaptive.check_before_tool(tool_name, args, reasoning)
        if warning:
            result['warnings'].append(warning)
            self._session_stats['warnings_given'] += 1
        
        # 2. Tool Oracle: Validate tool choice
        if task_description:
            validation = self.oracle.validate_choice(tool_name, task_description, args)
            result['predicted_success'] = validation['confidence']
            
            if not validation['is_optimal'] and validation['suggested']:
                result['better_tool'] = validation['suggested']
                result['warnings'].append(
                    f"Consider {validation['suggested']} instead ({validation['confidence']:.0%} confidence)"
                )
            
            if validation['issues']:
                result['warnings'].extend(validation['issues'])
            if validation['improvements']:
                result['suggestions'].update(validation['improvements'])
        
        # 3. Sequence Learner: Suggest next tool in chain
        if self._recent_tools:
            seq_suggestion = self.sequences.suggest_next_tool(self._recent_tools)
            if seq_suggestion:
                result['sequence_suggestion'] = seq_suggestion
                if seq_suggestion.get('warning'):
                    result['warnings'].append(seq_suggestion['warning'])
        
        # 4. Anomaly Detector: Check for unusual behavior
        anomaly = self.anomaly.detect_anomaly(tool_name, args, reasoning, self._recent_tools)
        if anomaly:
            result['anomaly'] = anomaly
            result['warnings'].append(self.anomaly.build_warning(anomaly))
            self._session_stats['anomalies_detected'] += 1
        
        # 5. Risk scoring
        result['risk_score'] = self.anomaly.get_risk_score(tool_name, args, reasoning, self._recent_tools)
        if result['risk_score'] > 0.5:
            result['warnings'].append(f"High risk score: {result['risk_score']:.0%}. Proceed with caution.")
        
        # 6. Arg validation
        arg_warnings = self.oracle._validate_args(tool_name, args or {})
        result['warnings'].extend(arg_warnings)
        
        # Build injection text
        if result['warnings'] or result['suggestions'] or result['sequence_suggestion']:
            parts = []
            if result['risk_score'] > 0.3:
                parts.append(f"⚠️ RISK: {result['risk_score']:.0%}")
            if result['warnings']:
                parts.append("WARNINGS:")
                for w in result['warnings'][:3]:
                    parts.append(f"  • {w}")
            if result['suggestions']:
                parts.append("SUGGESTIONS:")
                for k, v in result['suggestions'].items():
                    parts.append(f"  → Add {k}={v}")
            if result['sequence_suggestion']:
                parts.append(f"CHAIN: After this, consider {result['sequence_suggestion']['tool']}")
            result['injection'] = "\n".join(parts)
        
        return result
    
    def after_tool(self, tool_name: str, args: Dict, 
                   result: Any, error: str, reasoning: str = "",
                   task_description: str = ""):
        """
        Called after every tool call. Immediate learning.
        """
        self._session_stats['calls'] += 1
        
        is_success = not error and not (isinstance(result, dict) and result.get('error'))
        if is_success:
            self._session_stats['successes'] += 1
        
        # 1. Adaptive Cortex: Learn immediately
        self.adaptive.learn_from_outcome(tool_name, args, result, error, reasoning)
        
        # 2. Sequence Learner: Record in chain
        self.sequences.record_tool(tool_name, is_success)
        
        # 3. Reasoning Analyzer: Analyze if we have reasoning
        if reasoning:
            analysis = self.reasoning.analyze_reasoning(reasoning, "success" if is_success else "failure", [tool_name])
            if analysis['flaws_found']:
                self._session_stats['reasoning_flaws'] += len(analysis['flaws_found'])
        
        # 4. Track recent tools
        self._recent_tools.append(tool_name)
        if len(self._recent_tools) > 10:
            self._recent_tools = self._recent_tools[-10:]
        
        # 5. Update classic Cortex with new tip
        if not is_success:
            self._session_stats['lessons_learned'] += 1
            # Tip was already stored by adaptive.learn_from_outcome
        
        # 6. Complete task if it seems done (heuristic: no tool call for 30s)
        # This would need actual timing - simplified here
    
    def build_context_injection(self, user_message: str = "") -> str:
        """
        Build personalized context injection for LLM.
        
        Combines:
        - Recent lessons from this session
        - My skill status
        - Relevant tips from Cortex
        - Tool predictions for current task
        """
        parts = []
        
        # 1. Recent lessons (immediate learning)
        lessons = self.adaptive.get_recent_lessons(3)
        if lessons:
            parts.append("🧠 RECENT LESSONS (this session):")
            for lesson in lessons:
                parts.append(f"  • {lesson}")
        
        # 2. My skill status
        stats = self.adaptive.get_my_stats()
        if stats['total_calls'] > 5:
            parts.append(f"\n📊 YOUR STATS: {stats['success_rate']:.0%} success ({stats['total_calls']} calls)")
            
            # Highlight problem areas
            problem_tools = []
            for tool, ts in stats['tool_breakdown'].items():
                if ts['calls'] > 3 and ts['success_rate'] < 0.7:
                    problem_tools.append(f"{tool} ({ts['success_rate']:.0%})")
            
            if problem_tools:
                parts.append(f"⚠️  Needs attention: {', '.join(problem_tools)}")
        
        # 3. Tool prediction for current task
        if user_message:
            prediction = self.oracle.predict_tools(user_message)
            if prediction['primary'] and prediction['confidence'] > 0.6:
                parts.append(f"\n🔮 For this task, consider: {prediction['primary']}")
                if prediction['arg_suggestions']:
                    parts.append(f"   Suggested args: {prediction['arg_suggestions']}")
        
        # 5. Reasoning analysis injection
        reasoning_injection = self.reasoning.build_injection()
        if reasoning_injection:
            parts.append(reasoning_injection)
        
        # 6. Session stats
        if self._session_stats['calls'] > 5:
            parts.append(f"\n📈 SESSION: {self._session_stats['calls']} calls, "
                        f"{self._session_stats['successes']/self._session_stats['calls']:.0%} success, "
                        f"{self._session_stats['lessons_learned']} lessons, "
                        f"{self._session_stats['anomalies_detected']} anomalies")
        
        return "\n".join(parts) if parts else ""
    
    def get_session_report(self) -> Dict:
        """Get report on this session's learning."""
        duration = time.time() - self._session_stats['start_time']
        calls = self._session_stats['calls']
        
        return {
            'duration_min': duration / 60,
            'total_calls': calls,
            'success_rate': self._session_stats['successes'] / calls if calls > 0 else 0,
            'warnings_given': self._session_stats['warnings_given'],
            'lessons_learned': self._session_stats['lessons_learned'],
            'current_proficiency': self.adaptive.get_my_stats()
        }


# Singleton for plugin use
_unified_instance = None

def get_unified_cortex() -> UnifiedCortex:
    """Get or create singleton."""
    global _unified_instance
    if _unified_instance is None:
        _unified_instance = UnifiedCortex()
    return _unified_instance


# Convenience functions for plugin hooks
def before_tool(tool_name: str, args: Dict, reasoning: str = "") -> Dict:
    """Plugin hook: before tool call."""
    return get_unified_cortex().before_tool(tool_name, args, reasoning)


def after_tool(tool_name: str, args: Dict, result: Any, 
               error: str, reasoning: str = ""):
    """Plugin hook: after tool call."""
    return get_unified_cortex().after_tool(tool_name, args, result, error, reasoning)


def build_injection(user_message: str = "") -> str:
    """Plugin hook: build context injection."""
    return get_unified_cortex().build_context_injection(user_message)


if __name__ == "__main__":
    print("="*70)
    print("UNIFIED CORTEX TEST")
    print("="*70)
    
    uc = UnifiedCortex()
    
    # Test 1: Before tool
    print("\n[1] Before tool call...")
    guidance = uc.before_tool(
        "terminal",
        {"command": "rm -rf /tmp/*"},
        "I need to clean temp files",
        "clean temp files"
    )
    print(f"  Warnings: {guidance['warnings']}")
    print(f"  Suggestions: {guidance['suggestions']}")
    print(f"  Predicted success: {guidance['predicted_success']:.0%}")
    if guidance['injection']:
        print(f"  Injection:\n{guidance['injection']}")
    
    # Test 2: After tool (success)
    print("\n[2] After successful tool...")
    uc.after_tool("terminal", {"command": "ls"}, {"output": "file1 file2"}, "", "listing files")
    
    # Test 3: After tool (error)
    print("\n[3] After failed tool...")
    uc.after_tool(
        "web_search",
        {"query": "a"},
        {"error": "Query too short"},
        "Query too short",
        "searching for something"
    )
    
    # Test 4: Build injection
    print("\n[4] Context injection...")
    injection = uc.build_context_injection("I need to find a file")
    if injection:
        print(injection)
    else:
        print("  (No injection yet - need more data)")
    
    # Test 5: Session report
    print("\n[5] Session report...")
    report = uc.get_session_report()
    print(f"  Calls: {report['total_calls']}")
    print(f"  Success rate: {report['success_rate']:.0%}")
    print(f"  Warnings given: {report['warnings_given']}")
    print(f"  Lessons learned: {report['lessons_learned']}")
    
    print("\n" + "="*70)
    print("UNIFIED CORTEX READY")
    print("="*70)
