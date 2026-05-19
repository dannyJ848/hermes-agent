---
name: hermes-working-state-preservation
title: Hermes Working State Preservation
description: |
  Capture, snapshot, and restore Hermes Agent working state across sessions.
  Prevents catastrophic loss of cognitive orchestrator wiring, auth caches,
  and provider configuration. Use when the user expresses frustration about
  losing working state, when creating deployment packages, or before risky
  configuration changes.
triggers:
  - When user says "save my state", "don't lose this", "capture working config"
  - When user expresses frustration about broken state after restart
  - Before attempting any fix that might break current working session
  - When creating deployment packages for new CLI instances
  - When auth or provider config finally works and user wants to preserve it
category: devops
---

# Hermes Working State Preservation

## Overview

Hermes working state is fragile — it spans config files, auth caches, source code
modifications, shell environment, and git state. Losing it means re-discovering
provider endpoints, auth flows, and cognitive subsystem wiring. This skill
provides a systematic capture and restore system.

## The Preservation Protocol

### Phase 1: Emergency Capture (When User Says "Stop" or "It's Working")

When the user signals that something is finally working ("holy shit you're back",
"this works", "don't change anything"), immediately capture state BEFORE attempting
any further fixes or improvements.

```bash
# 1. Create timestamped snapshot directory
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SNAP_DIR="$HOME/.hermes/snapshots/working-$TIMESTAMP"
mkdir -p "$SNAP_DIR"

# 2. Capture config layer
cp ~/.hermes/config.yaml "$SNAP_DIR/"
cp ~/.hermes/.env "$SNAP_DIR/"
cp ~/.hermes/auth.json "$SNAP_DIR/" 2>/dev/null || true

# 3. Capture shell environment
cp ~/.zshrc "$SNAP_DIR/"
env | sort > "$SNAP_DIR/environment.txt"

# 4. Capture source code state
cd ~/hermes-agent
git rev-parse HEAD > "$SNAP_DIR/git-commit.txt"
git diff > "$SNAP_DIR/uncommitted-changes.patch"
git diff --name-only > "$SNAP_DIR/modified-files.txt"

# 5. Commit source changes if any
git add -A && git commit -m "Working state snapshot: $TIMESTAMP"
```

### Phase 2: Create Deployment Artifacts

```bash
# Create restore script
cat > "$HOME/.hermes/snapshots/restore-hermes-working-state.sh" << 'EOF'
#!/bin/bash
# Restores Hermes to last known working state
set -e
SNAP_DIR="$HOME/.hermes/snapshots/working-TIMESTAMP"
# ... (full restore logic)
EOF

# Create deployment script for fresh systems
cat > "$HOME/.hermes/snapshots/deploy-hermes-working-state.sh" << 'EOF'
#!/bin/bash
# Deploys working state to fresh ~/.hermes
# ... (full deploy logic)
EOF

# Create self-contained archive
cd ~/.hermes/snapshots/working-$TIMESTAMP
tar -czf "$HOME/.hermes/snapshots/hermes-working-state-$TIMESTAMP.tar.gz" \
  config.yaml .env auth.json .zshrc environment.txt \
  ../restore-hermes-working-state.sh \
  ../deploy-hermes-working-state.sh
```

The deployment script should:
1. Accept an optional `TARGET_DIR` argument (default `~/.hermes`)
2. Backup existing state before overwriting
3. Deploy config.yaml, .env, auth.json
4. Verify source code is at correct git commit
5. Run config validation (correct base URL, provider, model name)
6. Set file permissions (600 for secrets, 644 for config)
7. Create a `verify.sh` script in the target directory
8. Print clear next steps for the user

See `references/deployment-script-template.sh` for a complete implementation.

### Phase 3: Documentation

Create `HERMES_WORKING_STATE.md` with:
- Git commit hash for source code
- Critical configuration details (base URLs, key formats, env var names)
- Known pitfalls that were overcome
- Step-by-step restore instructions
- Troubleshooting for common failures

## What Constitutes "Working State"

| Layer | Files | Why It Matters |
|-------|-------|----------------|
| Config | `~/.hermes/config.yaml` | Provider, model, tool, plugin configuration |
| Secrets | `~/.hermes/.env` | API keys (Hermes prefers this over shell env) |
| Auth Cache | `~/.hermes/auth.json` | Credential pool with valid/known status |
| Shell Env | `~/.zshrc`, `~/.zshenv` | Env vars for new terminal windows |
| Source Code | `~/hermes-agent/` | Cognitive orchestrator, custom modules |
| Git State | Commit hash | Exact source code version |

## Provider-Specific State (Kimi Example)

When preserving working state for a specific provider, capture ALL fields that affect auth and routing:

```bash
# Extract provider-specific config for documentation
grep -A2 "^model:" ~/.hermes/config.yaml
grep "default:" ~/.hermes/config.yaml
grep -A10 "kimi-coding:" ~/.hermes/config.yaml
```

Key fields to verify match between working and broken sessions:
- `model.default:` — the model name (e.g., `kimi-for-coding` vs `kimi-k2.6`)
- `providers.X.models:` — model definitions (context_length, supports_tools)
- `fallback_model.model:` — fallback model name
- `base_url` — NO `/v1` suffix for Kimi
- `api_key_env` — `KIMI_API_KEY` vs `MOONSHOT_API_KEY`

When restoring to a fresh CLI, ALL these fields must match, not just the provider name.

## The User Frustration Signal

When user says:
- "holy shit you're back" → Capture immediately, they just recovered from loss
- "stop doing X" → Halt current approach, preserve what works, ask for direction
- "this is wrong" → Don't continue down rabbit hole, capture and pivot
- "don't lose this" → Highest priority preservation
- "I spent hours getting this back" → Working state loss is traumatic, prevent recurrence

## Restore Scenarios

### Scenario 1: Fresh CLI on Same Machine

```bash
# Source code
cd ~/hermes-agent && git checkout COMMIT_HASH

# Config and secrets
~/.hermes/snapshots/deploy-hermes-working-state.sh

# Verify
~/.hermes/verify.sh

# Start
hermes
```

### Scenario 2: Broken Auth After Key Update

```bash
# 1. Restore config from snapshot
cp ~/.hermes/snapshots/working-TIMESTAMP/config.yaml ~/.hermes/
cp ~/.hermes/snapshots/working-TIMESTAMP/.env ~/.hermes/

# 2. Clear exhausted auth cache
rm ~/.hermes/auth.json

# 3. Update key in BOTH locations
#    ~/.hermes/.env (authoritative for Hermes)
#    ~/.zshrc (for shell tools)

# 4. Restart
hermes
```

### Scenario 3: Source Code Diverged

```bash
cd ~/hermes-agent
git stash  # preserve any new work
git checkout COMMIT_HASH  # return to working state
# If cognitive subsystems don't load, source is the problem
```

## Verification Script Template

Create `~/.hermes/verify.sh` during deployment:

```bash
#!/bin/bash
echo "=== Hermes Configuration Verification ==="

# Provider configured
if grep -q "provider: kimi-coding" ~/.hermes/config.yaml; then
    echo "PASS: Provider configured"
else
    echo "FAIL: Provider not configured"; exit 1
fi

# Base URL correct
if grep -q "api.kimi.com/coding\"" ~/.hermes/config.yaml; then
    echo "PASS: Base URL correct (no /v1)"
else
    echo "FAIL: Base URL wrong"; exit 1
fi

# API key present
if grep -q "KIMI_API_KEY" ~/.hermes/.env; then
    echo "PASS: API key present"
else
    echo "FAIL: API key missing"; exit 1
fi

echo "All checks passed!"
```

## Pitfalls

- **Capturing after the fix:** Don't wait until everything is perfect — capture when user signals "this works"
- **Forgetting auth.json:** The credential cache is critical — without it, Hermes re-runs auth discovery
- **Missing shell env:** New terminal windows need env vars in `.zshenv` or `.zsh_profile`, not just `.zshrc`
- **Source code not committed:** Uncommitted cognitive orchestrator wiring is invisible to git checkout
- **Assuming config is enough:** Auth behavior depends on source code (credential_pool.py, auth.py) — capture both
- **Not documenting the commit hash:** Without the exact commit, source code restore is guesswork
- **Over-optimizing before capture:** User said "this works" — capture NOW, improve LATER
- **Ignoring the frustration signal:** "Stop" means stop — don't continue debugging, preserve and ask

## References

- `references/deployment-script-template.sh` — Full deployment script with all phases, config validation, and verification
- `references/restore-script-template.sh` — Full restore script with backup logic
- `references/verification-script-template.sh` — Config verification script
- `references/working-state-checklist.md` — Pre-flight checklist before risky changes
- `references/user-constraint-preservation-pattern.md` — When user says "don't touch X" or "stop doing X" — absolute constraint preservation protocol with verification steps and workaround strategies
- `references/yantrikdb-ingest-pattern.md` — Copying cortex/cerebrum memories into YantrikDB (queue handling, embedder setup, field mapping)
- `references/orphan-alias-cleanup.md` — Detecting and removing stale Hermes profile alias wrapper scripts that point to deleted profiles. Includes manual detection recipe and prevention pattern.
- `references/persistence-layer-verification-checklist.md` — Post-update verification protocol. After updating MEMORY.md, SOUL.md, USER.md, or MASTER.md, run this checklist to ensure all persistence layers (git, memory files, skills, doctor output) are consistent. Prevents drift where files disagree about system state.
