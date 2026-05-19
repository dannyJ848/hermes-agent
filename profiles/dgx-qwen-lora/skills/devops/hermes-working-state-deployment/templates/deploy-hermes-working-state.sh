#!/bin/bash
# HERMES FULL WORKING STATE DEPLOYMENT
# =====================================
# This script deploys the complete working Hermes state to a fresh environment
# Generated: 2026-05-16
# Source commit: b6fa8f918
# Branch: qwen27b-training-artifacts-may3-2026
#
# Usage: ./deploy-hermes-working-state.sh

set -e

# Configuration
SNAPSHOT_DIR="$HOME/.hermes/snapshots/working-20260516-144642"
HERMES_DIR="$HOME/.hermes"
SOURCE_DIR="$HOME/hermes-agent"

echo "=== Hermes Working State Deployment ==="
echo "Snapshot: ${SNAPSHOT_DIR}"
echo "Target:   ${HERMES_DIR}"
echo "Source:   ${SOURCE_DIR}"
echo ""

# 1. Backup existing state
echo "[1/6] Backing up existing state..."
BACKUP_DIR="${HERMES_DIR}/backups/pre-deploy-$(date +%Y%m%d-%H%M%S)"
mkdir -p "${BACKUP_DIR}"
cp -r "${HERMES_DIR}/config.yaml" "${BACKUP_DIR}/" 2>/dev/null || true
cp -r "${HERMES_DIR}/.env" "${BACKUP_DIR}/" 2>/dev/null || true
cp -r "${HERMES_DIR}/auth.json" "${BACKUP_DIR}/" 2>/dev/null || true
echo "      Backed up to: ${BACKUP_DIR}"

# 2. Verify source code commit
echo "[2/6] Verifying source code..."
cd "${SOURCE_DIR}"
CURRENT_COMMIT=$(git rev-parse HEAD)
if [ "${CURRENT_COMMIT}" != "b6fa8f918" ]; then
    echo "      WARNING: Source code at ${CURRENT_COMMIT}, expected b6fa8f918"
    echo "      Checking out correct commit..."
    git stash
    git checkout b6fa8f918
fi
echo "      Source code verified: ${CURRENT_COMMIT}"

# 3. Deploy config files
echo "[3/6] Deploying configuration..."
cp "${SNAPSHOT_DIR}/config.yaml" "${HERMES_DIR}/"
cp "${SNAPSHOT_DIR}/.env" "${HERMES_DIR}/"
cp "${SNAPSHOT_DIR}/auth.json" "${HERMES_DIR}/" 2>/dev/null || true
echo "      Config deployed"

# 4. Verify critical values
echo "[4/6] Verifying configuration..."
ERRORS=0

# Check provider
if ! grep -q "provider: kimi-coding" "${HERMES_DIR}/config.yaml"; then
    echo "      ERROR: kimi-coding provider not configured"
    ERRORS=$((ERRORS + 1))
else
    echo "      PASS: Provider configured (kimi-coding)"
fi

# Check base URL (no /v1 suffix)
if grep -q "api.kimi.com/coding/v1" "${HERMES_DIR}/config.yaml"; then
    echo "      ERROR: Base URL has /v1 suffix (will cause 404)"
    ERRORS=$((ERRORS + 1))
else
    echo "      PASS: Base URL correct (no /v1 suffix)"
fi

# Check API key
if ! grep -q "KIMI_API_KEY" "${HERMES_DIR}/.env"; then
    echo "      ERROR: KIMI_API_KEY not found in .env"
    ERRORS=$((ERRORS + 1))
else
    echo "      PASS: KIMI_API_KEY present in .env"
fi

# Check auth cache
if [ -f "${HERMES_DIR}/auth.json" ]; then
    echo "      PASS: Auth cache exists"
else
    echo "      WARNING: Auth cache missing (will be recreated on first run)"
fi

if [ ${ERRORS} -gt 0 ]; then
    echo ""
    echo "FAILED: ${ERRORS} verification errors"
    exit 1
fi

# 5. Create verification script
echo "[5/6] Creating verification script..."
cat > "${HERMES_DIR}/verify.sh" << 'EOF'
#!/bin/bash
# Hermes Working State Verification

echo "=== Hermes Working State Verification ==="
ERRORS=0

# Check config exists
if [ ! -f "$HOME/.hermes/config.yaml" ]; then
    echo "FAIL: config.yaml missing"
    ERRORS=$((ERRORS + 1))
else
    echo "PASS: config.yaml exists"
fi

# Check provider
if grep -q "provider: kimi-coding" "$HOME/.hermes/config.yaml"; then
    echo "PASS: Provider configured (kimi-coding)"
else
    echo "FAIL: kimi-coding provider not configured"
    ERRORS=$((ERRORS + 1))
fi

# Check base URL
if grep -q "api.kimi.com/coding/v1" "$HOME/.hermes/config.yaml"; then
    echo "FAIL: Base URL has /v1 suffix"
    ERRORS=$((ERRORS + 1))
else
    echo "PASS: Base URL correct"
fi

# Check API key
if grep -q "KIMI_API_KEY" "$HOME/.hermes/.env"; then
    echo "PASS: KIMI_API_KEY in .env"
else
    echo "FAIL: KIMI_API_KEY missing from .env"
    ERRORS=$((ERRORS + 1))
fi

# Check auth cache
if [ -f "$HOME/.hermes/auth.json" ]; then
    echo "PASS: Auth cache exists"
else
    echo "WARN: Auth cache missing"
fi

echo ""
if [ ${ERRORS} -eq 0 ]; then
    echo "ALL CHECKS PASSED"
else
    echo "FAILED: ${ERRORS} errors"
    exit 1
fi
EOF
chmod +x "${HERMES_DIR}/verify.sh"
echo "      Created: ${HERMES_DIR}/verify.sh"

# 6. Summary
echo "[6/6] Deployment complete!"
echo ""
echo "=== Summary ==="
echo "Config:      ${HERMES_DIR}/config.yaml"
echo "API Keys:    ${HERMES_DIR}/.env"
echo "Auth Cache:  ${HERMES_DIR}/auth.json"
echo "Verify:      ${HERMES_DIR}/verify.sh"
echo "Backup:      ${BACKUP_DIR}"
echo ""
echo "To verify:   ~/.hermes/verify.sh"
echo "To start:    hermes"
echo ""
echo "If issues occur, restore from backup:"
echo "  cp ${BACKUP_DIR}/* ~/.hermes/"
