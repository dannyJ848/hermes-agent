#!/usr/bin/env python3
# Context Updater
# Updates unified_context.db after each significant action

import sqlite3
import json
from datetime import datetime

class ContextUpdater:
    def __init__(self):
        self.conn = sqlite3.connect('/Users/dannygomez/.hermes/unified_context.db')
    
    def update_tool_result(self, tool_name, success, latency_ms, error=None):
        """Update tool intelligence after each call."""
        c = self.conn.cursor()
        c.execute('''
            SELECT success_rate, total_calls FROM tool_intelligence_snapshot
            WHERE tool_name = ?
        ''', (tool_name,))
        row = c.fetchone()
        
        if row:
            old_rate, old_count = row
            new_count = old_count + 1
            new_rate = ((old_rate * old_count) + (1.0 if success else 0.0)) / new_count
            
            state = 'CLOSED' if new_rate > 0.6 else 'OPEN'
            
            c.execute('''
                UPDATE tool_intelligence_snapshot
                SET success_rate = ?, total_calls = ?, avg_latency_ms = ?,
                    circuit_state = ?, last_failure = ?
                WHERE tool_name = ?
            ''', (new_rate, new_count, latency_ms, state, 
                  error if not success else None, tool_name))
        
        self.conn.commit()
    
    def record_error(self, tool_name, error_message, fix):
        """Record new error pattern."""
        c = self.conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO error_registry
            (signature, tool_name, root_cause, fix, occurrences, last_seen)
            VALUES (?, ?, ?, ?, 
                COALESCE((SELECT occurrences + 1 FROM error_registry WHERE signature = ?), 1),
                datetime('now'))
        ''', (error_message[:100], tool_name, 'auto', fix, error_message[:100]))
        self.conn.commit()
    
    def update_session(self, session_id, task=None, decision=None, file=None):
        """Update active session."""
        c = self.conn.cursor()
        c.execute('''
            SELECT active_tasks, decisions_made, files_modified
            FROM session_continuity WHERE session_id = ?
        ''', (session_id,))
        row = c.fetchone()
        
        if row:
            tasks = json.loads(row[0]) if row[0] else []
            decisions = json.loads(row[1]) if row[1] else []
            files = json.loads(row[2]) if row[2] else []
            
            if task and task not in tasks:
                tasks.append(task)
            if decision and decision not in decisions:
                decisions.append(decision)
            if file and file not in files:
                files.append(file)
            
            c.execute('''
                UPDATE session_continuity
                SET last_activity = datetime('now'),
                    active_tasks = ?, decisions_made = ?, files_modified = ?
                WHERE session_id = ?
            ''', (json.dumps(tasks), json.dumps(decisions), json.dumps(files), session_id))
        
        self.conn.commit()
    
    def set_context(self, key, value, category='general', priority=5):
        """Set arbitrary context key."""
        c = self.conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO cli_context (key, category, value, priority, last_updated)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (key, category, value, priority))
        self.conn.commit()

if __name__ == '__main__':
    updater = ContextUpdater()
    print("Context updater ready")
