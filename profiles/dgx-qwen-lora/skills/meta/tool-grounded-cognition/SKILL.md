---
name: tool-grounded-cognition
version: 3.0.0
description: "Plugin-based tool learning system with 4 mastery engines (24+ dimensions, 45 DB tables). Every tool call is intercepted, classified, and fed into iterative learning. All engines hook into pre_llm_call/pre_tool_call/post_tool_call."
trigger: When reasoning about tool performance, debugging tool failures, improving tool-call accuracy/speed, or ADDING NEW LEARNING DIMENSIONS to the mastery system.
---

# Tool-Grounded Cognition + Total Iterative Mastery

## Architecture (4 Engines, 24+ Dimensions)

```
pre_llm_call hook  → Inject: capability model + mastery advice + operational tips + session meta
pre_tool_call hook → Start timer, log intent, warn about predicted errors
post_tool_call hook → Classify result, feed ALL 4 engines, record outcomes
```

### Engine 1: Fluid Reasoning (`fluid_reasoning.py`)
- 10 strategy types (hypothesis-first, brute-force, iterative-fix, etc.)
- Detects reasoning strategy from tool call sequences
- 2 tables: `cognitive_patterns`, `reasoning_sessions`

### Engine 2: Total Mastery (`mastery_engine.py`)
- 6 dimensions: argument learning, error prediction, composition recipes, confidence calibration, prompt optimization, context preservation
- 6 tables: `argument_patterns`, `error_predictions`, `composition_recipes`, `confidence_calibration`, `prompt_optimization`, `context_preservation`

### Engine 3: Operational Mastery (`operational_mastery.py`)
- 10 dimensions: search query quality, delegation routing, patch precision, terminal patterns, memory retrieval value, skill ROI, retry strategy, browser navigation, task splitting, response quality
- 10 tables matching dimension names

### Tool Coverage
- **48 engineering tools** tracked with full mastery (ENGINEERING_TOOLS set)
- **47 auxiliary tools** tracked with generic classification
- **8 low-value tools** skipped (cost_check, watchdog_heartbeat, etc.)
- **Total: 95 tools covered**, organized into 12 categories: file ops, code execution, web/research, delegation/reasoning, browser, memory/knowledge, messaging/social, skills/learning, scheduling/goals, verification, vision/media, cron
- Each category has specialized detail extraction in `_feed_iteration_engine` for meaningful iteration engine records

### Engine 4: Session Meta-Mastery (`session_meta_mastery.py`)
- 8 dimensions: checkpoint value, cron tracking, cross-session transfer, recovery speed, proactive messaging, sequence optimizer, reflection quality, context injection ROI
- 8 tables matching dimension names

## Key Files

- **Plugin**: `~/.hermes/plugins/evey-tool-intelligence/__init__.py` (ALL hooks)
- **Engine source**: `~/hermes-agent/plugins/memory/cerebrum/` (4 engine .py files)
- **Shared DB**: `~/.hermes/cerebrum_memory.db` (45 tables total, shared with Cerebrum memory)
- **Capability DB**: `~/subconscious/tool_capability.db` (tool_stats, call_log, tool_recipes)
- **Iteration Engine**: `~/subconscious/iteration_engine.py`
- **Controller**: `~/subconscious/controller.py` (hourly cron: 300ccbf2ac5a)

## How to Add a New Learning Wave

Follow this exact procedure to add new learning dimensions:

### Step 1: Create the engine file
```python
# ~/hermes-agent/plugins/memory/cerebrum/new_engine.py
from __future__ import annotations  # REQUIRED for Python 3.8 compat in terminal testing
import sqlite3, time, logging
logger = logging.getLogger(__name__)

class NewEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_tables()

    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _ensure_tables(self):
        # Create your tables here
        ...

    def record_X(self, ...):
        # Record outcomes
        ...

    def get_X_advice(self, ...):
        # Retrieve lessons for injection
        ...

    def on_pre_llm_injection(self) -> str:
        # Aggregate all advice for context injection
        parts = []
        # ... gather tips
        return "\n".join(parts) if parts else ""
```

### Step 2: Test in isolation
```bash
# MUST use venv Python — system Python is 3.8.8, venv is 3.11.14
/Users/dannygomez/hermes-agent/venv/bin/python3 -c "
import sys
sys.path.insert(0, '/Users/dannygomez/hermes-agent/plugins/memory/cerebrum')
from new_engine import NewEngine
ne = NewEngine('/Users/dannygomez/.hermes/cerebrum_memory.db')
# Test record + retrieval
print(ne.get_status())
"
```

### Step 3: Add lazy-init to plugin
In `~/.hermes/plugins/evey-tool-intelligence/__init__.py`:

```python
# ── New Engine ──
_new_engine = None

def _get_new_engine():
    global _new_engine
    if _new_engine is not None:
        return _new_engine
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "memory" / "cerebrum"))
        from new_engine import NewEngine
        _new_engine = NewEngine(str(CEREBRUM_DB))
        logger.info("New Engine initialized")
    except Exception as exc:
        logger.debug("Could not init new engine: %s", exc)
    return _new_engine
```

### Step 4: Hook into pre_llm_call (context injection)
Find the `on_pre_llm_call` handler, add after existing engine injections:
```python
ne = _get_new_engine()
if ne:
    ne_injection = ne.on_pre_llm_injection()
    if ne_injection:
        parts.append(ne_injection)
```

### Step 5: Hook into post_tool_call (recording)
Find the `on_post_tool_call` handler, add after existing engine recording:
```python
ne = _get_new_engine()
if ne:
    try:
        ne.on_post_tool_call_hook(tool_name=tool_name, args=args,
            status=status, speed_ms=speed_ms, error_pattern=error_pattern)
    except Exception as exc:
        logger.debug("New engine record failed: %s", exc)
```

### Step 6: Propagate to all squad profiles
```bash
for profile in soma-coder soma-researcher soma-tester; do
    cp ~/.hermes/plugins/evey-tool-intelligence/__init__.py \
       ~/.hermes-profiles/$profile/plugins/evey-tool-intelligence/__init__.py
done
```

### Step 7: Verify table count
```bash
sqlite3 ~/.hermes/cerebrum_memory.db 'SELECT COUNT(*) FROM sqlite_master WHERE type="table"'
```

## Multi-Wave Audit Pattern

When expanding the mastery system, use iterative gap analysis:

1. **Wave N**: Build engine, integrate, test
2. **Wave N+1 Audit**: Walk through EVERY step of your operation cycle, check "is this covered?"
3. **Identify gaps**: List all uncovered dimensions
4. **Build Wave N+1**: Create engine for those dimensions
5. **Repeat until no gaps**

Example audit dimensions to check: pre-reasoning, tool selection, tool execution, post-reasoning, session continuity, cron execution, cross-session transfer, error recovery, sequencing, proactive messaging.

### Proven Audit Table Method
After each wave, build a coverage table mapping every action in your operation cycle to its learning engine. Actions with no engine = gaps for next wave. The cycle converges when every row has an engine:

```
| Action                  | Learning?  | Engine            |
|-------------------------|------------|-------------------|
| Receive message         | Covered    | All 4 engines     |
| Recall memory           | Covered    | Operational       |
| ...                     | ...        | ...               |
| [UNCOVERED ACTION]      | NO GAP     | → Next wave       |
```

Typical convergence: 3 waves (core → operational → meta). Each wave adds 6-10 dimensions.

## Integration Points (Hermes Pipeline)

1. `model_tools.py:handle_function_call()` — dispatches all tool calls
2. Line 405: `invoke_hook("pre_tool_call", ...)` — before dispatch
3. Line 427: `invoke_hook("post_tool_call", ...)` — after dispatch
4. `run_agent.py:~6507` — `invoke_hook("pre_llm_call", ...)` — before model reasoning
5. Plugin discovery: `~/.hermes/plugins/` directory, `plugin.yaml` + `__init__.py` with `register(ctx)`

## VALID_HOOKS
- pre_tool_call
- post_tool_call
- pre_llm_call
- post_llm_call
- on_session_start
- on_session_end

## Propagation
Copied to all squad profiles: soma-coder, soma-researcher, soma-tester.
Squad profiles only contain `plugins/` — they share the main config.yaml and the shared DB.

## Debugging
- Check plugin loaded: `grep "tool.intelligence" ~/.hermes/logs/*.log`
- Check mastery tables: `sqlite3 ~/.hermes/cerebrum_memory.db "SELECT name, (SELECT COUNT(*) FROM sqlite_master WHERE type='table') FROM sqlite_master WHERE type='table' LIMIT 1"`
- Check call log: `sqlite3 ~/subconscious/tool_capability.db "SELECT * FROM call_log ORDER BY timestamp DESC LIMIT 10"`
- Run controller manually: `cd ~/subconscious && python3 controller.py`

## Testing Plugins Without Restarting Gateway
```python
import importlib.util, os
spec = importlib.util.spec_from_file_location(
    "hermes_plugins.plugin_name",
    os.path.expanduser("~/.hermes/plugins/plugin_name/__init__.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class MockCtx:
    def __init__(self): self.tools = []; self.hooks = []
    def register_tool(self, **kw): self.tools.append(kw.get("name"))
    def register_hook(self, name, cb): self.hooks.append(name)

ctx = MockCtx()
module.register(ctx)
print(f"Tools: {ctx.tools}, Hooks: {ctx.hooks}")
```

## Pitfalls
- **Handler must accept **kwargs**: Hermes passes extra kwargs (e.g., `task_id`, `session_id`) to tool handlers. ALWAYS use `def handler(args: dict, **kwargs)`.
- **Use venv Python for testing**: System Python is 3.8.8, venv is 3.11.14. Terminal tests with 3.10+ syntax fail. Always use `/Users/dannygomez/hermes-agent/venv/bin/python3`.
- **DB path in __init__**: Set `db_path` to the param passed in constructor. Don't rely on it being set elsewhere.
- **threading.local() for DB connections**: Never share SQLite connections across threads. Each method should call `self._conn()` to get a fresh connection.
- **PII redaction in terminal**: `os.environ.get("API_KEY")` may show `***` in terminal output. Not corruption. Verify with `ast.parse()`.
- **Advice minimum samples**: Require 2+ samples before injecting advice to avoid hallucinated guidance from single data points.
- **Trailing commas in tool schemas**: Z.AI rejects `description` as a tuple (trailing comma makes it `(str,)` not `str`). Never leave trailing commas in tool schema definitions.
- **Gateway restart needed**: Code changes to plugin files require a gateway restart to take effect. The plugin is loaded once at startup.
- **WARN USER BEFORE GATEWAY RESTART**: `hermes gateway restart` kills ALL active sessions, including the user's other terminals. Always ask before restarting. Save checkpoint first.
- **Python scoping in plugin hooks**: Variables assigned inside `if tracker:` blocks cannot be referenced outside that block in Python 3.11+. Extract shared variables (like `task_context`) BEFORE any conditional blocks, at the top level of the function.
- **Check gateway.error.log for hook failures**: When hooks silently fail, the error appears in `~/.hermes/logs/gateway.error.log` or `~/.hermes/logs/errors.log` as `WARNING evey.tool-intelligence: pre_llm_call hook failed: ...`. Always check these logs after plugin changes.
- **pre_llm_call kwargs are: user_message, conversation_history, model, session_id, platform, is_first_turn** — NOT `messages` or `prompt`. See `run_agent.py` line 6646.
- **sys.path.insert for imports**: Engine files in `plugins/memory/cerebrum/` aren't on the default path. Use `sys.path.insert(0, ...)` before importing.

## Config Notes
- Memory char limit: `~/.hermes/config.yaml` at `memory.memory_char_limit` (50K as of Apr 2026).
- Controller cron: job_id `300ccbf2ac5a`, runs every hour.
