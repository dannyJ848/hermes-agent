#!/bin/bash
# HERMES FULL WORKING STATE DEPLOYMENT
# =====================================
# This script deploys the complete working Hermes state to a fresh environment
# Usage: ./deploy-hermes-working-state.sh [TARGET_DIR]
#   TARGET_DIR: Optional directory to deploy to (default: ~/.hermes)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-${HOME}/.hermes}"
HERMES_AGENT="${HOME}/hermes-agent"

echo "=========================================="
echo "HERMES WORKING STATE DEPLOYMENT"
echo "=========================================="
echo "Source: ${SCRIPT_DIR}"
echo "Target: ${TARGET_DIR}"
echo "Agent source: ${HERMES_AGENT}"
echo ""

# Verify source snapshot exists
if [ ! -f "${SCRIPT_DIR}/config.yaml" ]; then
    echo "ERROR: Source snapshot not found at ${SCRIPT_DIR}"
    echo "Expected files: config.yaml, .env, auth.json"
    exit 1
fi

# Create target directory
mkdir -p "${TARGET_DIR}"
mkdir -p "${TARGET_DIR}/logs"
mkdir -p "${TARGET_DIR}/skills"
mkdir -p "${TARGET_DIR}/sessions"
mkdir -p "${TARGET_DIR}/memory"

# Backup existing state
BACKUP_TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="${TARGET_DIR}/backups/pre-deploy-${BACKUP_TIMESTAMP}"
if [ -f "${TARGET_DIR}/config.yaml" ]; then
    echo "[1/8] Backing up existing state..."
    mkdir -p "$BACKUP_DIR"
    cp "${TARGET_DIR}/config.yaml" "$BACKUP_DIR/" 2>/dev/null || true
    cp "${TARGET_DIR}/.env" "$BACKUP_DIR/" 2>/dev/null || true
    cp "${TARGET_DIR}/auth.json" "$BACKUP_DIR/" 2>/dev/null || true
    echo "      Backed up to: ${BACKUP_DIR}"
else
    echo "[1/8] No existing state to backup"
fi

# Deploy config files
echo "[2/8] Deploying config.yaml..."
cp "${SCRIPT_DIR}/config.yaml" "${TARGET_DIR}/config.yaml"

echo "[3/8] Deploying .env (API keys)..."
cp "${SCRIPT_DIR}/.env" "${TARGET_DIR}/.env"

echo "[4/8] Deploying auth.json (credential cache)..."
cp "${SCRIPT_DIR}/auth.json" "${TARGET_DIR}/auth.json"

# Verify source code is at correct commit
echo "[5/8] Verifying source code..."
cd "$HERMES_AGENT"
CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
if [ "$CURRENT_COMMIT" != "EXPECTED_COMMIT_HASH" ]; then
    echo "      WARNING: Source code at ${CURRENT_COMMIT}, expected EXPECTED_COMMIT_HASH"
    echo "      Run: cd ${HERMES_AGENT} && git checkout EXPECTED_COMMIT_HASH"
else
    echo "      Source code verified: EXPECTED_COMMIT_HASH"
fi

# Verify critical config values
echo "[6/8] Verifying critical config..."
ERRORS=0

# Check base URL
if grep -q "api.kimi.com/coding/v1" "${TARGET_DIR}/config.yaml"; then
    echo "      FIXING: Wrong base URL (/coding/v1) -> correcting to /coding"
    sed -i '' 's|api.kimi.com/coding/v1|api.kimi.com/coding|g' "${TARGET_DIR}/config.yaml"
    ERRORS=$((ERRORS + 1))
fi

# Check provider config
if ! grep -q "provider: kimi-coding" "${TARGET_DIR}/config.yaml"; then
    echo "      WARNING: kimi-coding provider not configured"
    ERRORS=$((ERRORS + 1))
fi

# Check .env has KIMI_API_KEY
if ! grep -q "KIMI_API_KEY" "${TARGET_DIR}/.env"; then
    echo "      WARNING: KIMI_API_KEY not found in .env"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -eq 0 ]; then
    echo "      All checks passed"
else
    echo "      ${ERRORS} issue(s) found and fixed"
fi

# Set permissions
echo "[7/8] Setting permissions..."
chmod 600 "${TARGET_DIR}/.env"
chmod 600 "${TARGET_DIR}/auth.json" 2>/dev/null || true
chmod 644 "${TARGET_DIR}/config.yaml"

# Create startup verification script
echo "[8/8] Creating verification script..."
cat > "${TARGET_DIR}/verify.sh" << 'EOF'
#!/bin/bash
# Quick verification that Hermes is properly configured

echo "=== Hermes Configuration Verification ==="
echo ""

# Check config exists
if [ ! -f "${HOME}/.hermes/config.yaml" ]; then
    echo "FAIL: config.yaml not found"
    exit 1
fi

# Check .env exists
if [ ! -f "${HOME}/.hermes/.env" ]; then
    echo "FAIL: .env not found"
    exit 1
fi

# Check provider
if grep -q "provider: kimi-coding" "${HOME}/.hermes/config.yaml"; then
    echo "PASS: Provider configured (kimi-coding)"
else
    echo "FAIL: Provider not configured"
    exit 1
fi

# Check base URL
if grep -q "api.kimi.com/coding\"" "${HOME}/.hermes/config.yaml"; then
    echo "PASS: Base URL correct (no /v1 suffix)"
elif grep -q "api.kimi.com/coding/v1" "${HOME}/.hermes/config.yaml"; then
    echo "FAIL: Base URL has /v1 suffix (will cause 404)"
    exit 1
else
    echo "WARN: Base URL not found in expected format"
fi

# Check API key
if grep -q "KIMI_API_KEY" "${HOME}/.hermes/.env"; then
    echo "PASS: KIMI_API_KEY present in .env"
else
    echo "FAIL: KIMI_API_KEY not found in .env"
    exit 1
fi

# Check auth cache
if [ -f "${HOME}/.hermes/auth.json" ]; then
    echo "PASS: Auth cache exists"
else
    echo "WARN: Auth cache missing (will be recreated on first run)"
fi

echo ""
echo "=== All checks passed! Hermes should work. ==="
echo "Start with: hermes"
EOF
chmod +x "${TARGET_DIR}/verify.sh"

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "Working state deployed to: ${TARGET_DIR}"
echo ""
echo "To verify:"
echo "  ${TARGET_DIR}/verify.sh"
echo ""
echo "To start Hermes:"
echo "  hermes"
echo ""
echo "If auth fails:"
echo "  1. Check KIMI_API_KEY is valid at https://kimi.com/code"
echo "  2. Update ${TARGET_DIR}/.env with new key"
echo "  3. Remove ${TARGET_DIR}/auth.json to clear cache"
echo "  4. Restart Hermes"
echo ""
echo "Source code commit: EXPECTED_COMMIT_HASH"
echo "If source diverges: cd ${HERMES_AGENT} && git checkout EXPECTED_COMMIT_HASH"
