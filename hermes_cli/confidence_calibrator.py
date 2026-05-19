#!/usr/bin/env python3
# Confidence Calibration
# Knows when uncertain vs certain

import sqlite3
from datetime import datetime

class ConfidenceCalibrator:
    def __init__(self):
        self.conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
        self._ensure_table()
    
    def _ensure_table(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS confidence_log (
                id INTEGER PRIMARY KEY,
                claim TEXT,
                stated_confidence REAL,
                actual_correct BOOLEAN,
                calibration_error REAL,
                timestamp TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def assess_confidence(self, claim, evidence_strength, verification_available=True):
        """Assess confidence in a claim."""
        
        if evidence_strength == 'direct_observation':
            base = 0.95
        elif evidence_strength == 'inferred':
            base = 0.70
        elif evidence_strength == 'assumed':
            base = 0.50
        else:
            base = 0.30
        
        if not verification_available:
            base *= 0.8
        
        if self._has_failed_before(claim):
            base *= 0.7
        
        return {
            'confidence': base,
            'should_verify': base < 0.7,
            'should_disclaim': base < 0.5,
            'recommendation': 'Verify before stating' if base < 0.7 else 'Proceed'
        }
    
    def _has_failed_before(self, claim):
        """Check if similar claim failed before."""
        c = self.conn.cursor()
        c.execute('''
            SELECT COUNT(*) FROM confidence_log
            WHERE claim LIKE ? AND actual_correct = FALSE
        ''', (f'%{claim[:50]}%',))
        return c.fetchone()[0] > 0
    
    def record_outcome(self, claim, stated_confidence, was_correct):
        """Record whether claim was correct."""
        error = abs(stated_confidence - (1.0 if was_correct else 0.0))
        
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO confidence_log (claim, stated_confidence, actual_correct, calibration_error, timestamp)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (claim, stated_confidence, was_correct, error))
        self.conn.commit()

if __name__ == '__main__':
    calibrator = ConfidenceCalibrator()
    
    # Test with my actual mistake
    result = calibrator.assess_confidence(
        "DeepSeek is in judge ensemble",
        evidence_strength='assumed',
        verification_available=False
    )
    print(f"Confidence: {result}")
