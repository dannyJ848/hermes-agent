#!/usr/bin/env python3
"""
anomaly_detector.py — Predictive interruption for NEW mistakes.

Detects when I'm about to make a mistake I've NEVER made before
by identifying anomalies in my reasoning and tool selection.

Usage:
    from anomaly_detector import AnomalyDetector
    ad = AnomalyDetector()
    
    # Before tool call
    anomaly = ad.detect_anomaly(tool_name, args, reasoning_trace)
    if anomaly:
        print(f"ANOMALY: {anomaly['description']}")
        print(f"Confidence: {anomaly['confidence']:.0%}")
"""

import sys
import os
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter

sys.path.insert(0, str(Path.home() / "hermes-agent"))
from agent.cortex_access import CortexDB, cortex_cursor


class AnomalyDetector:
    """Detects anomalous behavior before it becomes a mistake."""
    
    def __init__(self, db: Optional[CortexDB] = None):
        self.db = db or CortexDB()
        self._my_patterns = self._load_patterns()
        self._global_stats = self._load_global_stats()
    
    def _load_patterns(self) -> Dict:
        """Load my normal patterns from database."""
        patterns = {
            'tools': Counter(),
            'args': defaultdict(Counter),
            'sequences': defaultdict(Counter),
            'reasoning_keywords': Counter(),
        }
        
        try:
            with cortex_cursor() as cur:
                # Load from my_skills
                cur.execute("SELECT skill_name, total_calls FROM my_skills")
                for row in cur.fetchall():
                    patterns['tools'][row['skill_name']] = row['total_calls']
                
                # Load from tool_sequences
                cur.execute("SELECT tools, total_count FROM tool_sequences WHERE total_count > 1")
                for row in cur.fetchall():
                    tools = json.loads(row['tools'])
                    for i in range(len(tools) - 1):
                        patterns['sequences'][tools[i]][tools[i+1]] += row['total_count']
        except Exception:
            pass
        
        return patterns
    
    def _load_global_stats(self) -> Dict:
        """Load global statistics for baseline comparison."""
        stats = {
            'avg_chain_length': 3.5,
            'common_first_tools': ['web_search', 'terminal', 'read_file'],
            'rare_tools': ['vision_analyze', 'screencapture', 'send_message'],
        }
        return stats
    
    def detect_anomaly(self, tool_name: str, args: Dict,
                      reasoning: str, recent_tools: List[str] = None) -> Optional[Dict]:
        """
        Detect if current behavior is anomalous.
        
        Returns anomaly dict or None if normal.
        """
        anomalies = []
        
        # Check 1: Tool I've never used before
        if tool_name not in self._my_patterns['tools']:
            anomalies.append({
                'type': 'new_tool',
                'description': f"You've never used {tool_name} before. Review documentation?",
                'severity': 'info',
                'confidence': 0.9
            })
        
        # Check 2: Tool I rarely use (less than 3 times)
        elif self._my_patterns['tools'][tool_name] < 3:
            anomalies.append({
                'type': 'rare_tool',
                'description': f"You've only used {tool_name} {self._my_patterns['tools'][tool_name]} times. Proceed carefully.",
                'severity': 'low',
                'confidence': 0.7
            })
        
        # Check 3: Unusual sequence
        if recent_tools:
            last_tool = recent_tools[-1]
            if last_tool in self._my_patterns['sequences']:
                transitions = self._my_patterns['sequences'][last_tool]
                total = sum(transitions.values())
                
                if total > 5:
                    # Check if this transition is rare
                    current_count = transitions.get(tool_name, 0)
                    probability = current_count / total
                    
                    if probability < 0.1 and current_count < 2:
                        # Very rare transition
                        common_next = transitions.most_common(1)[0][0]
                        anomalies.append({
                            'type': 'rare_sequence',
                            'description': f"You usually use {common_next} after {last_tool}, not {tool_name}",
                            'severity': 'medium',
                            'confidence': 1 - probability
                        })
        
        # Check 4: Unusual reasoning keywords
        if reasoning:
            reasoning_lower = reasoning.lower()
            
            # Check for keywords I never use
            unusual_keywords = ['hack', 'workaround', 'temporary fix', 'good enough',
                              'probably fine', 'should work', 'maybe later']
            
            for keyword in unusual_keywords:
                if keyword in reasoning_lower:
                    anomalies.append({
                        'type': 'unusual_reasoning',
                        'description': f"Unusual reasoning pattern: '{keyword}'. Consider more rigorous approach.",
                        'severity': 'medium',
                        'confidence': 0.6
                    })
        
        # Check 5: Argument anomalies
        if args and tool_name in self._my_patterns['args']:
            arg_patterns = self._my_patterns['args'][tool_name]
            
            for arg_key, arg_val in args.items():
                if arg_key in arg_patterns:
                    # Check if value is unusual
                    common_values = arg_patterns[arg_key].most_common(3)
                    if common_values:
                        str_val = str(arg_val)
                        is_unusual = all(str_val != v for v, _ in common_values)
                        if is_unusual:
                            anomalies.append({
                                'type': 'unusual_arg',
                                'description': f"Unusual value for {arg_key}: {str_val[:50]}. Common: {', '.join(v for v, _ in common_values[:2])}",
                                'severity': 'low',
                                'confidence': 0.5
                            })
        
        # Return highest confidence anomaly
        if anomalies:
            # Sort by severity then confidence
            severity_order = {'high': 3, 'medium': 2, 'low': 1, 'info': 0}
            anomalies.sort(key=lambda x: (severity_order.get(x['severity'], 0), x['confidence']), reverse=True)
            return anomalies[0]
        
        return None
    
    def get_risk_score(self, tool_name: str, args: Dict,
                      reasoning: str, recent_tools: List[str] = None) -> float:
        """Calculate overall risk score 0-1."""
        score = 0.0
        
        # Base risk from tool familiarity
        if tool_name not in self._my_patterns['tools']:
            score += 0.3
        elif self._my_patterns['tools'][tool_name] < 5:
            score += 0.15
        
        # Sequence risk
        if recent_tools:
            last_tool = recent_tools[-1]
            if last_tool in self._my_patterns['sequences']:
                transitions = self._my_patterns['sequences'][last_tool]
                total = sum(transitions.values())
                if total > 5:
                    prob = transitions.get(tool_name, 0) / total
                    score += max(0, 0.2 - prob * 2)
        
        # Reasoning risk
        if reasoning:
            risky_keywords = ['hack', 'temporary', 'workaround', 'probably', 'maybe']
            for kw in risky_keywords:
                if kw in reasoning.lower():
                    score += 0.1
        
        return min(1.0, score)
    
    def build_warning(self, anomaly: Dict) -> str:
        """Build a warning message from anomaly."""
        severity_emoji = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢',
            'info': '🔵'
        }
        
        emoji = severity_emoji.get(anomaly['severity'], '⚠️')
        return f"{emoji} ANOMALY ({anomaly['type']}): {anomaly['description']}"


# Singleton
_detector_instance = None

def get_detector() -> AnomalyDetector:
    """Get singleton."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = AnomalyDetector()
    return _detector_instance


if __name__ == "__main__":
    print("="*70)
    print("ANOMALY DETECTOR TEST")
    print("="*70)
    
    ad = AnomalyDetector()
    
    # Test 1: Normal behavior
    print("\n[1] Normal behavior (web_search):")
    anomaly = ad.detect_anomaly("web_search", {"query": "python tutorial"}, 
                                  "I need to find Python docs")
    if anomaly:
        print(f"    Anomaly: {anomaly}")
    else:
        print("    ✓ No anomaly detected")
    
    # Test 2: New tool
    print("\n[2] New tool (vision_analyze):")
    anomaly = ad.detect_anomaly("vision_analyze", {"image_url": "test.jpg"},
                                  "Analyzing this image")
    if anomaly:
        print(f"    {ad.build_warning(anomaly)}")
    
    # Test 3: Rare sequence
    print("\n[3] Rare sequence (terminal after web_search):")
    anomaly = ad.detect_anomaly("terminal", {"command": "ls"},
                                  "Listing files",
                                  recent_tools=["web_search"])
    if anomaly:
        print(f"    {ad.build_warning(anomaly)}")
    else:
        print("    ✓ No anomaly (or not enough data)")
    
    # Test 4: Risk score
    print("\n[4] Risk scores:")
    for tool in ["web_search", "vision_analyze", "screencapture"]:
        risk = ad.get_risk_score(tool, {}, "Testing")
        print(f"    {tool}: {risk:.0%} risk")
    
    print("\n" + "="*70)
    print("ANOMALY DETECTOR READY")
    print("="*70)
