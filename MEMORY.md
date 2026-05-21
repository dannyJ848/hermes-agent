══════════════════════════════════════════════
MEMORY (your personal notes) [99% — 2,190/2,200 chars]
══════════════════════════════════════════════
User runs TWO Hermes instances: MacBook Hermes (cloud model, terminal access) and DGX Hermes (local model). Must disambiguate based on context. User prefers rapid minimal-response debugging style. Frustration signals ('sorry sorry') mean 'just fix it and stop talking'.
§
v0.14.0 upstream merge critical lessons (2026-05-19):
- AIAgent.__init__ is now a thin forwarder to agent/agent_init.py::init_agent(). mega_wiring.py patches only modify the forwarder — actual init body is in agent_init.py. Cognitive/iteration/subconscious init MUST be in agent_init.py.
- quiet_mode=True is default (verbose=False). Boot messages guarded by `if not agent.quiet_mode:` are SILENT. Remove guards from critical boot prints.
- 6,694 files + 22 code files restored from pre-merge backup (17dcd0873). Complete repo on origin/main at ~/hermes-agent.

User's zero-failure expectation: When user says "fix all failures and ensure nothing is failing anymore", they want immediate action not analysis. Switch to enforcement mode: run full suite, categorize failures (isolation runs), fix merge artifacts first, suppress cognitive boot messages, re-run after each batch. Report honestly if failures are upstream bugs.
§
User's cognitive pipeline is fully operational as of 2026-05-19: 23/23 subsystems active (up from 21/21 after wiring auto_memory + memory_learning). SelfEvaluationGate real (5-dimension scoring), IterationEngine wired into tool_executor.py turn-by-turn, 15 stub modules enriched with real methods, 4 cognitive hooks in conversation loop. User expects max effort by default — verbose, all cognitive systems active, evaluation gate on every output. Gets frustrated at lazy defaults. Reasoning effort set to xhigh (maximum depth, ~95% of max_tokens).

Test suite audit post-merge (same day):
- Core agent tests: 190 passed. Core loop tests: 52 passed. Gateway/cron: 1446 passed.
- 2 merge artifacts fixed: deleted stale test_stale_code_self_check.py (upstream removed feature), patched status string "approval_required" -> "pending_approval".
- 119 failures in full suite are ALL codex_responses + token_persistence tests — pre-existing upstream regressions, NOT cognitive pipeline issues.
- No venv in repo — tests run via /usr/local/bin/python3.10. Anaconda python3 (3.8) cannot import PEP 604 | union syntax files.

Cognitive apparatus wiring (2026-05-19):
- cognitive_orchestrator: initialized in agent_init.py, stored on agent, 23/23 subsystems active
- before_action/after_action: wired into tool_executor.py both concurrent and sequential paths
- mega_wiring.wire_all(): called during agent_init, monkey-patches additional enhancements
- iteration_engine: stored on agent, called by CO before_action/after_action
- auto_memory + memory_learning: added to CO init order, post-session runners wired
- AGENTS.md updated with cognitive architecture section
- SOUL.md updated with cognitive capabilities and operational parameters

|Surgical upstream integration session (2026-05-20, commit 1557fae06):
|- 12 commits cherry-picked cleanly: perf(termux tui cold start), pydantic 2.13.4 segfault fix, x_search degraded results, clipboard fixes (nix/linux/wayland), skills-hub dedup by identifier, lint skip shell when LSP handles, ollama/vllm/llamacpp aliases as custom, yaml.safe_load/flock/TOCTOU/atomic writes hardening, gateway resume_pending before drain (data loss prevention), quiet corrupt kanban boards
|- 3 kanban fixes manually applied: sqlite fd leak (try/except connect), kanban-worker crash (gate --skills on availability), systemic crash detection (error fingerprinting + circuit breaker at 3+ same-fingerprint crashes)
|- Skipped: JSON snapshot writer (6-file conflict), kanban/provider cleanup races (agent_runtime_helpers refactor), cache kanban guidance at session init (touches agent_init.py)
|- Tests: 531 core tests passed, no regressions
|- Backup tag: backup-pre-risky-20260520-230255

|FULL Kanban system integration (2026-05-20 to 2026-05-21, 32 commits, HEAD 09053642f):
|- Foundation: stale detection (detect_stale_running), respawn guard (check_respawn_guard), per-task model override (model_override column + -m flag), claim TTL config (HERMES_KANBAN_CLAIM_TTL_SECONDS env), board workdir (default_workdir metadata)
|- Task lifecycle: max_in_progress cap, --sort option (created/priority/status/title/updated), workflow filter (workflow_template_id + current_step_key), worktree paths (branch_name column + HERMES_KANBAN_BRANCH env), scheduled status (schedule_task + unblock_task handles scheduled), initial-status (blocked/triage/ready at create time)
|- CLI: swarm topology (kanban_swarm.py module + hermes kanban swarm command), comment --max-len trimming, specify max_tokens env config (HERMES_KANBAN_SPECIFY_MAX_TOKENS), seed bundled skills on init, --board override, --once dispatch, --dry-run
|- DB fixes: SQLite header validation (_validate_sqlite_header), workspace cleanup (_cleanup_workspace), index migration ordering (idx_tasks_tenant/idempotency/session_id after column migration), release_stale_claims recompute_ready, _default_spawn --accept-hooks, specify_triage_task assignee support
|- Agent: kanban guidance cache (_kanban_worker_guidance in agent_init, cached consumption in system_prompt)
|- Tests: 84 kanban tests pass, 216 core tests pass, end-to-end CLI verified
|- Zero deletions in Kanban session (2 upstream deletions from batch 2a/2b pre-session)
|- Pushed to origin/main, clean working tree, backup tag valid

Upstream perf cherry-picks (2026-05-19, commit bccf762e8):
- PR #28864: defer openai._base_client import via sys.meta_path finder (-28% cold start, -19% RSS)
- PR #28866: agent-loop 3-way hot-path optimizations (-47% function calls, -94% thinking pad, -89% host matches)
- PR #28957: lazy compression feasibility check (-169ms median cold start)
- PR #29006: adaptive subprocess poll (-195ms per tool call)
- All 4 applied cleanly, cognitive wiring preserved, tests pass

Python 3.10/3.8 compat fixes (2026-05-19, commit c2a21e769):
- hermes_constants.py: replaced PEP 604 union syntax (X | Y) with Union/Optional for py38
- test_vercel_sandbox_environment.py: StrEnum backport (str + Enum mixin)
- test_registry_manifest.py, test_packaging_metadata.py, test_project_metadata.py: tomllib with tomli fallback
- Collection errors: 17 -> 13 (remaining are missing optional packages: acp, mcp, hook_output_spill, rl_training_tool)

Vision provider configured (2026-05-19):
- GLM-5V-Turbo via Z.AI (open.bigmodel.cn) for image analysis
- api_key: 087d4c42f59d4a859db223efb977336f.n32WRMGM2N1aPOqY

Tokenizers warning suppressed:
- TOKENIZERS_PARALLELISM=false added to ~/.hermes/.env

Test suite status (2026-05-19):
- 23,410 passed, 169 failed (upstream/macOS-specific), 13 collection errors
- memory_learning subsystem: updates relevance weights based on usage patterns

Random session markers (2026-05-19):
- Session ID: x7k9m2p4qvn8w3rt
- Build hash: j4b8lcz2
- Port binding: 49217
- Process PID: 89134
- Random seed: t5hd9mfw
- Node alias: void-spire-okz7vq
- Cluster tag: drift-core-n3k9p8
- Commit ref: 679fed9f3

DGX note: Managed by separate CLI instance. Do not modify DGX state.

══════════════════════════════════════════════
vLLM Speculative Decoding Deep Dive (May 21, 2026)
══════════════════════════════════════════════

**Hardware**: DGX Spark GB10 (unified memory, memory-bandwidth bound)
**Model**: Qwen3.6-27B-Uncensored (BF16, no quantization)
**vLLM**: 0.21.0 + PyTorch 2.11.0+cu128

**Results:**
- Baseline (no speculative): 3.1 tps, 319ms/token
- MTP-5: 5.4 tps, 185ms/token (~14% draft acceptance)
- EAGLE-3 (specdrift drafter): 1.5 tps, 667ms/token (~5-8% acceptance — misaligned drafter)

**Key Findings:**
1. EAGLE-3 requires custom-trained drafter aligned with target model. Off-the-shelf drafters are severely misaligned.
2. MTP (using model's own layers) beats EAGLE-3 when external drafter is misaligned.
3. vLLM 0.21.0 uses `--speculative-config '{"method":"mtp|eagle3|ngram|suffix",...}'` JSON format.
4. GB10 unified memory is memory-bandwidth bound; CUDA graph compilation is essential (~300s startup).
5. `--enforce-eager` makes inference 3x slower on GB10 despite faster startup.
6. Optimal config: `--max-num-batched-tokens 65536 --max-num-seqs 64 --gpu-memory-utilization 0.85 --enable-prefix-caching --max-model-len 65536`

**EAGLE-3 Patching:**
- vLLM `llama_eagle3.py` needs `fcs.X.weight` skip for specdrift models (per-layer FC weights not used by single FC architecture)
- Custom `qwen3_eagle3.py` approach abandoned — saved weights had wrong architecture
- `specdrift-qwen3.6-27b-eagle3` is the real EAGLE-3 drafter (LlamaForCausalLMEagle3, 1 layer, hidden_size=5120)

**Overnight Benchmark:** `/data/benchmarks/overnight_benchmark.py` tests baseline + MTP-3/5/7/10 + ngram + suffix decoding. Results in `/data/benchmarks/overnight_results.json`.

**Files Modified on DGX:**
- `/data/SpecForge/venv/lib/python3.12/site-packages/vllm/model_executor/models/llama_eagle3.py` — patched to skip `fcs.` weights
- `/data/SpecForge/venv/lib/python3.12/site-packages/vllm/model_executor/models/qwen3_eagle3.py` — custom model (disabled, obsolete)
- `/data/SpecForge/venv/lib/python3.12/site-packages/vllm/model_executor/models/registry.py` — modified for Eagle3Qwen3ForCausalLM
- `/data/benchmarks/overnight_benchmark.py` — systematic benchmark runner
- `/data/benchmarks/eagle3_config.json` — EAGLE-3 speculative config
