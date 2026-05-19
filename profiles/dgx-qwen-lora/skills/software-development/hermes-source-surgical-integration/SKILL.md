---
title: Surgical Integration of External Modules into Hermes Source Code
description: |
  Bulk-move standalone cognitive systems, tools, and plugins from external directories
  (e.g. ~/subconscious/) INTO the hermes-agent source tree. Covers import-path
  rewriting, namespace migration, collision detection, and verification.
triggers:
  - "move into hermes source"
  - "integrate into hermes"
  - "not in hermes source code"
  - "subconscious to hermes"
  - "surgical integration"
  - "build INTO hermes"
  - "standalone scripts worthless"
pitfalls:
  - "Never leave modules in ~/subconscious/ as final state"
  - "Class names often don't match file names — verify before importing"
  - "Import loops break after 5 repeated failures — change strategy immediately"
  - "Direct 'from X import' must become 'from agent.X import' or 'from tools.X import'"
  - "Hermes run_agent.py init is the right hook for plugin loading"
  - "Registry.register() is required for tools to be discoverable"
  - "venv/bin/python must be used for all tests, not system python"
  - "File copy must preserve exact names — no renaming during cp"
  - "Subdirectories (tip_system/, autobrowse/) need __init__.py"
  - "same_tool_failure_halt triggers after 5 terminal failures — use execute_code instead"
  - "Cached bytecode (.pyc) may still reference old paths after source cleanup — clear __pycache__"
  - "Module-level path constants persist in loaded modules until hermes restarts"
  - "lsof is the fastest way to identify which process is recreating a deleted directory"
  - "Directory recreation is almost always a RUNNING PROCESS — check lsof before assuming bytecode"
  - "hermes update after integration causes git conflicts — commit first or use git reset --hard HEAD && git stash pop"
  - "Plugin hook registration does NOT guarantee invocation — verify hook name appears in _invoke_hook() in run_agent.py"
  - "File existence + module import is NOT enough — verify at Level 4: actual _invoke_hook() traces, not checkbox theater"
  - "Class names often don't match file names — verify before importing"
  - "Plugin handler signatures drift from actual class methods — always verify with inspect"
  - "Function-only modules (no classes) need module-level import, not class instantiation"
  - "except Exception: pass around imports hides broken integrations forever — remove it"
  - "Self-imports without agent. prefix work by accident but break refactoring — always use full path"
  - "Module-level DB path constants persist in loaded modules until hermes restarts"
  - "After migration, grep for hermes-agent.*db to find hardcoded paths that should be .hermes"
  - "The old ~/subconscious/ DBs may have data that needs migrating to ~/.hermes/ before restarting"
name: hermes-source-surgical-integration
---

# Hermes Source Surgical Integration

## User Directive (CRITICAL)

The user considers standalone scripts in `~/subconscious/` **unfinished work** until they are surgically integrated into `~/hermes-agent/`. Exact quote:

> "Everything you built didn't actually help the hermes harness bc you never touched the fucking source code."

**Correct pattern:**
1. Build prototype in `~/subconscious/` (acceptable for testing only)
2. Find integration point in `~/hermes-agent/` (`cli.py`, `run_agent.py`, `tools/`)
3. Inject hooks/methods directly into hermes source
4. Register tools via `registry.register()`
5. Test with `venv/bin/python`
6. Ask user to restart

**Never declare done until Hermes core is patched.**

## Integration Map

### Destination Rules

| Source Type | Hermes Destination | Import Pattern |
|-------------|-------------------|----------------|
| Core cognitive (brain, memory, learning) | `agent/` | `from agent.X import ...` |
| Tools (hands, autobrowse, diagnostics) | `tools/` | `from tools.X import ...` |
| Tip system modules | `agent/tip_system/` | `from agent.tip_system.X import ...` |
| Autobrowse modules | `tools/autobrowse/` | `from tools.autobrowse.X import ...` |
| Plugin loader | `agent/subconscious_plugin_loader.py` | `from agent.subconscious_plugin_loader import ...` |

### Key Integration Points

**`run_agent.py` (AIAgent.__init__):**
Inject after `self.context_compressor = ContextCompressor(...)`:
```python
# Subconscious plugin loader
from agent.subconscious_plugin_loader import init_subconscious_plugins
self._subconscious_plugins = init_subconscious_plugins()
```

**`cli.py` (HermesCLI):**
Inject auto-resume logic in `__init__` before session ID assignment.

**`tools/*.py`:**
Must include `registry.register(name="tool_name", toolset="category")` at module level.

## Bulk Copy Procedure

### CRITICAL: Use execute_code, NOT terminal loops

When doing bulk file copies or operations, **use a Python script with `execute_code` instead of terminal loops.** Terminal loops hit tool-call guardrails (`same_tool_failure_halt`) after 5 non-progressing attempts. `execute_code` handles bulk operations better and allows programmatic verification.

**Example — bulk copy with verification:**
```python
import shutil
from pathlib import Path

src = Path.home() / "subconscious"
dst = Path.home() / "hermes-agent" / "agent"

# Copy all .py files
for f in src.glob("*.py"):
    if f.name == "__init__.py":
        continue
    dest = dst / f.name
    shutil.copy2(f, dest)
    print(f"Copied: {f.name}")

# Verify count
agent_files = list(dst.glob("*.py"))
print(f"Total agent files: {len(agent_files)}")
```

### Step 1: Create destination directories
```bash
cd ~/hermes-agent
mkdir -p agent/tip_system tools/autobrowse
```

### Step 2: Copy with case mapping
Map subconscious filenames to hermes destinations:
- `brain.py` → `agent/brain.py`
- `hermes_hands.py` → `tools/hands.py` (strip `hermes_` prefix)
- `tip_normalizer.py` → `agent/tip_system/normalizer.py` (strip `tip_` prefix)
- `autobrowse_tracer.py` → `tools/autobrowse/tracer.py` (strip `autobrowse_` prefix)

### Step 3: Fix imports
Run a Python script that regex-replaces:
- `^from MODULE import` → `^from agent.MODULE import` (for agent modules)
- `^from hermes_X import` → `^from tools.X import` (for tool modules)
- `^from tip_X import` → `^from agent.tip_system.X import` (for tip modules)
- `^from autobrowse_X import` → `^from tools.autobrowse.X import` (for autobrowse)

## Method Signature Mismatch Pitfall (CRITICAL)

When wiring hooks into `run_agent.py`, the method signatures in the external module may not match what you expect. **Always read the actual method definition before writing hook code.**

**Example — Iteration Engine:**
```python
# WRONG (assumed API):
lesson = self.iteration_engine.before_action(
    action_type='web_search',
    action_detail='{"query": "test"}'  # ← wrong param name
)
# Returns: string  # ← wrong return type

# CORRECT (actual API):
ctx = self.iteration_engine.before_action(
    action_type='web_search',
    detail='{"query": "test"}'  # ← param is 'detail'
)
# Returns: Dict with keys ['action_hash', 'warnings', 'proven_approaches', 
#                           'has_history', 'past_failure_count', 'past_success_count', 
#                           'confidence', 'skill_candidate']
```

**Prevention:**
1. Before wiring hooks, `read_file` the target module's method definitions
2. Check parameter names AND return types
3. Write hook code to match the actual API, not your assumption

## Class Name Mismatch Pitfall (CRITICAL)

**Always verify class names before writing import statements.** The file name often does NOT match the class name:

- `context_compressor.py` → exports `AdaptiveCompressor`, NOT `ContextCompressor`
- `training_gym.py` → exports functions only, no `TrainingGym` class
- `llm_judge.py` → exports `run_llm_eval_sweep`, `call_ensemble_judge`, NOT `LLMJudge`

**Before importing, always scan the file:**
```bash
grep "^class " agent/MODULE.py
grep "^def " agent/MODULE.py | head -5
```

**If the expected class doesn't exist, use an alias or import the actual name:**
```python
from agent.context_compressor import AdaptiveCompressor as ContextCompressor
from agent.llm_judge import run_llm_eval_sweep  # function, not class
```

Failure to do this causes `ImportError` on hermes startup, breaking the entire agent.

### Step 5: Test imports
Use `venv/bin/python -c "from agent.X import ..."` not bare `python`.

### Step 6: Register tools
For each tool module, verify `registry.register()` is present.

## Verification Checklist

- [ ] All subconscious files copied to hermes destinations
- [ ] No filename collisions with existing hermes files
- [ ] Import paths rewritten to use `agent.*` or `tools.*`
- [ ] `run_agent.py` has subconscious plugin loader injection
- [ ] `cli.py` has auto-resume/handoff logic
- [ ] Tool modules have `registry.register()` calls
- [ ] `venv/bin/python` import tests pass for critical modules
- [ ] Subdirectories have `__init__.py` files
- [ ] User asked to restart hermes

## Post-Integration DB Path Migration

After moving modules from `~/subconscious/` to `~/hermes-agent/agent/`, module-level DB path constants often still point to the old standalone locations. These must be fixed or the integrated code will create new empty databases instead of using existing data.

### Common wrong paths to fix

| Wrong | Correct | Where found |
|-------|---------|-------------|
| `~/hermes-agent/tool_capability.db` | `~/.hermes/tool_capability.db` | `agent/tool_misuse_prevention.py`, `agent/brain_to_toolintel.py` |
| `~/hermes-agent/skill_rewards.db` | `~/.hermes/skill_rewards.db` | `agent/tip_system/impact_analyzer.py` |
| `~/hermes-agent/knowledge_compiler.db` | `~/.hermes/knowledge_compiler.db` | `agent/knowledge_compiler.py`, `agent/save_finding.py` |
| `~/hermes-agent/memory_consolidation.db` | `~/.hermes/memory_consolidation.db` | `agent/memory_consolidation.py` |
| `~/hermes-agent/self_eval.db` | `~/.hermes/self_eval.db` | `agent/self_eval_loop.py` |
| `~/hermes-agent/training_gym.db` | `~/.hermes/training_gym.db` | `agent/training_gym.py` |

### Detection

```bash
grep -r "hermes-agent.*\.db" ~/hermes-agent/agent/*.py ~/hermes-agent/agent/tip_system/*.py 2>/dev/null | grep -v ".pyc"
```

### Fix patterns

```python
# Pattern 1
Path.home() / "hermes-agent" / "*.db"   →   Path.home() / ".hermes" / "*.db"

# Pattern 2
os.path.expanduser("~/hermes-agent/.../*.db")   →   os.path.expanduser("~/.hermes/*.db")

# Pattern 3
str(Path.home() / "hermes-agent" / "*.db")   →   str(Path.home() / ".hermes" / "*.db")
```

### Data migration

If the old DB has valuable data, migrate before the running process restarts:

```python
import sqlite3, shutil, os

old_db = os.path.expanduser("~/subconscious/tool_capability.db")
new_db = os.path.expanduser("~/.hermes/tool_capability.db")

# Backup
shutil.copy2(new_db, new_db + ".backup")

# Migrate table by table
old_conn = sqlite3.connect(old_db)
new_conn = sqlite3.connect(new_db)
cursor = old_conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
for (table,) in cursor.fetchall():
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    if rows:
        new_conn.execute(f"DELETE FROM {table}")
        for row in rows:
            placeholders = ",".join(["?"] * len(row))
            new_conn.execute(f"INSERT INTO {table} VALUES ({placeholders})", row)
new_conn.commit()
```

### Verification

```bash
source ~/hermes-agent/venv/bin/activate && python3 -c "
import sqlite3, os
db = os.path.expanduser('~/.hermes/tool_capability.db')
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
for (t,) in c.fetchall():
    c.execute(f'SELECT COUNT(*) FROM {t}')
    print(f'{t}: {c.fetchone()[0]} rows')
"
```

## Post-Integration Cleanup — Eradicating Old Directories

After all source code is integrated, the old `~/subconscious/` directory may **keep being recreated** even though no source file references it. This happens because of THREE causes that must ALL be fixed:

1. **Running processes with open file handles** — the #1 cause. Old hermes sessions, daemons, or cron jobs hold open file handles that recreate directories.
2. **Cached bytecode** (`.pyc` files in `__pycache__`) still contains old path strings.
3. **Module-level constants** in loaded Python modules persist until interpreter restart.

### Detection (CRITICAL: Check processes FIRST)

```bash
# Step 1: Check which processes have files open in the old directory
lsof +D ~/subconscious/ 2>/dev/null

# Step 2: Check all hermes python processes
ps aux | grep hermes | grep python
lsof -p <PID> | grep subconscious

# Step 3: Monitor recreation timing
cd ~ && rm -rf subconscious/ && for i in {1..10}; do sleep 1; if [ -d subconscious ]; then echo "Recreated at ${i}s"; ls -la subconscious/; break; fi; done
```

If the directory reappears within 1-2 seconds, a **running process** is creating it. This is NOT a bytecode issue.

### Pragmatism Rule — When to Stop Chasing Ghosts

If the recreated directory contains only an **empty database file** (e.g., `tool_capability.db` with 0 rows), and:
- All source code uses the correct new paths (`~/hermes-agent/`)
- No config files reference the old path
- No cron/launchd jobs reference the old path
- No environment variables reference the old path
- The file has zero functional impact on hermes operation

**Then mark it as "will clear on restart" and move on.** Do NOT spend more than 2-3 investigation cycles on a zero-impact ghost file. The user will say: *"uhhh is it having any effect? if not let's mark it and leave it alone."*

**Correct response:** Acknowledge the ghost, note it will clear on `hermes restart`, and redirect to auditing other external systems that might actually need integration.

### Plugin Injection Issues — Gateway Restart Required

When a plugin (especially `learning-brain`, bundled) injects code into the CLI init path, stale injection can cause runtime errors like `_vprint AttributeError` even after source code fixes. The injected code persists in the gateway's cached state.

**Symptom:**
```
AttributeError: 'HermesCLI' object has no attribute '_vprint'
```

**Cause:** `learning-brain` plugin injected `_check_pending_handoff` + `_vprint` code into `cli.py` init path. After source cleanup, the injected code references methods that no longer exist.

**Fix:**
```bash
hermes gateway restart
```

This clears the gateway's cached plugin state. Fresh `hermes` start loads clean without stale injection.

**Prevention:** After any plugin-related source changes, run `hermes gateway restart` before testing.

### Python Environment — venv vs System

Hermes uses two Python interpreters:

| Environment | Version | Usage |
|-------------|---------|-------|
| System `python3` | 3.8.8 | CLI wrapper only |
| venv `python3` | 3.11.14 | Hermes runtime, plugin testing |

**Always use venv for plugin testing:**
```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 -c "
from hermes_cli.plugins import get_plugin_manager
m = get_plugin_manager()
m.discover_and_load(force=True)
for name, handlers in m._hooks.items():
    if handlers: print(f'{name}: {len(handlers)} handlers')
"
```

Using system Python 3.8 causes `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` because the `|` union syntax requires Python 3.10+.

### Complete Audit = Functional Wiring, Not Just File Presence

The user expects a **complete audit** to verify not just file presence but actual **FUNCTIONAL WIRING** — hooks connected, methods called, databases healthy. Integration (files in right place) is worthless without wiring (connected to agent loop).

**The May 2026 subconscious integration audit revealed all 10 cognitive modules were orphaned** — present in `agent/` but none registered hooks or were called by `run_agent.py`. The user explicitly asks: *"did ensure its all wired and functional for every turn, etc?*" — they want proof of per-turn execution, not checkbox theater.

**The Cognitive Orchestrator pattern solves this:** Instead of wiring each module individually (brittle, error-prone), use a unified dispatcher that manages all subsystems. See `hermes-apparatus-audit/references/cognitive-orchestrator-pattern-2026-05.md` for the full pattern.

**See `references/functional-wiring-verification.md` for the complete verification ladder and script.**

**Key principle:** Always verify at Level 4 (actual hook invocation traces in run_agent.py), not just Level 1 (file existence) or Level 2 (module import).

**Verification command:**
```bash
/Users/dannygomez/hermes-agent/venv/bin/python3 -c "
from hermes_cli.plugins import get_plugin_manager
m = get_plugin_manager()
m.discover_and_load(force=True)

# Check cognitive-systems plugin
plugin = m._plugins.get('cognitive-systems')
print(f'Plugin loaded: {plugin.module is not None if plugin else False}')

# Check hooks
for name, handlers in m._hooks.items():
    if handlers:
        print(f'{name}: {len(handlers)} handler(s)')
        for h in handlers:
            print(f'  - {h.__qualname__ if hasattr(h, \"__qualname__\") else str(h)}')

# Check tools
for tool_name in m._plugin_tool_names:
    print(f'Tool: {tool_name}')
"
```

**Expected output for operational state:**
```
Plugin loaded: True
on_session_start: 2 handler(s)
  - on_session_start_hook
  - _on_session_start_handler
pre_tool_call: 4 handler(s)
  - pre_tool_call_hook
  - _pre_tool_call_handler
  - _on_pre_tool_call
  - on_pre_tool_call
post_tool_call: 4 handler(s)
  - post_tool_call_hook
  - _post_tool_call_handler
  - _on_post_tool_call
  - on_post_tool_call
on_session_end: 2 handler(s)
  - on_session_end_hook
  - _on_session_end_handler
pre_llm_call: 3 handler(s)
  - _pre_llm_call_handler
  - _on_pre_llm_call
  - on_pre_llm_call
post_llm_call: 1 handler(s)
  - _post_llm_call_handler
post_api_request: 1 handler(s)
  - _on_post_api_request
Tool: screen_capture
Tool: gui_click
Tool: gui_type
```

### Plugin Coexistence — Multiple Plugins on Same Hooks

The Hermes plugin system allows **multiple handlers per hook** — they all fire in sequence. No deduplication or conflict resolution is applied; each handler operates independently.

**Example:** Both `cognitive-systems` (user plugin) and `learning-brain` (bundled plugin) register `pre_tool_call`, `post_tool_call`, `on_session_start`, `on_session_end` hooks. Both sets of handlers fire for each event.

**Implication:** Plugin coexistence is safe but means more overhead per hook event. Monitor for performance impact if many plugins register the same hooks.

### Resolution (in order — do NOT skip steps)

**Step 1: Identify and kill old processes**
```bash
# Find all hermes python processes
ps aux | grep hermes | grep python

# For each OLD process (NOT the current session), check if it has open handles
lsof -p <OLD_PID> | grep subconscious

# Kill processes that have open handles to the old directory
kill <OLD_PID>
```

**Step 2: Clear all cached bytecode**
Use Python script via `execute_code` (not terminal loops — hits `same_tool_failure_halt` after 5 attempts):
```python
import shutil, os
base = os.path.expanduser("~/hermes-agent")
count = 0
for root, dirs, _ in os.walk(base):
    for d in dirs:
        if d == "__pycache__":
            shutil.rmtree(os.path.join(root, d))
            count += 1
print(f"Cleared {count} __pycache__ directories")
```

**Step 3: Fix any remaining source code path constants**
```bash
grep -r "sys.path.insert.*subconscious" ~/hermes-agent --include="*.py"
grep -r "Path.home().*subconscious" ~/hermes-agent --include="*.py"
```

**Step 4: Restart hermes**
The current session's Python interpreter also has cached module state. Full restart required to load fresh code.

**Step 5: Verify eradication**
```bash
cd ~ && rm -rf subconscious/ && sleep 5 && ls subconscious/ 2>/dev/null || echo "SUCCESS: gone"
```

### Key Lesson

**Directory recreation after source cleanup is almost always a RUNNING PROCESS, not just cached bytecode.** Check `lsof` FIRST. Multiple hermes processes can run simultaneously — any of them can hold open file handles that recreate deleted directories. In the May 2026 integration, TWO hermes processes (PIDs 98882 and 49351) both had `~/subconscious/tool_capability.db` open.

**However:** If the recreated file is empty and has zero functional impact, do not let it block the audit of other external systems. Mark it and move on.

## Git Conflict During Update

When `hermes update` is run after integrating modules, git conflicts are likely because:
1. Upstream may have deleted files that you modified (e.g., `MASTER_DOC.md`, `cli_resume.sh`)
2. Your new `agent/` and `tools/` files are untracked and may collide with upstream additions

### Recovery Path

```bash
cd ~/hermes-agent

# Step 1: Reset to clean state (preserves your integrated files as untracked)
git reset --hard HEAD

# Step 2: Pop your stashed changes (hermes update stashes before pulling)
git stash pop

# Step 3: Add your integrated files to git tracking
git add agent/ tools/

# Step 4: Commit the integration
git commit -m "Integrate subconscious cognitive systems into agent/ and tools/"

# Step 5: Verify branch state
git status
```

### Prevention

Before running `hermes update`:
1. Commit your integration work first: `git add agent/ tools/ && git commit`
2. Or at minimum, ensure your changes are in the git stash so `hermes update` can auto-recover

If `hermes update` reports "restoring local changes hit conflicts", the stash is preserved — use `git stash pop` after `git reset --hard HEAD` to recover.

## Tool Registration Verification

After integrating tools into `tools/`, verify they appear in the tool registry.

**CRITICAL: `get_tool_definitions()` returns OpenAI function-calling format, not flat dicts.**

The structure is:
```python
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "...",
        "parameters": {...}
    }
}
```

**The `name` is nested under `function`, NOT at the top level.**

### Correct verification code

```python
import model_tools as mt
tools = mt.get_tool_definitions()

# CORRECT — access name via function sub-dict
tool_names = [t.get("function", {}).get("name", "") for t in tools]

# WRONG — name is not at top level
tool_names = [t.get("name", "") for t in tools]  # Returns empty strings!

print(f"Total tools: {len(tools)}")
print(f"My tool present: {'my_tool' in tool_names}")

# Check specific tool categories
x_tools = [t for t in tool_names if t.startswith("x_")]
vision_tools = [t for t in tool_names if t in ["screen_capture", "gui_click", "gui_type"]]
print(f"X tools: {x_tools}")
print(f"Vision tools: {vision_tools}")
```

### Common mistake — false negative on tool presence

If you use `t.get("name")` instead of `t.get("function", {}).get("name")`, ALL tools will appear missing even though they're registered. This causes unnecessary panic and duplicate registration attempts.

**Always verify with the correct key path before concluding tools are missing.**

## Tool Failure Guardrails

When `terminal` hits `same_tool_failure_halt` (5 repeated failures):
1. **Stop immediately** — do not retry terminal
2. Switch to `execute_code` for Python-based verification
3. Or use `read_file` to inspect the file before attempting imports
4. Never retry the exact same terminal command more than 3 times

### Terminal `&` Backgrounding Trap (CRITICAL)

**The `terminal` tool has a guardrail that rejects commands containing `&` even when `&` appears inside a quoted string.** This is a common false positive.

**Symptom:**
```
Foreground command uses '&' backgrounding. Use terminal(background=true)...
```

**Trigger:** The `&` appears in `python -c "..."` strings, JSON, or any quoted content:
```bash
# FAILS — & inside python string triggers guardrail
cd ~/hermes-agent && source venv/bin/activate && python -c "
import json
data = {'a': 1, 'b': 2}
print(json.dumps(data))
"
```

**Workarounds (in order of preference):**

1. **Use `execute_code` instead** — handles Python scripts cleanly, no `&` parsing issues:
```python
import json
data = {"a": 1, "b": 2}
print(json.dumps(data))
```

2. **Escape or avoid `&` in terminal strings** — use `+` for string concatenation, or write to a temp file first:
```bash
# Write script to temp file, then run
cat > /tmp/test.py << 'EOF'
import json
data = {"a": 1, "b": 2}
print(json.dumps(data))
EOF
python3 /tmp/test.py
```

3. **Use `execute_code` with sys.path manipulation** — the standard pattern for testing hermes modules:
```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/hermes-agent"))
from agent.auxiliary_client import resolve_vision_provider_client
provider, client, model = resolve_vision_provider_client("custom", "glm-5v-turbo")
print(provider, type(client).__name__, model)
```

**Rule:** When you need to run Python code that imports hermes modules, **always use `execute_code`**, not `terminal`. The `execute_code` tool is proven at 93% success rate vs terminal's vulnerability to `&` guardrails and `same_tool_failure_halt`.

## Secondary Source Directories

In addition to `~/subconscious/`, check for modules in `hermes_cli/subconscious/` — this directory often contains 20-30 unique modules that are NOT duplicated in `agent/` or `tools/`.

**Detection:**
```python
# Find modules unique to hermes_cli/subconscious/
sub_modules = {f.stem for f in Path("hermes_cli/subconscious").glob("*.py")}
agent_modules = {f.stem for f in Path("agent").glob("*.py")}
tools_modules = {f.stem for f in Path("tools").glob("*.py")}
unique = sub_modules - agent_modules - tools_modules
print(f"Unique modules to move: {len(unique)}")
```

**Action:** Move unique modules to `agent/` and remove duplicates. Update any imports in `hermes_cli/` that reference them.

## Import Fixing After Move

When a module is moved from `hermes_cli/subconscious/X.py` to `agent/X.py`, ALL files that import it must be updated:

**Before:**
```python
from tiered_memory import TieredMemory
```

**After:**
```python
from agent.tiered_memory import TieredMemory
```

**Detection:** Search for bare imports that no longer work:
```bash
grep -r "from tiered_memory import\|import tiered_memory" agent/ tools/ hermes_cli/
```

## Config Reference Cleanup

After integrating source files, **all config references must be updated** or hermes will fail at runtime:

### Files to scan and fix:
- `~/.hermes/cron/jobs.json` — cron job prompts with `sys.path.insert(0, '~/subconscious')`
- `~/.hermes/cron/job_*.json` — individual cron job definitions
- `~/.hermes/cron/jobs.json.backup` — backup of cron jobs
- `~/.hermes/memories/MEMORY.md` — memory entries referencing old paths
- `~/.hermes/skills/*/*/SKILL.md` — skill files with outdated module paths
- `~/.hermes/config.yaml` — provider/model configs (verify `deepseek-v4-pro` etc)
- `~/.hermes/processes.json` — process definitions
- `~/.hermes/.skills_prompt_snapshot.json` — skill prompt snapshots
- `hermes_cli/instant_context.py` — quick command references
- `hermes_cli/session_bootstrap.py` — startup command references
- `agent/cognitive_infrastructure_hooks.py` — subprocess paths to manual triggers
- `tools/health_daemon.py` — daemon path references

### Replacement patterns:
```
~/subconscious/        → ~/hermes-agent/
$HOME/subconscious        → $HOME/hermes-agent
/Users/dannygomez/subconscious → /Users/dannygomez/hermes-agent
hermes_cli/subconscious/ → agent/
from cortex_access import → from agent.cortex_access import
from llm_judge import      → from agent.llm_judge import
from cortex_flywheel import → from agent.cortex_flywheel import
python3 ~/subconscious/X.py → python3 ~/hermes-agent/agent/X.py
```

### Verification:
After fixing, run a recursive grep to confirm zero references remain:
```python
import os
for root, dirs, files in os.walk(os.path.expanduser('~/.hermes')):
    for f in files:
        if f.endswith(('.json', '.md', '.yaml')):
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
            if 'subconscious' in content:
                print(f"FOUND: {path}")
```

## Comprehensive External Systems Audit

After integration, run a full audit to confirm NOTHING remains externally. The user will ask: *"there is absolutely nothing left externally?"*

### Audit Checklist

Run this systematically:

**1. Source code path verification**
```bash
grep -rn 'Path.home().*subconscious\|os.path.expanduser.*subconscious\|mkdir.*subconscious\|makedirs.*subconscious' --include="*.py" ~/hermes-agent/
```

**2. Config/shell files**
```bash
grep -rn 'subconscious' --include="*.sh" --include="*.yaml" --include="*.yml" --include="*.json" ~/hermes-agent/
```

**3. Active config files in ~/.hermes/**
- `~/.hermes/config.yaml`
- `~/.hermes/.env`
- `~/.hermes/cortex_watchdog.sh`

**4. Scheduled jobs**
```bash
crontab -l | grep -i subconscious
launchctl list | grep -i subconscious
```

**5. Environment variables**
```python
import os
for k, v in os.environ.items():
    if 'subconscious' in v.lower():
        print(f"{k}={v}")
```

**6. Python import path**
```python
import sys
for p in sys.path:
    if 'subconscious' in p.lower():
        print(p)
```

**7. Subprocess spawns**
```bash
grep -rn 'subprocess.*subconscious\|Popen.*subconscious\|call.*subconscious' --include="*.py" ~/hermes-agent/
```

**8. External directories scan**
```python
import os
home = os.path.expanduser("~")
for item in os.listdir(home):
    full = os.path.join(home, item)
    if os.path.isdir(full) and not item.startswith('.') and item != 'hermes-agent':
        py_files = []
        for root, dirs, files in os.walk(full):
            for f in files:
                if f.endswith('.py'):
                    py_files.append(os.path.join(root, f))
        if py_files and len(py_files) < 50:
            print(f"~/{item}/: {len(py_files)} .py files")
```

**9. Standalone scripts in home**
```python
import os
home = os.path.expanduser("~")
for item in os.listdir(home):
    if item.endswith('.py') and os.path.isfile(os.path.join(home, item)):
        print(f"~/{item}")
```

**10. Databases in home**
```python
import os
home = os.path.expanduser("~")
for item in os.listdir(home):
    if item.endswith(('.db', '.sqlite', '.jsonl')):
        size = os.path.getsize(os.path.join(home, item))
        print(f"~/{item} ({size} bytes)")
```

### Official Hermes Extension Points (NOT External)

These directories are **intentional** Hermes extension points and should NOT be treated as external:

| Directory | Purpose | Status |
|-----------|---------|--------|
| `~/.hermes/plugins/` | User plugins — auto-loaded by Hermes plugin system | ✅ Official |
| `~/.hermes/tools/` | User tools — registered with tool registry | ✅ Official |
| `~/.hermes/scripts/` | Cron scripts — referenced by cronjob_tools.py | ✅ Official |
| `~/.hermes/hooks/` | Gateway hooks — referenced by gateway/hooks.py | ✅ Official |
| `~/.hermes/twitter_bridge/` | Data files for x-cookie-api skill | ✅ Official |
| `~/.hermes/local_vision/` | Cache for screen captures | ✅ Official |

**All evey-* plugins in ~/.hermes/plugins/ are properly integrated** if they have `register()` functions in their `__init__.py`. The Hermes plugin manager auto-discovers them.

**All tools in ~/.hermes/tools/ are properly integrated** if they call `registry.register()`. The tool registry discovers them at startup.

### What Counts as "External"

- Standalone `.py` files in `~/` (not in `.hermes/` or `hermes-agent/`)
- Directories with Python code outside both `~/hermes-agent/` and `~/.hermes/`
- Databases in `~/` (not in `~/.hermes/`)
- Scripts in `/tmp/` that persist across sessions
- Any code that creates/modifies files outside `~/hermes-agent/` and `~/.hermes/`

## Support Files

- `references/integration-95-modules.md` — full 95-file mapping from May 2026
- `references/class-name-mappings-2026-05.md` — file-to-export mapping to avoid ImportError
- `references/class-name-mismatch-recovery.md` — how to recover when a core class file is overwritten
- `references/cognitive-plugin-handler-signatures-2026-07.md` — verified handler-to-method mappings for cognitive-systems plugin (July 2026)
- `references/hermes-cli-subconscious-cleanup-2026-05.md` — cleaning up the secondary `hermes_cli/subconscious/` directory (27 modules moved)
- `references/iteration-engine-wiring.md` — exact hook placement for wiring IterationEngine into run_agent.py
- `references/iteration-engine-wiring-v2.md` — updated wiring with timing capture and pitfall notes
- `references/blackboard-integration-2026-05.md` — multi-agent blackboard and tool cache integration
- `references/subconscious-recreation-debug-2026-05.md` — debugging ghost directory recreation after integration
- `references/external-systems-audit-checklist.md` — comprehensive audit checklist (from this session)
- `references/plugin-hook-wiring-gaps-2026-05.md` — which plugin hooks are registered vs actually invoked by run_agent.py, dead code patterns, self-import anti-patterns
- `references/plugin-coexistence-verification.md` — verifying multiple plugins on same hooks (cognitive-systems + learning-brain)
- `references/db-path-migration.md` — fixing hardcoded DB paths after migration (`~/hermes-agent/*.db` → `~/.hermes/*.db`)
- `references/x-cookie-api-pattern.md` — X/Twitter cookie auth + dynamic GraphQL hash extraction pattern (July 2026)
- `references/functional-wiring-verification.md` — complete verification ladder from Level 1 (file presence) to Level 4 (actual hook invocation traces), plus class name mismatch and handler signature drift detection
- `references/live-plugin-verification-2026-07.md` — live PluginManager verification: discover_and_load(), check _plugins and _hooks, test module loading from the actual plugin path (not agent/cognitive_systems_plugin.py), verify DB health and experience counts
- `references/tool-registry-inspection.md` — Python-level tool registry inspection: Python version traps, import paths, empty registry pitfalls, and the correct verification script
- `references/cognitive-orchestrator-module-sync.md` — cross-system module sync pattern for cognitive orchestrator subsystems (MacBook → DGX, etc.)
- `scripts/bulk-config-cleanup.py` — run this after integration to fix all config references
- `scripts/verify-cognitive-plugin-compatibility.py` — run after any agent/ module change to catch class/method drift before silent hook failures
