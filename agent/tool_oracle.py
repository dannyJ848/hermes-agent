#!/usr/bin/env python3
"""
tool_oracle.py — Predictive tool selection and argument optimization.

Analyzes my task → Predicts optimal tool sequence → Validates my choice →
Suggests improvements.

Usage:
    from tool_oracle import ToolOracle
    oracle = ToolOracle()
    
    # Before I choose a tool
    prediction = oracle.predict_tools("I need to find a file")
    print(f"Recommended: {prediction['primary']} (confidence: {prediction['confidence']:.0%})")
    
    # After I choose
    validation = oracle.validate_choice("search_files", "I need to find a file")
    if not validation['is_optimal']:
        print(f"Better option: {validation['suggested']}")
"""

import sys
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

sys.path.insert(0, str(Path.home() / "hermes-agent"))
from agent.cortex_access import CortexDB, cortex_cursor


class ToolOracle:
    """Predicts optimal tool selection based on task and my history."""
    
    # Task → Tool mapping (learned from my history + common patterns)
    TASK_PATTERNS = {
        # File operations
        r'find.*file|locate.*file|search.*file|where is|find all': ['search_files', 'terminal'],
        r'read.*file|show.*content|get.*content|cat.*file|contents of': ['read_file', 'terminal'],
        r'write.*file|create.*file|save.*to|make.*file': ['write_file', 'terminal'],
        r'edit.*file|modify.*file|patch.*file|change.*in': ['patch', 'write_file'],
        r'list.*file|ls.*dir|show.*directory|files in': ['search_files', 'terminal'],
        
        # Web operations
        r'search.*web|google.*for|look up|find.*online|search for': ['web_search', 'web_extract'],
        r'visit.*website|go to.*url|open.*page|navigate to': ['browser_navigate', 'web_extract'],
        r'scrape.*website|extract.*from.*site|get.*from.*url': ['web_extract', 'browser_navigate'],
        
        # Code operations
        r'run.*python|execute.*script|python.*code|run code': ['execute_code', 'terminal'],
        r'run.*command|execute.*shell|bash.*command|shell command': ['terminal', 'execute_code'],
        r'build.*project|compile.*code|make.*install|npm install': ['terminal', 'execute_code'],
        
        # Database operations
        r'query.*database|sql.*query|select.*from|run.*sql': ['terminal', 'execute_code'],
        r'check.*database|inspect.*db|schema.*info|database status': ['terminal'],
        
        # System operations
        r'check.*disk|free.*space|df.*-h|disk usage': ['terminal'],
        r'check.*process|ps.*aux|kill.*process|process status': ['terminal', 'process'],
        r'check.*network|ping.*host|curl.*url|network test': ['terminal'],
        
        # Information extraction
        r'get.*info|extract.*data|pull.*from|fetch.*data': ['web_extract', 'web_search'],
        r'analyze.*image|describe.*picture|what.*in.*image|vision': ['vision_analyze'],
        r'take.*screenshot|capture.*screen|screen shot': ['screencapture'],
        
        # Communication
        r'send.*message|email|notify|alert': ['send_message'],
        r'schedule.*task|cron.*job|run.*later': ['cronjob'],
        
        # Development
        r'git.*clone|git.*pull|git.*push|git.*commit': ['terminal'],
        r'docker.*build|docker.*run|docker.*compose': ['terminal'],
        r'test.*code|run.*test|pytest|unittest': ['terminal', 'execute_code'],
    }
    
    # Tool → Common argument patterns (for validation)
    ARG_PATTERNS = {
        'terminal': {
            'required_sometimes': ['timeout'],
            'recommended': ['workdir'],
            'dangerous_patterns': ['rm -rf /', 'rm -rf ~', '> /dev/null', 'mkfs'],
            'common_success_patterns': ['timeout=30', 'workdir=', 'set -e'],
        },
        'web_search': {
            'min_query_length': 10,
            'recommended': ['limit'],
            'anti_patterns': ['query=""', 'query="a"', 'query="the"'],
        },
        'read_file': {
            'recommended': ['offset', 'limit'],
            'anti_patterns': ['path=""', 'path="/"'],
        },
        'execute_code': {
            'recommended': ['timeout'],
            'dangerous_patterns': ['os.system', 'subprocess.call', 'eval(', 'exec('],
        },
        'browser_navigate': {
            'required': ['url'],
            'anti_patterns': ['url=""', 'url="http://"'],
        },
    }
    
    def __init__(self, db: Optional[CortexDB] = None):
        self.db = db or CortexDB()
        self._my_history: Dict[str, List[Dict]] = defaultdict(list)
        self._load_my_history()
    
    def _load_my_history(self):
        """Load my tool usage history from database."""
        try:
            with cortex_cursor() as cur:
                cur.execute("""
                    SELECT tool_name, task_preview, actual_tools, accuracy
                    FROM tool_predictions
                    WHERE learned_at > NOW() - INTERVAL '7 days'
                    ORDER BY accuracy DESC
                    LIMIT 100
                """)
                for row in cur.fetchall():
                    self._my_history[row['tool_name']].append({
                        'task': row['task_preview'],
                        'tools': row['actual_tools'],
                        'accuracy': row['accuracy']
                    })
        except Exception:
            pass
    
    def predict_tools(self, task_description: str, 
                      available_tools: List[str] = None) -> Dict:
        """
        Predict optimal tool(s) for a task.
        
        Returns:
            {
                'primary': 'tool_name',
                'alternatives': ['tool2', 'tool3'],
                'confidence': 0.85,
                'reasoning': 'why this tool',
                'arg_suggestions': {'key': 'value'}
            }
        """
        task_lower = task_description.lower()
        
        # Step 1: Pattern matching
        matches = []
        for pattern, tools in self.TASK_PATTERNS.items():
            if re.search(pattern, task_lower, re.IGNORECASE):
                for tool in tools:
                    matches.append((tool, 0.8))
        
        # Step 2: My history matching
        if self._my_history:
            for tool, history in self._my_history.items():
                for entry in history:
                    if entry['task'] and self._task_similarity(task_lower, entry['task'].lower()) > 0.6:
                        matches.append((tool, entry['accuracy'] * 0.7))
        
        # Step 3: Score and rank
        tool_scores = defaultdict(float)
        for tool, score in matches:
            tool_scores[tool] += score
        
        if not tool_scores:
            return {
                'primary': None,
                'alternatives': [],
                'confidence': 0,
                'reasoning': 'No strong pattern match. Consider web_search for discovery.',
                'arg_suggestions': {}
            }
        
        # Rank by score
        ranked = sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
        primary = ranked[0][0]
        confidence = min(0.95, ranked[0][1])
        
        # Get alternatives
        alternatives = [t for t, s in ranked[1:3] if s > 0.3]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(primary, task_lower)
        
        # Suggest args
        arg_suggestions = self._suggest_args(primary, task_lower)
        
        return {
            'primary': primary,
            'alternatives': alternatives,
            'confidence': confidence,
            'reasoning': reasoning,
            'arg_suggestions': arg_suggestions
        }
    
    def _task_similarity(self, task1: str, task2: str) -> float:
        """Simple word overlap similarity."""
        words1 = set(task1.split())
        words2 = set(task2.split())
        if not words1 or not words2:
            return 0
        overlap = len(words1 & words2)
        return overlap / max(len(words1), len(words2))
    
    def _generate_reasoning(self, tool: str, task: str) -> str:
        """Generate human-readable reasoning for tool choice."""
        reasons = {
            'search_files': 'Best for finding files by name or pattern',
            'read_file': 'Best for reading file contents',
            'write_file': 'Best for creating or overwriting files',
            'patch': 'Best for targeted edits to existing files',
            'terminal': 'Best for complex shell operations and system commands',
            'execute_code': 'Best for running Python scripts and data processing',
            'web_search': 'Best for finding information online',
            'web_extract': 'Best for extracting content from specific URLs',
            'browser_navigate': 'Best for interactive web browsing and JavaScript sites',
            'vision_analyze': 'Best for analyzing images and screenshots',
            'screencapture': 'Best for capturing the current screen',
        }
        return reasons.get(tool, f'{tool} matches the task pattern')
    
    def _suggest_args(self, tool: str, task: str) -> Dict:
        """Suggest arguments based on task and tool."""
        suggestions = {}
        
        if tool == 'terminal':
            if 'dangerous' in task or 'rm' in task or 'delete' in task:
                suggestions['timeout'] = '30'
            if 'build' in task or 'compile' in task or 'install' in task:
                suggestions['timeout'] = '300'
        
        elif tool == 'web_search':
            if 'limit' not in task:
                suggestions['limit'] = '5'
        
        elif tool == 'read_file':
            if 'large' in task or 'big' in task:
                suggestions['limit'] = '100'
        
        return suggestions
    
    def validate_choice(self, chosen_tool: str, task_description: str,
                       args: Dict = None) -> Dict:
        """
        Validate if my tool choice is optimal.
        
        Returns:
            {
                'is_optimal': True/False,
                'confidence': 0.85,
                'suggested': 'better_tool',
                'issues': ['issue1', 'issue2'],
                'improvements': {'arg': 'suggestion'}
            }
        """
        prediction = self.predict_tools(task_description)
        
        is_optimal = prediction['primary'] == chosen_tool
        
        issues = []
        improvements = {}
        
        # Check if there's a better tool
        if not is_optimal and prediction['confidence'] > 0.7:
            issues.append(
                f"{prediction['primary']} might be better ({prediction['reasoning']})"
            )
        
        # Validate args
        if args:
            arg_issues = self._validate_args(chosen_tool, args)
            issues.extend(arg_issues)
            
            # Suggest improvements
            for key, val in prediction.get('arg_suggestions', {}).items():
                if key not in args:
                    improvements[key] = val
        
        return {
            'is_optimal': is_optimal or prediction['confidence'] < 0.5,
            'confidence': prediction['confidence'],
            'suggested': prediction['primary'] if not is_optimal else None,
            'issues': issues,
            'improvements': improvements
        }
    
    def _validate_args(self, tool: str, args: Dict) -> List[str]:
        """Validate arguments for a tool."""
        issues = []
        
        if tool not in self.ARG_PATTERNS:
            return issues
        
        patterns = self.ARG_PATTERNS[tool]
        
        # Check required args
        if 'required' in patterns:
            for req in patterns['required']:
                if req not in args or not args[req]:
                    issues.append(f"Missing required arg: {req}")
        
        # Check anti-patterns
        if 'anti_patterns' in patterns:
            for anti in patterns['anti_patterns']:
                key, val = anti.split('=') if '=' in anti else (anti, '')
                if key in args:
                    arg_val = str(args[key])
                    if val and arg_val == val:
                        issues.append(f"Invalid value for {key}: {arg_val}")
                    elif not val and not arg_val:
                        issues.append(f"Empty value for {key}")
        
        # Check dangerous patterns
        if 'dangerous_patterns' in patterns:
            arg_str = json.dumps(args).lower()
            for danger in patterns['dangerous_patterns']:
                if danger in arg_str:
                    issues.append(f"Dangerous pattern detected: {danger}")
        
        return issues
    
    def record_outcome(self, task_description: str, predicted: str, 
                       actual: str, success: bool):
        """Record prediction outcome for learning."""
        try:
            task_hash = hashlib.md5(task_description.encode()).hexdigest()[:16]
            accuracy = 1.0 if predicted == actual else 0.0
            
            with cortex_cursor() as cur:
                cur.execute("""
                    INSERT INTO tool_predictions
                    (task_hash, task_preview, predicted_tools, actual_tools, accuracy)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    task_hash,
                    task_description[:200],
                    json.dumps([predicted]),
                    json.dumps([actual]),
                    accuracy
                ))
        except Exception:
            pass


# Singleton
_oracle_instance = None

def get_oracle() -> ToolOracle:
    """Get singleton instance."""
    global _oracle_instance
    if _oracle_instance is None:
        _oracle_instance = ToolOracle()
    return _oracle_instance


if __name__ == "__main__":
    oracle = ToolOracle()
    
    # Test predictions
    tests = [
        "I need to find all Python files in the project",
        "Search for information about quantum computing",
        "Read the contents of config.yaml",
        "Run a Python script to process data",
        "Take a screenshot of the current screen",
    ]
    
    for task in tests:
        pred = oracle.predict_tools(task)
        print(f"\nTask: {task}")
        print(f"  Primary: {pred['primary']} ({pred['confidence']:.0%})")
        print(f"  Why: {pred['reasoning']}")
        if pred['alternatives']:
            print(f"  Alternatives: {', '.join(pred['alternatives'])}")
        if pred['arg_suggestions']:
            print(f"  Arg suggestions: {pred['arg_suggestions']}")
