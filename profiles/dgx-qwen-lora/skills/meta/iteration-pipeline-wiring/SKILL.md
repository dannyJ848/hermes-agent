---
name: iteration-pipeline-wiring
version: 1.0
created: 2026-04-27
description: |
  Audit, repair, and harden a broken or incomplete agent iteration/learning pipeline.
  Covers: mapping dead code → creating missing DB tables → wiring data flows →
  adding bottleneck guards (batching, caching, throttling) → performance validation.
  The specific pattern: take modules that exist but don't connect, and wire them
  into the hot path with strict latency budgets.
triggers:
  - When learning/iteration modules exist but produce no observable effect
  - When DB tables are missing or empty despite code that should write to them
  - When per-turn overhead from learning systems exceeds acceptable budget
  - When the user says "make the iteration apparatus stable every turn"
  - After adding new cognitive modules that need integration into run_agent.py
---

# Iteration Pipeline Wiring

## Problem Class

You have multiple learning/iteration modules (error_learning, predictive_tools, 
cortex_learning, self_improvement_daemon) that:
- Import cleanly
- Have their own DB tables
- Run their own logic
- But produce **zero observable effect** on agent behavior

This is the "dead pipeline" problem — modules exist in isolation but never feed
the agent's decision loop.

## The Wiring Pattern

### Pattern A: Per-Module Hook Wiring (Legacy)
Each cognitive module wires itself independently into `run_agent.py`. See pitfalls
#8-15 for why this becomes unmaintainable at 3+ modules.

### Pattern B: Cognitive Orchestrator (Recommended for 3+ Subsystems)
A single unified dispatcher initializes all subsystems and routes lifecycle hooks.
See `agent-cognitive-infrastructure` skill for full implementation. Key benefits:
- Single point of control — add subsystem = one line in `initialize()`
- Fail-safe — each subsystem wrapped in try/except, crash of one doesn't kill others
- Centralized health — `get_status()` returns health of all subsystems
- Non-blocking post-session — ThreadPoolExecutor runs audits in background
- Clean run_agent.py — only 4 integration points

### Phase 1: Audit — Map What's Actually Connected

```bash
# 1. Find all modules that CLAIM to be part of iteration
ls agent/cortex*.py agent/error_learning.py agent/predictive_tools.py agent/*daemon*.py

# 2. For each module, find its injection point in the agent loop
grep -rn "cortex_learning\|error_learning\|predictive_tools\|self_improvement" run_agent.py

# 3. Check DB tables — which exist, which are empty
for table in memory_units memory_usage_log error_patterns error_occurrences tool_usage_patterns; do
  python3 -c "from agent.cortex_access import cortex_query; print('$table:', cortex_query('SELECT COUNT(*) FROM $table'))"
done

# 4. Check for dead code: functions defined but never called
grep -n "def _ensure_schema\|def get_distilled_tips\|def predict_needed_tools" agent/*.py
```

**Post-merge API discovery — methods may have been renamed:**
After a large upstream merge, the public API of learning modules often changes. Instead of guessing method names, introspect live:

```python
# Quick: list all public methods on each engine
import inspect

from agent.error_learning import ErrorLearningEngine
for name, method in inspect.getmembers(ErrorLearningEngine, predicate=inspect.isfunction):
    if not name.startswith('_'):
        sig = inspect.signature(method)
        print(f"ErrorLearningEngine.{name}{sig}")

# Verify signatures before calling
print(inspect.signature(ErrorLearningEngine().on_error))
```

**Common post-merge renames:**
- `get_injectable_tips(query, max_tips)` → `predict_relevant_memories(query, limit)`
- `get_patterns(context, limit)` → `get_preemptive_warning(action_description)`
- `predict_tools(query, top_k)` → `get_tool_recommendations(query, available_tools)`
- `learn_from_error(action_type, detail, error, context)` → `on_error(error_text, context, session_id)`
- `evaluate_session(telemetry)` → `get_loop_status()` + `get_waste_report()`
- `ingest_session(telemetry)` → `run_full_cycle(eval_pairs)`

Always verify signatures with `inspect.signature()` before calling.

**Common finding**: `_ensure_schema()` defined but never called. Tables never created.
**Common finding**: `get_distilled_tips()` exists but no caller in run_agent.py.
**Common finding**: Module imported but only used for health checks, not hot path.

### Phase 2: Create Missing Infrastructure

**DB tables with proper indexing:**
```python
def _ensure_schema(self):
    """Idempotent schema creation for learning tables."""
    with _cortex_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS memory_units (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                unit_type TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT,
                confidence FLOAT DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT NOW(),
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mu_type ON memory_units(unit_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mu_confidence ON memory_units(confidence)")
        # ... more tables
```

**Critical**: Call `_ensure_schema()` from `__init__()` AND from every method that
reads/writes the table. Defensive against "table doesn't exist" in fresh environments.

### Phase 3: Wire the Hot Path

The hot path is `_build_system_prompt()` in run_agent.py. This runs EVERY turn.
All injection must complete in < 50ms total.

**Tip injection (from local SQLite, NOT PostgreSQL):**
```python
# In run_agent.py _build_system_prompt():
from agent.cortex_learning import get_learning_engine
engine = get_learning_engine()
tips = engine.store.get_distilled_tips(limit=20)  # reads cerebrum_memory.db
# Relevance-filter by query overlap
query_words = set(query.lower().split())
relevant = [t for t in tips if query_words & set(t.get('text','').lower().split())]
# Inject up to 15% of remaining context budget
```

**Why local SQLite?** PostgreSQL round-trip = 5-20ms. SQLite = 0.5-2ms. With 16 API
calls per turn already, every millisecond matters.

**Error learning (batched, not per-error):**
```python
# In error_learning.py:
class ErrorLearningEngine:
    def __init__(self):
        self._batch_buffer = []
        self._batch_size = 5
        self._flush_interval = 60  # seconds
        self._last_flush = time.time()
    
    def on_error(self, error_text, context, session_id):
        # Pattern write stays sync (small, fast)
        result = self.store.record_error(error_text, context, session_id)
        # Occurrence write is batched
        self._batch_buffer.append({
            'pattern_id': result['pattern_id'],
            'context': context,
            'session_id': session_id,
        })
        if len(self._batch_buffer) >= self._batch_size or \
           (time.time() - self._last_flush) > self._flush_interval:
            self._flush_batch()
        return result
```

**Predictive tools (throttled):**
```python
# In run_agent.py — only every 5 turns:
if self._turn_counter % 5 == 0:
    from agent.predictive_tools import get_predictive_loader
    loader = get_predictive_loader()
    preds = loader.predict_needed_tools(query, top_k=3)
    # Inject tool schemas for predicted tools
```

### Phase 4: Add Bottleneck Guards

| Guard | Where | Trigger | Action |
|-------|-------|---------|--------|
| **Circuit breaker** | All DB writes | 3 consecutive failures | Stop writing, log alert |
| **Cache TTL** | Tip reads | 5 minutes | Re-read from SQLite |
| **Batch flush** | Error occurrences | 5 items OR 60s | Flush to DB |
| **Throttle** | Predictions | Every 5 turns | Skip otherwise |
| **Budget cap** | Injection | 15% of context | Truncate if exceeded |
| **Reentrancy guard** | Compression | Nested call detected | Skip second compression |

**Circuit breaker pattern:**
```python
from agent.cortex_access import circuit_breaker

@circuit_breaker(threshold=3, timeout=300)
def write_to_cortex(data):
    # ... DB write
```

**Compression reentrancy guard:**
```python
if getattr(self, '_compression_in_progress', False):
    logger.warning("Compression reentrancy detected, skipping")
    return
self._compression_in_progress = True
try:
    # ... compression logic
finally:
    self._compression_in_progress = False
```

### Phase 5: Fix Cursor Compatibility

**The psycopg2 tuple vs dict gotcha:**
- `psycopg2` cursors return tuples by default
- `psycopg2.extras.RealDictCursor` returns dicts
- If your code uses `row['column']` but cursor returns tuples → `TypeError`

**Fix all at once with a script:**
```python
import re
# Replace: row['column_name'] -> row[N] based on SELECT column order
# Or: use RealDictCursor everywhere (slower, more memory)
# Or: standardize on tuple access and document column order
```

**Recommended**: Use tuple access with documented column order. Faster and explicit.

### Phase 6: Validate Performance

```python
import time

# Test each hot path component
print("=== HOT PATH PERFORMANCE ===")

# 1. Tip injection
start = time.time()
tips = engine.store.get_distilled_tips(limit=20)
print(f"Tips: {(time.time()-start)*1000:.1f}ms")

# 2. Error batching
start = time.time()
for i in range(3):
    err_engine.on_error(f"test {i}", context="test", session_id="test")
print(f"3 errors: {(time.time()-start)*1000:.1f}ms")

# 3. Predictions
start = time.time()
preds = loader.predict_needed_tools("search files", top_k=3)
print(f"Prediction: {(time.time()-start)*1000:.1f}ms")

# 4. Health check
start = time.time()
health = cortex_health_check()
print(f"Health: {(time.time()-start)*1000:.1f}ms")

# ALL must be < 50ms per turn combined
```

**Character-based compression validation:**
```python
from agent.context_compressor import ContextCompressor

comp = ContextCompressor(model='kimi-for-coding', provider='kimi-coding')
print(f"Char threshold: {comp.char_threshold:,}")  # Should be 200_000
print(f"Token threshold: {comp.threshold_tokens:,}")  # Should be ~38K

# Test: 150K chars should NOT compress
small_msgs = [{'role': 'user', 'content': 'x' * 150000}]
print(f"150K chars: {comp.should_compress(messages=small_msgs)}")  # False

# Test: 250K chars SHOULD compress
large_msgs = [{'role': 'user', 'content': 'x' * 250000}]
print(f"250K chars: {comp.should_compress(messages=large_msgs)}")  # True
```

## Common Pitfalls

0. **Learning system only extracts from failures — misses 97% of experiences**: If the distillation daemon queries `WHERE frequency >= N AND lesson != ''` but the learning pipeline only writes lessons for failed/regression experiences, success experiences (the vast majority) never get lessons → never qualify for distillation → no tips generated.
   → **Detection**: Check result distribution: `SELECT result, COUNT(*) FROM experiences GROUP BY result`. If 90%+ are `success` but `SELECT COUNT(*) FROM experiences WHERE lesson != ''` is tiny, this is the issue.
   → **Fix**: Add `extract_lesson_from_success()` heuristic — map common action_types to positive lessons:
   ```python
   def extract_lesson_from_success(action_type, action_detail, result):
       lessons = {
           'terminal': 'Use terminal for shell commands, builds, git. Set timeout=300+ for long tasks.',
           'execute_code': 'Use execute_code for Python scripts with 3+ tool calls. Print final result.',
           'skill_view': 'Load skills proactively with skill_view(name) before matching tasks.',
           'skill_manage': 'Save successful workflows as skills. Patch existing skills when pitfalls found.',
           'read_file': 'Use read_file instead of cat/head/tail. Use offset/limit for large files.',
           'write_file': 'Use write_file instead of echo/heredoc. Auto-runs syntax checks.',
           'patch': 'Use patch for targeted edits. Include enough context for uniqueness.',
           'search_files': 'Use search_files instead of grep/find. Use target=files for directory listing.',
           'delegate_task': 'Delegate reasoning-heavy subtasks. Provide full context.',
           'delegate_with_model': 'Use cheap models for simple tasks. Route code to qwen-coder-free.',
           'web_search': 'Use web_search for current info, fact verification.',
           'web_extract': 'Use web_extract for articles, docs. Use max_chars to limit output.',
           'browser_navigate': 'Use browser_navigate first, then click/type/scroll.',
           'memory': 'Save user preferences, environment facts, tool quirks to memory.',
           'learn_from_interaction': 'Call after delegation, research, or non-trivial tool use.',
           'status_check': 'Call status_check FIRST every session. Free - shows bridge, costs, cron.',
           'cost_check': 'Check cost_check BEFORE expensive operations.',
       }
       return lessons.get(action_type, f'{action_type} worked successfully - note pattern for reuse')
   ```
   → Also add `backfill_missing_lessons()` that runs on daemon startup to process all existing experiences:
   ```python
   def backfill_missing_lessons():
       conn = sqlite3.connect(str(DB_PATH), timeout=5)
       conn.execute("PRAGMA journal_mode=WAL")
       cursor = conn.execute("SELECT id, action_type, result, error_pattern, action_detail FROM experiences WHERE lesson = '' OR lesson IS NULL")
       updated = 0
       for row in cursor.fetchall():
           exp_id, action_type, result, error_pattern, action_detail = row
           if result == 'regression' or error_pattern:
               lesson = extract_lesson_from_failure(action_type, error_pattern, result)
           else:
               lesson = extract_lesson_from_success(action_type, action_detail, result)
           if lesson:
               conn.execute("UPDATE experiences SET lesson = ? WHERE id = ?", (lesson, exp_id))
               updated += 1
       conn.commit()
       conn.close()
       return updated
   ```
   → Lower frequency threshold from 3 to 2 so more experiences qualify after backfill.
   → **Result**: 238/247 experiences got lessons → 59 tips generated (was 7).

1. **Schema not ensured**: `_ensure_schema()` defined but never called. Tables don't exist.
   → Call from `__init__()` AND from every read/write method. **Alternative**: lazy-init on first write (defensive against import-time DB connections).

2. **Dead injection path**: Module produces data but no code injects it into the LLM context.
   → Find `_build_system_prompt()` or `pre_llm_call` hook and add injection.

3. **Per-turn PostgreSQL**: Reading from Postgres every turn adds 5-20ms overhead.
   → Cache in local SQLite or in-memory with TTL.

4. **Synchronous error writes**: Writing every error occurrence to DB synchronously.
   → Batch occurrences; keep pattern writes sync (they're small).

5. **Dict cursor mismatch**: Code expects `row['column']` but cursor returns tuples.
   → Standardize on tuple access OR use RealDictCursor consistently.

6. **Unbounded tracking lists**: `self._recent_tools_used` grows forever.
   → Cap at N entries: `self._recent_tools_used = self._recent_tools_used[-20:]`

7. **Missing turn counter**: Predictive tools throttle "every 5 turns" but no counter exists.
   → Add `self._turn_counter` incremented each turn in the agent loop.

8. **Patch overwrites critical code**: When patching run_agent.py, `old_string` matches multiple places or replaces a line that's still needed.
   → Always verify the patch context with `grep -n` before applying. Check for `parsed_calls.append()`, `return` statements, or loop control flow that might be collateral damage.

9. **Missing stdlib imports in patched files**: Adding `Path` usage but forgetting `from pathlib import Path`.
   → Run `py_compile` after every patch: `python3 -m py_compile file.py`

10. **Character vs token confusion**: User says "154K" meaning characters, but compressor works on tokens.
    → For kimi-for-coding (no usage data), use **character-based threshold** as primary signal. Hardwire at 200K chars ≈ 38K tokens (5.2 chars/token for mixed content).

11. **Missing `remaining_budget` property**: `InjectionBudget` class used by adaptive injection expects `budget.remaining_budget` but property not defined.
    → Add `@property def remaining_budget(self) -> int: return self.total_budget - self.used`

12. **Shadowed `should_compress` method**: `ContextCompressor.should_compress()` gains `messages` kwarg, but `LCMEngine` (subclass or separate instance) shadows it without the new parameter.
    → Update ALL `should_compress()` signatures to accept `messages=None` kwarg. Check `plugins/context_engine/lcm/engine.py` and any other context engine implementations.

13. **Submodule commits not propagating**: `plugins/context_engine/lcm` is a git submodule. Changes committed inside it don't auto-commit to parent repo.
    → `cd plugins/context_engine/lcm && git add -A && git commit -m "..." && cd ../../.. && git add plugins/context_engine/lcm && git commit -m "..."`

14. **Bash `set -u` + empty array expansion**: Scripts using `set -euo pipefail` with `ARGS=("$@")` and `"${ARGS[@]}"` crash when called with no arguments. The `set -u` (nounset) treats unbound variables as fatal errors, and an empty array expansion triggers this.
    → Use `"${ARGS[@]:-}"` (colon-dash default) which expands to empty string when array is unset/empty, instead of `"${ARGS[@]}"`.
    → Example fix in `scripts/run_tests.sh`: change `"${ARGS[@]}"` to `"${ARGS[@]:-}"` on the pytest invocation line.
    → Also verify: `set -u` is active (check for `set -euo pipefail` or `set -u` near script top).

15. **Tests calibrated to broken hardcoded values**: When a hardcoded override (e.g., `threshold_tokens = int(char_threshold / 5.2)`) has been in place long enough, tests get written that pass ONLY with the broken values. When you restore correct behavior (e.g., `threshold_tokens = max(int(context_length * threshold_percent), MINIMUM)`), those tests fail because their inputs no longer trigger the expected code paths.
    → **Detection**: Test passes on the broken commit but fails after fix, with symptoms like "expected function X to be called but wasn't" or "assertion failed: None == expected_value". The test's input (e.g., `current_tokens=100000`) is below the restored threshold (e.g., `threshold_tokens=160000`), so compression never triggers.
    → **Fix**: Update test inputs to exceed the restored threshold, OR lower the test's threshold to match the old hardcoded behavior if the test specifically exercises the hardwired path. Also check if the test uses `__new__` + manual attribute assignment — newly added attributes (e.g., `_ineffective_compression_count`, `_lcm_cleanup_interval`) will be missing and must be added to the test setup.
    → **Example**: In `test_compress_focus.py`, `compressor.compress(messages, current_tokens=100000)` failed because 100000 < 160000 (restored threshold). Changed to 170000. Also added `_ineffective_compression_count = 0` and `_lcm_cleanup_interval = 5` to `_make_compressor()` because the restored correct behavior now exercises code paths that need those attributes.
    → **Rule**: When fixing a hardcoded override, grep for all test files that exercise the affected code path and verify their inputs still trigger the behavior after restoration.

16. **Reasoning model API incompatibility (DeepSeek V4 Pro, R1, o1, o3)**: Reasoning models put their output in `reasoning_content` instead of `content` when `response_format: {"type": "json_object"}` is used. The `max_tokens` budget gets consumed entirely by reasoning, leaving zero tokens for actual output. The API returns `content: ""` and `finish_reason: "length"`.
    → **Detection**: JSON parse fails with `Expecting value: line 1 column 1 (char 0)` because `_call_llm` returns empty string. Check raw API response — if `reasoning_content` is populated but `content` is empty, this is the issue.
    → **Fix**: Remove `response_format` from the payload entirely. Rely on explicit JSON instructions in the system/user prompt. Reasoning models will think in `reasoning_content` and output clean JSON in `content` when not forced by `response_format`.
    → **Example patch**:
    ```python
    # BEFORE (breaks with reasoning models):
    payload = {
        "model": self.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}  # ← REMOVE THIS
    }
    
    # AFTER (works with reasoning models):
    payload = {
        "model": self.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    # Plus stronger system prompt: "You must return ONLY a valid JSON object. No explanations, no markdown, just raw JSON."
    ```
    → **Also add**: `_extract_json_from_text()` fallback method that searches for JSON between ` ```json ` fences, plain ` ``` ` fences, or the first `{...}` block in case the model wraps JSON in markdown.
    → **Affected models**: `deepseek-v4-pro`, `deepseek-reasoner`, `o1`, `o3-mini`, `o3` — any model with a separate reasoning channel.

16b. **Judge max_tokens too small for full JSON response**: When the judge prompt requests detailed dimension ratings (specificity, actionability, accuracy, generality) plus reasoning, the response can exceed 800 tokens. With `max_tokens=800`, the JSON gets truncated mid-object, causing `json.JSONDecodeError: Unterminated string` or `Expecting value: line 1 column 1` if truncation happens at the very end.
    → **Detection**: Judge returns `winner: "t"` with `reasoning: "LLM evaluation failed: ..."`. Raw response length is ~300-500 chars but JSON is cut off (e.g., `{"winner": "b", "dimensions": {"specificity": {"a": 7, "b":` — no closing braces).
    → **Fix**: Increase `max_tokens` in `_call_llm()` from 800 to 2000 (or 1500 minimum). The reasoning model's thinking tokens consume part of the budget, so the actual output JSON needs headroom.
    → **Example**: `def _call_llm(self, messages, temperature=0.3, max_tokens=2000)` — was 800, changed to 2000 for DeepSeek V4 Pro judge.
    → **Verification**: Test with `compare_tips()` using tips that trigger full dimension ratings. Response should be complete JSON with all fields.
    → **Cost impact**: At DeepSeek V4 Pro pricing ($0.218/1M output tokens), increasing from ~500 tokens to ~1500 tokens per call adds ~$0.0002 per call — negligible.

17. **Hardcoded injection cap mismatch with config**: The distillation plugin hardcodes `_INJECTION_MAX_CHARS = 3600` while `config.yaml` sets `memory_char_limit: 2500`. The plugin silently exceeds the user's intended budget, wasting tokens.
    → **Detection**: Compare plugin constants against config values. Search for `_INJECTION_MAX_CHARS`, `memory_char_limit`, `context_char_limit` across both plugin code and config.
    → **Fix**: Lower the hardcoded cap to match config, OR wire the plugin to read from config dynamically. Also proportionally reduce `_INJECTION_MAX_LINES` and `_MAX_INJECT` so the total injected content fits the new budget.
    → **Example**:
    ```python
    # BEFORE:
    _INJECTION_MAX_CHARS = 3600
    _INJECTION_MAX_LINES = 18
    _MAX_INJECT = 12
    
    # AFTER (matching config memory_char_limit: 2500):
    _INJECTION_MAX_CHARS = 2500
    _INJECTION_MAX_LINES = 12
    _MAX_INJECT = 8
    ```
    → **Verification**: After patching, run `python3 -c "import re; f=open('plugin/__init__.py').read(); print(re.search(r'_INJECTION_MAX_CHARS = (\d+)', f).group(1))"` to confirm the new value.

18. **Judge model cost map missing new provider**: Switching the LLM judge to a new API provider (e.g., DeepSeek direct instead of OpenRouter) without updating the cost map causes cost tracking to return `$0.00` for all calls, hiding true spend.
    → **Detection**: After a judge run, `total_cost` stays at `0.0` despite successful API calls.
    → **Fix**: Add the new model identifier to `self.cost_map` with per-1M-token pricing (input, output). Check the provider's pricing page for current rates.
    → **Example**:
    ```python
    self.cost_map = {
        "deepseek-v4-pro": (0.109, 0.218),  # $/1M tokens (discounted until 2026/05/31)
        "deepseek-chat": (0.14, 0.28),
        # ... existing entries
    }
    ```
    → **Also update**: The docstring and CLI `--model` default to reflect the new primary provider.

19. **`.env` file not loaded by subprocess scripts**: Scripts in `~/subconscious/` import modules that need API keys, but the keys are stored in `~/.hermes/.env` which isn't automatically loaded by Python subprocesses or cron jobs.
    → **Fix**: Add manual `.env` parsing at module import time. Parse `KEY=VALUE` lines, skip comments/empty lines, only set if not already in `os.environ`.
    → **Example**:
    ```python
    _ENV_PATH = Path.home() / ".hermes" / ".env"
    if _ENV_PATH.exists():
        with open(_ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    if key not in os.environ:
                        os.environ[key] = val
    ```

20. **Schema drift between code and database — silent empty-result caching**: The code queries columns (`content`, `category`, `usage_count`) that don't exist in the actual DB table (`condition`, `recommendation`, `tip_type`, `frequency`). SQLite raises `OperationalError: no such column`, which gets caught by a broad `except Exception`, logged at DEBUG level, and returns an empty list. That empty list gets cached for 5 minutes (TTL), so even after fixing the schema, the cache serves stale emptiness.
    → **Detection**: Query returns 0 results despite table having thousands of rows. Check raw query vs schema: `sqlite3 db.db ".schema table_name"`. Look for `except Exception` swallowing `OperationalError`.
    → **Fix**: 
      1. Match the query to the actual schema — query existing columns, not expected ones.
      2. Build a content string by concatenating available fields (`condition + recommendation + rationale`).
      3. Map semantic fields: `domain` or `tip_type` → `category`, `frequency` → `usage_count`.
      4. Clear the cache immediately after patching: `engine.store._tip_cache = []`.
      5. Replace broad `except Exception` with specific handling that logs at WARNING and includes the actual error class.
    → **Example**:
    ```python
    # BEFORE (broken — queries non-existent columns):
    cur.execute("SELECT content, category, confidence, usage_count FROM distilled_tips")
    for row in cur.fetchall():
        tips.append({"content": row["content"], "category": row["category"]})
    
    # AFTER (fixed — queries actual columns, builds content):
    cur.execute("SELECT tip_type, condition, recommendation, rationale, domain, confidence, frequency FROM distilled_tips")
    for row in cur.fetchall():
        parts = []
        if row["condition"]: parts.append(f"Condition: {row['condition']}")
        if row["recommendation"]: parts.append(f"Action: {row['recommendation']}")
        if row["rationale"]: parts.append(f"Why: {row['rationale']}")
        content = " | ".join(parts)
        tips.append({
            "content": content,
            "category": row["domain"] or row["tip_type"] or "general",
            "confidence": row["confidence"],
            "usage_count": row["frequency"] or 0,
        })
    ```
    → **Verification**: After patch, force cache clear and test: `engine.store._tip_cache = []; tips = engine.store.get_distilled_tips(limit=5); assert len(tips) > 0`.
    → **Prevention**: Add a schema version check at module load time. If expected columns don't match actual schema, raise a loud warning instead of silently returning empty results.

21. **PostgreSQL code running against SQLite — complete module incompatibility**: An entire module (error_learning.py, predictive_tools.py) was written for PostgreSQL (`UUID`, `gen_random_uuid()`, `NOW()`, `JSONB`, `text[]`, `%s` placeholders, `ILIKE`, `&&` array operators, `ON CONFLICT DO UPDATE`, `FILTER (WHERE ...)`) but connects to an SQLite database. Every query fails with syntax errors, but the module uses `try/except Exception` that catches and silently ignores everything, returning empty results.
    → **Detection**: Module appears to work (no crashes, returns empty lists) but database tables stay empty despite code that should write to them. Check `_cortex_cursor()` — if it imports from `cortex_access.py` (psycopg2), but the DB path is `.hermes/cerebrum_memory.db` (SQLite), this is the issue.
    → **CRITICAL**: Some modules have their OWN `_cortex_cursor()` that uses SQLite, while others use the shared `cortex_access.py` PostgreSQL cursor. Before converting ANY placeholders, verify which cursor the module actually uses:
    ```bash
    grep -n "def _cortex_cursor" agent/error_learning.py agent/predictive_tools.py agent/cortex_learning.py
    # If the file defines its own _cortex_cursor() → it's SQLite (uses sqlite3, ? placeholders)
    # If it imports from cortex_access → it's PostgreSQL (uses psycopg2, %s placeholders)
    ```
    → **Fix**: Rewrite the entire module for SQLite:
      1. Replace `_cortex_cursor()` with a SQLite-backed version:
         ```python
         def _cortex_cursor():
             import sqlite3
             from pathlib import Path
             db_path = Path.home() / ".hermes" / "cerebrum_memory.db"
             conn = sqlite3.connect(str(db_path))
             conn.row_factory = sqlite3.Row
             return _SQLiteCursorContext(conn)
         
         class _SQLiteCursorContext:
             def __init__(self, conn): self.conn = conn; self.cur = None
             def __enter__(self):
                 self.cur = self.conn.cursor()
                 return self.cur
             def __exit__(self, exc_type, exc_val, exc_tb):
                 if exc_type is None: self.conn.commit()
                 else: self.conn.rollback()
                 self.cur.close(); self.conn.close()
                 return False
         ```
      2. Convert schema: `UUID PRIMARY KEY DEFAULT gen_random_uuid()` → `INTEGER PRIMARY KEY AUTOINCREMENT`
      3. Convert timestamps: `NOW()` → `CURRENT_TIMESTAMP`
      4. Convert types: `JSONB` / `text[]` → `TEXT`, `FLOAT` → `REAL`
      5. Convert placeholders: `%s` → `?`
      6. Convert operators: `ILIKE` → `LIKE`, `&&` (array overlap) → `LIKE` matching
      7. Convert upserts: `ON CONFLICT DO UPDATE` → manual `SELECT` then `UPDATE` or `INSERT`
      8. Convert aggregates: `COUNT(*) FILTER (WHERE ...)` → `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`
    → **Example — error_learning.py full conversion**:
    ```python
    # BEFORE (PostgreSQL — all queries fail silently on SQLite):
    cur.execute("SELECT id, occurrence_count FROM error_patterns WHERE fingerprint = %s", (fp,))
    cur.execute("UPDATE error_patterns SET last_occurred = NOW() WHERE id = %s", (id,))
    cur.execute("INSERT INTO error_occurrences (pattern_id, resolution_successful) VALUES (%s, %s)", (id, True))
    
    # AFTER (SQLite — works):
    cur.execute("SELECT id, occurrence_count FROM error_patterns WHERE fingerprint = ?", (fp,))
    cur.execute("UPDATE error_patterns SET last_occurred = CURRENT_TIMESTAMP WHERE id = ?", (id,))
    cur.execute("INSERT INTO error_occurrences (pattern_id, resolution_successful) VALUES (?, ?)", (id, 1))
    ```
    → **Verification**: After full conversion, test all CRUD operations:
    ```python
    from agent.error_learning import get_error_engine
    engine = get_error_engine()
    result = engine.on_error("TestError: test", context="test", session_id="test")
    assert result['occurrence_count'] == 1
    result2 = engine.on_error("TestError: test", context="test", session_id="test2")
    assert result2['is_repeat'] == True
    assert result2['occurrence_count'] == 2
    stats = engine.store.get_error_stats()
    assert stats['total_patterns'] >= 1
    ```
    → **Prevention**: When creating new learning modules, default to SQLite. If PostgreSQL is needed, create a separate `*_postgres.py` variant. Never mix PostgreSQL syntax with SQLite connections.
    → **Mixed backend architecture**: The iteration pipeline deliberately uses BOTH databases:
    - `cortex_learning.py` → PostgreSQL (shared memory, cross-session persistence)
    - `error_learning.py` → SQLite (local cerebrum_memory.db, fast per-error writes)
    - `predictive_tools.py` → SQLite (local cerebrum_memory.db, fast per-turn predictions)
    This split keeps hot-path latency low (<50ms) while allowing richer querying for memory retrieval. When patching, NEVER assume all modules use the same backend — check each file's `_cortex_cursor()` definition first.

22. **Placeholder confusion cascade — ? vs %s**: When fixing a mixed backend pipeline, it's easy to batch-convert ALL `?` placeholders to `%s` (or vice versa) across all files. But if some files are SQLite-backed (need `?`) and others are PostgreSQL-backed (need `%s`), a global conversion breaks the SQLite files.
    → **Detection**: After a "fix", SQLite-backed modules start throwing `sqlite3.OperationalError: near "(": syntax error` (because `%s` is invalid SQLite syntax). PostgreSQL modules throw `IndexError: tuple index out of range` (because `?` is treated as literal text, not a placeholder).
    → **Fix**: 
      1. STOP and audit each file individually: `grep -n "def _cortex_cursor" file.py`
      2. If file defines its own `_cortex_cursor()` with `sqlite3` → use `?` placeholders
      3. If file imports from `cortex_access.py` with `psycopg2` → use `%s` placeholders
      4. Never batch-convert across files without checking backend first
    → **Recovery**: If you already converted wrong, revert the specific file:
    ```bash
    git checkout -- agent/error_learning.py  # or git diff to manually revert
    ```
    Then re-apply ONLY the changes that match the file's actual backend.
    → **Prevention**: Add a comment at the top of each module's `_cortex_cursor()`:
    ```python
    def _cortex_cursor():
        """SQLite backend — uses ? placeholders, CURRENT_TIMESTAMP, INTEGER PRIMARY KEY AUTOINCREMENT"""
        import sqlite3
        ...
    ```

23. **End-to-end integration test — simulate the actual agent loop**: Individual component tests don't catch integration failures. You must simulate what run_agent.py actually does every turn.
    → **Test pattern**:
    ```python
    import time
    from agent.cortex_learning import get_learning_engine
    from agent.error_learning import get_error_engine
    from agent.predictive_tools import get_predictive_loader
    
    engine = get_learning_engine()
    err_engine = get_error_engine()
    loader = get_predictive_loader()
    
    # Test tip injection (every turn)
    times = []
    for _ in range(50):
        start = time.time()
        engine.store._tip_cache = []
        engine.store._tip_cache_time = 0
        tips = engine.store.get_distilled_tips(limit=20)
        # ... scoring and injection logic ...
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    print(f"Tip injection: {sum(times)/len(times):.1f}ms avg")
    
    # Test error recording (on failure)
    times = []
    for i in range(50):
        start = time.time()
        err_engine.on_error(f"Test error {i}", context="test", session_id="perf-test")
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    print(f"Error recording: {sum(times)/len(times):.1f}ms avg")
    
    # Test predictive tools (every 5 turns)
    times = []
    for _ in range(50):
        start = time.time()
        loader.predict_needed_tools("test query", recent_tools_used=[], top_k=3)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    print(f"Tool prediction: {sum(times)/len(times):.1f}ms avg")
    ```
    → **Expected results** (from actual run on 1890 tips, local SQLite):
    - Tip injection: ~1.2ms
    - Error recording: ~2.2ms
    - Tool prediction: ~1.3ms
    - Combined: ~1.7ms (all well under 50ms budget)
    → **If over budget**: Add caching, reduce query limits, or defer non-critical work to cron.

23. **Schema mismatch with empty-result caching — the silent killer**: When code queries columns that don't exist in the actual DB, SQLite raises `OperationalError: no such column`. If caught by a broad `except Exception` and logged at DEBUG, the empty result gets cached with a 5-minute TTL. Even after fixing the schema, the cache serves stale emptiness until TTL expires.
    → **Detection**: Query returns 0 results despite table having thousands of rows. Check raw query vs schema: `sqlite3 db.db ".schema table_name"`. Look for `except Exception` swallowing `OperationalError`.
    → **Fix**: 
      1. Match the query to the actual schema — query existing columns, not expected ones.
      2. Build a content string by concatenating available fields (`condition + recommendation + rationale`).
      3. Map semantic fields: `domain` or `tip_type` → `category`, `frequency` → `usage_count`.
      4. **Clear the cache immediately after patching**: `engine.store._tip_cache = []`.
      5. Replace broad `except Exception` with specific handling that logs at WARNING.
    → **Verification**: After patch, force cache clear and test: `engine.store._tip_cache = []; tips = engine.store.get_distilled_tips(limit=5); assert len(tips) > 0`.

24. **PostgreSQL code running against SQLite — complete module incompatibility**: An entire module (error_learning.py, predictive_tools.py) written for PostgreSQL (`UUID`, `gen_random_uuid()`, `NOW()`, `JSONB`, `text[]`, `%s` placeholders, `ILIKE`, `&&` array operators, `ON CONFLICT DO UPDATE`, `FILTER (WHERE ...)`) but connects to SQLite. Every query fails with syntax errors, but `try/except Exception` catches and silently ignores everything, returning empty results.
    → **Detection**: Module appears to work (no crashes, returns empty lists) but tables stay empty. Check `_cortex_cursor()` — if it imports from `cortex_access.py` (psycopg2) but DB path is `.hermes/cerebrum_memory.db` (SQLite), this is the issue.
    → **Fix**: Full SQLite rewrite:
      1. Replace `_cortex_cursor()` with a SQLite-backed version:
         ```python
         def _cortex_cursor():
             import sqlite3
             from pathlib import Path
             db_path = Path.home() / ".hermes" / "cerebrum_memory.db"
             conn = sqlite3.connect(str(db_path))
             conn.row_factory = sqlite3.Row
             return _SQLiteCursorContext(conn)
         
         class _SQLiteCursorContext:
             def __init__(self, conn): self.conn = conn; self.cur = None
             def __enter__(self):
                 self.cur = self.conn.cursor()
                 return self.cur
             def __exit__(self, exc_type, exc_val, exc_tb):
                 if exc_type is None: self.conn.commit()
                 else: self.conn.rollback()
                 self.cur.close(); self.conn.close()
                 return False
         ```
      2. Convert schema: `UUID PRIMARY KEY DEFAULT gen_random_uuid()` → `INTEGER PRIMARY KEY AUTOINCREMENT`
      3. Convert timestamps: `NOW()` → `CURRENT_TIMESTAMP`
      4. Convert types: `JSONB` / `text[]` → `TEXT`, `FLOAT` → `REAL`
      5. Convert placeholders: `%s` → `?`
      6. Convert operators: `ILIKE` → `LIKE`, `&&` (array overlap) → `LIKE` matching
      7. Convert upserts: `ON CONFLICT DO UPDATE` → manual `SELECT` then `UPDATE` or `INSERT`
      8. Convert aggregates: `COUNT(*) FILTER (WHERE ...)` → `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`
    → **Verification**: After full conversion, test all CRUD operations. For error_learning: simulate 2 errors with same fingerprint, verify `occurrence_count == 2` and `is_repeat == True`. For predictive_tools: record tool usage, verify predictions return the tool.
    → **Prevention**: Default new learning modules to SQLite. If PostgreSQL needed, create a separate `*_postgres.py` variant. Never mix PostgreSQL syntax with SQLite connections.

28. **Schema migration for old table format — DROP/RECREATE vs ALTER TABLE**: When a module's expected schema doesn't match the actual DB table (e.g., old code created columns `error_signature` but new code expects `fingerprint`), SQLite doesn't support `ALTER TABLE DROP COLUMN`.
    → **Detection**: `PRAGMA table_info(table_name)` shows old columns. Module queries fail with `OperationalError: no such column`.
    → **Fix**: Detect old schema, drop and recreate:
    ```python
    def _ensure_schema(self):
        with _cortex_cursor() as cur:
            cur.execute("PRAGMA table_info(error_patterns)")
            existing_cols = {row[1] for row in cur.fetchall()}
            
            if existing_cols and 'error_signature' in existing_cols:
                # Old schema detected — drop and recreate
                cur.execute("DROP TABLE error_patterns")
                cur.execute("DROP TABLE IF EXISTS error_occurrences")
            
            # Create with new schema
            cur.execute("""
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fingerprint TEXT UNIQUE NOT NULL,
                    ...
                )
            """)
    ```
    → **Why drop/recreate**: SQLite lacks `DROP COLUMN`. For small tables (<10K rows), this is fast and clean. For large tables, use `CREATE TABLE new AS SELECT ...` then rename.
    → **Verification**: After migration, test CRUD: insert a row, query it back, verify columns match expected schema.

29. **Cognitive orchestrator over per-module wiring**: When wiring 3+ cognitive subsystems into run_agent.py, per-module hooks become unmaintainable (scattered try/except blocks, no centralized health, adding a module requires editing run_agent.py again).
    → **Fix**: Use a unified `CognitiveOrchestrator` dispatcher. See `agent-cognitive-infrastructure` skill for full implementation.
    → **Integration points**: Only 4 hooks in run_agent.py:
      - `__init__`: `orchestrator.initialize(self)`
      - `before_action`: `orchestrator.before_action(action_type, detail)`
      - `after_action`: `orchestrator.after_action(action_type, detail, result, duration_ms)`
      - `session_end`: `orchestrator.session_end(telemetry)`
    → **Benefits**: Fail-safe (each subsystem wrapped in try/except), centralized health monitoring, non-blocking post-session (ThreadPoolExecutor), clean run_agent.py.
    → **When to use**: 3+ subsystems. For 1-2 subsystems, per-module wiring is fine.

26. **Curator integration into iteration pipeline**: The Hermes Curator (agent/curator.py) reviews agent-created skills for quality, overlap, and staleness. By default it only runs via gateway cron (7-day interval). For active skill maintenance, wire it into the per-turn iteration loop.
    → **Integration pattern**:
    ```python
    # agent/curator_integration.py — lightweight shim
    def maybe_run_curator_in_iteration(turn_count, tool_usage_history, error_history, force=False):
        if not force and turn_count % 50 != 0:
            return None
        from agent.curator import maybe_run_curator
        return maybe_run_curator(
            idle_for_seconds=float('inf'),
            on_summary=lambda msg: logger.info("curator[iteration]: %s", msg),
        )
    
    def record_skill_creation(skill_name, trigger, quality_score=0.5):
        from agent.cortex_learning import get_learning_engine
        engine = get_learning_engine()
        engine.store.save_memory_unit(
            content=f"Agent-created skill: {skill_name} (trigger: {trigger})",
            memory_type="agent_skill",
            source="iteration_pipeline",
            confidence=quality_score,
        )
    ```
    → **Wiring in run_agent.py**:
    ```python
    # In the main turn loop (after turn counter increment):
    from agent.curator_integration import maybe_run_curator_in_iteration
    maybe_run_curator_in_iteration(
        turn_count=self._turn_counter,
        tool_usage_history=getattr(self, '_recent_tools_used', []),
        error_history=getattr(self, '_error_history', []),
    )
    
    # Track errors for curator context:
    if not hasattr(self, '_error_history'):
        self._error_history = []
    self._error_history.append({
        "error_type": error_info.get('error_type', 'unknown'),
        "tool_name": function_name,
        "timestamp": time.time(),
        "is_known": error_info.get('is_known', False),
    })
    
    # Track skill creation:
    if function_name == "skill_manage":
        _sm_args = json.loads(tool_call.function.arguments)
        if isinstance(_sm_args, dict) and _sm_args.get("action") in ("create", "write_file"):
            from agent.curator_integration import record_skill_creation
            record_skill_creation(
                skill_name=_sm_args.get("name", "unknown"),
                trigger="agent_tool_call",
                quality_score=0.7,
            )
    ```
    → **Dual trigger paths**:
    - **Iteration pipeline**: Every 50 turns during active sessions (catches skills created mid-session)
    - **Gateway cron**: Hourly poll when idle (7-day interval gate for deep review)
    → **Verification**: Run smoke test — curator should trigger at turn 50, report "auto: no changes" (or actual transitions if stale skills exist), and skill creations should appear in memory_units.

27. **Full apparatus smoke test — all modules together with latency validation**: After wiring the iteration pipeline, run a comprehensive smoke test that exercises ALL modules in sequence and validates the total latency budget. This catches backend mismatches, API drift, and performance regressions that individual module tests miss.
    → **Test pattern**:
    ```python
    import time
    from agent.cortex_learning import get_learning_engine
    from agent.error_learning import get_error_engine
    from agent.predictive_tools import get_predictive_loader
    
    engine = get_learning_engine()
    err_engine = get_error_engine()
    pred_loader = get_predictive_loader()
    
    # Warm up connections (first call has connection overhead)
    _ = engine.store.get_distilled_tips(limit=1)
    _ = engine.predict_relevant_memories('warmup', limit=1)
    _ = err_engine.get_preemptive_warning('warmup')
    _ = pred_loader.get_tool_recommendations('warmup', [])
    
    # Now measure steady-state
    times = {}
    
    # 1. Tip injection (SQLite hot path)
    t = []
    for _ in range(3):
        start = time.time()
        tips = engine.store.get_distilled_tips(limit=5)
        t.append((time.time()-start)*1000)
    times['tips'] = sorted(t)[1]  # median
    
    # 2. Memory prediction (PostgreSQL)
    t = []
    for _ in range(3):
        start = time.time()
        memories = engine.predict_relevant_memories('test query', limit=5)
        t.append((time.time()-start)*1000)
    times['memories'] = sorted(t)[1]
    
    # 3. Error learning
    t = []
    for _ in range(3):
        start = time.time()
        warn = err_engine.get_preemptive_warning('search files')
        t.append((time.time()-start)*1000)
    times['error_warn'] = sorted(t)[1]
    
    t = []
    for _ in range(3):
        start = time.time()
        result = err_engine.on_error('TestError: smoke', context='test', session_id='test')
        t.append((time.time()-start)*1000)
    times['error_record'] = sorted(t)[1]
    
    # 4. Tool prediction
    t = []
    for _ in range(3):
        start = time.time()
        preds = pred_loader.get_tool_recommendations('test query', ['search_files', 'terminal'])
        t.append((time.time()-start)*1000)
    times['tool_pred'] = sorted(t)[1]
    
    t = []
    for _ in range(3):
        start = time.time()
        pred_loader.record_tool_usage('terminal', 'test query', successful=True, latency_ms=45.2)
        t.append((time.time()-start)*1000)
    times['tool_record'] = sorted(t)[1]
    
    total = sum(times.values())
    print(f"Total: {total:.1f}ms (budget: 50ms)")
    assert total < 50, f"Budget exceeded: {total:.1f}ms"
    ```
    → **Expected steady-state results** (from actual run on 1890 tips):
    - Tip injection: ~0.0-2ms
    - Memory prediction: ~0.4-1ms
    - Error warning: ~1-2ms
    - Error recording: ~2-3ms
    - Tool prediction: ~0.9-1ms
    - Tool usage record: ~1-1.5ms
    - **Total: ~6ms** (well under 50ms budget)
    → **If first-call is slow**: Connection establishment overhead. The smoke test should warm up all connections before measuring, or report both "cold start" and "steady-state" numbers.
    → **Backend verification**: The smoke test implicitly verifies which backend each module uses. If error_learning.py were accidentally converted to `%s` placeholders (PostgreSQL syntax) while still using sqlite3, `on_error()` would crash with `sqlite3.OperationalError` — caught immediately instead of silently returning empty results.
    → **API drift detection**: If a post-merge rename changed `get_tool_recommendations` to `predict_needed_tools`, the smoke test fails with `AttributeError` — forcing immediate discovery of the API mismatch.
    → **Run this smoke test**: After EVERY iteration pipeline wiring session, before declaring victory. Also run after any upstream merge that touches `agent/cortex_learning.py`, `agent/error_learning.py`, or `agent/predictive_tools.py`.

## Verification Checklist

- [ ] All tables created with `_ensure_schema()`
- [ ] Schema call is idempotent (CREATE IF NOT EXISTS)
- [ ] Injection wired into `_build_system_prompt()` or `pre_llm_call`
- [ ] Local SQLite used for per-turn reads (not PostgreSQL)
- [ ] Error occurrences batched (not sync per error)
- [ ] Predictions throttled (not every turn)
- [ ] All DB writes have circuit breaker
- [ ] Cursor type matches access style (tuple vs dict)
- [ ] Hot path latency < 50ms total
- [ ] No unbounded data structures
- [ ] Turn counter exists for throttling
- [ ] Tool usage tracking capped
- [ ] Compression reentrancy guarded
- [ ] Commit and checkpoint after wiring

## Files Typically Modified

| File | What | Backend |
|------|------|---------|
| `agent/cortex_learning.py` | Fix schema mismatch (query actual columns, build content string, clear cache) | **PostgreSQL** (psycopg2, %s placeholders) |
| `agent/error_learning.py` | Fix cursor/backend mismatch OR full SQLite rewrite | **SQLite** (sqlite3, ? placeholders, local cerebrum_memory.db) |
| `agent/predictive_tools.py` | Fix cursor/backend mismatch OR full SQLite rewrite | **SQLite** (sqlite3, ? placeholders, local cerebrum_memory.db) |
| `run_agent.py` | Wire injection into `_build_system_prompt()`, add turn counter, tool tracking | N/A (orchestrator) |
| `agent/memory_bloat_monitor.py` | Auto-trim critical files | N/A |
| `agent/adaptive_injection.py` | Add `InjectionBudget.remaining_budget` property | N/A |
| `plugins/context_engine/lcm/engine.py` | Update `should_compress()` to accept `messages` kwarg | N/A |
| `agent/context_compressor.py` | Hardwire character-based threshold (e.g., 200K chars for kimi-for-coding) | N/A |

## Resume Pattern (After Interruption)

When returning to a paused iteration pipeline:

```bash
# 1. Check which cron jobs are paused vs active
hermes cron list | grep -E "(paused|active)"

# 2. Check training status (if applicable)
ssh djg6228@10.0.0.171 "tail -3 /data/models/.../training.log"

# 3. Check brain cycle status
pgrep -f "parallel_brain.py" | wc -l  # Should be 0 (cron spawns, not persistent)
tail -5 ~/subconscious/cortex_daemon.jsonl

# 4. Resume paused jobs in priority order:
#    a. Brain cycles (alpha, bravo, charlie) — every 2-5 min
#    b. Training gym — every 15 min
#    c. AGI continuous loop — every 3 min
#    d. Quality sweeps — every 2h
hermes cron resume brain-cycle-alpha
hermes cron resume brain-cycle-bravo
hermes cron resume brain-cycle-charlie
hermes cron resume training-gym

# 5. Verify judge is functional (test a pair)
python3 -c "from llm_judge import LLMJudge; j=LLMJudge(); r=j.compare_tips({'text':'test a','domain':'test'},{'text':'test b','domain':'test'}); print(r.get('winner'))"

# 6. Verify end-to-end: tip injection → eval → DB write
python3 -c "from cortex_learning import get_learning_engine; e=get_learning_engine(); print(len(e.store.get_distilled_tips(limit=5)), 'tips loaded')"
```

**Critical**: After resuming, the first few cron runs may fail if the judge was broken during the pause. Fix judge FIRST (see pitfall #16 and #16b above), then resume cron jobs.

## Post-Resume Validation

After resuming all jobs, run this within 5 minutes:
```bash
# Check that brain cycles are actually spawning
hermes cron list | grep brain-cycle | head -3

# Check that daemon log has fresh entries
tail -3 ~/subconscious/cortex_daemon.jsonl | python3 -c "import sys,json; [print(json.loads(l)['timestamp']) for l in sys.stdin]"

# Check DB for recent activity
python3 -c "from cortex_access import cortex_cursor; 
with cortex_cursor(commit=False) as cur:
    cur.execute(\"SELECT cycle_type, status, started_at FROM cortex_flywheel ORDER BY started_at DESC LIMIT 3\")
    for r in cur.fetchall(): print(r)"
```

## Resume Pattern

After this work, the checkpoint should include:
1. All schema tables created
2. All hot paths wired and latency-tested
3. Circuit breakers on all DB writes
4. Cron job for daemon (not per-turn)
5. Git commit with full description of bottleneck guards

## Post-Wiring Sanity Checks

After committing, run these before declaring victory:

```bash
# 1. Syntax check all modified files
python3 -m py_compile agent/cortex_learning.py agent/error_learning.py run_agent.py

# 2. Verify no critical lines were accidentally removed
grep -n "parsed_calls.append" run_agent.py  # Should return results
grep -n "from pathlib import Path" agent/cortex_learning.py  # Should exist

# 3. Check compressor threshold is character-based
python3 -c "from agent.context_compressor import ContextCompressor; c=ContextCompressor('kimi-for-coding','kimi-coding'); print(c.char_threshold, c.threshold_tokens)"

# 4. Full integration test (all modules load, all tables exist)
python3 -c "
from agent.cortex_learning import get_learning_engine
from agent.error_learning import get_error_engine
from agent.predictive_tools import get_predictive_loader
from agent.self_improvement_daemon import SelfImprovementDaemon
engine = get_learning_engine()
err = get_error_engine()
loader = get_predictive_loader()
daemon = SelfImprovementDaemon()
print('ALL MODULES LOAD')
"

# 5. Verify adaptive_injection budget property exists
python3 -c "from agent.adaptive_injection import InjectionBudget; b=InjectionBudget(1000); b.allocate('test',100); print(b.remaining_budget)"

# 6. Check LCMEngine accepts messages kwarg
python3 -c "
from plugins.context_engine.lcm.engine import LCMEngine
e = LCMEngine()
print(e.should_compress(messages=[{'role':'user','content':'test'}]))
"

# 7. Verify submodule changes are committed in parent repo
git status  # Should show clean working tree, no modified submodules
```
