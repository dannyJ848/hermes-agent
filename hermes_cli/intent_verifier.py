#!/usr/bin/env python3
# Intent Verification
# Verifies output matches user intent

import sqlite3
from datetime import datetime

class IntentVerifier:
    def __init__(self):
        self.conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
        self._ensure_table()
    
    def _ensure_table(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS intent_checks (
                id INTEGER PRIMARY KEY,
                task_description TEXT,
                expected_outcome TEXT,
                actual_outcome TEXT,
                match_score REAL,
                verified BOOLEAN,
                timestamp TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def should_verify(self, task_description, tool_count, duration_seconds):
        """Determine if verification is needed."""
        if tool_count > 5:
            return True
        if duration_seconds > 300:
            return True
        if any(word in task_description.lower() for word in ['merge', 'update', 'fix', 'refactor']):
            return True
        return False
    
    def record_intent(self, task, expected):
        """Record what user intended."""
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO intent_checks (task_description, expected_outcome, timestamp)
            VALUES (?, ?, datetime('now'))
        ''', (task, expected))
        self.conn.commit()
        return c.lastrowid
    
    def verify_outcome(self, check_id, actual, auto_score=True):
        """Verify actual outcome matches intent."""
        c = self.conn.cursor()
        
        if auto_score:
            c.execute('SELECT expected_outcome FROM intent_checks WHERE id = ?', (check_id,))
            row = c.fetchone()
            if row is None:
                return {'match_score': None, 'needs_clarification': True, 'error': 'check_id not found'}
            expected = row[0]
            score = self._calculate_match(expected, actual)
        else:
            score = None
        
        c.execute('''
            UPDATE intent_checks
            SET actual_outcome = ?, match_score = ?, verified = ?
            WHERE id = ?
        ''', (actual, score, score is not None and score > 0.7, check_id))
        self.conn.commit()
        
        return {
            'match_score': score,
            'needs_clarification': score is not None and score < 0.5
        }
    
    def _calculate_match(self, expected, actual):
        """Simple text similarity."""
        exp_words = set(expected.lower().split())
        act_words = set(actual.lower().split())
        
        if not exp_words:
            return 0.0
        
        intersection = exp_words & act_words
        return len(intersection) / len(exp_words)

if __name__ == '__main__':
    verifier = IntentVerifier()
    print("Intent verification ready")
