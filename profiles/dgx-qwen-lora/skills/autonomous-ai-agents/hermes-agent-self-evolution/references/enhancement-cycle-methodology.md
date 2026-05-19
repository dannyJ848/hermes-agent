# Enhancement Cycle Methodology

Session: 2026-05-09 — Hermes cognitive apparatus v2.1 enhancement

## What Triggered This

User said: "keep enhancing, when you've gone through enough compression I start a new cli and restart, but until then, keep running audits and enhancements"

## The Method (5 Phases)

### Phase 1: Audit
Always start with measurement. Count everything:
- Subconscious modules: 530 total, 485 orphaned (91% dead code)
- Custom tools: 46 built, 1 registered (98% invisible)
- Databases: 42 files, 32 empty ghosts (0.0MB)
- Plugins: 38 total, 32 enabled, 6 dormant
- Tips: 1902 distilled, quality unknown

### Phase 2: Cleanup
Surgical removal of dead weight:
- Archive 453 orphaned modules → `~/subconscious/archive/`
- Delete 12 empty databases
- Register 10 high-value tools with `@register_tool`
- Enable 3 dormant plugins (honcho, mesh, sandbox)

### Phase 3: Quality Systems
Build measurement into the pipeline:
- `tip_survival` table — track opportunities vs applications
- Auto-prune: mark tips <30% survival after 100+ ops
- Adversarial validation — red-team tips with DeepSeek V4 Pro
- Predictive routing — route around weak tools

### Phase 4: Advanced Cognition
- Project clustering — auto-detect domains, map sessions
- Prompt fragment Elo — A/B test system prompt components
- Error pattern prediction — pre-empt known failures
- Token efficiency tracking — optimize for outcomes per token

### Phase 5: Self-Monitoring
- Health daemon (cron every 5 min) — tip health, tool degradation, DB size
- Rapid learning extraction — lessons from every session
- Auto-skill pipeline — queue high-quality docs for SKILL.md generation
- Enhancement effectiveness — track each cycle's impact

## Key Files Created

| File | Purpose |
|------|---------|
| `~/subconscious/hermes_harness_v2.py` | Unified status dashboard |
| `~/subconscious/predictive_router.py` | Tool routing by success rate |
| `~/subconscious/error_guard.py` | Pre-emptive error prevention |
| `~/subconscious/hermes_health_daemon.py` | Cron health monitor |
| `~/subconscious/tool_router_v2.py` | Smart tool dispatch |
| `~/qwen-training-data/` | Exported corpus for Qwen fine-tuning |

## Tables Created in cerebrum_memory.db

- `tip_survival` — opportunity/application tracking
- `tip_adversarial` — adversarial validation results
- `tip_quality_dashboard` — unified quality view
- `projects` — project clustering
- `project_memories` — memory-to-project links
- `project_sessions` — session tracking
- `session_project_map` — auto-assignment
- `prompt_fragments` — prompt component Elo
- `auto_skill_pipeline` — skill generation queue
- `rapid_learnings` — session lesson extraction
- `error_patterns_predictive` — known failure modes
- `token_efficiency` — compression tracking
- `enhancement_effectiveness` — cycle impact measurement

## Known Weak Tools (from 2057 calls)

| Tool | Success Rate | Issue | Alternative |
|------|-------------|-------|-------------|
| `cronjob` | 13% | id field confusion | `terminal` with crontab syntax |
| `delegate_parallel` | 33% | frequent failure (3x) | `delegate_task` sequential |
| `patch` | 94% | old_string mismatch | `write_file` for full replacement |

## Proven Tool Combos

- `web_search` → `web_extract` for research
- `execute_code` → `write_file` for bulk operations
- `read_file` → `patch` for surgical edits (verify text first)
- `search_files` → `read_file` for discovery

## Cost of This Session

- Duration: ~2 hours
- Tool calls: 2057+
- Dead code archived: 453 modules
- New cognitive systems: 13 active
- Training data exported: 1.8MB (1884 tips + 1965 patterns)

## What Made This Effective

1. **Audit before action** — measured everything first
2. **Surgical precision** — kill all, re-enable selectively (user's style)
3. **Self-monitoring** — every system tracks its own effectiveness
4. **Predictive routing** — don't dispatch tools known to fail
5. **Continuous loops** — health daemon, rapid learning, auto-skill all run autonomously
