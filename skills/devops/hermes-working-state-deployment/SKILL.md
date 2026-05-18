---
title: Hermes Working State Deployment
name: hermes-working-state-deployment
category: devops
description: Capture, snapshot, and deploy Hermes Agent working state across CLI sessions. Ensures consistent configuration, auth, and source code.
version: 1.0
tags: [hermes, deployment, config, auth, backup]
---

# Hermes Working State Deployment

Capture and restore complete Hermes Agent working state including configuration, API keys, credential cache, and source code commit.

## When to Use

- Before making risky config changes
- When spawning new Hermes CLI instances
- After fixing auth issues to preserve working state
- When migrating to a new machine or environment
- When one CLI works and another doesn't
- **When user says "get ready for a new CLI" — this means update all persistence layers, commit, push, verify cognitive systems green**

## What Gets Captured

| Component | File | Purpose |
|-----------|------|---------|
| Config | `~/.hermes/config.yaml` | Provider, model, tool, plugin settings |
| API Keys | `~/.hermes/.env` | KIMI_API_KEY, DEEPSEEK_API_KEY, etc. |
| Auth Cache | `~/.hermes/auth.json` | Credential pool with working state |
| Shell Env | `~/.zshrc` | PATH, env vars |
| Source Code | `~/hermes-agent/` | Git commit with cognitive orchestrator |

## What Gets Verified During Deployment

| Check | Why It Matters |
|-------|--------------|
| Git status clean | Uncommitted changes can cause drift between sessions |
| All persistence layers updated | MEMORY.md, SOUL.md, MASTER.md must reflect current state |
| Skills count matches | 93 builtin + local vs 384 after source install — know which you have |
| Tool count matches | 27 core vs 90+ with API keys — verify .env has expected keys |
| Cognitive systems load | All 7 inline systems must pass integration test |
| Git push succeeds | Local-only commits are invisible to other CLI instances |

## Critical Config Rules

### Kimi Provider
- **Base URL**: `https://api.kimi.com/coding` (NO `/v1` suffix)
  - SDK appends `/v1/messages` internally
  - `.../coding/v1` → `/coding/v1/v1/messages` → 404
- **Model name**: Must match in THREE locations:
  1. `model.default`
  2. `providers.kimi-coding.models` (key name)
  3. `fallback_model.model`
- **Auth**: `KIMI_API_KEY` in `~/.hermes/.env` (NOT just shell env)
  - Credential pool prefers `.env` over `os.environ`

### Source Code
- Commit `b6fa8f918` on branch `qwen27b-training-artifacts-may3-2026`
- Includes cognitive orchestrator (19/20 subsystems)
- New modules: distillation_bridge, training_gym, subconscious_hook_wiring

## Deployment Steps

### 0. Pre-Deployment Persistence Layer Update (CRITICAL)

When user says "get ready for a new CLI" or similar, do this FIRST before any deployment:

1. **Update MEMORY.md** — add current state entry with date, what was done, final scores
2. **Update SOUL.md** — add any new learned behaviors from this session
3. **Update MASTER.md** — refresh system status table, last updated date, component statuses
4. **Verify cognitive systems** — run integration test, all 7 must pass
5. **Verify skills load** — `hermes skills list` should show expected count (91 builtin + local)
6. **Verify tools** — `hermes doctor` tool availability section
7. **Git commit all changes** — MEMORY.md, SOUL.md, MASTER.md, any fixed agent/ files
8. **Git push to origin/main** — verify push succeeds
9. **Only then** proceed to deployment steps below

**Pitfall**: Skipping step 0 and going straight to deployment. The new CLI will load stale context files and appear broken even if the source code is correct.

### 1. Capture Current Working State

```bash
# Create snapshot directory
SNAP="$HOME/.hermes/snapshots/working-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$SNAP"

# Copy config files
cp ~/.hermes/config.yaml "$SNAP/"
cp ~/.hermes/.env "$SNAP/"
cp ~/.hermes/auth.json "$SNAP/" 2>/dev/null || true
cp ~/.zshrc "$SNAP/"

# Record git state
cd ~/hermes-agent && git rev-parse HEAD > "$SNAP/git-commit.txt"
```

### 2. Deploy to Fresh Environment

```bash
# 1. Ensure source at correct commit
cd ~/hermes-agent && git checkout b6fa8f918

# 2. Deploy config
cp ~/.hermes/snapshots/working-XXXX/config.yaml ~/.hermes/
cp ~/.hermes/snapshots/working-XXXX/.env ~/.hermes/
cp ~/.hermes/snapshots/working-XXXX/auth.json ~/.hermes/

# 3. Verify
~/.hermes/verify.sh

# 4. Start
hermes
```

### 3. Automated Deployment Script

Use the deployment script from the skill templates:

```bash
# Copy from skill to a working location
cp ~/.hermes/skills/devops/hermes-working-state-deployment/templates/deploy-hermes-working-state.sh /tmp/
bash /tmp/deploy-hermes-working-state.sh
```

This script:
- Backs up existing state
- Deploys all config files
- Verifies critical values
- Creates `verify.sh`
- Reports any issues

Or use the restore script for a specific snapshot:

```bash
cp ~/.hermes/skills/devops/hermes-working-state-deployment/templates/restore-hermes-working-state.sh /tmp/
bash /tmp/restore-hermes-working-state.sh ~/.hermes/snapshots/working-20260516-144642
```

## Verification

Run `~/.hermes/verify.sh` after deployment:

```
PASS: Provider configured (kimi-coding)
PASS: Base URL correct (no /v1 suffix)
PASS: KIMI_API_KEY present in .env
PASS: Auth cache exists
```

## Troubleshooting

See `references/kimi-auth-debugging-pattern-may16-2026.md` for the complete Kimi auth debugging pattern — model name drift across three config locations, base URL /v1 suffix pitfall, and credential pool preference for `~/.hermes/.env` over shell environment variables.

### Auth 401 — Invalid Key
1. Check which key is actually being used: `grep -A5 "kimi-coding" ~/.hermes/auth.json | grep "source"`
2. If source is `env:KIMI_API_KEY`, verify `~/.hermes/.env` has the correct key
3. If source is `env:MOONSHOT_API_KEY`, check shell env with `echo $MOONSHOT_API_KEY`
4. Get new key from https://kimi.com/code → Settings → API Keys
5. Update `~/.hermes/.env`: `KIMI_API_KEY=your-new-key`
6. Remove `~/.hermes/auth.json` to clear cache
7. Restart Hermes

**Critical**: Hermes credential pool PREFERS `~/.hermes/.env` over shell environment variables. Even if `MOONSHOT_API_KEY` is set in your shell, Hermes will use `KIMI_API_KEY` from `.env` if it exists.

### Auth 404 — Wrong Base URL
```bash
# Check
grep "api.kimi.com" ~/.hermes/config.yaml

# Fix
sed -i '' 's|api.kimi.com/coding/v1|api.kimi.com/coding|g' ~/.hermes/config.yaml
```

**Root cause**: The Kimi `/coding` endpoint speaks Anthropic Messages protocol. The Anthropic SDK internally appends `/v1/messages`. So:
- Correct: `https://api.kimi.com/coding` → SDK adds `/v1/messages` → `/coding/v1/messages` ✓
- Wrong: `https://api.kimi.com/coding/v1` → SDK adds `/v1/messages` → `/coding/v1/v1/messages` ✗ 404

### Model Mismatch
Check all three locations have same model name:
```bash
grep -n "default:\|kimi-coding:\|fallback_model:" ~/.hermes/config.yaml
```

**Common drift**: `kimi-k2.6` vs `kimi-for-coding` — all three locations must match. Drift causes silent auth failures even when API key is valid.

### Source Code Mismatch
If cognitive subsystems don't load:
```bash
cd ~/hermes-agent
git stash
git checkout b6fa8f918
```

## File Locations

| Path | Description |
|------|-------------|
| `~/.hermes/config.yaml` | Main configuration |
| `~/.hermes/.env` | API keys (sensitive) |
| `~/.hermes/auth.json` | Credential pool cache |
| `~/.hermes/snapshots/` | Working state snapshots |
| `~/.hermes/verify.sh` | Verification script |
| `~/hermes-agent/` | Source code |

## DGX Deployment Specifics

### DGX Hermes Service Setup (May 16, 2026)

For running Hermes as a persistent systemd service on DGX connected to local vLLM:

1. **Wrapper script** (`run_hermes_dgx_fixed.py`): Handles module shadowing + `asyncio.run(main())` coroutine issue
2. **systemd service** (`hermes-dgx.service`): Auto-restarts after power cycles, depends on docker
3. **vLLM flags**: Must include `--enable-auto-tool-choice --tool-call-parser hermes` for Hermes compatibility

See `references/dgx-hermes-service-setup-may16-2026.md` for complete setup including:
- Wrapper script with module shadowing fix
- systemd service configuration
- vLLM Docker launch with tool calling
- Post-power-cycle recovery procedure
- Verification commands

### Module Shadowing Fix (May 16, 2026)

When deploying Hermes on DGX, Python module shadowing can break imports:
- `hermes_cli/gateway.py` shadows the `gateway/` package directory
- `hermes_cli/cron.py` shadows the `cron` package

**Fix**: Pre-import packages via `importlib.util` before importing hermes_cli modules:

```python
import importlib.util
import sys

# Pre-import to prevent shadowing
spec = importlib.util.spec_from_file_location("gateway", "/path/to/gateway/__init__.py")
gateway_mod = importlib.util.module_from_spec(spec)
sys.modules["gateway"] = gateway_mod
spec.loader.exec_module(gateway_mod)

# Now safe to import hermes_cli
from hermes_cli import run_agent
```

**Alternative**: Rename shadowing files:
```bash
cd /data/SpecForge/hermes-agent
mv hermes_cli/gateway.py hermes_cli/gateway_cmd.py
mv hermes_cli/cron.py hermes_cli/cron_cmd.py
# Update all imports accordingly
```

### Cognitive Orchestrator Initialization (May 16, 2026)

The cognitive orchestrator does NOT auto-load. Must be explicitly initialized:

```python
from hermes_cli.cognitive_orchestrator import initialize_orchestrator

# Initialize with agent instance
initialize_orchestrator(agent)

# Verify all 20 subsystems
status = orchestrator.get_status()
assert len(status["subsystems"]) == 20, f"Only {len(status['subsystems'])} subsystems active"
```

**Common pitfall**: Assuming the orchestrator loads automatically when Hermes starts. It must be explicitly wired into `run_agent.py` startup sequence.

## Known Snapshots

| Date | Location | Commit | Notes |
|------|----------|--------|-------|
| 2026-05-16 | `~/.hermes/snapshots/working-20260516-144642/` | b6fa8f918 | Module shadowing fix + cognitive orchestrator + 20/20 subsystems |
| 2026-05-18 | `~/.hermes/` (current) | 7f6281ca9 | Monolithic cognitive integration v4, 384 skills, 27 tools (45 with API keys) |
| 2026-05-18 | DGX `/data/SpecForge/hermes-agent` | 7f6281ca9 | Full port complete: venv, config, .env, 385 skills, ~50 tools, 21 cognitive subsystems |

## Reference Files

| File | Description |
|------|-------------|
| `references/dgx-full-port-procedure-may18-2026.md` | Complete DGX port: venv, config, .env, skills, cognitive verification |
| `references/kimi-auth-debugging-pattern-may16-2026.md` | Kimi auth 401/404 debugging — model name drift, base URL /v1 suffix, credential pool preference |
| `references/module-shadowing-fix-may16-2026.md` | Python module shadowing between hermes_cli/gateway.py and gateway/ package |
| `references/dgx-hermes-service-setup-may16-2026.md` | DGX systemd service + vLLM + tool calling setup |
| `references/cognitive-orchestrator-init-may16-2026.md` | Explicit initialization required — does NOT auto-load |
| `references/skills-tool-count-discrepancy-may18-2026.md` | Skills/tool count mismatch investigation — broken backup vs fresh setup |
