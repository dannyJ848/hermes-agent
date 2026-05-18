---
name: auto-generated-plugin-debug
description: Debug and fix auto-generated or reconstructed Hermes plugin code. Covers return type mismatches, constructor arg gaps, SQL escaping, and shell quoting pitfalls.
version: 1.0
---

# Auto-Generated Plugin Debug

## Trigger
When a plugin was auto-generated or reconstructed (e.g., after corruption), and needs systematic debugging before it is trusted. Especially when the original source is lost and you are working from generated code.

## Bug Classes (ordered by likelihood)

### 1. Return Type Mismatch - Tuple Unpacking vs Single Return

**Symptom:** `ValueError: not enough values to unpack` or `TypeError` on function calls.

**Pattern:** Auto-generators assume functions return tuples, but many return single values:
```python
# WRONG - _check_duplicate returns Optional[str], not tuple
is_dup, existing_id = _check_duplicate(condition=..., recommendation=..., domain=...)

# CORRECT
existing_id = _check_duplicate(condition=..., recommendation=..., domain=...)
if existing_id:  # str if dup found, None otherwise
    _touch_node(existing_id)
```

**Detection:** Search for `a, b = some_func(` patterns where `some_func` returns a single Optional value.

### 2. Constructor Arg Gaps - Modules Set to None

**Symptom:** Module-level variables are `None`, causing `AttributeError: 'NoneType' object has no attribute X`.

**Pattern:** Auto-generator sees constructor needing more than 1 arg and sets `_module = None`:
```python
# WRONG - generator gave up because WorldModel needs session_id
_wm = None  # needs params, instantiated on first use

# CORRECT - pass session_id="default"
_wm = WorldModel(session_id="default")
```

**Bulk fix:** Use regex to find all `= None  # needs params` and replace with proper instantiation. Write a Python script (to /tmp/) that:
1. Reads the plugin file
2. Finds `= None  # needs params` lines
3. Looks back 1-3 lines for the `from X import ClassName` import
4. Replaces `_var = None` with `_var = ClassName(session_id="default")`

**Invalid modules to skip:**
- `ToolCircuitBreaker` - needs `tool_name` arg, instantiated per-tool, NOT at module level

### 3. SQL String Escaping - JSON in LIKE Clauses

**Symptom:** `SyntaxError: invalid syntax` on a line with SQL string concatenation.

**Pattern:** Trying to filter JSON-formatted text in SQL via Python string:
```python
# WRONG - {" breaks the Python double-quoted string
"AND text NOT LIKE '{"action_hash":%%' "

# CORRECT - use length or other proxy filter
"AND length(text) > 50 "
```

**Rule:** NEVER put JSON content (with double-quotes) inside Python double-quoted SQL strings. Use proxy filters (`length()`, `text NOT ILIKE '{%' `) or filter in Python after the query.

### 4. Duplicate SQL WHERE Clauses

**Symptom:** Rows matched by identical WHERE AND clauses twice - functional but inefficient, and can indicate a copy-paste bug where the second line was supposed to be different.

**Detection:** Scan for consecutive identical `"AND ..."` lines in SQL string concatenation.

**Fix:** Remove the duplicate. If the second should have been different, add the correct condition.

## Shell Quoting Avoidance

When fixing these bugs, NEVER use inline Python in terminal() with complex strings (nested quotes, f-strings, SQL). Instead:

```python
# WRONG - shell quoting nightmare with nested quotes
# terminal("""python3 -c "print('hello "world"')" """)

# CORRECT - write script to /tmp/, then execute
write_file("/tmp/fix_plugin.py", content)
terminal("python3 /tmp/fix_plugin.py")
```

This avoids all escaping issues for:
- SQL strings with JSON content
- Python f-strings with embedded braces
- Multi-line string replacements
- Regex patterns with backreferences

## Verification Checklist

After fixing, run these in order:

1. **Syntax check:** `python3 -c "import ast; ast.parse(open('plugin.py').read())"`
2. **Load test:** Import the plugin and verify all hooks register (time it - should be under 1s)
3. **Injection test:** Call `build_injection()` and verify it returns real content, not empty
4. **DB audit:** Run the 23-check audit script against the Cortex database
5. **E2E test:** Run through all hook paths (post_tool_call, pre_tool_call, pre_llm_call, post_api_request)

## Pitfalls

- **try/except silencing:** Many module imports are wrapped in try/except that silently sets variables to None. A module that fails to construct becomes None, and later code hits AttributeError. Always verify the module actually loaded, not just that the import did not crash the whole plugin.
- **Variable name reuse:** `_cbm_manager = CircuitBreakerManager(...)` on one line but `_cbm_manager = ContextBudgetManager(...)` later overwrites it with a different class. Scan for duplicate variable names.
- **Per-process singletons:** `_INSTANCE` pattern (intrinsic_metacognition) creates one instance in the daemon process and a DIFFERENT instance in the plugin process. Metacog rounds in the daemon do not transfer to the plugin. Fix: store state in Postgres, not in-memory singletons.
