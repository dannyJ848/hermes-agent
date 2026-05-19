# USER.md — User Profile

## Identity
- Name: Danny
- Role: Medical student
- Handle: 42-evey (GitHub), The Curator (content persona)

## Communication Style
- Values quick iteration over polished deliverables
- Treats projects as capability experiments — will pivot abruptly
- Expects proactive maintenance without being asked
- Working state loss is traumatic — always capture before fixing
- Expects comprehensive session checkpoints with full context (file paths, commands tried, failures, clear next steps)
- Says "stop" = immediate halt
- Says "cycled it" = power-cycled the machine — stop all SSH attempts, wait for boot
- Says "hmmm" = deliberating/evaluating, not frustration
- Prefers marking tasks pending over forcing completion when blocked
- Explicitly rejects autonomous agents running without permission (May 17, 2026)
- Explicitly rejects systemd daemons — use screen/tmux only for persistent processes

## Work Patterns
- Thoroughness over speed when requested ("run all benchmarks, i dont care how long it takes")
- Expects persistence layers updated without being asked
- Wants daily autonomous cognitive apparatus optimization
- Treats infrastructure as experiments — quick iteration, may abandon

## Critical Infrastructure (DO NOT TOUCH WITHOUT EXPLICIT PERMISSION)
- **Kimi model config**: `~/.hermes/config.yaml` — provider `kimi-coding`, model `kimi-for-coding`
  - CRITICAL: model name must match across `default.model`, `providers.kimi-coding.models`, and `fallback_model.model`
  - Previous drift caused hours of recovery (May 16 2026)
- **DGX vLLM**: Another CLI is managing this — DO NOT interfere

## Environment
- MacBook (local) + DGX Spark (spark-85e8.local, user djg6228)
- DGX has 8TB external SSD at /mnt/bigssd for datasets
- DGX runs Hermes gateway + distillation daemon (managed separately)
- Full capabilities: local write, MacBook SSH+write, web access, browser automation, Git, Docker

## Active Projects
- The Lens (propaganda demystification engine) — built, tested end-to-end
- Qwen 27B training (on DGX, managed separately)
- AGI self-improvement loop (continuous)
- 5-repo integration: hermeshub, superpowers, obsidian-skills, paperclip-adapter, yantrikdb — all operational May 17 2026

## Preferences
- Prefers concise terminal output over verbose markdown
- No attachment channel — state file paths in plain text
- Likes being surprised with funny voices for storytime moments (if TTS available)
- Screen/tmux only for persistent processes — no systemd daemons

## Hermes State (May 17 2026)
- **Skills**: 399 enabled (78 builtin, 321 local)
- **Plugins**: 41 enabled, 4 disabled
- **Memory**: yantrikdb provider active (~33K memories)
- **Profiles**: spark-quality, spark-speed, training-gym
- **Cron**: 43 jobs active
