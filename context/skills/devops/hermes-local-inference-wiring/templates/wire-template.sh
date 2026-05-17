#!/bin/bash
# =============================================================================
# Wire Local Inference Server to Hermes Agent (Template)
# =============================================================================
# Usage: bash wire-local-to-hermes.sh <SERVER_IP> [options]
#
# Prerequisites:
#   - Hermes profiles created: hermes profile create <name> --clone
#   - Profile configs have SERVER_IP_PLACEHOLDER in base_url
#   - Local server running OpenAI-compatible API
# =============================================================================

set -uo pipefail

SERVER_IP=""
TUNNEL_MODE=false
HERMES_HOME="${HOME}/.hermes"
CONFIG="$HERMES_HOME/config.yaml"
PROFILES_DIR="$HERMES_HOME/profiles"

while [[ $# -gt 0 ]]; do
    case $1 in
        --tunnel) TUNNEL_MODE=true; shift ;;
        --help|-h)
            echo "Usage: bash wire-local-to-hermes.sh [--tunnel] SERVER_IP"
            exit 0 ;;
        *) SERVER_IP="$1"; shift ;;
    esac
done

[[ -z "$SERVER_IP" ]] && { echo "ERROR: Provide server IP"; exit 1; }

# ── Step 1: Patch profile configs with real IP ──
for profile_dir in "$PROFILES_DIR"/*/; do
    cfg="$profile_dir/config.yaml"
    [[ -f "$cfg" ]] || continue
    if grep -q "SERVER_IP_PLACEHOLDER" "$cfg"; then
        sed -i.bak "s|SERVER_IP_PLACEHOLDER|${SERVER_IP}|g" "$cfg"
        profile_name=$(basename "$profile_dir")
        echo "[OK] Patched $profile_name with IP $SERVER_IP"
    fi
done

# ── Step 2: Add provider to default config ──
# (Use Python for safe YAML modification — see skill for full example)
python3 << PYEOF
import yaml, os

config_path = "$CONFIG"
with open(config_path) as f:
    cfg = yaml.safe_load(f)

if 'providers' not in cfg or cfg['providers'] is None:
    cfg['providers'] = {}

# TODO: Add your provider config here
# cfg['providers']['your-provider'] = {
#     'api': f'http://$SERVER_IP:8000/v1',
#     'api_key': 'not-needed',
#     'name': 'your-provider',
#     'models': { 'your-model': {'context_length': 262144} },
# }

with open(config_path, 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
PYEOF

echo "[OK] Default config updated (provider added, default model UNCHANGED)"

# ── Step 3: Optional SSH tunnel ──
if [[ "$TUNNEL_MODE" == true ]]; then
    echo "Setting up SSH tunnel..."
    ssh -f -N -L 8000:localhost:8000 -L 8001:localhost:8001 "$SERVER_IP" 2>/dev/null
    # Update configs to use localhost
    for profile_dir in "$PROFILES_DIR"/*/; do
        cfg="$profile_dir/config.yaml"
        [[ -f "$cfg" ]] || continue
        sed -i '' "s|http://${SERVER_IP}|http://localhost|g" "$cfg"
    done
    echo "[OK] SSH tunnel active (localhost:8000, :8001)"
fi

echo ""
echo "Done. Launch profiles:"
echo "  hermes chat          # Cloud model (default)"
for profile_dir in "$PROFILES_DIR"/*/; do
    name=$(basename "$profile_dir")
    [[ "$name" == "default" || "$name" == "training-gym" ]] && continue
    echo "  $name chat           # Local model"
done
