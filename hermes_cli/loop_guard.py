#!/usr/bin/env python3
# Loop Detection Guard
# Detects and prevents repetitive tool call loops

import sqlite3
import json
from datetime import datetime

class LoopGuard:
    def __init__(self, threshold=3, window_seconds=60):
        self.threshold = int(threshold)
        self.window = int(window_seconds)
        self.conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
        self._ensure_table()
    
    def _ensure_table(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS loop_detection (
                id INTEGER PRIMARY KEY,
                tool_name TEXT,
                args_hash TEXT,
                timestamp TIMESTAMP,
                session_id TEXT
            )
        ''')
        self.conn.commit()
    
    def check_loop(self, tool_name, args, session_id="default"):
        """Check if this tool call would create a loop."""
        import hashlib
        args_hash = hashlib.md5(json.dumps(args, sort_keys=True).encode()).hexdigest()[:16]
        
        c = self.conn.cursor()
        c.execute('''
            SELECT COUNT(*) FROM loop_detection
            WHERE tool_name = ? AND args_hash = ?
            AND timestamp > datetime('now', '-{} seconds')
        '''.format(self.window), (tool_name, args_hash))
        
        count = int(c.fetchone()[0])
        
        # Log this attempt
        c.execute('''
            INSERT INTO loop_detection (tool_name, args_hash, timestamp, session_id)
            VALUES (?, ?, datetime('now'), ?)
        ''', (tool_name, args_hash, session_id))
        self.conn.commit()
        
        if count >= self.threshold:
            return {
                'is_loop': True,
                'count': count + 1,
                'recommendation': self._get_alternative(tool_name),
                'action': 'BLOCK'
            }
        
        return {'is_loop': False, 'count': count + 1}
    
    def _get_alternative(self, tool_name):
        """Get alternative tool based on intelligence."""
        alternatives = {
            'patch': 'Use write_file or terminal sed instead',
            'skill_manage': 'Use write_file to create SKILL.md directly',
            'cronjob': 'Use terminal crontab or python schedule library',
        }
        return alternatives.get(tool_name, 'Try a different approach')
    
    def cleanup(self):
        """Remove old entries."""
        c = self.conn.cursor()
        c.execute('''
            DELETE FROM loop_detection
            WHERE timestamp < datetime('now', '-1 hour')
        ''')
        self.conn.commit()

if __name__ == '__main__':
    guard = LoopGuard()
    # Test
    result = guard.check_loop('patch', {'path': '/test', 'old': 'a', 'new': 'b'})
    print(f"Loop check: {result}")
