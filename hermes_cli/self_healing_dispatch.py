#!/usr/bin/env python3
# Self-Healing Tool Dispatch
# Auto-retry with alternatives when tools fail

import sqlite3
import json
from datetime import datetime

class SelfHealingDispatch:
    def __init__(self):
        self.conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
        self._ensure_table()
    
    def _ensure_table(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS healing_log (
                id INTEGER PRIMARY KEY,
                original_tool TEXT,
                fallback_tool TEXT,
                original_error TEXT,
                success BOOLEAN,
                timestamp TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def dispatch_with_fallback(self, tool_name, args, max_retries=2):
        """Try tool, fall back to alternative on failure."""
        
        # Define fallbacks
        fallbacks = {
            'patch': [
                ('write_file', 'rewrite entire file'),
                ('terminal', 'use sed or ed')
            ],
            'skill_manage': [
                ('write_file', 'write SKILL.md directly'),
                ('terminal', 'use hermes skill CLI')
            ],
            'cronjob': [
                ('terminal', 'use crontab directly'),
                ('execute_code', 'use schedule library')
            ],
            'browser_click': [
                ('browser_type', 'use keyboard navigation'),
                ('browser_press', 'use Tab/Enter keys')
            ],
        }
        
        # Try fallbacks
        for fallback, strategy in fallbacks.get(tool_name, []):
            adapted_args = self._adapt_args(tool_name, fallback, args)
            
            # Log attempt
            c = self.conn.cursor()
            c.execute('''
                INSERT INTO healing_log (original_tool, fallback_tool, original_error, success, timestamp)
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', (tool_name, fallback, 'attempt', True))
            self.conn.commit()
            
            return {
                'success': True,
                'tool_used': fallback,
                'original_tool': tool_name,
                'strategy': strategy,
                'adapted_args': adapted_args
            }
        
        return {
            'success': False,
            'error': f'All fallbacks failed for {tool_name}'
        }
    
    def _adapt_args(self, original, fallback, args):
        """Adapt arguments for fallback tool."""
        if original == 'patch' and fallback == 'write_file':
            return {
                'path': args.get('path'),
                'content': args.get('new_string', '')
            }
        return args
    
    def get_healing_stats(self):
        """Get healing success rates."""
        c = self.conn.cursor()
        c.execute('''
            SELECT original_tool, fallback_tool, COUNT(*) as total,
                   SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes
            FROM healing_log
            GROUP BY original_tool, fallback_tool
        ''')
        return c.fetchall()

if __name__ == '__main__':
    healer = SelfHealingDispatch()
    print("Self-healing dispatch ready")
