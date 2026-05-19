# Scheduler Daemon with Auto-Cleanup Pattern

## Context
When a background daemon spawns work cycles (flywheel evaluations, training jobs, etc.) that call external APIs, cycles will inevitably get stuck due to API timeouts or DB locks. Without cleanup, "running" cycles accumulate indefinitely.

## Pattern

Add a cleanup function to the daemon that kills stuck cycles every N ticks:

```python
def cleanup_stuck_cycles(max_age_minutes=30):
    """Kill cycles stuck running longer than threshold."""
    try:
        import psycopg2  # or sqlite3
        conn = psycopg2.connect(dbname='cortex', ...)
        cur = conn.cursor()
        cur.execute(
            "UPDATE flywheel_cycles SET status = 'killed' "
            "WHERE status = 'running' AND started_at < NOW() - INTERVAL '%s minutes'",
            (max_age_minutes,)
        )
        killed = cur.rowcount
        conn.commit()
        if killed > 0:
            print(f"[Cleanup] Killed {killed} stuck cycles")
    except Exception as e:
        print(f"[Cleanup] Error: {e}")

# In the daemon main loop:
tick_count = 0
while RUNNING:
    tick()  # do work
    
    # Cleanup every 10 ticks (~10 minutes if tick is every 60s)
    tick_count += 1
    if tick_count >= 10:
        cleanup_stuck_cycles()
        tick_count = 0
    
    sleep(60)
```

## Rule of Thumb
Any daemon that inserts a "running" row into a database must also have a cleanup routine that kills rows older than 2× the expected completion time.

## Real-World Example
This session (May 3, 2026): The cortex flywheel had 51 cycles stuck "running" because DeepSeek API calls were timing out. The scheduler daemon kept creating new cycles but they never completed. Adding `cleanup_stuck_cycles()` killed 48 old cycles and reduced "running" from 51 to 3.
