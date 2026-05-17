# MEMORY.md — Long-Term Memory

Last updated: 2026-05-17

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

## Active Projects
- The Lens (propaganda demystification engine) — built, tested end-to-end
- Qwen 27B training (on DGX, managed separately)
- AGI self-improvement loop (continuous)
- 5-repo integration: hermeshub, superpowers, obsidian-skills, paperclip-adapter, yantrikdb — all operational May 17 2026

## Hermes Configuration (May 17 2026)
- **Version**: v0.13.0 (config v23)
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
