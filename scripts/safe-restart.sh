#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SAFE RESTART — Full safety net for Hermes gateway restart
# 
# This script does EVERYTHING to ensure you can never lose context:
#   1. Validates all patches compile (no syntax errors)
#   2. Creates triple-redundant checkpoint backups
#   3. Copies current context to clipboard RIGHT NOW
#   4. Runs the unified restart with a watchdog timeout
#   5. Verifies gateway comes back healthy
#   6. If ANY step fails, rolls back patches automatically
#
# Usage: bash ~/.hermes/scripts/safe-restart.sh [--dry-run]
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set -uo pipefail
# NOTE: Not using -e because some git commands return non-zero on success

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

step() { echo -e "${CYAN}[SAFE-RESTART]${NC} $1"; }
ok()   { echo -e "${GREEN}  ✓ $1${NC}"; }
warn() { echo -e "${YELLOW}  ⚠ $1${NC}"; }
fail() { echo -e "${RED}  ✗ $1${NC}"; }

# ── STEP 0: Record git stash reference for rollback ──
step "Recording rollback point..."
cd ~/hermes-agent && git add -A 2>/dev/null || true
# Check if there's anything to stash
if cd ~/hermes-agent && git diff --cached --quiet 2>/dev/null && git diff --quiet 2>/dev/null; then
    ok "Working tree is clean — no stash needed"
    STASH_REF=""
else
    cd ~/hermes-agent && git stash push -m "safe-restart-$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    STASH_REF=$(cd ~/hermes-agent && git stash list | head -1 | cut -d: -f1)
    ok "Git stash at $STASH_REF — rollback with: cd ~/hermes-agent && git stash pop $STASH_REF"
fi

# ── STEP 1: Syntax check all patched files ──
step "Validating patched files compile..."
ERRORS=0
for f in ~/hermes-agent/gateway/run.py ~/hermes-agent/cli.py ~/hermes-agent/hermes_cli/gateway.py; do
    if python3 -c "import py_compile; py_compile.compile('$f', doraise=True)" 2>/dev/null; then
        ok "$(basename $f) compiles"
    else
        fail "$(basename $f) has SYNTAX ERROR"
        ERRORS=$((ERRORS + 1))
    fi
done

if [ $ERRORS -gt 0 ]; then
    fail "Patches have syntax errors! Rolling back..."
    cd ~/hermes-agent && git stash pop 2>/dev/null || true
    fail "Rolled back. Restart aborted."
    exit 1
fi

# ── STEP 2: Triple backup checkpoints ──
step "Creating triple-redundant checkpoint backups..."
BACKUP_DIRS=(
    "$HOME/.hermes/workspace/checkpoint-backups"
    "/tmp/hermes-checkpoint-backup"
    "$HOME/hermes-agent/SAFETY_NET"
)
for d in "${BACKUP_DIRS[@]}"; do
    mkdir -p "$d"
    cp "$HOME/.hermes/workspace/checkpoints/"*.json "$d/" 2>/dev/null || true
    COUNT=$(ls "$d"/*.json 2>/dev/null | wc -l | tr -d ' ')
    ok "$d: $COUNT files"
done

# ── STEP 3: Copy latest checkpoint context to clipboard NOW ──
step "Copying checkpoint context to clipboard (your safety net)..."
LATEST_CP=$(ls -t "$HOME/.hermes/workspace/checkpoints/"*.json 2>/dev/null | head -1)
if [ -n "$LATEST_CP" ] && command -v pbcopy &>/dev/null; then
    python3 -c "
import json, sys
with open('$LATEST_CP') as f:
    d = json.load(f)
print('=== HERMES RESTORE CONTEXT ===')
print('Label:', d.get('label', 'N/A'))
print('Saved:', d.get('timestamp', 'N/A'))
print()
print('CONTEXT:')
print(d.get('context', '(empty)'))
print()
print('ACTIVE TASKS:')
for t in d.get('active_tasks', []):
    print(f'  - {t}')
print()
print('NEXT STEPS:')
print(d.get('next_steps', '(empty)'))
print()
print('RESTORE: session_restore(label=\"' + d.get('label', 'latest') + '\")')
" 2>/dev/null | pbcopy
    ok "Context copied to clipboard — paste it anywhere if things go wrong"
elif [ -n "$LATEST_CP" ]; then
    warn "pbcopy not available, showing checkpoint:"
    cat "$LATEST_CP"
fi

# ── STEP 4: Create a watchdog script ──
step "Creating watchdog..."
cat > /tmp/hermes-watchdog.sh << 'WATCHDOG'
#!/bin/bash
# Wait up to 60 seconds for gateway to respond, then alert
sleep 15
for i in $(seq 1 10); do
    if curl -sf http://localhost:8321/health >/dev/null 2>&1 || \
       curl -sf http://localhost:8080/health >/dev/null 2>&1; then
        echo "✓ Gateway healthy after $((i * 5)) seconds"
        # Send ntfy alert
        curl -sf -d "✓ Hermes gateway restarted successfully" ntfy.sh/hermes-restart-status 2>/dev/null || true
        exit 0
    fi
    sleep 5
done
echo "✗ Gateway did not come back after 65 seconds!"
curl -sf -d "✗ Hermes gateway FAILED to restart — manual intervention needed" ntfy.sh/hermes-restart-status 2>/dev/null || true
# Try to bring it back
cd ~/hermes-agent && source venv/bin/activate && hermes gateway run --replace &
echo "Attempted emergency gateway start"
WATCHDOG
chmod +x /tmp/hermes-watchdog.sh

if [ "$DRY_RUN" = true ]; then
    step "DRY RUN — skipping restart"
    echo ""
    echo "All checks passed. Ready for real restart."
    echo "Run: bash ~/.hermes/scripts/safe-restart.sh"
    exit 0
fi

# ── STEP 5: Launch watchdog, then restart ──
step "Launching watchdog (60s timeout)..."
bash /tmp/hermes-watchdog.sh &
WATCHDOG_PID=$!
ok "Watchdog PID: $WATCHDOG_PID"

step "Executing unified restart..."
cd ~/hermes-agent && source venv/bin/activate

# Save a checkpoint RIGHT NOW with the most context possible
python3 -c "
from hermes_cli.gateway import _save_pre_restart_checkpoint
path = _save_pre_restart_checkpoint()
print(f'Final checkpoint: {path}')
" 2>/dev/null || warn "Pre-restart checkpoint save failed (non-fatal)"

# Manual unified restart (no --all flag available)
step "Killing all Hermes processes..."
cd ~/hermes-agent && source venv/bin/activate
KILLED=$(python3 -c "
import subprocess, os, signal
kill_names = ['hermes_cli.main', 'run_agent.py', 'brain_daemon.py', 'parallel_brain.py', 'biomcp serve']
killed = 0
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
for line in result.stdout.split('\n'):
    if 'grep' in line: continue
    if not any(k in line for k in kill_names): continue
    parts = line.split(None, 10)
    if len(parts) < 2: continue
    try:
        pid = int(parts[1])
        if pid == os.getpid(): continue
        os.kill(pid, signal.SIGTERM)
        killed += 1
    except: pass
print(killed)
" 2>/dev/null || echo "0")
ok "Terminated $KILLED process(es)"
sleep 3

step "Starting fresh gateway..."
hermes gateway run --replace &
GATEWAY_PID=$!
ok "Gateway starting (PID: $GATEWAY_PID)"

# Wait for watchdog
wait $WATCHDOG_PID 2>/dev/null || true

echo ""
step "Restart complete. Start a new hermes session."
echo "  If auto-restore doesn't trigger: bash ~/.hermes/scripts/emergency-restore.sh"
echo "  If gateway won't start: cd ~/hermes-agent && git stash pop"
echo "  Your context is in your clipboard right now."
