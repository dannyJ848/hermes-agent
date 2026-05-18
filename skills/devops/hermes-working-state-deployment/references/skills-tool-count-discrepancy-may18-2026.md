# Skills & Tool Count Discrepancy (May 18, 2026)

## Symptom

User reports: "You show 92 tools / 412 skills but the new CLI shows 27 tools / 90 skills. What happened?"

## Root Cause

The old context numbers came from a **broken backup** (`~/.hermes_broken_20260517_182538`) with a fully configured setup. The current CLI is a fresh setup with:
- No API keys configured → most toolsets disabled
- Only builtin skills loaded → 93 skills (91 builtin + 3 local)
- Source skills not installed → missing 300+ skills from `hermes-agent/skills/`

## Investigation Steps

### 1. Verify actual skill directories

```bash
# Check local skills
ls ~/.hermes/skills/

# Check source skills
ls ~/hermes-agent/skills/

# Count SKILL.md files
find ~/.hermes/skills -name SKILL.md | wc -l
find ~/hermes-agent/skills -name SKILL.md | wc -l
```

### 2. Check tool availability

```bash
hermes doctor | grep -A 30 "Tool Availability"
```

### 3. Verify config.yaml toolsets

```bash
grep toolsets ~/.hermes/config.yaml
```

Expected: `toolsets: [hermes-cli]` or similar.

### 4. Check .env for API keys

```bash
grep -E "API_KEY|TOKEN" ~/.hermes/.env
```

## Resolution

### For Skills (384 target)

Install source skills into local directory:

```bash
cd ~/.hermes
# Copy each category from source
cp -r ~/hermes-agent/skills/* skills/
# Or selectively install categories
```

Verify: `hermes skills list` should show 384+ skills.

### For Tools (90+ target)

Configure API keys in `~/.hermes/.env`:

| Key | Enables |
|-----|---------|
| `OPENROUTER_API_KEY` | moa toolset |
| `EXA_API_KEY` | web search |
| `PARALLEL_API_KEY` | web search |
| `TAVILY_API_KEY` | web search |
| `FIRECRAWL_API_KEY` | web extraction |
| `DISCORD_BOT_TOKEN` | discord toolset |
| `TINKER_API_KEY` | rl training tools |
| `WANDB_API_KEY` | rl training tools |
| `HASS_TOKEN` | homeassistant tools |

Verify: `hermes doctor` should show 45+ tools in hermes-cli toolset.

## Key Insight

The **hermes-cli toolset defines 45 tools** in `toolsets.py`. But the CLI only shows 27 because:
- 15 enabled (core, no API keys needed)
- 12 disabled (need API keys or system deps)
- 18 gated by `check_fn` (kanban only for workers, ha_* needs HASS_TOKEN, etc.)

With all API keys: 45 tools enabled.
With additional toolsets (discord, web, moa, rl): 90+ tools.

## Prevention

Always verify counts after restoring from backup:

```bash
# Skills
hermes skills list | tail -5

# Tools
hermes doctor | grep -E "^  [✓⚠]"
```

Document the expected counts in MEMORY.md so future sessions know what "normal" looks like.
