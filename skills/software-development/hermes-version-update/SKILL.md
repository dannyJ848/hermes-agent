---
name: hermes-version-update
description: Safe Hermes Agent version update with patch preservation, breakage analysis, and process restart.
version: 2.0
---

# Hermes Agent Version Update

## When to Use
Updating Hermes Agent when behind on upstream commits. Involves preserving custom patches, pulling, resolving conflicts, and restarting.

## Current Local Patches (as of Apr 2026, v0.8.0+)

These files have local modifications that must survive the pull:

1. **run_agent.py** — post_tool_call hooks (2 locations) + greeting strip + greeting break
   - Two `post_tool_call` invoke_hook blocks (~15 lines each) at tool completion points
   - Post-compression greeting strip after context_compressor.compress() (~20 lines)
   - Greeting break in tool loop (~25 lines) — stops autonomous work on throwaway greetings
   - **CONFLICT PATTERN**: Upstream v0.8 replaced `_save_oversized_tool_result` with `maybe_persist_tool_result` (from `tools.tool_result_storage`). Both our hooks AND the upstream function must be kept — our hook first, then upstream's function. The `_save_oversized_tool_result` call must be dropped entirely.

2. **cli.py** — Restore-context injection (~14 lines at ~line 6310)
   - Injects `~/.hermes/.restore-context.txt` into first message after restart
   - Also shows restart marker warning banner on CLI startup
   - Auto-merges cleanly (additive insertion in stable location)

3. **gateway/run.py** — Distillation recall + Agent Mesh context injection (~100 lines at ~line 2340)
   - Distillation recall disabled (comment block, now handled by plugin)
   - Injects Agent Mesh coordination context (active agents, locks, messages)
   - Restart marker checkpoint injection for gateway sessions
   - All wrapped in try/except (non-fatal failures)
   - Auto-merges cleanly (additive insertion in stable location)

4. **agent/context_compressor.py** — Throwaway greeting detection (~20 lines)
   - `_THROWAWAY_PATTERNS` regex and `_is_throwaway_greeting()` function
   - No upstream changes expected (isolated file, rarely touched upstream)

5. **plugins/distillation/** — Custom bidirectional distillation plugin
   - `__init__.py` (~52KB): post_tool_call + pre_llm_call + post_api_request hooks
   - `plugin.yaml`: declares `provides_hooks` (NOT `hooks`)
   - `register()` function: Uses backward-compat pattern (`isinstance(ctx, dict)` check) to support both old dict API and new PluginContext API (v0.20+)
   - No upstream changes (custom plugin, not in upstream repo)

## Update Procedure

### Step 1: Audit Local Modifications
```bash
cd ~/hermes-agent
git status --short          # See what's dirty
git diff --name-only        # Tracked modified files
git stash list              # Any existing stashes
```

### Step 2: Save Backups (belt and suspenders)
```bash
# Save patches of local commits (includes commit message + metadata)
mkdir -p ~/dgx-spark-prep/hermes-local-patches/
git format-patch -1 <LOCAL_COMMIT_HASH> -o ~/dgx-spark-prep/hermes-local-patches/

# Save full diff of all local changes vs merge base
MERGE_BASE=$(git merge-base HEAD origin/main)
git diff $MERGE_BASE..HEAD > ~/dgx-spark-prep/hermes-local-patches/all-local-changes.patch

# Save full files (for manual re-apply if stash conflicts)
cp agent/prompt_builder.py /tmp/pb_backup.py

# Save entire custom plugin directories
cp -r plugins/distillation /tmp/distillation-backup
```

### Step 3: Nuke Garbage Staged Files
```bash
# SAFETY_NET/ or other bulk checkpoint dirs block the merge
git rm -r --cached SAFETY_NET/ 2>/dev/null
rm -rf SAFETY_NET/
```

### Step 4: Stash Targeted Files and Pull
```bash
# Stash ONLY our modified files (not untracked garbage)
git stash push -m 'pre-update-$(date +%Y%m%d)' -- cli.py gateway/run.py plugins/distillation/

# Pull upstream
git pull origin main

# If fast-forward: stash pop usually works clean
# If merge required: check for conflicts
git stash pop
```

### Step 5: Handle Conflicts (if any)
```bash
# Check which files conflicted
git diff --name-only --diff-filter=U

# For each conflicted file, manually re-apply from backups:
# Open the file, find conflict markers, resolve by keeping both upstream + local changes
# Our patches are small and targeted — they usually auto-merge fine
```

### Step 6: Reinstall Dependencies
```bash
# CRITICAL: Use the venv Python, NOT system python3
# System python3 is likely ancient anaconda that can't satisfy new deps
~/hermes-agent/venv/bin/python3 -m pip install -e '.[all]' --quiet
```

### Step 7: Clear Caches and Restart
```bash
# Clear all stale __pycache__ (causes silent plugin loading failures)
find ~/hermes-agent -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
find ~/.hermes/plugins -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null

# Restart gateway
hermes gateway restart
```

### Step 8: Verify Everything Loaded
```bash
# Check gateway is alive
hermes logs --lines 50 | grep -E 'plugin|hook|ERROR|WARNING'

# Must see these lines:
# "Distillation plugin: post_tool_call hook registered"
# "Distillation plugin: pre_llm_call hook registered"
# "Mesh plugin: all 4 tools registered successfully"
# "Plugin discovery complete: N found, M enabled"

# Check our patches survived
grep -c 'restore-context' cli.py          # Should be 1
grep -c 'Distillation recall' gateway/run.py  # Should be 2
grep -c 'Agent Mesh' gateway/run.py           # Should be 2
```

## Post-Update Feature Audit (Systematic)

After updating, systematically evaluate new features for integration potential:

### Step 1: Get the Full Diff
```bash
cd ~/hermes-agent
git log --oneline HEAD..origin/main | wc -l              # count commits
git log --oneline HEAD..origin/main --grep="feat"          # new features
git log --oneline HEAD..origin/main --grep="fix" | head -30 # key fixes
git diff --name-status HEAD..origin/main | grep "^A" | grep "\.py$"  # new files
```

### Step 2: Filter for Training/Learning Relevance
```bash
# Search for RL, training, memory, agent-improvement related commits
git log --oneline HEAD..origin/main | grep -iE "rl|training|learning|distill|reward|trajectory|memory|tip|skill"
# Search for new tools/MCP/delegation
git log --oneline HEAD..origin/main | grep -iE "tool|toolset|mcp|delegat|subagent|sandbox"
# Search for new plugin infrastructure
git log --oneline HEAD..origin/main | grep -iE "plugin|hook|provider"
```

### Step 3: Read New Files That Matter
```bash
# New Python files are the highest-signal -- read their docstrings
for f in $(git diff --name-status HEAD~262..HEAD | grep "^A" | grep "\.py$" | awk '{print $2}'); do
  echo "=== $f ===" && head -30 "$f" 2>/dev/null
done
```

### Step 4: Tier by Impact
- **TIER S (Game Changer)**: New subsystems that fundamentally change capability (e.g., new memory providers, new plugin types)
- **TIER A (High Value)**: New tools/classifiers that can be wired into existing workflows
- **TIER B (Useful)**: Bug fixes, performance improvements, config options
- **TIER C (Skip)**: Platform adapters, UI changes, docs

### Step 5: Check Infrastructure Integration Points
1. New skills: `ls ~/hermes-agent/skills/`
2. New providers needing API keys: `git diff HEAD~N .env.example`
3. New plugin hooks: grep for `register_hook\|provides_hooks` in new code
4. New memory providers: `ls plugins/memory/`
5. Config changes: `hermes_cli/config.py` for new DEFAULT_CONFIG keys

### Step 6: Identify Gaps
After evaluating what's new, ask: what DON'T we have that would help?
- Are any new features built but not configured?
- Are any new hooks not wired to our plugins?
- Do new features need local models/APIs we already have?

## Hook Compatibility Audit (Post-Update)

After pulling and resolving conflicts, **systematically verify hook signatures haven't changed** in ways that break our plugins:

### Step 1: Find All Hook Invocation Sites
```bash
# Find where each hook is invoked in the core code
cd ~/hermes-agent
grep -rn 'invoke_hook.*pre_llm_call' run_agent.py
grep -rn 'invoke_hook.*post_tool_call' run_agent.py
grep -rn 'invoke_hook.*pre_tool_call' run_agent.py
```

### Step 2: Check New kwargs
For each invocation site, check if new keyword args were added:
```bash
# e.g., check pre_llm_call invocation for new params like sender_id
sed -n '<start>,<end>p' run_agent.py  # view the invocation block
```

Compare against our plugin's hook function signatures:
```bash
grep 'def _on_pre_llm_call\|def _on_post_tool_call' ~/.hermes/plugins/distillation/__init__.py
```

**Key rule**: If our plugin uses `**kwargs`, new upstream kwargs are safely absorbed. If we use explicit positional args, new upstream kwargs may cause TypeError.

### Step 3: Syntax Check the Plugin
```bash
cd ~/.hermes/plugins/distillation
python3 -c 'import py_compile; py_compile.compile("__init__.py", doraise=True)'
```

### Step 4: Check Context Compressor Integration
```bash
# Verify our throwaway greeting patches survived the merge
grep -c '_THROWAWAY_PATTERNS\|_is_throwaway_greeting' agent/context_compressor.py
```

### Recent Findings (Apr 2026, 70-commit update)
- `pre_llm_call` gained `sender_id` kwarg — safe because our plugin uses `**kwargs`
- `post_tool_call` signature unchanged — same `tool_name, args, result, task_id, session_id`
- New `ContextEngine` ABC at `agent/context_engine.py` — base class for pluggable context compression
- New `register_context_engine()` on PluginContext — only one engine allowed
- New `gateway/restart.py` — shared restart constants with drain timeout
- Delegate tool now supports `delegation.reasoning_effort` config for child agent reasoning level
- Process registry has `watch_patterns` — background processes can trigger notifications on output patterns
- Auxiliary client hardened — response shape validation + api_mode honor

## Hard-Reset Strategy (100+ commits behind, few local patches)

When 50+ commits behind and local changes are small (a few files), the cleanest approach
is hard reset to upstream, then re-apply local patches on top. Stash/rebase causes cascading
conflicts across dozens of upstream commits — not worth it for 2-3 patched files.

```bash
cd ~/hermes-agent
git fetch origin
git log --oneline HEAD..origin/main | wc -l    # count incoming commits

# === Step 1: BACKUP ALL PATCHED FILES BEFORE TOUCHING ANYTHING ===
cp agent/prompt_builder.py /tmp/pb_backup.py
cp run_agent.py /tmp/run_agent_backup.py
cp -r plugins/context_engine/hindsight /tmp/hindsight_backup/
# Also save the full diff for reference
git diff HEAD -- agent/prompt_builder.py run_agent.py > /tmp/our_patches.diff

# === Step 2: Identify which upstream files overlap with ours ===
git log --oneline HEAD..origin/main -- agent/prompt_builder.py | wc -l
git log --oneline HEAD..origin/main -- run_agent.py | wc -l
# If run_agent.py has 20+ upstream commits, stash will DEFINITELY conflict.
# Hard reset is the only sane path.

# === Step 3: Hard reset to upstream ===
git reset --hard origin/main
# WARNING: This blows away uncommitted changes in tracked files!
# Untracked dirs like plugins/context_engine/hindsight/ may survive as empty dirs
# but their CONTENT is gone — restore from /tmp/ backup in step 5.

# === Step 4: Verify we're on upstream ===
git log --oneline HEAD..origin/main | wc -l   # Should be 0

# === Step 5: Re-apply local patches on top ===
# Do NOT use terminal() inline Python for string manipulation — shell quoting breaks.
# Instead, write a /tmp/ script:
#   content = open('agent/prompt_builder.py').read()
#   content = content.replace(OLD, NEW, 1)
#   open('agent/prompt_builder.py', 'w').write(content)
# For full files, just cp from backup:
mkdir -p plugins/context_engine/hindsight
cp /tmp/hindsight_backup/__init__.py plugins/context_engine/hindsight/__init__.py

# === Step 6: Syntax check everything ===
source venv/bin/activate
python3 -c 'import ast; ast.parse(open("agent/prompt_builder.py").read()); ast.parse(open("run_agent.py").read()); print("OK")'

# === Step 7: Import check (with venv!) — ALSO catches plugin API breakage ===
source venv/bin/activate
rm -rf ~/.hermes/plugins/*/__pycache__
python3 -c 'from run_agent import AIAgent' 2>&1 | grep -i "failed\|error\|PluginContext"
# CRITICAL: Look for "Failed to load plugin" lines — they mean register() API broke

# === Step 8: Verify local patches ===
grep -c "HERMES_LOAD_AGENTS_MD\|_build_keepalive" agent/prompt_builder.py  # Should be 1+
test -f plugins/context_engine/hindsight/__init__.py && echo "Hindsight OK"
grep -c "compare_digest" hermes_cli/web_server.py  # security patches

# === Step 8: Commit local patches on top ===
git add agent/prompt_builder.py plugins/context_engine/hindsight/__init__.py
git commit -m 'feat: local patches re-applied on upstream'
```

KEY GOTCHAS:
- **Shell quoting**: NEVER try to do Python string replacement via terminal() inline commands.
  The triple-quoted strings, backslashes, and quotes create bash syntax errors. Write a Python
  script to /tmp/ and run `python3 /tmp/apply_patches.py` instead.
- **Untracked custom dirs survive reset as EMPTY dirs**: `git reset --hard` cleans tracked
  files but leaves untracked directory shells. Your custom `plugins/context_engine/hindsight/`
  will exist as an empty dir — you must `cp` the files back in manually.
- **~/.hermes/plugins/ is untouchable**: User plugins in `~/.hermes/plugins/distillation/`
  are NOT in the hermes-agent repo at all. Git operations on ~/hermes-agent/ never affect them.
  Only ~/hermes-agent/plugins/ (upstream) directory is affected by git reset.

## Post-Update Verification (Essential Steps)

### Step 1: Config Migration
```bash
# After merging, check for config version changes
hermes doctor 2>&1 | grep "Config version"
# If outdated, auto-fix:
hermes doctor --fix
```

Config migrations are common — v17→v19 added new settings. Running `hermes doctor --fix`
is safer than manual config editing.

### Step 2: Overlap Analysis (Before Merging)
```bash
# Check if upstream touched the same files as our local patches
git log --oneline HEAD..origin/main -- agent/prompt_builder.py  # our patched files
git log --oneline HEAD..origin/main -- plugins/context_engine/hindsight/
# If 0 overlap: merge will be clean. If >0: check diff for conflicts.
git diff HEAD..origin/main -- agent/prompt_builder.py | head -40
```

This lets you predict conflicts BEFORE merging and decide between stash, rebase,
or hard-reset approach.

### Step 3: Verify Critical Upstream Fixes
After merging, grep for specific fixes to confirm they landed:
```bash
# Context bursting fix (cooldown guard):
grep -c "summary_failure_cooldown_until" agent/context_compressor.py  # Should be >0

# Cloudflare 403 Codex fix:
grep -l "CF-Connecting\|cloudflare" agent/auxiliary_client.py tools/*.py 2>/dev/null

# Thinking block stripping:
grep -c "stripped all thinking blocks" run_agent.py  # Should be >0

# Per-provider timeout config:
grep -c "request_timeout" hermes_cli/timeouts.py  # Should be >0
```

### Step 4: Verify Local Patches Survived
```bash
# AGENTS.md env gate:
grep -c "HERMES_LOAD_AGENTS_MD" agent/prompt_builder.py  # Should be 1+

# Hindsight context engine:
test -f plugins/context_engine/hindsight/__init__.py && echo "OK"

# Syntax check:
source venv/bin/activate
python3 -m py_compile run_agent.py agent/prompt_builder.py && echo "syntax OK"
```

## Pre-merge Local Commit Audit

Before choosing merge vs rebase vs hard-reset, audit what local commits actually exist:

```bash
cd ~/hermes-agent
git fetch origin

# See what commits we have that upstream doesn't
git log --oneline origin/main..HEAD

# Categorize local commits:
# - Daily backup / cron commits (e.g., "daily-backup: 20260420...") -> harmless
# - Merge commits ("Merge remote-tracking branch 'origin/main'") -> harmless
# - Real patches ("feat: ...", "fix: ...", "local: ...") -> MUST preserve
```

**Decision matrix**:
- **Mostly backups + 1 real patch** -> `git merge origin/main` (preserves cron history, single merge commit)
- **Many real patches with upstream overlap** -> `git stash && git merge && git stash pop` or hard-reset + re-apply
- **100+ commits behind, few local patches** -> hard-reset strategy (see below)
- **Working tree dirty with real changes** -> stash first, then merge

## Fast-Path Merge (1-2 local commits, clean tree)

When local has only diverged by 1-2 autocommits (e.g., daily backup) and working tree is clean:

```bash
cd ~/hermes-agent
git fetch origin
git log --oneline HEAD..origin/main | wc -l    # count incoming commits

# If working tree is clean (no unstaged changes), merge directly:
git merge origin/main --no-edit

# Verify with grep counts (faster than Python import checks):
grep -c "_build_keepalive_httpx_client\|_force_close_tcp_sockets" run_agent.py  # TCP patches
test -f plugins/context_engine/hindsight/__init__.py && echo "Hindsight OK"
grep -c "compare_digest" hermes_cli/web_server.py                                # security
source venv/bin/activate
python3 -m py_compile run_agent.py && echo "syntax OK"
```

This avoids the stash/pop dance entirely. Only use the full stash procedure above when there are unstaged modifications.

## Key Pitfalls

- **System Python vs venv Python**: `which python3` returns anaconda 3.8.8 on this machine. ALWAYS use `~/hermes-agent/venv/bin/python3` for hermes operations. The `hermes` CLI binary already points to venv via its shebang.
- **Stale __pycache__**: After ANY code change + restart, clear __pycache__. The gateway uses importlib which can load stale .pyc files, causing plugins to silently fail.
- **SAFETY_NET/ blocks merge**: If there are hundreds of staged checkpoint files, `git stash` won't include them (they're added not modified). Delete them before pulling.
- **plugin.yaml uses `provides_hooks`**: NOT `hooks`. The gateway only recognizes `provides_hooks`.
- **Fast-forward merges are safest**: If `git pull` says "fast-forward", stash pop will almost always succeed.
- **X/Twitter content**: Use `https://api.vxtwitter.com/{user}/status/{id}` (zero-auth, returns JSON with `text`, `media`, `user_name`) to fetch tweet text when web_extract fails on X (JS-rendered). Alternative: `https://api.fxtwitter.com/{user}/status/{id}`.
- **Non-interactive rebase continue**: `git rebase --continue` opens an editor. Use `GIT_EDITOR=true git rebase --continue` to skip the editor. Without this, the command times out waiting for editor input.
- **Rebase vs merge for divergent branches**: When local has custom commits diverged from main, `git pull --rebase origin main` or `git rebase origin/main` replays local commits ON TOP of upstream. Conflicts appear one at a time — resolve, `git add`, `git rebase --continue`. Cleaner than merge commits. Confirmed working for 483 commits in Apr 2026.
- **Plugin register() API changed (v0.20+)**: Upstream replaced the dict-based `register(hook_registry: dict)` with PluginContext object: `register(ctx)` where `ctx` is a PluginContext instance with `register_hook()` and `register_tool()` methods. Old dict-style `ctx["hook_name"] = callback` now fails with "PluginContext object does not support item assignment". FIX: Use backward-compat pattern in every plugin's register():
  ```python
  def register(ctx) -> None:
      if isinstance(ctx, dict):
          # Legacy dict-based registration (older hermes-agent)
          ctx["post_tool_call"] = _on_post_tool_call
      else:
          # New PluginContext-based registration (v0.20+)
          ctx.register_hook("post_tool_call", _on_post_tool_call)
  ```
  After any upstream pull, do `source venv/bin/activate && python3 -c "from run_agent import AIAgent"` and check for "Failed to load plugin" warnings.
- **Plugin API breakage is SILENT**: When a plugin fails to load (e.g., register() TypeError), the agent still starts. The only sign is a warning line in the output. Always scan for "Failed to load plugin" after pulling upstream.
- **cli.py conflict pattern (tips + restart marker)**: Upstream adds random tip display, we added restart marker detection. Both are additive insertions at different locations. Resolution: keep BOTH blocks — upstream tips first, then our restart marker. They don't interfere.
- **run_agent.py conflict pattern**: When upstream changes the tool result handling code (e.g., _save_oversized → maybe_persist), our post_tool_call hook will conflict. Resolution: keep BOTH — our invoke_hook block first, then the upstream function call. Drop the old function call that upstream replaced.
- **DB paths are in ~/subconscious/**, NOT in the plugin directory. The distillation plugin uses `~/subconscious/skill_rewards.db`, `~/subconscious/tool_capability.db`, `~/subconscious/api_analytics.db`, etc. Don't accidentally create empty DBs in the plugin dir by running sqlite3 against wrong paths.
- **Ghost submodules (gitlink without .gitmodules entry)**: If `git status` shows `modified: some/path (modified content)` and the path has its own `.git/` directory but is NOT in `.gitmodules`, it's a nested repo without proper submodule registration. Git tracks it as a gitlink but doesn't manage it as a submodule. Fix: `cd` into the nested repo, commit changes there, then `git add the/path` from the main repo to update the gitlink pointer. The nested repo's changes are invisible to the outer repo's diff.
- **New CLI session needed**: After updating run_agent.py and restarting gateway, existing CLI sessions still use the OLD code. Start a new `hermes` CLI to activate v0.8 in interactive mode. Gateway uses new code immediately.

## Notable Upstream Features (latest, Apr 2026)

### New Since v0.8.1+70 (Apr 12, 2026)
- **Skill Loading 20% More Aggressive (#8286)**: System prompt now says skills encode "user's preferred approach, conventions, and quality standards" — load even for tasks agent already knows how to do. Previously only loaded when skill "clearly matched."
- **69 New Hidden-Gem Tips (#8237)**: 279 total platform tips. Tips shown on session start via `get_random_tip()`.
- **`/compress <focus>` (#8017)**: Guided compression with a focus topic — preserves context relevant to the focus.
- **`/model` Picker (#8224/fix)**: Native modal for provider→model selection mid-session. Fixed external credentials not appearing.
- **`hermes backup`/`import` (#7997)**: Snapshot and restore Hermes state for migration or backup.
- **Gateway Restart with Graceful Drain**: Built-in drain/reload in core. `GATEWAY_SERVICE_RESTART_EXIT_CODE=75`.
- **Xiaomi MiMo Provider**: Native support for MiMo models.
- **Duplicate Update Prompt Spam Fix (#8343)**: Prevents repeated update notifications.
- **Empty Model Config Fallback (#8303)**: Falls back to provider's default model when model config is empty.
- **Session Auto-Reset Fix (#8299)**: Prevents unwanted session reset after graceful gateway restart.
- **Compression Task Logging Fix**: title_generator no longer logs as 'compression' task.
- **Codex Token Refresh (#8277)**: Writes refreshed Codex tokens back to `~/.codex/auth.json`.
- **Gateway Model Switch (#8276)**: Evicts cached agent on `/model` switch + diagnostic logging.

### New Since v0.8.0+70 (Apr 11, 2026)
- **ContextEngine ABC** (`agent/context_engine.py`): Pluggable context compression via plugins. `register_context_engine()` on PluginContext. Config-driven: `context.engine` in config.yaml. Only one engine active. Opportunity: build HindsightContextEngine that uses knowledge graph for smarter compaction.
- **Watch Patterns** (`tools/process_registry.py`): Background processes can trigger agent notifications when output matches patterns. Rate-limited (8 per 10s window). Overload protection disables after 45s sustained. Useful for training gym output monitoring.
- **Delegate Reasoning Config**: `delegation.reasoning_effort` in config controls child agent reasoning depth. Overrides parent level.
- **Gateway Restart with Drain** (`gateway/restart.py`): Graceful drain/reload with configurable timeout. `GATEWAY_SERVICE_RESTART_EXIT_CODE=75` asks systemd to restart. `restart_drain_timeout` in config.
- **Auxiliary Client Hardened**: Response shape validation. `api_mode` honored for any API-key provider. Fewer silent auth failures.
- **MiniMax Provider Fixed**: Aligned with official API docs. Fixed incorrect Anthropic OAuth detection (was causing `mcp_` tool prefix).
- **Matrix Adapter Rewritten**: mautrix-python replaces matrix-nio.
- **Vision Tool Fixes**: Reject oversized images. Handle `file://` URIs.
- **sender_id in pre_llm_call**: New kwarg passed to pre_llm_call hooks. Backward compatible if plugin uses `**kwargs`.

### New Since v0.8.0 Base
- **Hindsight Memory Provider** (plugins/memory/hindsight/): Full knowledge graph with entity resolution + multi-strategy retrieval. Supports cloud, local embedded (can use local llama.cpp as LLM backend), and local external modes. GAME CHANGER for training memory.
- **Error Classifier** (agent/error_classifier.py): Structured FailoverReason enum taxonomy (auth, billing, rate_limit, overloaded, context_overflow, timeout, etc). Centralized smart failover/recovery.
- **Rate Limit Tracker** (agent/rate_limit_tracker.py): Parses x-ratelimit-* headers, tracks RPM/TPM remaining, time until reset. Critical for autonomous loops.
- **AIAgent.close()**: Proper subprocess/zombie cleanup (child agents, background processes, browser sessions). Fixes delegate zombie leaks.
- **Context Compressor v2**: Token-budget tail protection, tool tracking in summaries, degradation warnings, named constants.
- **Delegate max_concurrent_children**: Configurable parallel delegation limits.
- **File Sync** (tools/environments/file_sync.py): Shared file sync for remote environments -- needed for VPS deployment.
- **Context Pressure Warnings**: Tiered at 85%/95% of compaction threshold, deduped across gateway sessions.
- **BlueBubbles iMessage Adapter**: Native iMessage via BlueBubbles.
- **WeChat/Weixin Adapter**: Native WeChat via iLink Bot API.
- **Discord channel_skill_bindings**: Auto-load skills per channel.
- **Fast Mode** (/fast): Priority processing for supported models.
- **xAI Native Provider**: Direct xAI/Grok access.
- **Gateway contextvars**: Session state moved from os.environ to contextvars for concurrency safety.

### From v0.8.0 Base (Retained)

- **Session Boundary Hooks**: `on_session_finalize` (CLI exit, /quit, /reset) and `on_session_reset` (/new, /reset). Plugins subscribe via `ctx.register_hook()`. Gateway also fires these. Opportunity: distillation plugin could flush buffers on finalize.
- **`on_session_end` Hook**: Fires at end of every `run_conversation()`. Cleanup/flush opportunity.
- **`post_llm_call` Hook**: Fires once per turn after tool-calling loop completes. Gets conversation history.
- **Unified Spawn-Per-Call Execution**: All terminal backends (except ManagedModal) now spawn fresh bash per command with session snapshot. May change terminal behavior.
- **`maybe_persist_tool_result`**: Replaced `_save_oversized_tool_result`. Moved to `tools/tool_result_storage.py`. Accepts `content`, `tool_name`, `tool_use_id`, `env` params.
- **Live Model Switching** (`/model`): Mid-session model/provider switching across all platforms.
- **Google AI Studio (Gemini) Native Provider**: Direct Gemini access via AI Studio API.
- **Inactivity-Based Agent Timeouts**: Activity-based instead of wall-clock. Long-running active tasks never killed.
- **Approval Buttons**: Telegram and Slack get native approval buttons instead of /approve.
- **Self-Optimized GPT/Codex Tool-Use**: Agent auto-patched 5 failure modes in GPT/Codex tool calling.
- **Centralized Logging**: `hermes logs` CLI command, structured logs to `~/.hermes/logs/`.
- **MCP OAuth 2.1 PKCE**: Full OAuth for MCP server authentication.
- **Reasoning Effort Config-Only**: `HERMES_REASONING_EFFORT` env var removed — use `config.yaml` only.

**IMPORTANT**: Upstream v0.8 does NOT have `post_tool_call` — only `pre_api_request`, `post_api_request`, `post_llm_call`, `on_session_end`, `on_session_finalize`, `on_session_reset`. Our `post_tool_call` is entirely custom.
