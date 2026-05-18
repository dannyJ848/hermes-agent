#!/bin/bash
# DGX Hermes Permission Audit Script
# Run this to verify all permissions are still intact after updates/restarts

set -e

ERRORS=0

echo "=== DGX Hermes Permission Audit ==="
echo ""

# 1. SSH to MacBook
echo -n "1. SSH to MacBook... "
if ssh -o ConnectTimeout=5 -o BatchMode=yes macbook "echo OK" >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 2. Sudo
echo -n "2. Sudo (passwordless)... "
if sudo -n whoami >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 3. Docker
echo -n "3. Docker... "
if docker ps >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 4. System dirs writable
echo -n "4. System dirs writable... "
if touch /usr/local/bin/.perm_test 2>/dev/null && rm /usr/local/bin/.perm_test 2>/dev/null; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 5. Hermes service
echo -n "5. Hermes service... "
if systemctl --user is-active hermes-agent >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 6. vLLM
echo -n "6. vLLM... "
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 7. Web search
echo -n "7. Web search (DDGS)... "
if /data/SpecForge/hermes-agent/venv/bin/python3 -c "
import sys
sys.path.insert(0, '/data/SpecForge/hermes-agent')
from tools.web_tools import web_search_tool
result = web_search_tool('test', limit=1)
assert 'success' in result.lower()
" >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 8. Goals
echo -n "8. Goals... "
if /data/SpecForge/hermes-agent/venv/bin/python3 -c "
import sys
sys.path.insert(0, '/data/SpecForge/hermes-agent')
from hermes_cli.goals import load_goal
g = load_goal('dgx_optimize_vllm')
assert g and g.status == 'active'
" >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 9. Cognitive orchestrator
echo -n "9. Cognitive orchestrator... "
if /data/SpecForge/hermes-agent/venv/bin/python3 -c "
import sys
sys.path.insert(0, '/data/SpecForge/hermes-agent')
from agent.cognitive_orchestrator import get_orchestrator
orch = get_orchestrator()
status = orch.get_status()
assert status['active_count'] >= 15
" >/dev/null 2>&1; then
    echo "PASS"
else
    echo "FAIL"
    ERRORS=$((ERRORS + 1))
fi

# 10. Self-modification
echo -n "10. Self-modification... "
if touch /data/SpecForge/hermes-agent/.self_test 2>/dev/null && rm /data/SpecForge/hermes-agent/.self_test 2>/dev/null; then
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
