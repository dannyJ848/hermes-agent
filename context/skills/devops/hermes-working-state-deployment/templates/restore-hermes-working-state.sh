#!/bin/bash
# HERMES WORKING STATE RESTORE
# ============================
# Restores Hermes working state from a snapshot
# Usage: ./restore-hermes-working-state.sh [snapshot_dir]

set -e

SNAPSHOT_DIR="${1:-$HOME/.hermes/snapshots/working-20260516-144642}"
HERMES_DIR="$HOME/.hermes"
SOURCE_DIR="$HOME/hermes-agent"

if [ ! -d "${SNAPSHOT_DIR}" ]; then
    echo "ERROR: Snapshot directory not found: ${SNAPSHOT_DIR}"
    echo "Usage: $0 [snapshot_dir]"
    exit 1
fi

echo "=== Hermes Working State Restore ==="
echo "From: ${SNAPSHOT_DIR}"
echo "To:   ${HERMES_DIR}"
echo ""

# 1. Backup current state
echo "[1/4] Backing up current state..."
BACKUP_DIR="${HERMES_DIR}/backups/pre-restore-$(date +%Y%m%d-%H%M%S)"
mkdir -p "${BACKUP_DIR}"
cp -r "${HERMES_DIR}/config.yaml" "${BACKUP_DIR}/" 2>/dev/null || true
cp -r "${HERMES_DIR}/.env" "${BACKUP_DIR}/" 2>/dev/null || true
cp -r "${HERMES_DIR}/auth.json" "${BACKUP_DIR}/" 2>/dev/null || true
echo "      Backed up to: ${BACKUP_DIR}"

# 2. Restore config files
echo "[2/4] Restoring configuration..."
cp "${SNAPSHOT_DIR}/config.yaml" "${HERMES_DIR}/"
cp "${SNAPSHOT_DIR}/.env" "${HERMES_DIR}/"
if [ -f "${SNAPSHOT_DIR}/auth.json" ]; then
    cp "${SNAPSHOT_DIR}/auth.json" "${HERMES_DIR}/"
fi
echo "      Config restored"

# 3. Verify source code
echo "[3/4] Verifying source code..."
cd "${SOURCE_DIR}"
CURRENT_COMMIT=$(git rev-parse HEAD)
if [ "${CURRENT_COMMIT}" != "b6fa8f918" ]; then
    echo "      WARNING: Source at ${CURRENT_COMMIT}, expected b6fa8f918"
    echo "      Run: cd ${SOURCE_DIR} && git stash && git checkout b6fa8f918"
fi

# 4. Verify config
echo "[4/4] Verifying configuration..."
if [ -f "${HERMES_DIR}/verify.sh" ]; then
    bash "${HERMES_DIR}/verify.sh"
else
    echo "      No verify script found, manual check needed"
    echo "      Provider: $(grep 'provider:' ${HERMES_DIR}/config.yaml | head -1)"
    echo "      Base URL: $(grep 'base_url:' ${HERMES_DIR}/config.yaml | head -1)"
fi

echo ""
echo "=== Restore Complete ==="
echo "Start Hermes: hermes"
echo ""
echo "If issues occur, restore from backup:"
echo "  cp ${BACKUP_DIR}/* ${HERMES_DIR}/"
