#!/bin/bash
# Z.AI API Timeout Monitor & Quick Fix
# Usage: bash ~/.hermes/skills/meta/zai-api-resilience/scripts/timeout-monitor.sh [check|fix|report]

ACTION="${1:-check}"
ENV_FILE="$HOME/.hermes/.env"
ERROR_LOG="$HOME/.hermes/logs/errors.log"

case "$ACTION" in
  check)
    echo "=== Z.AI API Timeout Status ==="
    echo ""
    echo "Current env vars:"
    grep -E "HERMES_.*TIMEOUT" "$ENV_FILE" 2>/dev/null || echo "  (none set — using defaults)"
    echo ""
    echo "Timeouts today: $(grep "$(date +%Y-%m-%d)" "$ERROR_LOG" 2>/dev/null | grep -c 'timed out')"
    echo "Timeouts last 24h: $(find "$ERROR_LOG" -mtime -1 2>/dev/null | xargs grep -c 'timed out' 2>/dev/null | tail -1)"
    echo ""
    if grep -q "HERMES_STREAM_READ_TIMEOUT" "$ENV_FILE" 2>/dev/null; then
      echo "Status: FIXED (custom timeouts configured)"
    else
      echo "Status: VULNERABLE (using 60s default read timeout)"
      echo ""
      echo "Run this script with 'fix' to see the fix commands"
    fi
    ;;

  report)
    echo "=== Timeout Report (last 7 days) ==="
    for i in $(seq 0 6); do
      day=$(date -v-${i}d +%Y-%m-%d 2>/dev/null || date -d "$i days ago" +%Y-%m-%d)
      count=$(grep "$day" "$ERROR_LOG" 2>/dev/null | grep -c 'timed out')
      echo "  $day: $count timeouts"
    done
    echo ""
    echo "Total errors in log: $(wc -l < "$ERROR_LOG" 2>/dev/null)"
    ;;

  fix)
    echo "=== Fix Instructions ==="
    echo ""
    echo "Add these lines to $ENV_FILE:"
    echo ""
    echo "  HERMES_API_TIMEOUT=2400"
    echo "  HERMES_STREAM_READ_TIMEOUT=180"
    echo "  HERMES_STREAM_STALE_TIMEOUT=300"
    echo ""
    echo "Then restart Hermes:"
    echo "  pkill -f hermes_cli.main; pkill -f 'hermes -p'; sleep 2; hermes"
    echo ""
    echo "For squad profiles, also add to:"
    echo "  ~/.hermes/profiles/soma-coder/.env"
    echo "  ~/.hermes/profiles/soma-researcher/.env"
    echo "  ~/.hermes/profiles/soma-tester/.env"
    ;;

  *)
    echo "Usage: $0 [check|fix|report]"
    ;;
esac
