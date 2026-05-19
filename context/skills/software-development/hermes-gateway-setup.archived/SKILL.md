---
name: hermes-gateway-setup
description: Set up Hermes Agent's own Telegram gateway, replacing intermediary platforms like OpenClaw. Covers launchd service removal, env configuration, and gateway startup.
version: 1.0
---

# Hermes Gateway Direct Setup

## Context
When Hermes is managed by an intermediary platform (e.g., OpenClaw) that runs as a launchd service, you need to:
1. Kill the intermediary
2. Prevent it from respawning
3. Configure Hermes to run its own Telegram gateway

## Steps

### 1. Get a Telegram Bot Token
- Message @BotFather on Telegram
- Create a new bot or use `/token` on an existing one

### 2. Stop and Disable Intermediary Services (macOS launchd)
```bash
# Find the plist files
find ~/Library/LaunchAgents -name "*openclaw*" 2>/dev/null

# Unload each service
launchctl unload ~/Library/LaunchAgents/ai.openclaw.kimi.plist
launchctl unload ~/Library/LaunchAgents/ai.openclaw.dev.plist
launchctl unload ~/Library/LaunchAgents/ai.openclaw.gateway.plist

# Prevent respawn on reboot by renaming plists
mv ~/Library/LaunchAgents/ai.openclaw.kimi.plist{,.disabled}
mv ~/Library/LaunchAgents/ai.openclaw.dev.plist{,.disabled}
mv ~/Library/LaunchAgents/ai.openclaw.gateway.plist{,.disabled}

# Verify
launchctl list | grep openclaw  # should return nothing
ps aux | grep openclaw | grep -v grep  # should return nothing
```

**IMPORTANT**: `kill` and `pkill` alone won't work -- launchd respawns services. You MUST `launchctl unload` then rename/disable the plist files. `launchctl disable` alone is also insufficient; renaming the plist is the reliable approach.

### 3. Configure Hermes Environment
```bash
# Add to ~/.hermes/.env
echo 'TELEGRAM_BOT_TOKEN=<your_token>' >> ~/.hermes/.env
echo 'GATEWAY_ALLOW_ALL_USERS=true' >> ~/.hermes/.env
```

For production, replace ALLOW_ALL with specific user IDs:
```bash
echo 'TELEGRAM_ALLOWED_USERS=123456789,987654321' >> ~/.hermes/.env
```

### 4. Start the Gateway
```bash
cd ~/hermes-agent && source venv/bin/activate && hermes gateway
```

For background/long-running:
```bash
nohup hermes gateway > /dev/null 2>&1 &
```

### 5. Verify
- Check logs: `tail -f ~/.hermes/logs/gateway.log`
- Look for: "✓ telegram connected" and "Gateway running"
- Send a test message to the bot on Telegram
- Set home channel via the bot's `/start` flow

## Restarting the Gateway (for config/module changes)

When you need to restart the gateway to pick up patched Python modules or config changes:

```bash
# CORRECT: Use the built-in restart command
cd ~/hermes-agent && ./venv/bin/python3 -m hermes_cli.main gateway restart

# WRONG: Manual kill + start fails — gateway detects duplicate and refuses
kill <PID>  # Old process may not fully die
nohup ./venv/bin/python3 -m hermes_cli.main gateway run &  # FAILS: "Gateway already running"
```

The `gateway restart` command handles stop+start atomically, updates the launchd service definition, and returns a clean status. After restart, verify with:
```bash
sleep 3 && ps aux | grep "hermes_cli.main gateway" | grep -v grep
```

**When restart is needed:** After patching `.py` files in `~/hermes-agent/` or `~/subconscious/`, Python caches modules. A restart clears the cache. Always save a session checkpoint before restarting.

## Gotchas
- The "Command length must not exceed 32" error in logs is cosmetic -- doesn't affect messaging
- Gateway needs to stay running (foreground or background) to receive messages
- If switching from an old bot to a new one, users must start a NEW conversation with the new bot
- The `.env` file path is `~/.hermes/.env`, NOT `~/hermes-agent/.env`
- **Never manually kill+start the gateway** — always use `gateway restart` to avoid duplicate detection
- **Save checkpoint before restart** — restarting kills the current session's terminal connections
