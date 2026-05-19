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
        # Check if table exists and what columns it has
        c.execute("PRAGMA table_info(token_usage)")
        existing = c.fetchall()
        
        if not existing:
            # Create new table with correct schema
            c.execute('''
                CREATE TABLE token_usage (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT,
                    tool_name TEXT,
                    tokens_in INTEGER DEFAULT 0,
                    tokens_out INTEGER DEFAULT 0,
                    speed_ms REAL DEFAULT 0,
                    success INTEGER DEFAULT 1,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')
        else:
            # Check if session_id column exists
            columns = [col[1] for col in existing]
            if 'session_id' not in columns:
                c.execute('ALTER TABLE token_usage ADD COLUMN session_id TEXT')
            if 'tokens_in' not in columns:
                c.execute('ALTER TABLE token_usage ADD COLUMN tokens_in INTEGER DEFAULT 0')
            if 'tokens_out' not in columns:
                c.execute('ALTER TABLE token_usage ADD COLUMN tokens_out INTEGER DEFAULT 0')
        
        self.conn.commit()
    
    def log_usage(self, session_id, tool_name, tokens_in=0, tokens_out=0):
        """Log token usage."""
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO token_usage (session_id, tool_name, tokens_in, tokens_out, created_at)
            VALUES (?, ?, ?, ?, strftime('%s', 'now'))
        ''', (session_id, tool_name, tokens_in, tokens_out))
        self.conn.commit()
    
    def get_session_usage(self, session_id):
        """Get total usage for session."""
        c = self.conn.cursor()
        c.execute('''
            SELECT SUM(tokens_in), SUM(tokens_out), COUNT(DISTINCT tool_name)
            FROM token_usage
            WHERE session_id = ?
            AND created_at > strftime('%s', 'now', '-1 day')
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
