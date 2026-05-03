#!/bin/bash
# HERMES STATE DB EMERGENCY REVERT SCRIPT
# Created: Apr 23 2026
# Usage: bash ~/.hermes/REVERT_STATE_DB.sh

echo "=== HERMES STATE DB EMERGENCY REVERT ==="
echo ""

# Check if clean backup exists
CLEAN_BACKUP="/Users/dannygomez/.hermes/state.db.CLEAN_PRE_MERGE_20260423_100929"

if [ ! -f "$CLEAN_BACKUP" ]; then
    echo "ERROR: Clean backup not found at $CLEAN_BACKUP"
    echo "Looking for other backups..."
    ls -t /Users/dannygomez/.hermes/state.db.CLEAN_PRE_MERGE_* 2>/dev/null | head -5
    exit 1
fi

# Stop Hermes gateway if running
echo "[1/4] Stopping Hermes gateway..."
hermes gateway stop 2>/dev/null || pkill -f "hermes.*gateway" 2>/dev/null || true
sleep 2

# Backup current (possibly corrupted) state
echo "[2/4] Backing up current state.db..."
cp /Users/dannygomez/.hermes/state.db /Users/dannygomez/.hermes/state.db.CORRUPTED_$(date +%Y%m%d_%H%M%S)

# Remove WAL files that might contain corruption
echo "[3/4] Removing WAL/shm files..."
rm -f /Users/dannygomez/.hermes/state.db-wal
rm -f /Users/dannygomez/.hermes/state.db-shm

# Restore clean backup
echo "[4/4] Restoring clean backup..."
cp "$CLEAN_BACKUP" /Users/dannygomez/.hermes/state.db

# Verify
echo ""
echo "=== REVERT COMPLETE ==="
echo "Clean backup restored from: $CLEAN_BACKUP"
echo "Corrupted state saved to: /Users/dannygomez/.hermes/state.db.CORRUPTED_*"
echo ""
echo "Next steps:"
echo "  1. Start Hermes: hermes"
echo "  2. Verify no loop: try 'terminal' command with 'echo test'"
echo "  3. If clean, continue working"
echo "  4. If still corrupted, check if issue is in session state, not DB"
echo ""
