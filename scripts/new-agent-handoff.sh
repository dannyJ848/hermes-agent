#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEW AGENT HANDOFF — Give this to a fresh Hermes session
# if the unified restart fails completely.
#
# Usage: bash ~/.hermes/scripts/new-agent-handoff.sh
#   OR just:  cat ~/.hermes/scripts/new-agent-handoff.sh
#   Then paste the output into the new agent's first message.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "HERMES AGENT RECOVERY BRIEF — $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "WHAT HAPPENED:"
echo "  A 'unified restart' (hermes gateway restart --all) was attempted."
echo "  It may have failed partially or fully. You are a fresh session."
echo "  Your job: figure out what state things are in and resume work."
echo ""
echo "━━━ IMMEDIATE DIAGNOSTICS ━━━"
echo ""

echo "1. Is the gateway running?"
if ps aux | grep -v grep | grep "gateway run" > /dev/null 2>&1; then
    echo "   ✓ YES — gateway is running"
    ps aux | grep -v grep | grep "gateway run" | awk '{print "     PID:", $2, "CMD:", $11, $12, $13}'
else
    echo "   ✗ NO — gateway is NOT running"
    echo "     FIX: cd ~/hermes-agent && source venv/bin/activate && hermes gateway run --replace &"
fi
echo ""

echo "2. Are there checkpoint files?"
CP_DIR="$HOME/.hermes/workspace/checkpoints"
BACKUP1="$HOME/.hermes/workspace/checkpoint-backups"
BACKUP2="/tmp/hermes-checkpoint-backup"
BACKUP3="$HOME/hermes-agent/SAFETY_NET"

for d in "$CP_DIR" "$BACKUP1" "$BACKUP2" "$BACKUP3"; do
    COUNT=$(ls "$d"/*.json 2>/dev/null | wc -l | tr -d ' ')
    if [ "$COUNT" -gt 0 ]; then
        echo "   ✓ $d: $COUNT files"
    else
        echo "   ✗ $d: empty or missing"
    fi
done
echo ""

echo "3. Is there a restart marker?"
MARKER="$HOME/.hermes/.restart-marker"
if [ -f "$MARKER" ]; then
    echo "   ✓ YES — unconsumed marker at $MARKER"
    echo "     Content:"
    cat "$MARKER"
    echo ""
    echo "     This means the gateway never auto-restored the checkpoint."
    echo "     ACTION: Run session_restore, or read the checkpoint file directly."
else
    echo "   - No marker (either consumed or never created)"
fi
echo ""

echo "4. Latest checkpoint (richest context):"
LATEST=""
RICHEST=""
# Find the checkpoint with the most context
for d in "$CP_DIR" "$BACKUP1" "$BACKUP2"; do
    if [ -d "$d" ]; then
        BEST=$(python3 -c "
import json, os, sys
best_file, best_len = '', 0
for f in sorted(os.listdir('$d')):
    if not f.endswith('.json'): continue
    try:
        with open(os.path.join('$d', f)) as fh:
            d = json.load(fh)
        ctx_len = len(d.get('context', ''))
        if ctx_len > best_len:
            best_file, best_len = f, ctx_len
    except: pass
if best_file:
    print(os.path.join('$d', best_file))
" 2>/dev/null)
        if [ -n "$BEST" ]; then
            RICHEST="$BEST"
            break
        fi
    fi
done

if [ -n "$RICHEST" ] && [ -f "$RICHEST" ]; then
    echo "   File: $RICHEST"
    echo ""
    echo "   ┌─── CHECKPOINT CONTENT ───┐"
    python3 -c "
import json
with open('$RICHEST') as f:
    d = json.load(f)
print('Label:', d.get('label', 'N/A'))
print('Saved:', d.get('timestamp', 'N/A'))
print()
print('CONTEXT:')
print(d.get('context', '(empty)'))
print()
print('ACTIVE TASKS:')
for t in d.get('active_tasks', []):
    status = t.get('status', '?') if isinstance(t, dict) else '?'
    desc = t.get('content', t) if isinstance(t, dict) else t
    print(f'  [{status}] {desc}')
print()
print('KEY DECISIONS:')
for dec in d.get('decisions', []):
    print(f'  - {dec}')
print()
print('FILES MODIFIED:')
for f in d.get('files_modified', []):
    print(f'  - {f}')
print()
print('NEXT STEPS:')
print(d.get('next_steps', '(empty)'))
" 2>/dev/null || echo "   (parse failed, raw file: $RICHEST)"
    echo "   └──────────────────────────┘"
else
    echo "   ✗ No checkpoint found anywhere"
fi
echo ""

echo "5. Are our patches still applied?"
RUN_PY="$HOME/hermes-agent/gateway/run.py"
CLI_PY="$HOME/hermes-agent/cli.py"
if grep -q "restart-marker" "$RUN_PY" 2>/dev/null; then
    echo "   ✓ run.py has restart marker patches"
else
    echo "   ✗ run.py patches MISSING"
fi
if grep -q "RESTART MARKER DETECTED" "$CLI_PY" 2>/dev/null; then
    echo "   ✓ cli.py has marker warning"
else
    echo "   ✗ cli.py patches MISSING"
fi
echo ""

echo "6. Git stash (rollback) available?"
cd ~/hermes-agent 2>/dev/null && git stash list 2>/dev/null | head -3
echo ""

echo "━━━ WHAT TO DO ━━━"
echo ""
echo "IF GATEWAY IS DOWN:"
echo "  cd ~/hermes-agent && source venv/bin/activate && hermes gateway run --replace &"
echo ""
echo "IF GATEWAY IS UP BUT NO CONTEXT RESTORED:"
echo "  session_restore(label='<label from checkpoint above>')"
echo ""
echo "IF session_restore DOESN'T WORK:"
echo "  The checkpoint content is printed above — paste the CONTEXT and NEXT STEPS"
echo "  into your first message to the agent."
echo ""
echo "IF PATCHES ARE MISSING:"
echo "  cd ~/hermes-agent && git stash list  # find the stash with patches"
echo "  git stash pop stash@{N}             # restore them"
echo ""
echo "IF EVERYTHING IS BROKEN:"
echo "  1. Start gateway: cd ~/hermes-agent && source venv/bin/activate && hermes gateway run --replace &"
echo "  2. Start new session: hermes"
echo "  3. Paste the CHECKPOINT CONTENT from above as your first message"
echo ""
echo "━━━ DANNY'S PRIORITIES (from last session) ━━━"
echo "  1. Line-by-line logic audit of bottom-up/top-down distillation"
echo "  2. Black hat extraction"
echo "  3. AGI cycles"
echo "  4. Unified restart debugging (this mess)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Copy everything above and paste it into the new agent session."
echo "Or run: bash ~/.hermes/scripts/emergency-restore.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
