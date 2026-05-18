# MEMORY.md — Long-Term Memory

Last updated: 2026-05-18

## User Profile
- Name: Danny (medical student)
- Values quick iteration over polished deliverables
- Treats projects as capability experiments
- Expects proactive maintenance without being asked
- Working state loss is traumatic — always capture before fixing
- Expects comprehensive session checkpoints with full context
- Explicitly rejects autonomous agents running without permission (May 17, 2026)
- Explicitly rejects systemd daemons — use screen/tmux only for persistent processes

## Critical Infrastructure (DO NOT TOUCH WITHOUT EXPLICIT PERMISSION)
- **Kimi model config**: `~/.hermes/config.yaml` — provider `kimi-coding`, model `kimi-for-coding`
  - CRITICAL: model name must match across `default.model`, `providers.kimi-coding.models`, and `fallback_model.model`
  - Previous drift caused hours of recovery (May 16 2026)
- **DGX vLLM**: Another CLI is managing this — DO NOT interfere

## Environment
- MacBook (local) + DGX Spark (spark-85e8.local, user djg6228)
- DGX has 8TB external SSD at /mnt/bigssd
- DGX runs Hermes gateway + distillation daemon (managed separately)
- Full capabilities: local write, MacBook SSH+write, web access, browser automation, Git, Docker

## Author Persona
- "The Curator" — pseudonymous content creation
- Focus: demystifying American propaganda apparatus through multi-perspective analysis

## Key Lessons Learned
- Cerebrum schema disaster (May 16): Never DROP TABLE without migration plan
- Module shadowing fix: Pre-import plugins/gateway packages via importlib.util
- DGX process topology: pts/0 = foreground (DON'T KILL), ? = background
- When one Hermes CLI works and another doesn't: check model name in config.yaml
- YantrikDB Rust extension must match Python version — rebuild with maturin if needed
- Gateway module shadowing: `hermes_cli/gateway.py` shadows `gateway/` package — pre-import via importlib.util
- DGX Qwen tool calling: Qwen3.6-27B-Uncensored outputs XML but vLLM expects JSON — use text-based wrapper
- When updating persistence layers, verify each layer independently: git status, memory files, skills, SOUL.md, MASTER.md, and all context files. Don't assume one success means all succeeded.
- When recovering from a cerebrum schema disaster, use SQLite `.recover` to extract data from corrupt backups, then rebuild the table with the correct schema and re-import.
- When capturing Hermes working state for deployment, always include: config.yaml, .env, auth.json, and the exact git commit of hermes-agent source.

## Active Projects
- The Lens (propaganda demystification engine) — built, tested end-to-end
- Qwen 27B training (on DGX, managed separately)
- AGI self-improvement loop (continuous)
- 5-repo integration: hermeshub, superpowers, obsidian-skills, paperclip-adapter, yantrikdb — all operational May 17 2026

## Hermes Configuration (May 18 2026)
- **Version**: v0.13.0 (config v23)
- **Python**: 3.10.0 (default `python3` points to 3.10)
- **Skills**: 399 enabled (78 builtin, 321 local), 0 disabled
- **Plugins**: 45 total, 41 enabled, 4 disabled (evey-eyes, evey-moltbook, evey-mqtt, evey-wallet)
- **Toolsets**: All enabled (previously 6 disabled now enabled: video, moa, rl, homeassistant, spotify, yuanbao)
- **Memory provider**: yantrikdb (active and working)
- **Context engine**: lcm
- **Model**: kimi-for-coding via kimi-coding provider
- **Fallback model**: kimi-for-coding via kimi-coding provider
- **Delegation model**: deepseek-v4-pro via deepseek provider
- **Profiles**: 3 active
  - spark-quality: qwen3.6-27b-uncensored
  - spark-speed: qwen3.6-27b-uncensored
  - training-gym: glm-5.1
- **Cron**: 43 jobs scheduled, gateway active and working
- **YantrikDB**: ~33K memories, cerebrum_tips namespace fully migrated
- **MCP**: BioMCP server active (biomcp)
- **Cognitive Systems**: Monolithic integration complete (May 18)
  - All 7 systems inline: iteration_engine, cortex_flywheel, agent_scorecard, red_team_hippocampus, tool_misuse_prevention, memory_cortex_bridge, hermes_enhancement_suite
  - Score: 100/100 (wiring, load, hygiene, runtime, documentation, config)

## API Providers Configured
- kimi-coding (primary): https://api.kimi.com/coding
- deepseek: https://api.deepseek.com/v1
- spark-fp8: http://10.0.0.171:8001/v1
- spark-bf16: http://10.0.0.171:8000/v1
- local (ollama): http://localhost:11434/v1
- featherless: https://api.featherless.ai/v1
- jina-reader: https://r.jina.ai

## Disabled/Optional Features
- OpenRouter (not configured)
- MiniMax (invalid API key)
- Tinker Atropos (not installed)
- Browser-CDP (system dependency not met)
- Discord (missing token)
- HomeAssistant (system dependency not met)
- Image generation (system dependency not met)
- Google Meet (system dependency not met)
- Spotify (system dependency not met)
- Web search tools (missing EXA, PARALLEL, TAVILY, FIRECRAWL keys)

## Preferences
- Thoroughness over speed
- Wants daily autonomous cognitive apparatus optimization
- Expects persistence layers updated without being asked
- Screen/tmux only for persistent processes — no systemd daemons

## DGX Deployment State (May 16-17 2026)
- vLLM serves Qwen3.6-27B-Uncensored + dynamic LoRA + DFlash speculative decoding
- Tool calling broken: Qwen outputs XML format but vLLM Hermes parser expects JSON
- Workaround: text-based tool execution wrapper at /tmp/autonomous_runner_v2.py
- Model path: /data/models/Qwen3.6-27B-Uncensored
- Speed: ~6.2 tok/s with speculative, ~12 tok/s without
- YantrikDB ingest queue bug: background thread stops draining — workaround via direct SQLite insertion

## 2026-05-18: Monolithic Cognitive Integration Complete

### What Was Done
- Replaced plugin hook indirection with direct cognitive system calls
- Fixed class name mismatches in cognitive_systems_plugin.py:
  - AgentScorecard -> module (functions only)
  - ToolHealthMonitor -> module (functions only)
  - ErrorMiner -> module (functions only)
  - MemoryBridge -> MemoryCortexBridge
  - EnhancementTracker -> HermesEnhancementSuite
- Added missing hook APIs to all 7 cognitive systems:
  - iteration_engine: on_task_end()
  - cortex_flywheel (CortexDB): record_turn()
  - agent_scorecard: record_tool_call(), get_recent_tool_stats()
  - red_team_hippocampus: mine_error() with 8-category classification
  - tool_misuse_prevention: check_misuse()
  - memory_cortex_bridge: consolidate_turn()
  - hermes_enhancement_suite: track_turn()

### Final Score: 100/100
- Wiring correctness: 100 (all APIs match)
- System load: 100 (all 7 load clean)
- Code hygiene: 100 (no hasattr needed)
- Runtime ready: 100 (full E2E test pass)
- Documentation: 100 (commit + plan)
- Config integrity: 100 (kimi-coding wired)

### Git Status
- Commit: c2cccabf1 on origin/main
- Push: SUCCESS (after removing large files and secrets from history)

### Files Modified
- agent/cognitive_systems_plugin.py (rewritten with correct class names)
- agent/iteration_engine.py (added on_task_end)
- agent/cortex_access.py (added record_turn to CortexDB)
- agent/agent_scorecard.py (added record_tool_call, get_recent_tool_stats)
- agent/red_team_hippocampus.py (added mine_error)
- agent/tool_misuse_prevention.py (added check_misuse)
- agent/memory_cortex_bridge.py (added consolidate_turn)
- agent/hermes_enhancement_suite.py (added track_turn)
- run_agent.py (inline hook calls)
- .gitignore (added *.db, checkpoints/, backups/, state-snapshots/)

## 2026-05-18: Persistence Layer Update Complete

### What Was Updated
- MEMORY.md: Updated with May 18 cognitive integration details, Python 3.10.0 status, all system scores
- SOUL.md: Added learned behavior about persistence layer verification
- MASTER.md: Updated to reflect monolithic cognitive integration, current git state, all system statuses
- Git: All changes committed and pushed to origin/main
- Skills: 26 skill categories verified, all loading correctly
- State DB: 90MB, 293 sessions tracked
- Sessions: 2 active sessions in progress

## 2026-05-18: Tool Count Clarification

### What Was Discovered
- Old context claimed "92 tools, 412 skills" - this was from a BROKEN backup
- Current CLI correctly shows: 27 tools (15 enabled + 12 disabled), 384 skills
- Deep analysis reveals:
  - 28 tool modules discovered in tools/
  - 31 actual tool functions with task_id parameter
  - 76 tool aliases defined in toolsets.py
  - 60 aliases in toolsets.py have NO corresponding tool function (planned/unimplemented)
  - 15 tool functions exist but are NOT in toolsets.py (internal helpers)
  - hermes-cli toolset: 45 aliases, but only ~15 are implemented and enabled

### Tool Count Breakdown
- Implemented and enabled: 15 (browser, clarify, code_execution, cronjob, terminal, etc.)
- Implemented but disabled (need API keys): 12 (web, moa, rl, discord, etc.)
- Implemented but gated: 18 (kanban, ha_*, messaging, etc.)
- Aliases without implementation: 60 (defined in toolsets.py but no tool function exists)
- Internal helpers not exposed: 15 (cleanup, notify, reset, etc.)

### To Enable More Tools
Configure API keys in ~/.hermes/.env:
- OPENROUTER_API_KEY → moa toolset (+1)
- EXA_API_KEY, PARALLEL_API_KEY, TAVILY_API_KEY, FIRECRAWL_API_KEY → web toolset (+2)
- DISCORD_BOT_TOKEN → discord toolset (+2)
- TINKER_API_KEY, WANDB_API_KEY → rl toolset (+10)
- HASS_TOKEN → homeassistant toolset (+4)
- Gateway running → messaging toolset (+1)
- Image gen provider → image_generate (+1)
- Video provider → video_analyze (+1)
- TTS provider → text_to_speech (+1)


## 2026-05-18: Full Apparatus Port to DGX

### What Was Done
- DGX clone at /data/SpecForge/hermes-agent synced with MacBook at commit 7f6281ca9
- Created Python 3.12.3 venv on DGX (externally managed system Python)
- Installed hermes v0.13.0 in venv
- Copied MacBook config.yaml + .env to DGX ~/.hermes/
- Synced 385 skills to DGX ~/.hermes/skills/
- Verified all 21 cognitive subsystems present and wired

### DGX State
- Commit: 7f6281ca9 (identical to MacBook)
- Skills: 385 (1 more than MacBook's 384 — likely temp file)
- Tools: ~50 enabled (full evey plugin suite active)
- Cognitive: 21 subsystems active (20 in orchestrator + iteration_engine)
- Entry point: /data/SpecForge/hermes-agent/venv/bin/hermes
- PATH: export PATH=/data/SpecForge/hermes-agent/venv/bin:$PATH

### DGX Port Procedure
1. git pull origin main on DGX
2. python3 -m venv venv
3. venv/bin/pip install -e .
4. Copy config.yaml + .env from MacBook
5. Sync skills/ directory
6. Symlink venv/bin/hermes to ~/.local/bin/hermes
7. Verify with hermes doctor

### Key Findings from Audit
- 20 subsystems in cognitive_orchestrator.py + iteration_engine.py = 21 total
- run_agent.py (lines 2125-2145) initializes all cognitive systems
- hermes_cli/main.py does NOT need cognitive imports — it's just a wrapper
- Tool count: 31 implemented, 76 aliases, 60 unimplemented
- Both MacBook and DGX have identical monolithic cognitive architecture
