#!/bin/bash
# Health check script for vLLM DFlash container
# Run periodically (e.g., via cron every 5 minutes) to detect stuck containers
# 
# Known failure mode (May 15, 2026): Container appears running but stops processing
# requests after 4+ hours idle. GPU util drops to 0%, no new logs. Fix: docker restart.

CONTAINER_NAME="vllm-merged"
HEALTH_URL="http://localhost:8000/v1/models"
TIMEOUT=10
LOG_FILE="/var/log/vllm-health.log"
STUCK_THRESHOLD_MINUTES=30  # Consider stuck if no logs for 30 min

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "$(date): Container ${CONTAINER_NAME} not running. Starting..." | tee -a "$LOG_FILE"
    sudo systemctl start vllm-dflash.service
    exit 1
fi

# Check if vLLM responds to health check
RESPONSE=$(curl -s --max-time "$TIMEOUT" "$HEALTH_URL" 2>&1)
CURL_EXIT=$?
if [ $CURL_EXIT -ne 0 ]; then
    echo "$(date): vLLM unresponsive (curl exit $CURL_EXIT). Restarting..." | tee -a "$LOG_FILE"
    docker restart "$CONTAINER_NAME"
    exit 1
fi

# Check if response is valid JSON with expected fields
if ! echo "$RESPONSE" | grep -q '"id"'; then
    echo "$(date): vLLM returned invalid response. Restarting..." | tee -a "$LOG_FILE"
    docker restart "$CONTAINER_NAME"
    exit 1
fi

# Check GPU utilization — 0% for extended period indicates stuck container
GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | tr -d ' ')
if [ "$GPU_UTIL" -eq 0 ]; then
    # Check last log entry age (stuck containers stop logging)
    LAST_LOG=$(docker logs --since "${STUCK_THRESHOLD_MINUTES}m" "$CONTAINER_NAME" 2>/dev/null | tail -1)
    if [ -z "$LAST_LOG" ]; then
        echo "$(date): GPU idle (${GPU_UTIL}%) and no logs for ${STUCK_THRESHOLD_MINUTES}+ min. Container stuck. Restarting..." | tee -a "$LOG_FILE"
        docker restart "$CONTAINER_NAME"
        exit 1
    fi
fi

echo "$(date): Healthy (GPU: ${GPU_UTIL}%, response valid)" | tee -a "$LOG_FILE"
exit 0
