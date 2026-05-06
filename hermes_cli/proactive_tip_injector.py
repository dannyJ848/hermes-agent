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
        
        # Simple keyword matching — in practice use embeddings
        keywords = current_task.lower().split()
        
        c.execute('''
            SELECT text, elo, domain, confidence
            FROM cortex_nodes
            WHERE node_type = 'tip' AND is_active = TRUE
            AND (
        ''' + ' OR '.join(["LOWER(text) LIKE ?" for _ in keywords]) + '''
            )
            ORDER BY elo DESC, confidence DESC
            LIMIT ?
        ''', [f'%{k}%' for k in keywords] + [limit])
        
        return [{
            'text': row[0],
            'elo': row[1],
            'domain': row[2],
            'confidence': row[3]
        } for row in c.fetchall()]
    
    def format_tip(self, tip):
        """Format tip for injection."""
        return f"[TIP] {tip['text'][:100]}... (ELO: {tip['elo']})"

if __name__ == '__main__':
    injector = ProactiveTipInjector()
    tips = injector.get_relevant_tips("merge upstream features")
    for tip in tips:
        print(injector.format_tip(tip))
