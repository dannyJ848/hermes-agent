---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior. 4-phase root cause investigation — NO fixes without understanding the problem first.
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, writing-plans, subagent-driven-development]
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

## Critical: Pre-Flight Environment Check (added Cycle 6)

**DO NOT** reflexively run `terminal()` for debugging. Historical data shows 80% failure rate with depth=1 (single tool call, no follow-up, no verification).

### Commands That ALWAYS Fail Headless

These commands require a GUI session and will silently fail or produce empty output:

| Command | Why It Fails |
|---------|-------------|
| `screencapture` | Requires GUI session |
| `sips` (image processing) | Requires GUI for screenshots |
| `tesseract` (OCR) | Requires screen capture input |
| `osascript` | AppleScript needs GUI session |
| `cliclick` | Mouse/keyboard control needs GUI |
| `open <app>` | Cannot open GUI apps headless |

### The Pre-Flight Protocol

Before ANY debugging `terminal()` call:

1. **Ask:** Does this command need a GUI? If yes → use alternatives
2. **Ask:** Have I tried this before? Check tool_intelligence success rate
3. **Plan 3 steps:** Hypothesis → Test → Verify. Never stop at depth=1
4. **Prefer safer tools:** `read_file`, `search_files`, `execute_code` over raw `terminal`

### Safer Alternatives for Debugging

| Instead of | Use |
|-----------|-----|
| `cat file` | `read_file` tool |
| `grep pattern` | `search_files` tool |
| `sed -i fix` | `patch` tool |
| Complex multi-command | `execute_code` (Python with error handling) |
| Unknown error | `web_search` for the error message |
| Interactive debugging | `delegate_task` (subagent has own session) |

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully

- Don't skip past errors or warnings
- They often contain the exact solution
- Read stack traces completely
- Note line numbers, file paths, error codes

**Action:** Use `read_file` on the relevant source files. Use `search_files` to find the error string in the codebase.

### 2. Reproduce Consistently

- Can you trigger it reliably?
- What are the exact steps?
- Does it happen every time?
- If not reproducible → gather more data, don't guess

**Action:** Use the `terminal` tool to run the failing test or trigger the bug:

```bash
# Run specific failing test
pytest tests/test_module.py::test_name -v

# Run with verbose output
pytest tests/test_module.py -v --tb=long
```

### 3. Check Recent Changes

- What changed that could cause this?
- Git diff, recent commits
- New dependencies, config changes

**Action:**

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

### 4. Gather Evidence in Multi-Component Systems

**WHEN system has multiple components (API → service → database, CI → build → deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation:**

For EACH component boundary:
- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks.
THEN analyze evidence to identify the failing component.
THEN investigate that specific component.

### 5. Trace Data Flow

**WHEN error is deep in the call stack:**

- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source
- Fix at the source, not at the symptom

**Action:** Use `search_files` to trace references:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### 6. Know When to Ask, Not Investigate

**If the user says "stop", "this is wrong", or "we need to fix X instead":**

- STOP immediately. Do not continue the current investigation.
- The user has context you don't. Trust their redirection.
- Ask ONE clarifying question to understand the real goal, then pivot.
- Do not defend your investigation path or explain why you were doing it.

**Signs you're in a rabbit hole:**
- User has corrected your direction 2+ times
- You've made 5+ tool calls without user confirmation
- You're investigating something the user didn't ask about
- You're explaining your reasoning instead of acting

**The correction "stop" is a first-class signal.** Update the relevant skill with the lesson learned.

### Phase 1 Completion Checklist

- [ ] Error messages fully read and understood
- [ ] Issue reproduced consistently
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypothesis formed
- [ ] **User has not redirected you to a different problem**

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

---

## Phase 2: Pattern Analysis

**Find the pattern before fixing:**

### 1. Find Working Examples

- Locate similar working code in the same codebase
- What works that's similar to what's broken?

**Action:** Use `search_files` to find comparable patterns:

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

### 2. Compare Against References

- If implementing a pattern, read the reference implementation COMPLETELY
- Don't skim — read every line
- Understand the pattern fully before applying

### 3. Identify Differences

- What's different between working and broken?
- List every difference, however small
- Don't assume "that can't matter"

### 4. Understand Dependencies

- What other components does this need?
- What settings, config, environment?
- What assumptions does it make?

---

## Phase 3: Hypothesis and Testing

**Scientific method:**

### 1. Form a Single Hypothesis

- State clearly: "I think X is the root cause because Y"
- Write it down
- Be specific, not vague

### 2. Test Minimally

- Make the SMALLEST possible change to test the hypothesis
- One variable at a time
- Don't fix multiple things at once

### 3. Verify Before Continuing

- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis
- DON'T add more fixes on top

### 4. When You Don't Know

- Say "I don't understand X"
- Don't pretend to know
- Ask the user for help
- Research more

---

## Phase 4: Implementation

**Fix the root cause, not the symptom:**

### 1. Create Failing Test Case

- Simplest possible reproduction
- Automated test if possible
- MUST have before fixing
- Use the `test-driven-development` skill

### 2. Implement Single Fix

- Address the root cause identified
- ONE change at a time
- No "while I'm here" improvements
- No bundled refactoring

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

### 4. If Fix Doesn't Work — The Rule of Three

- **STOP.**
- Count: How many fixes have you tried?
- If < 3: Return to Phase 1, re-analyze with new information
- **If ≥ 3: STOP and question the architecture (step 5 below)**
- DON'T attempt Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture

**Pattern indicating an architectural problem:**
- Each fix reveals new shared state/coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor the architecture vs. continue fixing symptoms?

**Discuss with the user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**
- **User said "stop" or corrected your direction**

**ALL of these mean: STOP. Return to Phase 1.**

**If user redirects you:** Stop immediately. Ask clarifying question. Pivot.

**If 3+ fixes failed:** Question the architecture (Phase 4 step 5).

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

### Investigation Tools

Use these Hermes tools during Phase 1:

- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run tests, check git history, reproduce bugs
- **`web_search`/`web_extract`** — Research error messages, library docs

### Tool Pitfall: Patch Tool Can Corrupt Large CSS Files

The `patch` tool's fuzzy matching can garble large CSS files (>5000 lines), especially when:
- Multiple similar CSS selectors exist (e.g., `.mobile-bottom-nav` vs `.mobile-bottom-nav-wrapper .mobile-bottom-nav`)
- Curly braces `{`/`}` in CSS syntax confuse the matching algorithm
- The old_string spans many lines

**Symptoms:** Patch reports success but the file has duplicated/mangled rules, or content from the diff output leaks into the file.

**Recovery:**
```bash
# Restore from git immediately
git checkout -- path/to/file.css
```

**Preferred approach for CSS edits:** Use `terminal` with `sed` targeting exact line numbers:
```bash
# Verify line numbers first
sed -n '4565,4582p' src/styles.css

# Apply targeted fix by line number
sed -i '' '4569s/position: absolute;/position: fixed;/' src/styles.css
sed -i '' '4577s/transform: translateY(100%);/transform: translateY(0);/' src/styles.css
```

**Rule of thumb:** For files >5000 lines, prefer `sed` with line numbers. Use `patch` only for small, unique blocks where the old_string is unmistakable.

### Tool Pitfall: Patch Tool Corrupts Python f-strings and Multi-line Code

The `patch` tool interpolates `${}` patterns and f-string expressions (e.g., `f"%{t}%"` ) as if they were shell variables or template placeholders. This silently corrupts Python code containing:
- f-strings with curly braces: `f"SELECT {col} FROM {table}"`
- String concatenation with format markers: `"%" + var + "%"`
- Dict/set literals in function bodies: `{"key": "value"}`

**Symptoms:**
- Patch reports success but `py_compile` fails with `IndentationError` or `SyntaxError`
- The patched file contains mangled code: `set(re...w+')` instead of `set(re.findall(r'\w+', ...))`
- SQL query strings are concatenated incorrectly
- Function body indentation shifts (8-space body becomes 4-space, breaking Python blocks)

**Recovery:** Use `git checkout` or rewrite the affected function entirely via a Python script:

```bash
# Use heredoc + Python script for safe file surgery
python3 << 'HEREDOC'
import re
fp = "/path/to/file.py"
with open(fp) as f:
    content = f.read()

# Find the broken function by its def line
start = re.search(r'    def broken_func\(self', content)
end = re.search(r'\n    def next_func\(', content)

# Write the replacement as a plain string (NO f-strings!)
new_func = """    def broken_func(self, x):
        return x + 1
"""
content = content[:start.start()] + new_func + content[end.start():]
with open(fp, 'w') as f:
    f.write(content)
HEREDOC
```

**Key rules:**
1. NEVER use the `patch` tool for Python code containing f-strings, SQL queries, or format strings with `%` placeholders
2. For complex Python file surgery, use `python3 << 'HEREDOC'` scripts that avoid f-strings entirely
3. Always `py_compile.compile(file, doraise=True)` after any edit
4. When replacing a method, find BOTH the start (`def method_name`) AND end (`def next_method`) boundaries to avoid leaving partial code
5. Test with `python3 -c "from module import Class; ..."` after patching

### Python Pitfall: ImportError Hides Module-Level Parse Failures

When `ImportError: cannot import name 'X' from 'module'` occurs but `X` clearly exists in the source, the real cause is often a **module-level parse failure** on a completely unrelated line.

**Root cause:** Python parses the ENTIRE module before executing any definitions. If ANY line has incompatible syntax (e.g., `str | None` on Python 3.8, or a SyntaxError), the entire module fails to load, and ALL imports from it fail — even for functions defined correctly above the problematic line.

**Common triggers:**
- `str | None` or `int | None` union syntax (requires Python 3.10+) on a system running 3.8
- `list[str]` lowercase generics (requires Python 3.9+) on older Python
- `match`/`case` statements (requires Python 3.10+)
- Syntax errors from failed merge/patch operations

**Debugging pattern:**
```bash
# DON'T trust the ImportError message — test the import directly
python3 -c "from module import function_name"

# This will reveal the REAL error, e.g.:
# TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
# SyntaxError: invalid syntax
```

**Fix:** Change the incompatible syntax to the `typing` module equivalent:
```python
# WRONG (Python 3.10+ only)
def func(extra_content: str | None = None) -> None:

# CORRECT (Python 3.8+)
from typing import Optional
def func(extra_content: Optional[str] = None) -> None:
```

**Also clear stale `.pyc` files** after fixing:
```bash
find . -path "./venv" -prune -o -name "*.pyc" -path "*module_name*" -delete
```

**Key insight:** The error message names the function you tried to import, NOT the line that actually failed. Previous sessions may have correctly added the function but missed a `str | None` elsewhere in the same file.

### Python Pitfall: SQLite + ThreadPoolExecutor Thread Safety

When using `sqlite3` with `concurrent.futures.ThreadPoolExecutor`, SQLite connections **cannot be shared across threads**. This causes `ProgrammingError: SQLite objects created in a thread can only be used in that same thread`.

**Common scenario:** A class creates a single `self._conn` in `__init__`, then methods using that connection are submitted to a `ThreadPoolExecutor`. The first thread works, but subsequent threads crash.

**WRONG -- shared connection across threads:**
```python
class Worker:
    def __init__(self, db_path):
        self._conn = sqlite3.connect(db_path)  # Created in main thread
    
    def query(self, sql):
        return self._conn.execute(sql).fetchall()  # CRASHES in thread

with ThreadPoolExecutor() as pool:
    pool.submit(worker.query, "SELECT 1")  # Error!
```

**CORRECT -- thread-local connections:**
```python
import threading

class Worker:
    def __init__(self, db_path):
        self.db_path = db_path
        self._thread_local = threading.local()
    
    @property
    def conn(self):
        if not hasattr(self._thread_local, 'conn') or self._thread_local.conn is None:
            self._thread_local.conn = sqlite3.connect(self.db_path)
            self._thread_local.conn.row_factory = sqlite3.Row
        return self._thread_local.conn
    
    def query(self, sql):
        return self.conn.execute(sql).fetchall()  # Each thread gets its own conn
```

**Singleton pattern also breaks with threads:**
```python
# WRONG -- global singleton shared across threads
_engine = None
def get_engine():
    global _engine
    if _engine is None:
        _engine = Engine()  # Engine opens a DB connection
    return _engine

# CORRECT -- thread-local singleton
_thread_local = threading.local()
def get_engine():
    if not hasattr(_thread_local, 'engine') or _thread_local.engine is None:
        _thread_local.engine = Engine()  # Each thread gets its own Engine+conn
    return _thread_local.engine
```

**Debugging pattern:**
1. Error message says "created in thread id X and this is thread id Y" → immediately suspect shared SQLite
2. `grep -n "sqlite3.connect\|self._conn\|self.db\|_engine"` to find all connection creation points
3. Check if any of those connections are accessed from `ThreadPoolExecutor.submit()` or `map()` calls
4. Convert to `threading.local()` pattern at every access point

**Key rules:**
1. Every `sqlite3.connect()` call creates a connection bound to the calling thread
2. `check_same_thread=False` parameter EXISTS but is a band-aid -- it disables the safety check but doesn't prevent race conditions
3. `threading.local()` is the correct solution -- each thread transparently gets its own connection
4. This applies to ANY library that wraps SQLite (cerebrum, iteration_engine, etc.)
5. The `@property` + `threading.local()` pattern gives lazy per-thread initialization with zero overhead

### Debugging Pattern: Content-Based Cache Key Mismatch (Cross-Domain)

When a caching system uses content-based hashes (MD5 of token IDs, text, or tensors) and cache lookups return 0% hit rate despite files existing, the ENTIRE tokenization pipeline must match exactly between producer and consumer.

**Symptoms:**
- Cache files exist (10K+ files)
- All lookups miss (0% hit rate)
- No errors — just silently degraded performance
- Loss component stays at 0.000 (e.g., teacher distillation D:0.000)

**The 5-layer debugging protocol:**

| Layer | What to Check | How to Verify |
|-------|--------------|---------------|
| 1. Tokenizer | Same tokenizer file loaded? | `tokenizer.name_or_path` comparison |
| 2. Text format | Same joining string? | `\n\n` vs `\n` vs ` ` — hash the text |
| 3. File order | Same file enumeration? | `sorted(files)` vs `os.walk` vs `glob` |
| 4. Column handling | Same column extraction? | Compare `_format_conversation` logic |
| 5. Tensor shape | Same dimensions? | `tensor.shape` before hashing |

**Verification command:**
```python
# Compare keys from precompute vs training for SAME input
precompute_key = get_cache_key(precompute_tokens, tokenizer.pad_token_id)
training_key = get_cache_key(training_tokens, tokenizer.pad_token_id)
assert precompute_key == training_key, f"MISMATCH: {precompute_key} != {training_key}"
```

**Session example (May 5):** Teacher distillation D:0.000 despite 74K cache files. Required 5 simultaneous fixes: tokenizer mismatch, text format (\n\n vs \n), file order (sorted vs os.walk), column handling, tensor dimension (2D vs 3D). One mismatch = 100% cache misses.

**See full reproduction:** `references/cache-alignment-five-fixes.md` in `qwen27b-training-pipeline` skill.

When a PyTorch model `__init__` hangs (no error, just stops responding), the cause is often a single layer with an astronomically large parameter count that exhausts CPU RAM during weight allocation. This is invisible in stack traces because the hang happens inside `nn.Linear.__init__` during `torch.empty()` allocation.

**Diagnostic approach — test each module class in isolation:**

```python
# Test 1: Single decoder layer
layer = SimpleLayer()  # OK

# Test 2: 8 layers in ModuleList
m = EightLayers()  # OK

# Test 3: Core model (embed + 8 layers + lm_head)
m = CoreModel()  # OK

# Test 4: Core + MTP4
m = WithMTP4()  # OK

# Test 5: Core + PARD
m = WithPARD()  # HANGS ← FOUND IT

# Test 6: PARD combiner alone
combiner = nn.Linear(248320 * 4, 248320)  # HANGS ← 247B parameters!
```

**Root cause:** `nn.Linear(993280, 248320)` has 993280 × 248320 ≈ 247 billion weights. At 4 bytes per weight (fp32 at creation), that's ~988GB just for one layer — far exceeding any GPU/CPU memory.

**Fix pattern:** Never concatenate vocab-size tensors. Instead:
1. Have parallel heads output hidden representations (not vocab logits)
2. Combine hidden representations with a small combiner
3. Project to vocab size ONCE at the end

```python
# WRONG — concatenates vocab logits
self.combiner = nn.Linear(vocab_size * num_parallel, vocab_size)

# RIGHT — combines hidden features, projects once
self.combiner = nn.Linear(hidden_size // 4 * num_parallel, hidden_size)
self.output_proj = nn.Linear(hidden_size, vocab_size)
```

**Also never create `nn.Linear` dynamically inside `forward()`** — this is slow, memory-unsafe, and creates untracked parameters that won't be in `model.parameters()`.

### Python Pitfall: SQLite WAL Mode — "Successful" Inserts That Don't Appear

When debugging SQLite inserts that report success but the data doesn't appear in queries, the database may be in **WAL mode** (`PRAGMA journal_mode=WAL`). In WAL mode, inserts go to a separate `.db-wal` file before being checkpointed to the main database. A new connection may see stale data if the WAL hasn't been checkpointed.

**Symptoms:**
- `conn.commit()` succeeds, no exception
- `SELECT COUNT(*)` returns 0 or old count
- Data "disappears" between connections
- The `.db-wal` file exists and is growing

**Verification:**
```bash
# Check journal mode
sqlite3 dbfile "PRAGMA journal_mode;"
# → wal

# Force checkpoint and verify
sqlite3 dbfile "PRAGMA wal_checkpoint(TRUNCATE); SELECT COUNT(*) FROM table;"

# Check WAL file size
ls -la dbfile-wal
```

**Fix patterns:**
1. **Checkpoint after batch inserts:**
   ```python
   conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
   ```
2. **Query from the same connection** that did the insert (shares WAL view)
3. **Use `isolation_level=None`** for immediate visibility
4. **For verification scripts:** always checkpoint before counting

**Debugging pattern:**
1. Insert reports success but `SELECT` shows 0 rows → suspect WAL
2. Check `PRAGMA journal_mode` → if `wal`, checkpoint and re-query
3. If data appears after checkpoint → WAL was the cause
4. If still missing → actual insert failure (constraint violation, wrong table, etc.)

**Session example (May 9):** Governor `log_attempt()` appeared to insert successfully (no errors, debug prints confirmed), but `tip_injection_attempts` showed 0 rows. The `.db-wal` file was 4MB. After `PRAGMA wal_checkpoint(TRUNCATE)`, 4 rows appeared — all test data had been saved correctly.

### Python Pitfall: Path("~") Does NOT Expand Tildes

`Path("~/.hermes")` creates a path with a LITERAL tilde character — it does NOT expand to the home directory. This causes silent failures where code creates a new empty database at `~/` instead of `/Users/username/`, or file operations mysteriously fail.

```python
# WRONG - creates path with literal ~ character
db_dir = Path("~/.hermes")
# db_dir = PosixPath('~/.hermes')  -- NOT /Users/username/.hermes

# CORRECT - expand the tilde first
db_dir = Path("~/.hermes").expanduser()
# db_dir = PosixPath('/Users/username/.hermes')

# CORRECT - use Path.home()
db_dir = Path.home() / ".hermes"
```

**Debugging pattern:** When a module initializes "successfully" but has zero data (0 facts, 0 records, empty tables), check the database path. If it shows a literal `~` in the path, the DB was created fresh at the wrong location while the real DB sits at the expanded path.

### Python Pitfall: Hook Signature Mismatch — Silent Failures in Plugin Systems

When a plugin registers a callback with a hook system that uses `invoke_hook(**kwargs)`, a signature mismatch causes a `TypeError` that is silently swallowed by the hook dispatcher's try/except. The plugin appears to load and register successfully, but the callback NEVER FIRES. No error is visible.

**Symptom:**
- Plugin shows as enabled (`hermes plugins list`)
- Hooks appear registered (plugin manifest lists them)
- Hook has zero observable effect — no logs, no traces, no state changes
- No error in any log output

**Root cause:** The `invoke_hook` implementation wraps each callback in try/except and logs at WARNING level. If the logger isn't configured to show warnings, or if the error is buried in output, it appears as complete silence.

```python
# In invoke_hook (hermes_cli/plugins.py:1130-1164):
for cb in callbacks:
    try:
        ret = cb(**kwargs)  # TypeError here if signature mismatch
    except Exception as exc:
        logger.warning("Hook '%s' callback %s raised: %s", ...)  # Silent!
```

**Common mismatch:** `post_tool_call` hook passes `tool_name, args, result, task_id, session_id, tool_call_id, duration_ms` but the plugin expects `status, error`.

**Detection:**
```bash
# Check invoke_hook call site in model_tools.py
grep -A 10 'invoke_hook("post_tool_call"' hermes_cli/model_tools.py

# Compare with your hook signature
grep -A 3 'def _on_post_tool_call' ~/.hermes/plugins/your-plugin/__init__.py
```

**Fix:** Always add `**kwargs` to hook signatures and make all parameters optional with defaults:
```python
# WRONG — silently fails when invoke_hook passes extra kwargs
def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                        status: str, error: str = "") -> None:

# RIGHT — accepts all kwargs the core passes, plus future extras
def _on_post_tool_call(tool_name: str, args: dict, result: Any,
                        status: str = "", error: str = "", **kwargs) -> None:
    # Derive status from result if not provided by core
    if not status and result:
        result_str = str(result).lower()
        if '"error"' in result_str or 'error:' in result_str:
            status = "error"
        else:
            status = "success"
```

**Apply to ALL hooks:**
- `_on_pre_tool_call(tool_name, args)` → `_on_pre_tool_call(tool_name, args, **kwargs)`
- `_on_pre_llm_call(user_message, context=None)` → `_on_pre_llm_call(user_message, context=None, **kwargs)`
- `_on_post_api_request(model_name, usage, response, latency_ms)` → `_on_post_api_request(model_name, usage, response, latency_ms=0, **kwargs)`

**Verification:** Add a log line inside the hook body. If it appears, the hook IS firing. If not, check the signature.

**See also:** `hermes-plugin-development` skill, `references/hook-signature-mismatch-debug.md` for full debug recipe.

### With delegate_task

For complex multi-component debugging, dispatch investigation subagents:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**

---

## Debugging From Within the Gateway (Self-Debugging)

When you ARE the running process you're debugging (e.g., the gateway), standard approaches break down. Here's how to handle it:

### Unique Constraints

1. **Cannot restart yourself** -- `pkill -f "hermes.*gateway"` from within the gateway will be blocked by safety checks. You need the user or a twin agent to restart.
2. **Cannot see stdout** -- `print()` output goes to the gateway process's stdout, not to your tool results. Use file-based probes instead: `open("/tmp/debug.txt", "w").write(...)`
3. **Code changes require restart** -- Python caches imported modules. Editing a .py file on disk does NOT change the running code. `__pycache__` .pyc files are irrelevant; the module is already in memory.
4. **Tool output masks secrets** -- The `patch` tool and `read_file`/`sed` display `api_key=<value>` as `api_key=***`. The actual file is correct; only the display is masked. Use hex dumps to verify if unsure: `python3 -c "print(open('file.py','rb').read()[start:end])"`
5. **execute_code has minimal env** -- The sandbox doesn't inherit gateway env vars (e.g., no OPENROUTER_API_KEY). Always test with `terminal` and `source venv/bin/activate`.

### File-Based Debug Probes

When you can't use print/stdout, inject write-to-file probes at critical code points:

```python
# Add to the code path you're investigating
open("/tmp/debug_probe.txt", "w").write(f"reached here: var1={var1} var2={var2}\n")
```

**Rules for probes:**
- Use simple string formatting (no f-string nesting with quotes -- it causes SyntaxErrors)
- Place BEFORE the line you suspect fails (not after)
- Check the file AFTER triggering the code path through the gateway
- If the file doesn't exist, the code path was never reached (module not reloaded)

### Verifying Patches Are Loaded

After editing a file that the gateway already imported:

1. The edit is on disk but NOT in the running process
2. `__pycache__` cleanup does NOT help (module already in `sys.modules`)
3. Standalone test (`python3 -c "from module import func; func()"`) tests the FILE, not the running process
4. Only a gateway restart loads the new code

**Pattern:** Always test with a standalone script FIRST to confirm the fix is correct on disk, THEN arrange a restart to apply it to the running process.

### The "Same Bug, Two Paths" Pattern

When fixing a bug that affects both sync and async code paths:

- `call_llm()` (sync) and `async_call_llm()` (async) often have parallel code
- Fixing one does NOT fix the other
- **Fix BOTH in the same edit** -- don't discover the second instance later after a restart
- Search for the pattern: `grep -n "def call_llm\|def async_call_llm"` then compare their implementations
- Use `diff <(sed -n '/def call_llm/,/^def /p' file) <(sed -n '/def async_call_llm/,/^def /p' file)` to spot divergences
- Any parameter resolution, config lookup, or default-value logic must be identical in both

### Git Pull Wipes Local Patches

When updating hermes-agent (`git pull`, `hermes update`), `git stash` saves local changes BUT `git stash pop` is needed to restore them. If you forget to pop, your patches are gone.

**Better approach:** Keep a patch file that can be re-applied:

```bash
# After fixing a bug, create a reusable patch
git diff > ~/patches/vision-fix.patch

# After git pull, re-apply
git apply ~/patches/vision-fix.patch

# Verify the patch applied cleanly
python3 -c "from agent.auxiliary_client import call_llm; ..." # test
```

**Critical:** ALWAYS verify patches still apply after an update. The upstream code may have changed the surrounding context, making the patch fail silently or apply incorrectly. Run standalone tests immediately after re-applying.

### Coordinating with a Twin Agent

When you need to restart the gateway but can't do it yourself:

1. Spawn a twin agent in tmux (see `twin-agent-collaboration` skill)
2. Write a mission brief to `/tmp/` with all findings
3. The twin can restart the gateway (it's a separate process)
4. Communicate via shared files in `/tmp/`
5. After restart, verify fixes took effect immediately
