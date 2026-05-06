#!/usr/bin/env python3
# Token Budget Tracker
# Monitors token usage per session

import sqlite3
from datetime import datetime

class TokenBudgetTracker:
    def __init__(self, daily_budget=1000000):
        self.daily_budget = daily_budget
        self.conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
        self._ensure_table()
    
    def _ensure_table(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY,
                session_id TEXT,
                tool_name TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                timestamp TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def log_usage(self, session_id, tool_name, input_tokens, output_tokens):
        """Log token usage."""
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO token_usage (session_id, tool_name, input_tokens, output_tokens, timestamp)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (session_id, tool_name, input_tokens, output_tokens))
        self.conn.commit()
    
    def get_session_usage(self, session_id):
        """Get total usage for session."""
        c = self.conn.cursor()
        c.execute('''
            SELECT SUM(input_tokens), SUM(output_tokens), COUNT(DISTINCT tool_name)
            FROM token_usage
            WHERE session_id = ?
            AND timestamp > datetime('now', '-1 day')
        ''', (session_id,))
        row = c.fetchone()
        return {
            'input': row[0] or 0,
            'output': row[1] or 0,
            'total': (row[0] or 0) + (row[1] or 0),
            'tools_used': row[2] or 0
        }
    
    def get_budget_status(self, session_id):
        """Check if within budget."""
        usage = self.get_session_usage(session_id)
        remaining = self.daily_budget - usage['total']
        return {
            'used': usage['total'],
            'budget': self.daily_budget,
            'remaining': remaining,
            'percent_used': (usage['total'] / self.daily_budget) * 100,
            'status': 'OK' if remaining > 0 else 'OVER_BUDGET'
        }

if __name__ == '__main__':
    tracker = TokenBudgetTracker()
    print("Token budget tracker ready")
