#!/bin/bash
# EMERGENCY RESTORE — works even if gateway is dead, marker is gone, everything failed.
# Usage: bash ~/.hermes/scripts/emergency-restore.sh [checkpoint_label]
#
# What it does:
#   1. Finds the latest checkpoint (or the one you specify)
#   2. Prints the context, decisions, next_steps so you can paste them
#   3. Prints a ready-to-use session_restore command
#   4. Optionally copies everything to clipboard

set -e

CHECKPOINT_DIR="$HOME/.hermes/workspace/checkpoints"
LABEL="${1:-}"

# Find checkpoint
if [ -n "$LABEL" ]; then
    CP=$(find "$CHECKPOINT_DIR" -name "*${LABEL}*.json" -type f 2>/dev/null | sort -r | head -1)
else
    # Default: most recent checkpoint
    CP=$(ls -t "$CHECKPOINT_DIR"/*.json 2>/dev/null | head -1)
fi

if [ -z "$CP" ] || [ ! -f "$CP" ]; then
    echo "ERROR: No checkpoint found in $CHECKPOINT_DIR"
    echo "Available checkpoints:"
    ls -lt "$CHECKPOINT_DIR"/*.json 2>/dev/null || echo "  (none)"
    exit 1
fi

echo "============================================"
echo "EMERGENCY RESTORE"
echo "============================================"
echo ""
echo "Checkpoint: $CP"
echo "Modified:   $(stat -f '%Sm' "$CP")"
echo ""

# Parse and display
python3 -c "
import json, sys
with open('$CP') as f:
    d = json.load(f)

print('LABEL:', d.get('label', 'N/A'))
print('SAVED:', d.get('timestamp', 'N/A'))
print()
print('--- CONTEXT ---')
print(d.get('context', '(empty)')[:3000])
print()
print('--- ACTIVE TASKS ---')
for t in d.get('active_tasks', []):
    print(f'  - {t}')
print()
print('--- KEY DECISIONS ---')
for dec in d.get('decisions', []):
    print(f'  - {dec}')
print()
print('--- FILES MODIFIED ---')
for f in d.get('files_modified', []):
    print(f'  - {f}')
print()
print('--- NEXT STEPS ---')
print(d.get('next_steps', '(empty)'))
print()
print('============================================')
print('COPY-PASTE COMMAND:')
print(f'  session_restore(label=\"{d.get(\"label\", \"latest\")}\")')
print('============================================')
" 2>/dev/null || {
    echo "(python3 parse failed, raw JSON below)"
    cat "$CP"
}

# Offer clipboard copy
if command -v pbcopy &>/dev/null; then
    echo ""
    read -p "Copy context to clipboard? [y/N] " -t 10 yn
    if [ "$yn" = "y" ] || [ "$yn" = "Y" ]; then
        python3 -c "
import json
with open('$CP') as f:
    d = json.load(f)
out = 'CONTEXT:\n' + d.get('context','') + '\n\nTASKS:\n'
for t in d.get('active_tasks', []):
    out += f'- {t}\n'
out += '\nDECISIONS:\n'
for dec in d.get('decisions', []):
    out += f'- {dec}\n'
out += '\nNEXT STEPS:\n' + d.get('next_steps','')
print(out)
" 2>/dev/null | pbcopy
        echo "Copied to clipboard."
    fi
fi
