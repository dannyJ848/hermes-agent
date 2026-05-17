#!/usr/bin/env python3
"""
Estimate training completion ETA from log file.
Run on DGX Spark or locally with SSH access.

Usage:
    python3 estimate_training_eta.py /mnt/bigssd/train_v2_max1000.log
    # or via SSH:
    ssh djg6228@spark-85e8.local "python3 -" < estimate_training_eta.py
"""

import re
import sys
from datetime import datetime

def parse_log(filepath):
    """Extract step/timestamp pairs from training log."""
    pattern = re.compile(
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+)\s+\[INFO\]\s+Step\s+(\d+)/(\d+)'
    )
    steps = []
    with open(filepath) as f:
        for line in f:
            m = pattern.search(line)
            if m:
                ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f")
                step = int(m.group(2))
                total = int(m.group(3))
                steps.append((ts, step, total))
    return steps

def calculate_eta(steps, window_size=50):
    """Calculate ETA from recent step rate."""
    if len(steps) < 2:
        return None
    
    # Use last N steps for rate calculation
    recent = steps[-window_size:]
    start_ts, start_step, _ = recent[0]
    end_ts, end_step, total = recent[-1]
    
    elapsed = (end_ts - start_ts).total_seconds()
    steps_done = end_step - start_step
    
    if steps_done == 0:
        return None
    
    seconds_per_step = elapsed / steps_done
    remaining = total - end_step
    eta_seconds = remaining * seconds_per_step
    
    completion = end_ts + __import__('datetime').timedelta(seconds=eta_seconds)
    
    return {
        'current_step': end_step,
        'total_steps': total,
        'progress_pct': (end_step / total) * 100,
        'seconds_per_step': seconds_per_step,
        'remaining_steps': remaining,
        'eta_seconds': eta_seconds,
        'eta_minutes': eta_seconds / 60,
        'eta_hours': eta_seconds / 3600,
        'completion_time': completion,
        'elapsed_window_minutes': elapsed / 60,
        'window_steps': steps_done,
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 estimate_training_eta.py <log_file>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    steps = parse_log(log_file)
    
    if not steps:
        print("No step entries found in log")
        sys.exit(1)
    
    eta = calculate_eta(steps)
    if not eta:
        print("Could not calculate ETA (insufficient data)")
        sys.exit(1)
    
    print(f"Current: Step {eta['current_step']}/{eta['total_steps']} ({eta['progress_pct']:.1f}%)")
    print(f"Rate: {eta['seconds_per_step']:.1f} sec/step (last {eta['window_steps']} steps)")
    print(f"Remaining: {eta['remaining_steps']} steps")
    print(f"ETA: {eta['eta_minutes']:.1f} minutes ({eta['eta_hours']:.2f} hours)")
    print(f"Completion: ~{eta['completion_time'].strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Total training time estimate: {eta['total_steps'] * eta['seconds_per_step'] / 3600:.1f} hours")

if __name__ == '__main__':
    main()
