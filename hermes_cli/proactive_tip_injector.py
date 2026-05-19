#!/usr/bin/env python3
# Proactive Tip Injection
# Surfaces relevant past learnings before user asks

import sqlite3
from datetime import datetime

class ProactiveTipInjector:
    def __init__(self):
        self.conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
    
    def get_relevant_tips(self, current_task, limit=3):
        """Get tips relevant to current task."""
        c = self.conn.cursor()
        
        # Check available tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('cortex_nodes', 'distilled_tips')")
        tables = [r[0] for r in c.fetchall()]
        
        keywords = current_task.lower().split()
        tips = []
        
        # Try cortex_nodes first
        if 'cortex_nodes' in tables:
            try:
                c.execute('''
                    SELECT text, elo, domain, confidence
                    FROM cortex_nodes
                    WHERE node_type = 'tip' AND is_active = TRUE
                    AND (''' + ' OR '.join(["LOWER(text) LIKE ?" for _ in keywords]) + ''')
                    ORDER BY elo DESC, confidence DESC
                    LIMIT ?
                ''', [f'%{k}%' for k in keywords] + [limit])
                for row in c.fetchall():
                    tips.append({'tip': row[0], 'elo': row[1], 'domain': row[2], 'confidence': row[3]})
            except:
                pass
        
        # Fallback to distilled_tips
        if 'distilled_tips' in tables and len(tips) < limit:
            try:
                c.execute('''
                    SELECT condition, recommendation, tool_name, domain, confidence
                    FROM distilled_tips
                    WHERE (''' + ' OR '.join(["LOWER(condition) LIKE ? OR LOWER(recommendation) LIKE ? OR LOWER(tool_name) LIKE ?" for _ in keywords]) + ''')
                    ORDER BY confidence DESC, frequency DESC
                    LIMIT ?
                ''', [f'%{k}%' for k in keywords for _ in range(3)] + [limit - len(tips)])
                for row in c.fetchall():
                    tips.append({'tip': f"{row[0]} -> {row[1]}", 'tool': row[2], 'domain': row[3], 'confidence': row[4]})
            except:
                pass
        
        return tips
    
    def format_tip(self, tip):
        """Format tip for injection."""
        return f"[TIP] {tip['text'][:100]}... (ELO: {tip['elo']})"

if __name__ == '__main__':
    injector = ProactiveTipInjector()
    tips = injector.get_relevant_tips("merge upstream features")
    for tip in tips:
        print(injector.format_tip(tip))
