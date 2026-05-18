#!/bin/bash
# Freeze detector for Franken V8 training
# Monitors training log and writes alert if steps stop advancing
# Usage: Run via cron every 5 min: */5 * * * * /tmp/freeze_detector.sh

LOG_FILE="/data/models/FrankenV8-Batch2/training_dual_mode.log"
STATE_FILE="/tmp/last_step_state.txt"
ALERT_FILE="/tmp/FREEZE_ALERT"

CURRENT_STEP=$(grep -o "Step [0-9]*/3332" "$LOG_FILE" | tail -1 | sed "s/Step \([0-9]*\)\/3332/\1/")
CURRENT_TIME=$(date +%s)

if [ -z "$CURRENT_STEP" ]; then
    echo "$CURRENT_TIME:0" > "$STATE_FILE"
    exit 0
fi

if [ -f "$STATE_FILE" ]; then
    read LAST_TIME LAST_STEP < "$STATE_FILE"
    TIME_DIFF=$((CURRENT_TIME - LAST_TIME))
    
    if [ "$CURRENT_STEP" -eq "$LAST_STEP" ] && [ "$TIME_DIFF" -gt 600 ]; then
        echo "FREEZE at step $CURRENT_STEP after ${TIME_DIFF}s" > "$ALERT_FILE"
        echo "$(date): FREEZE at step $CURRENT_STEP after ${TIME_DIFF}s" >> /tmp/freeze_history.log
    fi
fi

if [ ! -f "$STATE_FILE" ] || [ "$CURRENT_STEP" -ne "$LAST_STEP" ]; then
    echo "$CURRENT_TIME:$CURRENT_STEP" > "$STATE_FILE"
fi
