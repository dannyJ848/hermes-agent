#!/usr/bin/env python3
# Failure Post-Mortem
# Auto-analyzes errors and extracts learnings

import sqlite3
import re
from datetime import datetime

class FailurePostMortem:
    def __init__(self):
        self.conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
        self._ensure_table()
    
    def _ensure_table(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS error_patterns (
                id INTEGER PRIMARY KEY,
                error_signature TEXT,
                tool_name TEXT,
                root_cause TEXT,
                fix_strategy TEXT,
                occurrence_count INTEGER DEFAULT 1,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                tip_generated BOOLEAN DEFAULT FALSE
            )
        ''')
        self.conn.commit()
    
    def analyze(self, tool_name, error_message, context=None):
        """Analyze an error and extract pattern."""
        
        # Extract signature
        signature = self._extract_signature(error_message)
        
        # Classify root cause
        root_cause = self._classify_error(error_message)
        
        # Determine fix
        fix = self._suggest_fix(tool_name, root_cause)
        
        # Store or update
        c = self.conn.cursor()
        # Check if table has the right schema
        c.execute("PRAGMA table_info(error_patterns)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'error_signature' not in columns:
            # Recreate table with correct schema
            c.execute('DROP TABLE IF EXISTS error_patterns')
            self._ensure_table()
        
        c.execute('''
            SELECT id, occurrence_count FROM error_patterns
            WHERE error_signature = ? AND tool_name = ?
        ''', (signature, tool_name))
        
        row = c.fetchone()
        if row:
            c.execute('''
                UPDATE error_patterns
                SET occurrence_count = ?, last_seen = datetime('now')
                WHERE id = ?
            ''', (row[1] + 1, row[0]))
        else:
            c.execute('''
                INSERT INTO error_patterns 
                (error_signature, tool_name, root_cause, fix_strategy, first_seen, last_seen)
                VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
            ''', (signature, tool_name, root_cause, fix))
        
        self.conn.commit()
        
        return {
            'signature': signature,
            'root_cause': root_cause,
            'fix': fix,
            'is_new': row is None
        }
    
    def _extract_signature(self, error):
        """Extract error signature for pattern matching."""
        # Remove variable parts (paths, line numbers)
        sig = re.sub(r'/[^\s]+', '/PATH', error)
        sig = re.sub(r'line \d+', 'line N', sig)
        sig = re.sub(r'0x[0-9a-f]+', 'ADDR', sig)
        return sig[:200]
    
    def _classify_error(self, error):
        """Classify error type."""
        patterns = {
            'SyntaxError': 'code_formatting',
            'IndentationError': 'code_formatting',
            'OperationalError': 'database_schema',
            'no such table': 'database_schema',
            'unterminated string': 'string_quoting',
            'identical': 'patch_logic',
            'timeout': 'performance',
            'connection': 'network',
        }
        
        for pattern, category in patterns.items():
            if pattern in error:
                return category
        
        return 'unknown'
    
    def _suggest_fix(self, tool, cause):
        """Suggest fix based on tool and cause."""
        fixes = {
            ('patch', 'patch_logic'): 'Verify old_string uniqueness before patching',
            ('execute_code', 'code_formatting'): 'Use write_file for multi-line strings',
            ('execute_code', 'string_quoting'): 'Escape quotes or use triple quotes',
            ('terminal', 'database_schema'): 'Check table exists before querying',
        }
        
        return fixes.get((tool, cause), 'Review error and try alternative approach')
    
    def get_common_errors(self, min_occurrences=2):
        """Get frequently occurring errors."""
        c = self.conn.cursor()
        c.execute('''
            SELECT tool_name, error_signature, root_cause, fix_strategy, occurrence_count
            FROM error_patterns
            WHERE occurrence_count >= ?
            ORDER BY occurrence_count DESC
        ''', (min_occurrences,))
        return c.fetchall()

if __name__ == '__main__':
    pm = FailurePostMortem()
    # Test with my actual errors
    pm.analyze('patch', 'old_string and new_string are identical')
    pm.analyze('terminal', 'OperationalError: no such table: cortex_nodes')
    pm.analyze('execute_code', 'SyntaxError: unterminated string literal')
    print("Post-mortem system ready")
