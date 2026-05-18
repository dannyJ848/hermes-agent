---
name: cerebrum-memory
version: 2.0.0
description: Biomimetic 4-tier memory system (Cerebrum) with Honcho dialectic. Cerebrum is the primary memory — sensory, working, episodic, semantic layers with trust scoring and auto-consolidation. Honcho serves as the dialectic user-modeling layer.
triggers:
  - session_start
  - memory_pressure
  - need_context
  - store_fact
  - recall_context
---

# Cerebrum Memory — Biomimetic 4-Tier Memory System

## Architecture

```
Layer 0: SENSORY BUFFER  — Raw inputs, 30s TTL auto-decay
Layer 1: WORKING MEMORY  — 5 active slots, Baddeley model, 5% decay/turn
Layer 2: EPISODIC BUFFER — 200-turn hippocampal fast learning with temporal context
Layer 3: SEMANTIC STORE  — Long-term facts with trust scoring + HRR compositional reasoning
Layer 4: DIALECTIC (Honcho) — User modeling via Honcho v3 API (optional)
```

## Tool: `cerebrum`

Single tool with 9 actions:

### store — Save a fact
```
cerebrum(action="store", content="...", tier="auto", category="general", tags="tag1,tag2", salience=0.8)
```
- tier="auto" routes by salience: >=0.7→semantic, >=0.5→episodic, else→sensory
- Categories: user_pref, project, tool, medical, general
- Entities auto-extracted from content

### recall — Search all layers
```
cerebrum(action="recall", query="SOMA 3D rendering", limit=10)
```
Returns results ranked by relevance, recency, and trust score.

### probe — Deep entity recall
```
cerebrum(action="probe", entity="SOMA")
```
Returns ALL facts about a specific entity across all layers.

### reason — Multi-entity compositional query
```
cerebrum(action="reason", entities=["SOMA", "WebGPU", "Three.js"])
```
Finds facts connected to MULTIPLE entities simultaneously.

### focus — Pull items into working memory
```
cerebrum(action="focus", query="current task context")
```

### contradict — Find conflicting memories
```
cerebrum(action="contradict", query="WebGPU iOS support")
```

### consolidate — Manually trigger consolidation
```
cerebrum(action="consolidate")
```
Transfers episodic → semantic. Also runs automatically every 10 turns and daily at 4am via cron.

### status — Check memory health
```
cerebrum(action="status")
```

### feedback — Rate a fact's usefulness
```
cerebrum(action="feedback", fact_id=42, helpful=true)
```

## Automatic Processes (hardwired in sync_turn)

All fire automatically via `memory_manager.sync_all()` after every completed turn. Zero manual intervention needed.

1. **Every turn: Sensory → Episodic encoding** — salience scoring, entity extraction, episodic ingestion
2. **Every 5 turns: Consolidation** — episodic → semantic transfer (REM sleep analog)
3. **Every 10 turns: Trust decay** — Ebbinghaus forgetting: facts not accessed in 24h lose 0.02 trust (floor 0.1)
4. **Every 20 turns: Contradiction scan + pruning** — flags conflicting knowledge, removes decayed items
5. **On every recall: Reconsolidation** — accessed facts gain +0.01 trust, access count incremented
6. **Every turn: Honcho sync** — dialectic user modeling (if Honcho available)
7. **Daily 4am cron: Full cycle** — full consolidation + contradiction check + status report (job_id: ece3733a111c)
8. **Pre-compress flush** — before context compression: save important items
9. **On session end: Full consolidation** — `on_session_end` → `pipeline.run_full_cycle()`

## Session Start Workflow

1. `cerebrum(action="status")` — verify system health
2. `cerebrum(action="recall", query="recent work and context", limit=10)` — get oriented
3. Proceed with task

## DB Location

- Primary: `~/.hermes/cerebrum_memory.db` (SQLite)
- Tables: semantic_facts, entities, fact_entities, memory_banks, facts_fts (FTS5)
- 548 facts across 7 categories (as of 2026-04-03)

## Honcho Dialectic Layer

- Honcho runs at localhost:8000, API version: **v3**
- Health check: `GET /v3/workspaces` (NOT `/health`)
- Sync endpoint: `POST /v3/workspaces/hermes/peers/evey/sessions`
- Workspace: "hermes", Peers: "evey" (agent), "danny" (user)
- Startup: `/tmp/honcho/start.sh`
- Monitoring: Grafana localhost:3000

## Migration History

- MEMORY.md (25 entries, 9,951 bytes) → cerebrum semantic store
- USER.md (4 entries) → cerebrum semantic store (category: user_pref)
- Knowledge findings (75 files, 507 sections) → cerebrum semantic store
- Honcho memories (11 unique) → cerebrum semantic store

## Pre-Action Recall (Automatic)

Every time the gateway processes a user message, BEFORE the model thinks, `prefetch_all()` runs against cerebrum and injects relevant memories as a system message. This forces the model to reason WITH accumulated knowledge, not in a vacuum.

**Injection point:** `run_agent.py` line ~6507 (after user message appended, before model call). Marked with `PRE-ACTION RECALL` comments. **Re-apply after `hermes update`** (gets overwritten).

## Metacognition Engine

`plugins/memory/cerebrum/metacognition.py` — 3-phase self-awareness:

1. **ANTICIPATION** — classifies task type, estimates difficulty, recalls past similar tasks, retrieves known pitfalls
2. **MONITORING** — detects circular reasoning (same action 3x), excessive iterations (2x above average)
3. **REFLECTION** — records outcome, calibrates confidence, extracts success/failure patterns as lessons

**DB Tables:** `reasoning_traces` (episodes), `reasoning_patterns` (frequency-tracked patterns). Initialized in `CerebrumProvider.__init__()` as `self._meta`.

**Auto-capture via `infer_and_record`:** Hooked into `sync_turn` every 3 turns. Uses `_classify_task()` and `_estimate_difficulty()` keyword heuristics (zero LLM cost) to infer task type, then writes a lightweight trace to `reasoning_traces`. No manual intervention needed — traces accumulate passively and build "judgment" over ~50+ sessions.

**Lesson learned:** The engine was initialized but had zero traces because `begin_reasoning`/`end_reasoning` require explicit caller coordination that never happened. The `infer_and_record` method was added to auto-capture from content heuristics instead. When patching metacognition.py, use `def get_status` as anchor — earlier methods like `begin_trace` don't exist (actual name is `begin_reasoning`).

## HERMES.md Auto-Loading (Session Context)

Hermes auto-loads context files via `agent/prompt_builder.py` → `build_context_files_prompt()`. Priority order (first found wins):

1. `.hermes.md` / `HERMES.md` — walks CWD to git root
2. `AGENTS.md` — CWD only
3. `CLAUDE.md` — CWD only
4. `.cursorrules` — CWD only

**Critical:** The scanner walks from CWD → git root, NOT from HERMES_HOME. The gateway runs from the hermes-agent repo (`/Users/dannygomez/hermes-agent/`), so HERMES.md must be at `/Users/dannygomez/hermes-agent/HERMES.md` to be discovered. Putting it at `~/.hermes/HERMES.md` will NOT work.

Each file is capped at 20,000 chars. YAML frontmatter is stripped. Content is scanned for prompt injection via `_scan_context_content()`.

**Deployment:** Created `/Users/dannygomez/hermes-agent/HERMES.md` with boot context (startup checks, active projects, infrastructure, session rules). Auto-loads on every new session — no cron or restart needed.

## Fluid Reasoning Layer

`plugins/memory/cerebrum/fluid_reasoning.py` — Real-time reasoning strategy tracking ("hypersonic missile" mid-flight course correction).

**CognitiveStrategyTracker** class detects 10 strategy types from tool sequences:
`hypothesis_first`, `brute_force`, `research_first`, `delegate_first`, `tool_first`, `iterative_fix`, `plan_then_execute`, `breadth_first`, `depth_first`, `adaptive`

**DB Tables:** `cognitive_patterns` (strategy → task_type → confidence/speed/outcomes), `reasoning_sessions` (per-episode tool sequences with strategy switches).

**Integration path:**
1. Module lives at `~/hermes-agent/plugins/memory/cerebrum/fluid_reasoning.py`
2. Imported lazily by `~/.hermes/plugins/evey-tool-intelligence/__init__.py` via `_get_fluid_tracker()`
3. `on_pre_llm_call` calls `tracker.get_strategy_advice(task_context)` — injects proven strategies + anti-patterns
4. `on_post_tool_call` calls `tracker.record_tool_use(tool_name, args, status, speed_ms)` — builds session picture
5. Session auto-closes after 60s timeout or explicit `close_current_session()`
6. Advice only shown after 2+ uses per strategy/task_type combo (prevents premature guidance)
7. Status exposed via `cerebrum(action="status")` → `fluid_reasoning` key

**Strategy detection** is purely heuristic (zero LLM cost): scores tool order patterns (e.g., research→action = hypothesis_first, repeated patch without read = brute_force, alternating read→patch = iterative_fix).

## Adding a New Cerebrum Module (Development Pattern)

Follow this exact sequence when adding any new cognitive module:

1. **Create module** at `~/hermes-agent/plugins/memory/cerebrum/<module>.py`
2. **DB tables**: Create via `_create_tables()` using `self._conn.executescript()`. Tables auto-created on first init.
3. **Wire into provider**: Import in `provider.py`, instantiate in `initialize()` where `db_path` is known (NOT in `__init__`). Use `self._module = None` in `__init__`, set in `initialize()`.
4. **Wire into tool-intelligence hooks** (if the module needs pre/post LLM data):
   - `~/.hermes/plugins/evey-tool-intelligence/__init__.py`
   - Use lazy initialization via `_get_module()` function (not global init)
   - Import path: `sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "memory" / "cerebrum"))`
5. **Test import** with `python3 -c "from plugins.memory.cerebrum.module import Class"` BEFORE restarting gateway
6. **Write multi-line test scripts** to a temp file, don't inline in terminal — shell escaping breaks
7. **Propagate** to squad profiles: `cp -f ~/.hermes/plugins/evey-tool-intelligence/__init__.py ~/.hermes-profiles/soma-coder/plugins/evey-tool-intelligence/` (repeat for each profile)

**Key paths:**
- Cerebrum modules: `~/hermes-agent/plugins/memory/cerebrum/`
- Plugin hooks: `~/.hermes/plugins/evey-tool-intelligence/__init__.py`
- Cerebrum DB: `~/.hermes/cerebrum_memory.db`
- Squad profiles: `~/.hermes-profiles/soma-{coder,researcher,tester}/plugins/`

## Pitfalls

- Honcho API is v3, not v1. All endpoints start with `/v3/`. Health check uses `GET /v3/workspaces` (NOT `/health` which returns 404)
- Honcho sync endpoint: `POST /v3/workspaces/hermes/peers/evey/sessions` with `{"messages": [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}]}`
- Gateway creates new agent per message — no persistent in-memory state between messages. Sensory/working layers reset each message (by design — biological analog)
- **Gateway caches agents per session key.** After code changes, MUST restart gateway AND send a new message to get fresh agent. Old cached agents run stale code.
- **`hermes gateway restart` often fails to actually restart.** Use `hermes gateway stop && hermes gateway start` instead, and verify with `tail -3 ~/.hermes/logs/gateway.log`.
- Python 3.11 venv required (system Python 3.8 can't parse PEP 604 union types like `Path | None`)
- Patch tool's lint checker reports phantom ES5 errors — ignore them, verify with `./venv/bin/python -c "import py_compile; py_compile.compile('file.py', doraise=True)"`
- **Agent init debugging:** Gateway spawns agents in background threads. `logger.info` and `print` often don't reach any log file. Use file-based diagnostics: `open('/tmp/diag.log','w').write(...)` for tracing init code paths.
- **Cerebrum plugin files live at** `/Users/dannygomez/hermes-agent/plugins/memory/cerebrum/` (repo path), NOT `~/.hermes/plugins/`. The `__init__.py` uses `Path(__file__).parent` for discovery.
- **Telegram agents (GLM-5.1) may not call cerebrum directly.** Falls back to terminal commands to check files/DB instead of using the cerebrum tool. The tool IS registered — the model just doesn't always recognize it. Don't trust Telegram agent's "cerebrum is missing" diagnosis without checking the session file directly.

## Critical Bugs Fixed (2026-04-03)

These bugs caused cerebrum to silently return EMPTY on all recall queries despite having 549 facts in the DB:

### Bug 1: Path Expansion
**File:** `provider.py` line 174
**Problem:** `Path(hermes_home)` where `hermes_home="~/.hermes"` creates path at literal `~/.hermes/` (tilde not expanded). Creates a NEW empty database instead of opening the real one at `/Users/dannygomez/.hermes/`.
**Fix:** `Path(hermes_home).expanduser()` — always call `.expanduser()` on paths from config/kwargs.

### Bug 2: Full-String Substring Search
**File:** `layers.py` `_basic_search()` method
**Problem:** Searched with `content LIKE '%<entire query>%'` — never matches because no single fact contains the entire user query as a substring.
**Fix:** Tokenize query (lowercase, strip stop words), search with `OR` across all tokens: `content LIKE '%soma%' OR content LIKE '%3d%' OR content LIKE '%anatomy%'`.

### Bug 3: Retriever Empty-Result Short-Circuit
**File:** `layers.py` `recall()` method
**Problem:** Holographic retriever returned empty `[]` (no error), and code did `return results` — never fell through to keyword search. Only fell through on exception.
**Fix:** Check `if results:` before returning. Empty list = fall through to `_basic_search()`.

### Bug 4: Patch Tool F-String Corruption (CRITICAL)
**Problem:** When using `patch` tool to edit Python files containing f-strings (e.g., `f"prefix {variable}"`), SQL queries (e.g., `"WHERE content LIKE ?"`), or dict literals with quotes, the patch tool's interpolation engine corrupts the `new_string` parameter. Symptoms: garbled output mixing old/new code, f-strings replaced with raw variable references, SQL queries mangled, indentation destroyed on subsequent lines. This caused hours of cascading `IndentationError` and `SyntaxError` chasing.
**Fix:** For ANY Python file edit involving f-strings, SQL, or complex quoting, use `terminal` with a heredoc Python script instead of the `patch` tool:
```python
# Instead of: patch(old_string="...", new_string="f\"{var}\"")
# Do this:
python3 << 'HEREDOC'
filepath = "/path/to/file.py"
with open(filepath) as f:
    content = f.read()
content = content.replace("old text", "new text")
with open(filepath, 'w') as f:
    f.write(content)
print("OK")
HEREDOC
```
Key: use `<< 'HEREDOC'` (quoted) to prevent shell interpolation, and use string concatenation instead of f-strings inside the heredoc. Always verify with `py_compile` after.

### Verification Command
```python
from plugins.memory.cerebrum.provider import CerebrumProvider
p = CerebrumProvider()
p.initialize('test', hermes_home='~/.hermes')
result = p.prefetch('SOMA 3D anatomy viewer')
assert result and 'Semantic Memory' in result, "Cerebrum recall is broken!"
print("OK:", result[:200])
```
