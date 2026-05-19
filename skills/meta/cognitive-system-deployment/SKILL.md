---
name: cognitive-system-deployment
description: 5-step pattern for deploying new cognitive systems into Evey's architecture
version: 1.0
category: meta
---

# Cognitive System Deployment Pattern

Based on the session of Apr 5, 2026 where 13 systems were deployed successfully.

## 5-Step Pattern (UPDATED July 2026 — Hermes Source Integration)

**CRITICAL**: The user considers standalone scripts in `~/subconscious/` **unfinished work** until surgically integrated into `~/hermes-agent/`. Exact quote: *"Everything you built didn't actually help the hermes harness bc you never touched the fucking source code."*

**Correct pattern:**
1. **Prototype in `~/subconscious/`** (acceptable for testing ONLY)
2. **Find integration point in `~/hermes-agent/`** (`cli.py`, `run_agent.py`, `tools/`, `agent/`)
3. **Inject hooks/methods directly into Hermes source**
4. **Register tools via `registry.register()`**
5. **Test with `venv/bin/python`**
6. **Ask user to restart**

**Never declare done until Hermes core is patched.**

### Detailed Steps

1. **Core Module Creation**: Write the Python module in `~/subconscious/` first for rapid prototyping. Include CLI test in `if __name__ == "__main__"` block.
2. **CLI Test Verification**: Run `python3 ~/subconscious/<module>.py` to verify basic functionality.
3. **Surgical Integration into Hermes Source**:
   - Core cognitive modules → `~/hermes-agent/agent/<module>.py`
   - Tools → `~/hermes-agent/tools/<module>.py`
   - Plugin registration → `~/.hermes/plugins/<plugin-name>/__init__.py` (official plugin system)
   - Update imports to use `from agent.<module> import ...` or `from tools.<module> import ...`
4. **Plugin Hook Wiring**: Register hooks via the official Hermes plugin system:
   - `pre_llm_call`: Inject context (top-down)
   - `post_llm_call`: Record data, run consolidation
   - `pre_tool_call`: Validate, predict, retrieve lessons
   - `post_tool_call`: Record outcomes, mine errors
   - `on_session_start`: Initialize systems
   - `on_session_end`: Run evolution, reflection
5. **Functional Wiring Verification**: Verify hooks actually fire — see `hermes-source-surgical-integration` skill for complete verification ladder.
6. **Session Checkpoint**: Save checkpoint with `session_checkpoint` tool.

## Safety Rules

- **ALWAYS integrate into Hermes source** — `agent/` for cognitive modules, `tools/` for tools
- Use `from agent.<module> import ...` or `from tools.<module> import ...` — NOT `sys.path.insert(0, "~/subconscious")`
- Wrap all hook integrations in try/except — never let a new system crash the agent loop
- Test with `venv/bin/python -c` — NOT bare `python3`
- Verify with `PluginManager.discover_and_load()` — see `references/live-cognitive-systems-verification.md`
- Gateway restart required after source code changes — existing CLI sessions cache run_agent.py

## Research-First Rule

Before building any system:
1. Search for SOTA papers on the topic
2. Extract key architectural insights
3. Design the system based on research findings
4. Save the research to `~/.hermes/knowledge/`

## Verified Systems (deployed Apr 5)
1. Semantic Tool Selector (AWS research)
2. Meta Self-Modifier (HyperAgents, arXiv 2603.19461)
3. Visual Diff Detection (Pillow-based)
4. Perspective Diversity Tracker (Societies of Thought)
5. Token Consumption Tracker (Jenius-Agent)
6. Cognitive Patch Proposer (DGM, arXiv 2505.22954)
7. Test Case Generator (DePro, arXiv 2603.19399)
8. Agent Scorecard (ICLR 2026 evaluation framework)
9. Circuit Breaker (Zylos Research graceful degradation)
10. Knowledge Synthesis Engine (cross-reference research papers)

## Integration Points
Each system is wired into the tool-intelligence plugin via:
- `on_pre_tool_call`: Circuit breaker check, timer start
- `on_post_tool_call`: Token tracker, circuit breaker recording, perspective diversity recording, mastery engines
- `on_pre_llm_call`: Semantic tool selector context, distillation tips, strategy advice
- `on_session_start`: Cache reset, mastery initialization

## Hermes Source Integration Pattern (R100-R134 verified, UPDATED July 2026)

The active plugin is `~/.hermes/plugins/distillation/__init__.py` (~1918 lines).
Modules live in `~/hermes-agent/agent/` and `~/hermes-agent/tools/`. Each module owns its own SQLite DB in `~/.hermes/`.

**CRITICAL**: After moving modules from `~/subconscious/` to `~/hermes-agent/`, they must be verified as actually operational — not just present. See `hermes-source-surgical-integration` skill for the complete verification ladder.

### Step 1: Build module in ~/hermes-agent/agent/ or tools/
- Create `<module_name>.py` with its own DB at `~/.hermes/<module_name>.db`
- Use WAL mode + 10s busy_timeout on all DB connections
- Expose: `score_step()` / `record_outcome()` for post_tool_call, `build_injection()` for pre_llm_call
- Include `if __name__ == "__main__"` test block
- Use singleton pattern: `_instance = None; def get_<name>() -> <Class>`
- Import paths: `from agent.<module> import ...` or `from tools.<module> import ...`

### Step 2: Test module standalone
```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "from agent.<module> import get_<factory>; m = get_<factory>(); print(m)"
```
Must pass before wiring into plugin.

### Step 3: Wire into plugin — POST_TOOL_CALL (record data)
Find insertion point in `_on_post_tool_call` (line ~489). Look for the most recent R-numbered block.
Use `patch` tool with enough surrounding context to uniquely identify the spot.
Pattern for each new module:
```python
        # ── R<NUM>: <Module Name> — <what it does> ──
        try:
            from agent.<module_name> import get_<factory> as _get_<alias>
            _<alias> = _get_<alias>()
            _<alias>.score_step(  # or .record_outcome() or .store_experience()
                session_id=os.environ.get("HERMES_SESSION_ID", "default"),
                tool_name=tool_name,
                outcome="error" if error else "success",
                # ... module-specific args ...
            )
        except Exception:
            pass
```
CRITICAL: Always wrap in try/except: pass. Never let a new module crash the plugin.

### Step 4: Wire into plugin — PRE_LLM_CALL (inject context)
Find insertion point in `_on_pre_llm_call` (line ~1187). Add AFTER existing module injections.
Pattern:
```python
        # ── R<NUM>: <Module Name> (<research source>) ──
        try:
            from agent.<module_name> import get_<factory> as _get_<alias>
            _<alias> = _get_<alias>()
            _injection = _<alias>.build_injection(user_message or "")
            if _injection:
                lines.append(_injection)
        except Exception:
            pass
```

### Step 5: Syntax check the entire plugin
```bash
cd ~/hermes-agent && source venv/bin/activate && python3 -c "import ast; ast.parse(open(os.path.expanduser('~/.hermes/plugins/distillation/__init__.py')).read()); print('OK')"
```
NEVER skip this — a syntax error kills ALL plugin hooks silently.

### Step 6: Integration test all modules together
```python
import sys; sys.path.insert(0, os.path.expanduser("~/hermes-agent"))
from agent.<module> import get_<factory>
# Test each module through the same import path the plugin uses
```

### Step 7: Functional wiring verification
Use `PluginManager.discover_and_load()` to verify the plugin actually loads and hooks fire. See `references/live-cognitive-systems-verification.md` in the `plugin-integration-audit` skill for the complete verification script.

### Step 8: Update memory with new module info
Use `memory(action='replace')` to update the TRAINING GYM STATE entry.

## Wrapper Class Pattern (for Function-Based Modules)

When the cognitive orchestrator expects a class but the module only exports functions, add a wrapper class at the bottom of the module file:

```python
# Wrapper class for cognitive orchestrator compatibility
class ModuleName:
    def __init__(self):
        # Initialize any state
        init_db()  # or similar
    
    def method_name(self, arg1, arg2):
        return function_name(arg1, arg2)
```

Example from distillation_bridge.py:
```python
class DistillationBridge:
    def __init__(self):
        self._ensure_tips_table()
    
    def _ensure_tips_table(self):
        _ensure_tips_table()
    
    def bottom_up_store(self, tool_name, args, status, speed_ms, error="", lesson="", failure_stage=""):
        return bottom_up_store(tool_name, args, status, speed_ms, error, lesson, failure_stage)
    
    def top_down_recall(self, task_context, max_items=None):
        return top_down_recall(task_context, max_items)
```

Example from training_gym.py:
```python
class TrainingGym:
    def __init__(self):
        init_db()
        seed_exercises()
    
    def get_next_exercise(self, category=None, tier=None):
        return get_next_exercise(category, tier)
    
    def record_attempt(self, exercise_id, score, max_score, tools_used=None, errors=None):
        return record_attempt(exercise_id, score, max_score, tools_used, errors)
    
    def get_stats(self):
        return get_stats()
```

Example from subconscious_hook_wiring.py:
```python
class SubconsciousHookWiring:
    def __init__(self):
        pass
    
    def install_hooks(self):
        # Hooks are already installed at module level
        pass
    
    def pre_tool_call(self, tool_name, args, task_id=""):
        return pre_tool_call_full(tool_name, args, task_id)
    
    def post_tool_call(self, tool_name, args, result, task_id=""):
        return post_tool_call_full(tool_name, args, result, task_id)
    
    def pre_llm_call(self, messages, context_limit=128000):
        return pre_llm_call_full(messages, context_limit)
```

## Cross-System Module Sync Pattern

When deploying cognitive modules from one system to another (e.g., MacBook → DGX):

1. **Identify missing modules**: Compare `ls agent/*.py` on both systems
2. **Check for naming differences**: File names may differ (`adaptive_context_sculptor.py` vs `context_sculptor.py`)
3. **Create tar archive**: `tar czf /tmp/modules.tar.gz file1.py file2.py ...`
4. **Transfer**: `scp /tmp/modules.tar.gz user@host:/tmp/`
5. **Extract**: `cd ~/hermes-agent/agent && tar xzf /tmp/modules.tar.gz`
6. **Verify imports**: `python3 -c "from agent.module import ClassName"`
7. **Restart gateway**: `sudo systemctl restart hermes-gateway.service`
8. **Test**: Run `hermes -z "test"` and check logs for subsystem initialization

### Naming Mismatch Resolution
When the orchestrator expects `context_sculptor` but the file is `adaptive_context_sculptor.py`:
- The `_init_context_sculptor()` method imports `from agent.adaptive_context_sculptor import get_sculptor`
- The file name doesn't matter — only the import path matters
- Verify the import path matches the actual file name on the target system

### Pitfalls (learned from 15+ crashes)
- **NEVER leave modules in ~/subconscious/ as final state** — user considers this unfinished work
- Shell quoting in `python3 -c` with f-strings breaks — use `execute_code` instead of terminal for complex Python
- Module must be importable from `~/hermes-agent/agent/` — check `venv/bin/python` import paths
- The `patch` tool needs enough context (2-3 lines) for unique matching in the 1918-line plugin
- Never use `kill` on any PID — it can match the gateway/Hermes process
- Gateway restart required after source code changes — existing CLI sessions cache run_agent.py
- If `patch` fails with "not unique", add more surrounding lines to old_string
- **Class names often don't match file names** — verify before importing (see `hermes-source-surgical-integration` skill)
- **Function-only modules** need module-level import, not class instantiation
- **Cognitive orchestrator expects classes, not functions** — if a module exports functions but the orchestrator tries to instantiate a class, create a wrapper class at the bottom of the module file (see Wrapper Class Pattern below)
- **Module names differ between systems** — `context_sculptor.py` vs `adaptive_context_sculptor.py`, `trust_scorer.py` vs `epistemic_trust_scorer.py`. Always verify the actual file names on both source and target systems before syncing
- **Sync via tar + scp** for batch module transfers between systems: `tar czf modules.tar.gz file1.py file2.py` then `scp` and `tar xzf`
- **Verify with Python import test** after sync: `python3 -c "from agent.module import ClassName"`

## Parallel Brain Integration Pattern

When a new cognitive system needs to run continuously (not just on tool calls), integrate it into the parallel brain in `~/hermes-agent/agent/parallel_brain.py`:

### 3-Patch Pattern for `parallel_brain.py`

1. **Imports** (top of file): Add with try/except fallback:
   ```python
   try:
       from agent.new_module import needed_functions
       NEW_MODULE_AVAILABLE = True
   except ImportError:
       NEW_MODULE_AVAILABLE = False
   ```

2. **perceive() phase**: Add status gathering with gated availability checks:
   ```python
   if NEW_MODULE_AVAILABLE:
       try:
           status = get_status()
           # Add periodic deep scans (e.g., every 10 cycles)
           if self.cycle_id % N == 0:
               results = deep_scan()
       except Exception as e:
           self.log("TAG", "Failed: {}".format(str(e)[:80]))
   ```

3. **synthesize() phase**: Add any content processing or storage sanitization. Include in the return dict.

### Daemon Thread Pattern for `brain_daemon.py`

For systems that need to run independently (not tied to brain cycles), create `~/hermes-agent/agent/brain_daemon.py`:

1. Add imports at top with try/except + `SECURITY_WIRED = True/False` flag
2. Write a `run_<name>_loop()` function with a `while True` + `time.sleep(interval)`
3. Add thread startup in `main()` after region threads, gated by availability flag
4. Use a separate state DB (`~/.hermes/<name>_state.db`) to avoid locking cerebrum_memory.db

### Critical Pitfalls

- **SQLite locking**: When brain daemon is running, it holds locks on `~/.hermes/cerebrum_memory.db`. Any new module that writes to it MUST use `sqlite3.connect(path, timeout=30)` and `PRAGMA journal_mode=WAL`. Without WAL, writes will fail with "database is locked" after ~5s timeout.
- **Schema mismatches**: Always verify column names before querying. `semantic_facts` uses `content` (not `fact_text` or `text`). Run `sqlite3 <db> '.schema <table>' | head -5` to check.
- **f-string in daemon**: Brain daemon uses `.format()` not f-strings (Python 3.8 compat for subprocess calls). Use `.format()` in daemon thread functions.
- **Module path**: Use `from agent.<module> import ...` — NOT `sys.path.insert(0, str(Path.home() / "subconscious"))`

## Controller Integration
The hourly controller runs 6 phases:
1. MEASURE (facts, predictions, cycles, tools)
2. ENFORCE (trust caps, dedup, stale predictions)
3. DISTILL (extract lessons from tool outcomes)
4. CALIBRATE (brain-hands loop)
5. SELF-MODIFY (meta-cognitive parameter tuning)
6. SCORECARD (ICLR 5-level evaluation)
