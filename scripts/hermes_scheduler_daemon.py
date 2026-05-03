#!/usr/bin/env python3
"""
Hermes Cron Scheduler Daemon.
Runs tick() every 60 seconds to check for and execute due jobs.
"""
import sys
import time
import signal
import os

# Add hermes-agent to path
sys.path.insert(0, '/Users/dannygomez/hermes-agent')

from cron.scheduler import tick

PID_FILE = "/tmp/hermes_scheduler_daemon.pid"
RUNNING = True

def handle_signal(signum, frame):
    global RUNNING
    print(f"[Scheduler] Received signal {signum}, shutting down...")
    RUNNING = False

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

def cleanup_stuck_cycles():
    """Kill flywheel cycles stuck running for >30 minutes."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname='cortex', user='hindsight', password='hindsight',
            host='localhost', port=5432
        )
        cur = conn.cursor()
        cur.execute(
            "UPDATE cortex_flywheel SET status = 'killed' "
            "WHERE status = 'running' AND started_at < NOW() - INTERVAL '30 minutes'"
        )
        killed = cur.rowcount
        conn.commit()
        conn.close()
        if killed > 0:
            print(f"[Scheduler] Cleaned up {killed} stuck flywheel cycles")
    except Exception as e:
        print(f"[Scheduler] Cleanup error: {e}")

def main():
    # Write PID file
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    
    print(f"[Scheduler] Daemon started (PID {os.getpid()}). Running tick() every 60s.")
    print(f"[Scheduler] PID file: {PID_FILE}")
    
    tick_count = 0
    while RUNNING:
        try:
            tick(verbose=False)
        except Exception as e:
            print(f"[Scheduler] tick() error: {e}")
        
        # Cleanup stuck cycles every 10 ticks (10 minutes)
        tick_count += 1
        if tick_count >= 10:
            cleanup_stuck_cycles()
            tick_count = 0
        
        # Sleep in 1-second increments to respond to signals quickly
        for _ in range(60):
            if not RUNNING:
                break
            time.sleep(1)
    
    print("[Scheduler] Daemon stopped.")
    try:
        os.remove(PID_FILE)
    except:
        pass

if __name__ == "__main__":
    main()
