#!/usr/bin/env python3
# Context Pressure Gauge
# Monitors token usage and spills to disk when >80%

import sqlite3
import json
import os

class ContextPressureGauge:
    def __init__(self, max_tokens=128000):
        self.max_tokens = max_tokens
        self.pressure_threshold = 0.8
        
    def measure_pressure(self, current_tokens):
        """Measure current context pressure."""
        pressure = current_tokens / self.max_tokens
        
        # Log pressure
        try:
            conn = sqlite3.connect('/Users/dannygomez/.hermes/cerebrum_memory.db')
            c = conn.cursor()
            c.execute("""
                INSERT INTO context_pressure (timestamp, current_tokens, max_tokens, pressure)
                VALUES (datetime('now'), ?, ?, ?)
            """, (current_tokens, self.max_tokens, pressure))
            conn.commit()
            conn.close()
        except:
            pass
        
        return pressure
    
    def should_spill(self, current_tokens):
        """Check if we should spill context to disk."""
        return self.measure_pressure(current_tokens) > self.pressure_threshold
    
    def spill_context(self, context_data, spill_path='/tmp/hermes_context_spill.json'):
        """Spill context to disk."""
        with open(spill_path, 'w') as f:
            json.dump(context_data, f)
        return spill_path

if __name__ == '__main__':
    gauge = ContextPressureGauge()
    print(f"Pressure at 100k tokens: {gauge.measure_pressure(100000):.2f}")
    print(f"Should spill: {gauge.should_spill(100000)}")
