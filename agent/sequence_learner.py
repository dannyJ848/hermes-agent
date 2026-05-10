#!/usr/bin/env python3
"""
sequence_learner.py — Learn optimal tool sequences and chains.

Discovers:
  1. Common tool chains (e.g., web_search → web_extract)
  2. Success patterns (which sequences work best)
  3. Failure patterns (which sequences fail)
  4. Optimization opportunities (skip unnecessary steps)

Usage:
    from sequence_learner import SequenceLearner
    sl = SequenceLearner()
    
    # After a task
    sl.record_sequence(['web_search', 'web_extract', 'write_file'], success=True)
    
    # Before starting
    suggestion = sl.suggest_next_tool(['web_search'])
    print(f"After web_search, try: {suggestion}")
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter

sys.path.insert(0, str(Path.home() / "hermes-agent"))
from agent.cortex_access import CortexDB, cortex_cursor


class SequenceLearner:
    """Learns optimal tool sequences from experience."""
    
    def __init__(self, db: Optional[CortexDB] = None):
        self.db = db or CortexDB()
        self._chains = defaultdict(lambda: {'success': 0, 'failure': 0, 'total': 0})
        self._transitions = defaultdict(lambda: Counter())
        self._current_chain = []
        self._load_historical()
    
    def _load_historical(self):
        """Load historical sequences from database."""
        try:
            with cortex_cursor() as cur:
                cur.execute("""
                    SELECT sequence_hash, tools, success_count, failure_count
                    FROM tool_sequences
                    WHERE total_count > 1
                    ORDER BY total_count DESC
                    LIMIT 100
                """)
                for row in cur.fetchall():
                    tools = json.loads(row['tools'])
                    key = tuple(tools)
                    self._chains[key] = {
                        'success': row['success_count'],
                        'failure': row['failure_count'],
                        'total': row['success_count'] + row['failure_count']
                    }
                    
                    # Build transition matrix
                    for i in range(len(tools) - 1):
                        self._transitions[tools[i]][tools[i+1]] += row['success_count'] + row['failure_count']
        except Exception:
            pass
    
    def record_tool(self, tool_name: str, success: bool = True):
        """Record a tool in the current chain."""
        self._current_chain.append({
            'tool': tool_name,
            'success': success,
            'time': time.time()
        })
    
    def complete_task(self, overall_success: bool = True):
        """Complete the current task and learn from the chain."""
        if len(self._current_chain) < 2:
            self._current_chain = []
            return
        
        tools = [step['tool'] for step in self._current_chain]
        key = tuple(tools)
        
        # Update in-memory
        self._chains[key]['total'] += 1
        if overall_success:
            self._chains[key]['success'] += 1
        else:
            self._chains[key]['failure'] += 1
        
        # Update transitions
        for i in range(len(tools) - 1):
            self._transitions[tools[i]][tools[i+1]] += 1
        
        # Store in database
        self._store_sequence(key, tools, overall_success)
        
        # Reset chain
        self._current_chain = []
    
    def _store_sequence(self, key: Tuple, tools: List[str], success: bool):
        """Store sequence in database."""
        try:
            with cortex_cursor() as cur:
                sequence_hash = hashlib.md5(json.dumps(tools).encode()).hexdigest()[:16]
                
                cur.execute("""
                    INSERT INTO tool_sequences 
                    (sequence_hash, tools, success_count, failure_count, total_count, last_used)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (sequence_hash) DO UPDATE SET
                        success_count = tool_sequences.success_count + EXCLUDED.success_count,
                        failure_count = tool_sequences.failure_count + EXCLUDED.failure_count,
                        total_count = tool_sequences.total_count + EXCLUDED.total_count,
                        last_used = NOW()
                """, (
                    sequence_hash,
                    json.dumps(tools),
                    1 if success else 0,
                    0 if success else 1,
                    1
                ))
        except Exception:
            pass
    
    def suggest_next_tool(self, current_chain: List[str]) -> Optional[Dict]:
        """
        Suggest the next tool based on current chain.
        
        Returns:
            {
                'tool': 'suggested_tool',
                'confidence': 0.85,
                'reason': 'why this tool',
                'alternatives': ['tool2', 'tool3']
            }
        """
        if not current_chain:
            return None
        
        current_tool = current_chain[-1]
        
        # Check transition probabilities
        if current_tool in self._transitions:
            transitions = self._transitions[current_tool]
            total = sum(transitions.values())
            
            if total > 0:
                ranked = sorted(transitions.items(), key=lambda x: -x[1])
                best_tool, best_count = ranked[0]
                confidence = best_count / total
                
                alternatives = [t for t, c in ranked[1:3]]
                
                # Check if this sequence has good history
                test_chain = current_chain + [best_tool]
                test_key = tuple(test_chain)
                
                if test_key in self._chains:
                    chain_stats = self._chains[test_key]
                    if chain_stats['total'] > 2:
                        success_rate = chain_stats['success'] / chain_stats['total']
                        if success_rate < 0.5:
                            # This sequence often fails, warn
                            return {
                                'tool': best_tool,
                                'confidence': confidence * 0.5,
                                'reason': f"Common next step, BUT this chain has {success_rate:.0%} success rate",
                                'alternatives': alternatives,
                                'warning': f"Low success rate for this sequence"
                            }
                
                return {
                    'tool': best_tool,
                    'confidence': confidence,
                    'reason': f"Used after {current_tool} in {best_count} tasks",
                    'alternatives': alternatives
                }
        
        # No data, suggest based on common patterns
        common_next = {
            'web_search': ['web_extract', 'browser_navigate'],
            'web_extract': ['write_file', 'execute_code'],
            'terminal': ['read_file', 'search_files'],
            'read_file': ['patch', 'write_file'],
            'search_files': ['read_file', 'terminal'],
        }
        
        if current_tool in common_next:
            return {
                'tool': common_next[current_tool][0],
                'confidence': 0.3,
                'reason': "Common pattern (no personal history yet)",
                'alternatives': common_next[current_tool][1:]
            }
        
        return None
    
    def get_optimal_chain(self, start_tool: str, end_goal: str) -> List[str]:
        """
        Find the optimal tool chain from start to goal.
        
        Uses BFS with success rate weighting.
        """
        # Simple BFS limited to depth 5
        from collections import deque
        
        queue = deque([(start_tool, [start_tool], 1.0)])
        best_chains = []
        
        while queue and len(best_chains) < 10:
            current, chain, prob = queue.popleft()
            
            if len(chain) > 5:
                continue
            
            # Check if we've reached something that can achieve the goal
            if self._can_achieve_goal(current, end_goal):
                best_chains.append((chain, prob))
                continue
            
            # Explore next tools
            if current in self._transitions:
                for next_tool, count in self._transitions[current].most_common(3):
                    # Calculate transition probability
                    total = sum(self._transitions[current].values())
                    transition_prob = count / total
                    
                    # Check chain success rate
                    test_key = tuple(chain + [next_tool])
                    if test_key in self._chains:
                        chain_stats = self._chains[test_key]
                        if chain_stats['total'] > 0:
                            chain_success = chain_stats['success'] / chain_stats['total']
                            transition_prob *= chain_success
                    
                    new_prob = prob * transition_prob
                    if new_prob > 0.1:  # Prune low probability paths
                        queue.append((next_tool, chain + [next_tool], new_prob))
        
        if best_chains:
            best_chains.sort(key=lambda x: -x[1])
            return best_chains[0][0]
        
        return [start_tool]
    
    def _can_achieve_goal(self, tool: str, goal: str) -> bool:
        """Check if a tool can achieve a goal."""
        goal_tool_map = {
            'find_file': ['search_files', 'terminal'],
            'read_content': ['read_file', 'terminal'],
            'write_content': ['write_file', 'patch'],
            'search_web': ['web_search', 'web_extract'],
            'run_code': ['execute_code', 'terminal'],
            'edit_file': ['patch', 'write_file'],
        }
        
        if goal in goal_tool_map:
            return tool in goal_tool_map[goal]
        
        return False
    
    def get_stats(self) -> Dict:
        """Get sequence learning stats."""
        return {
            'chains_learned': len(self._chains),
            'transitions_learned': len(self._transitions),
            'current_chain_length': len(self._current_chain),
            'top_chains': sorted(
                [(list(k), v['success'] / v['total'] if v['total'] > 0 else 0, v['total'])
                 for k, v in self._chains.items()],
                key=lambda x: -x[2]
            )[:5]
        }


import time

# Singleton
_learner_instance = None

def get_learner() -> SequenceLearner:
    """Get singleton."""
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = SequenceLearner()
    return _learner_instance


if __name__ == "__main__":
    print("="*70)
    print("SEQUENCE LEARNER TEST")
    print("="*70)
    
    sl = SequenceLearner()
    
    # Simulate some sequences
    print("\n[1] Recording sequences...")
    
    # Task 1: Search and extract
    sl.record_tool("web_search", True)
    sl.record_tool("web_extract", True)
    sl.record_tool("write_file", True)
    sl.complete_task(True)
    print("    Recorded: web_search → web_extract → write_file (success)")
    
    # Task 2: Same sequence, success
    sl.record_tool("web_search", True)
    sl.record_tool("web_extract", True)
    sl.record_tool("write_file", True)
    sl.complete_task(True)
    print("    Recorded: web_search → web_extract → write_file (success)")
    
    # Task 3: Different approach, failure
    sl.record_tool("web_search", True)
    sl.record_tool("browser_navigate", False)
    sl.complete_task(False)
    print("    Recorded: web_search → browser_navigate (failure)")
    
    # Test suggestions
    print("\n[2] Suggesting next tool...")
    suggestion = sl.suggest_next_tool(["web_search"])
    if suggestion:
        print(f"    After web_search, try: {suggestion['tool']} ({suggestion['confidence']:.0%})")
        print(f"    Why: {suggestion['reason']}")
        if suggestion.get('warning'):
            print(f"    ⚠ {suggestion['warning']}")
    
    # Test optimal chain
    print("\n[3] Finding optimal chain...")
    chain = sl.get_optimal_chain("web_search", "write_content")
    print(f"    web_search → {chain[1:]}")
    
    # Stats
    print("\n[4] Stats:")
    stats = sl.get_stats()
    print(f"    Chains learned: {stats['chains_learned']}")
    print(f"    Transitions: {stats['transitions_learned']}")
    print(f"    Top chains:")
    for chain, rate, count in stats['top_chains']:
        print(f"      {' → '.join(chain)}: {rate:.0%} ({count} times)")
    
    print("\n" + "="*70)
    print("SEQUENCE LEARNER READY")
    print("="*70)
