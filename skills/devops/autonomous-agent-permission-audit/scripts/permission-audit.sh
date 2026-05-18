#!/bin/bash
# Autonomous Agent Permission Audit Script
# Run this to verify all permissions are intact after updates/restarts

set -e

ERRORS=0
USER=${1:-$(whoami)}

echo "=== Autonomous Agent Permission Audit ==="
echo "User: $USER"
echo ""

# 1. Sudo
echo -n "1. Sudo (passwordless)... "
if sudo -n whoami >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 2. Docker
echo -n "2. Docker... "
if docker ps >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 3. System dirs writable
echo -n "3. System dirs writable... "
if touch /usr/local/bin/.perm_test 2>/dev/null && rm /usr/local/bin/.perm_test 2>/dev/null; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 4. Self-modification (adjust path)
echo -n "4. Self-modification... "
AGENT_DIR="${AGENT_DIR:-/data/SpecForge/hermes-agent}"
if touch "$AGENT_DIR/.self_test" 2>/dev/null && rm "$AGENT_DIR/.self_test" 2>/dev/null; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 5. Background processes
echo -n "5. Background processes... "
if sleep 1 & PID=$! && ps aux | grep -q "$PID.*sleep" && kill $PID 2>/dev/null; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 6. Cron
echo -n "6. Cron... "
if crontab -l >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 7. Network
echo -n "7. Network... "
if curl -s --max-time 5 https://httpbin.org/get >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 8. Package installation (pip dry-run)
echo -n "8. Package installation... "
if python3 -m pip install --dry-run requests >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "=== ALL CHECKS PASSED ==="
    exit 0
else
    echo "=== $ERRORS CHECK(S) FAILED ==="
    exit 1
fi
