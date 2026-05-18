#!/bin/bash
# Cortex Daemon Watchdog — runs every 5 minutes via cron
# Checks if daemon is alive, restarts if dead or stale
# Usage: bash ~/.hermes/cortex_watchdog.sh
# Cron: */5 * * * * bash /Users/dannygomez/.hermes/cortex_watchdog.sh

PID_FILE="$HOME/.hermes/cortex_daemon.pid"
LOG_FILE="$HOME/.hermes/cortex_daemon.log"
WATCHDOG_LOG="$HOME/.hermes/cortex_watchdog.log"
DAEMON_CMD="cd $HOME/hermes-agent && source venv/bin/activate && nohup python3 $HOME/subconscious/cortex_daemon.py start >> $LOG_FILE 2>&1 &"

log() {
    echo "[$(date '+%Y-%m-%dT%H:%M:%S')] $1" >> "$WATCHDOG_LOG"
}

# Check if daemon is running
daemon_alive=false
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        daemon_alive=true
    fi
fi

# Check if log is stale (>10 min old)
log_stale=false
if [ -f "$LOG_FILE" ]; then
    log_age=$(( ($(date +%s) - $(stat -f %m "$LOG_FILE" 2>/dev/null || stat -c %Y "$LOG_FILE" 2>/dev/null || echo 0)) / 60 ))
    if [ "$log_age" -gt 10 ]; then
        log_stale=true
    fi
fi

if [ "$daemon_alive" = false ] || [ "$log_stale" = true ]; then
    log "WATCHDOG: Daemon dead or stale. Restarting..."
    # Kill any existing daemon processes
    pkill -f "cortex_daemon.py start" 2>/dev/null
    sleep 1
    # Start fresh
    eval "$DAEMON_CMD"
    NEW_PID=$!
    echo "$NEW_PID" > "$PID_FILE"
    log "WATCHDOG: Daemon restarted with PID $NEW_PID"
else
    # Silent success — no log spam
    :
fi
