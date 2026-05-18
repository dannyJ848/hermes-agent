# MASTER.md — Hermes Agent Master Documentation

**System**: Hermes Agent v0.13.0 (config v23)
**Last Updated**: 2026-05-18
**Host**: MacBook (local) + DGX Spark (remote)
**Python**: 3.10.0 (default `python3` points to 3.10)

---

## Quick Reference

| Component | Status | Details |
|-----------|--------|---------|
| Primary Model | ✅ | kimi-for-coding (kimi-coding provider) |
| Fallback Model | ✅ | kimi-for-coding (kimi-coding provider) |
| Memory Provider | ✅ | yantrikdb (active, ~33K memories) |
| Context Engine | ✅ | lcm |
| Skills | ✅ | 399 enabled (78 builtin, 321 local) |
| Plugins | ✅ | 41 enabled, 4 disabled |
| Toolsets | ✅ | All enabled |
| Cron Gateway | ✅ | 43 jobs, active |
| MCP | ✅ | BioMCP server |
| **Cognitive Systems** | ✅ | Monolithic inline (May 18), 7/7 active, Score 100/100 |
| **Git Repo** | ✅ | Clean (commit bf53b5b9b) |
| **DGX Integration** | 🔄 | Config complete, needs vLLM verification |

---

## Architecture

### Local (MacBook)
- **Hermes Agent**: `/Users/dannygomez/hermes-agent/`
- **Virtual Env**: Python 3.10.0
- **Config**: `~/.hermes/config.yaml`
- **Memory**: `~/.hermes/yantrikdb_copy.db` (~33K records)
- **Skills**: `~/.hermes/skills/` (321 local)
- **Plugins**: `~/.hermes/plugins/` (yantrikdb, paperclip-adapter, etc.)

### Remote (DGX Spark)
- **Host**: spark-85e8.local (user: djg6228)
- **IP**: 10.0.0.171
- **vLLM BF16**: Qwen3.6-27B-Uncensored + LoRA @ port 8000
  - Base model: /data/models/Qwen3.6-27B-Uncensored
  - LoRA adapter: /data/checkpoints/final_model (merged-lora)
  - DType: bfloat16 (native, no quantization)
  - Context: 32768 tokens
  - Tool calling: XML vs JSON mismatch — needs --tool-call-parser qwen3_xml
- **Speed**: ~6.2 tok/s (speculative), ~12 tok/s (without)
- **Status**: Configured in Hermes, needs vLLM verification

---

## Configuration

### API Providers
```yaml
kimi-coding: https://api.kimi.com/coding  (primary)
deepseek:    https://api.deepseek.com/v1
spark-bf16:  http://10.0.0.171:8000/v1    (BF16 native — Qwen 27B + LoRA)
local:       http://localhost:11434/v1    (ollama)
featherless: https://api.featherless.ai/v1
jina-reader: https://r.jina.ai
```

### DGX Qwen Integration
- **Model**: Qwen3.6-27B-Uncensored D-Flash Final + LoRA
- **Endpoint**: http://10.0.0.171:8000/v1
- **LoRA module**: merged-lora
- **Context**: 32768 tokens
- **Tool calling**: XML vs JSON mismatch — needs vLLM parser fix
- **Launch**: `dgx-qwen-lora chat`

### Key Settings
- `model.default`: kimi-for-coding
- `memory.provider`: yantrikdb
- `context.engine`: lcm
- `delegation.model`: deepseek-v4-pro
- `fallback_model.model`: kimi-for-coding
- `agent.max_turns`: 90
- `terminal.timeout`: 180
- `checkpoints.enabled`: true

### Disabled Features
- evey-eyes, evey-moltbook, evey-mqtt, evey-wallet (plugins)
- OpenRouter (not configured)
- MiniMax (invalid key)
- Browser-CDP, Discord, HomeAssistant, ImageGen, Spotify (missing deps/tokens)

---

## Profiles

| Profile | Model | Purpose |
|---------|-------|---------|
| dgx-qwen-lora | merged-lora | **NEW** — Qwen 27B + LoRA BF16 on DGX |
| spark-quality | qwen3.6-27b-uncensored | DEPRECATED — use dgx-qwen-lora |
| spark-speed | qwen3.6-27b-uncensored | DEPRECATED — use dgx-qwen-lora |
| training-gym | glm-5.1 | Training and evaluation |

---

## Critical Files

### Must Not Modify Without Permission
- `~/.hermes/config.yaml` — especially model names in 3 locations
- `~/.hermes/.env` — API keys
- `~/.hermes/auth.json` — auth state

### Context Files (Auto-loaded)
- `~/.hermes/SOUL.md` — persona & learned behaviors
- `~/.hermes/MEMORY.md` — long-term memory
- `~/.hermes/USER.md` — user profile (365 chars)
- `~/.hermes/MASTER.md` — system status (this file)
- `~/.hermes/AGENTS.md` — workspace conventions

### Persistence Layers
- Git repo: `/Users/dannygomez/hermes-agent/` (hermes-agent source)
- Memory DB: `~/.hermes/yantrikdb_copy.db`
- State DB: `~/.hermes/state.db`
- Session logs: `~/.hermes/sessions/`
- Skills: `~/.hermes/skills/` + builtin
- Checkpoints: `~/.hermes/workspace/checkpoints/`

---

## 5-Repo Integration

| Repo | Location | Status |
|------|----------|--------|
| hermeshub | `~/.hermes/plugins/hermeshub/` | ✅ 22 skills |
| superpowers | `~/.hermes/plugins/superpowers/` | ✅ 14 skills |
| obsidian-skills | `~/.hermes/plugins/obsidian-skills/` | ✅ 5 skills |
| paperclip-adapter | `~/.hermes/plugins/paperclip-adapter/` | ✅ enabled |
| yantrikdb | `~/.hermes/plugins/yantrikdb/` | ✅ enabled, rebuilt for py3.11 |

---

## Known Issues & Workarounds

1. **YantrikDB Python version mismatch**: Rebuild with `maturin build --release --interpreter <python>`
2. **Gateway module shadowing**: Pre-import `gateway` via `importlib.util`
3. **DGX Qwen XML tool output**: Use text-based wrapper, not vLLM parser
4. **Cron stale jobs**: Gateway restart fixes (done May 17)
5. **Orphan aliases**: Remove from `~/.local/bin/` (done May 17)

---

## Operations

### Daily Checks
- `hermes doctor` — system health
- `hermes memory status` — memory provider
- `hermes cron list` — cron jobs

### Maintenance
- Memory consolidation: automatic via evey-memory-consolidate
- Curator: auto-archive after 90 days
- Checkpoints: auto-prune orphans, 7-day retention

### Emergency Recovery
1. Check model names in config.yaml (3 locations)
2. Verify `~/.hermes/.env` has API keys
3. Check git status for uncommitted changes
4. Run `hermes doctor --fix`
5. Rebuild YantrikDB if needed: `cd ~/.hermes/plugins/yantrikdb && maturin develop --release`

---

## User Constraints
- **NO systemd daemons** — screen/tmux only
- **NO autonomous agents without explicit permission**
- **NO touching DGX vLLM** — managed separately
- **NO modifying kimi config** — caused recovery incident May 16

---

*This document is the single source of truth for Hermes Agent state. Update it whenever configuration changes.*
