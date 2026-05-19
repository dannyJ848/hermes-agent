#!/bin/bash
# Training watchdog — runs ON DGX every 5 min via cron
# Checks: process alive, log recency
# Alerts via ntfy if crash detected
#
# Usage: copy to /tmp/dgx_watchdog_v2.sh on DGX, chmod +x, add to crontab:
#   */5 * * * * /tmp/dgx_watchdog_v2.sh >/dev/null 2>&1
#
# Why DGX-local: SSH from remote host fails under training load (network saturation).
# Cron on DGX is immune to SSH timeouts. ntfy.sh push works via outbound HTTP.

LOG_FILE="/mnt/bigssd/train_v2_max1000.log"
NTFY_TOPIC="dgx-training-alerts"
NTFY_URL="https://ntfy.sh/${NTFY_TOPIC}"
LOCK_FILE="/tmp/watchdog.lock"
ALERT_COOLDOWN_FILE="/tmp/last_alert"

# Prevent overlapping runs
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if kill -0 "$PID" 2>/dev/null; then
        exit 0
    fi
fi
echo $$ > "$LOCK_FILE"

# Check training process alive
PROC_COUNT=$(pgrep -f "train_lora_sae_teacher_v1.py" | wc -l)
if [ "$PROC_COUNT" -eq 0 ]; then
    NOW=$(date +%s)
    LAST_ALERT=0
    if [ -f "$ALERT_COOLDOWN_FILE" ]; then
        LAST_ALERT=$(cat "$ALERT_COOLDOWN_FILE")
    fi
    if [ $((NOW - LAST_ALERT)) -gt 300 ]; then
        curl -s -d "TRAINING CRASHED — no python process found" "$NTFY_URL" >/dev/null 2>&1
        echo "$NOW" > "$ALERT_COOLDOWN_FILE"
    fi
    rm -f "$LOCK_FILE"
    exit 1
fi

# Check log recency (alert if >30 min stale)
LOG_AGE=$(stat -c %Y "$LOG_FILE" 2>/dev/null || echo 0)
NOW=$(date +%s)
if [ "$LOG_AGE" -gt 0 ] && [ $((NOW - LOG_AGE)) -gt 1800 ]; then
    LAST_ALERT=0
    if [ -f "$ALERT_COOLDOWN_FILE" ]; then
        LAST_ALERT=$(cat "$ALERT_COOLDOWN_FILE")
    fi
    if [ $((NOW - LAST_ALERT)) -gt 300 ]; then
        curl -s -d "TRAINING STALLED — no log output for 30+ min" "$NTFY_URL" >/dev/null 2>&1
        echo "$NOW" > "$ALERT_COOLDOWN_FILE"
    fi
fi

rm -f "$LOCK_FILE"
exit 0
