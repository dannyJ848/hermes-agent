#!/usr/bin/env python3
# Context Pressure Gauge — Enhanced with self-manager integration
# Monitors token usage, tracks compressions, and triggers handoff at threshold

import sqlite3
import json
import os
import time
from pathlib import Path

class ContextPressureGauge:
    def __init__(self, max_tokens=128000):
        self.max_tokens = max_tokens
        self.pressure_threshold = 0.8
        self.compression_count = 0
        self.compression_log = Path.home() / ".hermes" / "workspace" / "compression_log.jsonl"
        self.compression_log.parent.mkdir(parents=True, exist_ok=True)
        
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
    
    def log_compression(self):
        """Log a compression event and increment counter."""
        self.compression_count += 1
        entry = {
            "timestamp": time.time(),
            "count": self.compression_count,
            "event": "compression"
        }
        with open(self.compression_log, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return self.compression_count
    
    def get_compression_count(self):
        """Get total compression count from log."""
        if not self.compression_log.exists():
            return self.compression_count
        
        # Count entries in current session (last hour)
        since = time.time() - 3600
        count = 0
        with open(self.compression_log) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get('timestamp', 0) > since:
                        count += 1
                except:
                    pass
        
        self.compression_count = max(self.compression_count, count)
        return count
    
    def check_handoff_threshold(self, threshold=5):
        """Check if compression count has reached handoff threshold."""
        return self.get_compression_count() >= threshold

if __name__ == '__main__':
    gauge = ContextPressureGauge()
    print(f"Pressure at 100k tokens: {gauge.measure_pressure(100000):.2f}")
    print(f"Should spill: {gauge.should_spill(100000)}")
    print(f"Compression count: {gauge.get_compression_count()}")
    print(f"Handoff threshold (5): {gauge.check_handoff_threshold()}")
