======================================================================
HERMES MASTER DOCUMENT — v0.13.0 INTEGRATION COMPLETE
Updated: 2026-05-07 23:50 UTC
======================================================================

[SYSTEM STATE]
  Hermes Version: v0.13.0 (2026.5.7)
  Branch: qwen27b-training-artifacts-may3-2026
  Upstream: 0 commits behind (fully merged)
  Custom commits: 905 ahead
  Uncommitted changes: 0
  Python: 3.11.14

[TRAINING — DGX Spark]
  Model: Qwen 27B expert logician
  Rank: 256 LoRA (stable after 1024→768→640→512→384 all OOM'd)
  Step: ~600/10000
  Loss: ~2.27 (trending down)
  GPU: ~62.6GB / 130GB
  PID: 180722
  Status: RUNNING
  ETA: ~54 hours remaining (~2.3 days)
  Checkpoints: Every 100 steps (100, 200, 300, 400, 500, 600)
  Monitor: Remote cron every 5 min + local Mac cron every 5 min
  Auto-resume: Enabled (validates checkpoint, clears GPU, restarts)

[CUSTOM CODE — ALL PRESERVED]
  hermes_cli/subconscious/          24 modules (autobrowse R191 + support)
  plugins/learning-brain/           Plugin with guarded imports
  hermes_cli/instant_context.py     Single source of truth
  hermes_cli/context_updater.py     Context injection
  custom_dflash/                  Training scripts, DGX monitoring
  agent/cortex_access.py            CortexDB bridge
  agent/cortex_learning.py          Learning loop
  agent/error_learning.py           Error pattern learning
  agent/memory_learning.py          Memory optimization
  agent/predictive_tools.py         Tool prediction
  agent/self_improvement_daemon.py  Background improvement
  agent/adaptive_injection.py       Adaptive context injection
  agent/memory_bloat_monitor.py     Memory monitoring
  agent/curator_integration.py      Curator bridge
  agent/curator_backup.py           Curator backup

[INTEGRATION BRANCHES]
  qwen27b-training-artifacts-may3-2026  ← MAIN (v0.13.0 + custom)
  v0.13-integration                     ← Integration staging (pushed)

[KEY UPSTREAM FIXES NOW ACTIVE]
  ✓ Secret redaction ON by default
  ✓ Post-write delta lint (write_file + patch syntax check)
  ✓ no_agent cron watchdog mode
  ✓ SearXNG search backend
  ✓ Brave Search + DDGS providers
  ✓ MCP SSE transport + OAuth
  ✓ Gateway auto-resume after restart
  ✓ 7 i18n locales
  ✓ ProviderProfile ABC (pluggable providers)
  ✓ Kanban durable multi-agent board
  ✓ /goal persistent cross-turn goals
  ✓ Checkpoints v2 with real pruning
  ✓ video_analyze tool
  ✓ xAI Custom Voices

[TOOL INTELLIGENCE — ROUTE AROUND WEAK]
  ✓ web_search: 96% (316 calls)
  ✓ browser_console: 95% (100 calls)
  ✓ web_extract: 94% (204 calls)
  ✓ execute_code: 94% (752 calls)
  ✓ write_file: 87% (520 calls)
  ✗ AVOID skill_manage: 59% (479 calls) — pinned skills block patches
  ✗ AVOID cronjob: 13% (31 calls) — use terminal crontab instead

[ACTIVE MONITORS]
  DGX Remote: /data/SpecForge/custom_dflash/training_monitor.sh (cron every 5 min)
  DGX Local: /tmp/dgx_local_monitor.sh (Mac cron every 5 min)
  Log: /tmp/dgx_monitor.log

[RECENT ACHIEVEMENTS]
  May 7: v0.13.0 integration complete (441 upstream commits)
  May 7: Autobrowse injector built (real-time tip feedback)
  May 7: Loop guard v2 deployed (intent-based detection)
  May 6: LLM Judge wired into learning-brain (deepseek-v4-pro)
  May 4: Distillation D:0.000→1.215 (5 tokenizer/format fixes)
  May 3: Training rank 256 first stable config (after 5 OOM attempts)

[IMMEDIATE NEXT STEPS]
  1. Monitor training to step 1000 (checkpoint validation)
  2. Evaluate loss curve at step 1000
  3. Consider rank increase if GPU headroom allows
  4. Run autobrowse injector regularly for self-improvement tips

[LONG-TERM GOALS]
  - Complete 10,000 step training run
  - Evaluate on reasoning benchmarks (GSM8K, MMLU)
  - Export LoRA weights for inference
  - Build inference pipeline with vLLM

======================================================================
