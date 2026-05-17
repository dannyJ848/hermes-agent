# hermes-telegram-command-length-bug

*Researched: 2026-04-05 03:03 CDT*

# Telegram Bot Command Registration Failure

## Problem
The Hermes gateway fails to register the Telegram bot command menu on EVERY startup with:
```
telegram.error.BadRequest: Command length must not exceed 32
```
This occurs in `gateway/platforms/telegram.py:630` when calling `self._bot.set_my_commands()`.

## Root Cause
The code has `_clamp_telegram_names()` for plugin commands (line 445) but skill-based slash commands may have names exceeding Telegram's 32-character limit. The function `telegram_menu_commands()` in `hermes_cli/commands.py:407` loads skill commands via `get_skill_commands()` but the clamping may not handle all edge cases.

## Impact
- Non-fatal but noisy (6+ occurrences in error log)
- Bot still works fine but doesn't show the command hint menu
- The error gets logged with full traceback on every gateway startup

## Fix Needed
Either:
1. Apply `_clamp_telegram_names()` to ALL command tiers (core, plugin, and skill)
2. Or filter out commands with names > 32 chars before calling `set_my_commands()`
3. Check `get_skill_commands()` output for oversized names

## Error Frequency
6+ occurrences between March 30-31, 2026. Every gateway restart triggers this.

## Source
Hermes Agent error log analysis, Dojo session April 5, 2026


## Sources

- file:///Users/dannygomez/hermes-agent/gateway/platforms/telegram.py
- file:///Users/dannygomez/hermes-agent/hermes_cli/commands.py
