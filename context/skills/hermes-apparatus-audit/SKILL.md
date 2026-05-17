---
name: hermes-apparatus-audit
description: Comprehensive audit methodology for Hermes Agent's cognitive apparatus — plugins, subconscious modules, custom tools, databases, skills, knowledge, and hook wiring. Maps what's active vs orphaned, identifies integration gaps, and produces surgical upgrade plans.
version: 2.1.0
metadata:
  hermes:
    tags: [audit, infrastructure, cleanup, hermes-agent, self-improvement, wiring]
    related_skills: [infrastructure-boundary-management, infrastructure-surgical-management, plugin-integration-audit, hermes-source-surgical-integration]
---

# Hermes Apparatus Audit

Comprehensive audit of Hermes Agent's cognitive infrastructure. Maps every layer, identifies dead code, empty databases, orphaned tools, and **broken hook wiring**, then produces a surgical cleanup plan.

**Critical distinction:** Integration (files in right place) ≠ Wiring (actually connected to the agent loop). This audit checks both.

## When to Use

- User says "audit my system", "what's actually working", "clean up dead code"
- User asks "is everything wired and functional"
- Before major upgrades or plugin installations
- After bulk integration (e.g., moving subconscious → agent/)
- When system feels slow or bloated
- Periodic maintenance (monthly recommended)

## Audit Layers

### 1. Plugin Layer
```bash
hermes plugins list  # Check enabled vs disabled
```

**Target:** 80%+ active. Flag dormant high-value plugins (honcho, mesh, sandbox).

### 2. Cognitive Systems / Hook Wiring Layer
**THE MOST IMPORTANT CHECK.** Files can exist in `agent/` without being wired.

```python
# Check what hooks run_agent.py actually invokes
import re
content = open("~/hermes-agent/run_agent.py").read()
hook_invocations = set(re.findall(r'invoke_hook\(\s*"(\w+)"', content))
print(f"Hooks invoked: {hook_invocations}")

# Check for asymmetric hook pairs
has_pre_tool = 'pre_tool_call' in content
has_post_tool = 'post_tool_call' in content
if has_pre_tool and not has_post_tool:
    print("⚠️  ASYMMETRY: pre_tool_call exists but post_tool_call missing — tool outcomes not captured")

# Check what cognitive systems register
for mod in ["cognitive_infrastructure_hooks", "cortex_flywheel", "brain_to_toolintel",
            "agent_scorecard", "tool_misuse_prevention", "red_team_hippocampus",
            "memory_cortex_bridge", "hermes_enhancement_suite"]:
    path = Path(f"~/hermes-agent/agent/{mod}.py")
    if path.exists():
        mod_content = path.read_text()
        registers = "register" in mod_content.lower() or "hook" in mod_content.lower()
        print(f"{mod}: {'registers hooks' if registers else 'ORPHANED — no hook registration'}")
```

**Target:** 100% of cognitive modules either register hooks or are explicitly called by run_agent.py. Zero orphaned modules.

**Red flag:** Module exists in `agent/` but is never imported or called by `run_agent.py`.

**Red flag:** Asymmetric hook pairs — e.g., `pre_tool_call` without `post_tool_call`. This means tool outcomes are intercepted but never learned from. Common in systems where pre-hooks were added for guardrails but post-hooks were never wired for learning.

**FALSE POSITIVE CHECK:** Before reporting a hook as "missing", verify at THREE levels:
1. **Agent loop level:** `grep 'invoke_hook("HOOK_NAME"' ~/hermes-agent/run_agent.py` — does the main loop fire it?
2. **Tool dispatch level:** `grep 'invoke_hook("HOOK_NAME"' ~/hermes-agent/model_tools.py` — does the tool wrapper fire it?
3. **Plugin registration level:** `grep 'register_hook("HOOK_NAME"' ~/hermes-agent/plugins/*/__init__.py` — do plugins receive it?

A hook is ONLY truly missing if ALL three checks are absent. In the 2026-05-16 session, `post_tool_call` was reported missing by the audit but verification showed it was properly fired in `model_tools.py` (lines 773-786) and registered by 4+ plugins. The confusion arose because `run_agent.py` uses `cognitive_orchestrator.after_action()` for learning (a separate path), while `model_tools.py` uses `invoke_hook("post_tool_call")` for plugin notifications (the standard path). Both exist — the audit script only checked the cognitive orchestrator path.

**Lesson:** Always distinguish between:
- **Cognitive learning hooks** (`cognitive_orchestrator.before_action/after_action`) — for internal learning systems
- **Plugin notification hooks** (`invoke_hook("pre_tool_call"/"post_tool_call")`) — for external plugins
- They serve different purposes and may be wired through different code paths

**Unified Dispatcher Pattern (Cognitive Orchestrator):**
Instead of wiring each module individually (brittle), use a single `CognitiveOrchestrator` that manages all subsystems:

```python
# In run_agent.py __init__:
from agent.cognitive_orchestrator import get_orchestrator
self.cognitive_orchestrator = get_orchestrator()
self.cognitive_orchestrator.initialize(self)

# In before_action:
_cognitive_lessons = self.cognitive_orchestrator.before_action(action_type, detail)

# In after_action:
self.cognitive_orchestrator.after_action(action_type, detail, result, duration_ms)

# In session_end:
self.cognitive_orchestrator.session_end(telemetry)
```

The orchestrator initializes all subsystems in dependency order, routes lifecycle calls to each, and runs post-session processing in parallel. See `references/cognitive-orchestrator-pattern-2026-05.md` for full implementation.

### 3. Iteration Engine Layer
```python
# Check if iteration engine is connected to action lifecycle
content = open("~/hermes-agent/run_agent.py").read()
has_before = "before_action" in content
has_after = "after_action" in content
print(f"Iteration engine connected: {has_before and has_after}")
```

**Target:** `before_action()` called before every tool call, `after_action()` called after. Disconnected = no experiential learning.

### 4. Custom Tools Layer
```python
# Check ~/.hermes/tools/ for registry.register() calls
for f in Path("~/.hermes/tools").glob("*.py"):
    content = f.read_text()
    if "registry.register" in content:
        print(f"✅ {f.name} — registered")
    elif "def handler" in content or "def " in content:
        print(f"⚠️  {f.name} — has functions but may not be registered")
```

**Target:** 100% registered. Orphaned tools = wasted development effort.

### 5. Database Layer
```python
import os, sqlite3
for db in glob.glob(os.path.expanduser("~/.hermes/*.db")):
    size = os.path.getsize(db)
    try:
        conn = sqlite3.connect(db)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        rows = sum(conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0] for t in tables)
        conn.close()
        status = "✅" if rows > 0 else "⚠️  EMPTY"
        print(f"{status} {os.path.basename(db)}: {size} bytes, {len(tables)} tables, {rows} rows")
    except Exception as e:
        print(f"❌ {os.path.basename(db)}: CORRUPTED ({e})")
```

**Target:** 0 corrupted DBs. 0 empty ghosts (schema but no data). Meaningful DBs should have rows.

**CRITICAL: Verify each persistence layer independently.** Don't assume one success means all succeeded. When distilling session state across persistence layers, check:
1. **Memory capacity** — `SELECT COUNT(*) FROM messages` in LCM DB
2. **Knowledge base connectivity** — `knowledge_stats()` or direct SQLite query
3. **Skill file integrity** — `hermes skills list` output
4. **Goals sync** — `~/.hermes/GOALS.md` exists and current
5. **SOUL.md updates** — learned behaviors recorded with timestamps

A common failure mode: tips are written to `staging_tips` but the `distilled_tips` table (expected by the knowledge API) is missing or stale. Always verify the API-facing table, not just the staging table.

**Schema drift detection:** After any table rebuild or migration, verify ALL consumers still work:
```bash
# Find every file that queries the table
find ~/.hermes -name "*.py" | xargs grep -l "distilled_tips" 2>/dev/null

# For each file, check if its query columns match the actual schema
sqlite3 ~/.hermes/cerebrum_memory.db "PRAGMA table_info(distilled_tips)"
```

**Data loss check:** Compare current row count against backups:
```bash
for f in ~/.hermes/cerebrum_memory.db*backup*; do
    echo -n "$f: "
    sqlite3 "$f" "SELECT COUNT(*) FROM distilled_tips" 2>/dev/null || echo "N/A"
done
```

### 6. Skills Layer
```bash
hermes skills list  # Check for stale/unused skills
```

**Target:** Archive skills unused for 90+ days.

### 7. Knowledge Layer
```python
knowledge_dir = os.path.expanduser("~/.hermes/knowledge")
docs = glob.glob(f"{knowledge_dir}/*.md")
# Score by size, completeness, recency
```

**Target:** Index 100%, quality-score >0.5 for active docs.

### 8. External Directory Layer
```python
# After integration, verify no cognitive systems remain external
standalone_dirs = ["~/subconscious", "~/atropos", "~/training_gym", "~/cortex"]
for d in standalone_dirs:
    exists = os.path.exists(os.path.expanduser(d))
    print(f"{'⚠️  EXISTS' if exists else '✅ GONE'} {d}")
```

**Target:** All cognitive systems in `agent/` or `tools/`. Zero external standalone directories.

## Wiring Verification Checklist

Run this after any bulk integration:

| Check | Command | Expected |
|-------|---------|----------|
| No external path refs | `grep -rn "subconscious" --include=*.py ~/hermes-agent/agent/ \| grep -v "def \|class \|#"` | Zero filesystem path references |
| Hooks registered | `grep -rn "register.*hook\|invoke_hook\|pre_action\|post_action" --include=*.py ~/hermes-agent/agent/` | Every cognitive module registers or is called |
| run_agent.py imports | `grep "from agent\." ~/hermes-agent/run_agent.py` | All cognitive modules imported |
| DB health | `sqlite3 ~/.hermes/unified_context.db ".tables"` | Tables exist and have data |
| Process handles | `lsof +D ~/subconscious 2>/dev/null` | No open files to old paths |

## Cleanup Playbook

### Phase 1: Fix Wiring (critical)
```python
# 1. Update subconscious_plugin_loader to look in agent/ not root
# 2. Add hook registrations to each cognitive module
# 3. Wire iteration_engine.before_action()/after_action() into run_agent.py
# 4. Verify all modules are imported, not just present
```

### Phase 2: Archive (safe)
```bash
mkdir -p ~/.hermes/archive/orphaned_modules/
mv ~/hermes-agent/agent/orphaned_module.py ~/.hermes/archive/orphaned_modules/
```

### Phase 3: Delete (irreversible)
```bash
# Corrupted DBs — rebuild, don't just rm
sqlite3 ~/.hermes/cerebrum_memory.db ".dump" > /tmp/backup.sql 2>/dev/null || true
rm ~/.hermes/cerebrum_memory.db
# Rebuild from scratch or restore from backup

# Abandoned experiments
rm ~/hermes-agent/agent/R150*.py
```

### Phase 4: Register (high-value)
```python
# Add registry.register() to orphaned tools
# Update ~/.hermes/config.yaml tool section
```

### Phase 5: Enable (dormant plugins)
```bash
hermes plugins enable evey-honcho
hermes plugins enable evey-mesh
hermes plugins enable evey-sandbox
```

## Expected Results

| Layer | Before | After |
|-------|--------|-------|
| Plugins | 84% active | 95% active |
| Cognitive modules wired | 10% | 100% |
| Iteration engine connected | ❌ | ✅ |
| Tools | 2% registered | 100% registered |
| Databases | 24% utilized, some corrupted | 80% utilized, 0 corrupted |
| Skills | ~60% relevant | 90% relevant |
| External directories | 1+ | 0 |

## Cognitive Orchestrator Quick Start

When you find orphaned cognitive modules, the fastest fix is:

1. **Run the audit script** (see `references/cognitive-orchestrator-pattern-2026-05.md`):
   ```bash
   python3 ~/hermes-agent/agent/cognitive_systems_audit.py
   ```

2. **If orphaned modules found**, create `agent/cognitive_orchestrator.py` with:
   - `initialize(agent)` — init all subsystems in dependency order
   - `before_action(type, detail)` — collect lessons from all
   - `after_action(type, detail, result, duration_ms)` — learn from outcomes
   - `session_end(telemetry)` — run post-session in parallel

3. **Wire 4 integration points in run_agent.py**:
   - `__init__` (~line 2127): `self.cognitive_orchestrator = get_orchestrator(); initialize()`
   - `before_action` (~line 10061): `_co.before_action(action_type, detail)`
   - `after_action` (~line 10161): `_co.after_action(...)`
   - `session_end` (~line 15028): `_co.session_end(telemetry)`

4. **Test**: All modules import, all tests pass, syntax valid

## Guardrails

1. **Integration ≠ Wiring** — always verify hooks after moving files
2. **Never delete without archiving first** — 7-day grace period
3. **Verify before enable** — test dormant plugins in isolation
4. **Backup cerebrum_memory.db** before any DB cleanup
5. **Document every change** — log to enhancement_effectiveness table
6. **Check lsof BEFORE rm -rf** — running processes recreate deleted dirs

## Integration

- Output feeds into `auto_skill_pipeline` for high-quality docs
- Orphaned modules feed into `tip_survival` tracking
- Results logged to `enhancement_effectiveness` table
- Triggers `rapid_learnings` extraction for lessons
- **Quick start:** Run `scripts/manual_audit.py` for a complete health snapshot — this is the primary audit tool and works even when the agent's built-in status checks fail.
```bash
python3 ~/.hermes/skills/hermes-apparatus-audit/scripts/manual_audit.py
```

**Fallback:** If `cognitive_systems_audit.py` exists in `agent/`, run it — but verify output against manual_audit.py since the script may reference tables/columns that no longer match the live schema.

**Full audit:** See `references/maximal-wiring-checklist.md` for the complete 12-layer verification
- **Live functional verification:** See `references/live-functional-verification.md` for hook firing tests, cognitive system deep checks, and database schema integrity (catches silent failures that file-existence checks miss)
- **Comprehensive cognitive systems audit:** See `references/comprehensive-cognitive-systems-audit.md` for the 8-phase audit used July 2026 to verify all cognitive modules, hooks, tools, databases after bulk integration
- **Cognitive Orchestrator pattern:** See `references/cognitive-orchestrator-pattern-2026-05.md` for the unified dispatcher pattern that wires all orphaned modules through a single integration point, plus 3 new enhancements (context sculptor, tool oracle, trust scorer)
- **Schema migration disaster:** See `references/schema-migration-disaster-may16-2026.md` for the table rebuild pitfall that lost 1,279 tips — detection, recovery, and prevention
- **User experimentation style:** See `references/user-experimentation-style.md` for how to handle projects the user treats as capability experiments rather than products
- **Common fixes:** See `references/common-import-fixes.md` for import path patterns that break during audits
- **Source vs standalone:** See `references/source-vs-standalone-audit-pattern.md` for answering "what was built into source?" with classification framework
- **Real audit session (May 2026):** See `references/audit-2026-05-16-cognitive-apparatus.md` for a complete worked example — score 62.8/100, full database inventory, hook wiring check, and prioritized action list
- **Learning apparatus repair session (May 2026):** See `references/audit-2026-05-16-learning-apparatus-repair.md` for the repair workflow — fixing 8 audit findings while preserving user constraints, handling broken cron tools, and detecting false-positive audit findings
- **False-positive hook wiring detection (May 2026):** See `references/audit-2026-05-16-learning-apparatus-repair.md` section "Hook Wiring 'Asymmetric' (FALSE POSITIVE)" — how to verify hooks at three levels (agent loop, tool dispatch, plugin registration) before reporting them missing
- **YantrikDB integration pitfalls (May 2026):** See `references/yantrikdb-integration-pitfalls.md` — `with_default()` for bundled embedder, `record_batch()` with queue flush via `think()`, ingest queue size limit (256 ops), text-only recall without embedder not supported, batch size tuning for queue throughput
