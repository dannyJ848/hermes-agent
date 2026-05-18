#!/bin/bash
# Hermes Config Verification Script
# Run after deployment to verify critical configuration values

set -e

ERRORS=0

echo "=== Hermes Config Verification ==="
echo ""

# Check provider configuration
if grep -q "kimi-coding" ~/.hermes/config.yaml; then
    echo "PASS: Provider configured (kimi-coding)"
else
    echo "FAIL: Provider not configured"
    ERRORS=$((ERRORS + 1))
fi

# Check base URL has no /v1 suffix
if grep "api.kimi.com" ~/.hermes/config.yaml | grep -qv "/coding/v1"; then
    echo "PASS: Base URL correct (no /v1 suffix)"
else
    echo "FAIL: Base URL has /v1 suffix — will cause 404"
    ERRORS=$((ERRORS + 1))
fi

# Check KIMI_API_KEY in .env
if grep -q "KIMI_API_KEY" ~/.hermes/.env; then
    echo "PASS: KIMI_API_KEY present in .env"
else
    echo "FAIL: KIMI_API_KEY missing from .env"
    ERRORS=$((ERRORS + 1))
fi

# Check auth cache exists
if [ -f ~/.hermes/auth.json ]; then
    echo "PASS: Auth cache exists"
else
    echo "WARN: Auth cache missing (will be recreated on first run)"
fi

# Check model name consistency
DEFAULT=$(grep "^  default:" ~/.hermes/config.yaml | head -1 | awk '{print $2}')
MODEL_IN_PROVIDER=$(grep -A10 "kimi-coding:" ~/.hermes/config.yaml | grep "^[ ]*[a-zA-Z0-9_-]*:" | head -1 | sed 's/://g' | tr -d ' ')
FALLBACK=$(grep "model:" ~/.hermes/config.yaml | tail -1 | awk '{print $2}')

echo ""
echo "Model name check:"
echo "  default:        $DEFAULT"
echo "  provider model: $MODEL_IN_PROVIDER"
echo "  fallback:       $FALLBACK"

if [ "$DEFAULT" = "$MODEL_IN_PROVIDER" ] && [ "$DEFAULT" = "$FALLBACK" ]; then
    echo "PASS: All model names match ($DEFAULT)"
else
    echo "FAIL: Model names don't match — will cause silent failures"
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
