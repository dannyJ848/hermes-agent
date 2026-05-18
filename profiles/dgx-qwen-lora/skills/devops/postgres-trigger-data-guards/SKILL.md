---
name: postgres-trigger-data-guards
version: 1.0
created: 2026-04-15
description: Use PostgreSQL BEFORE INSERT/UPDATE triggers as data integrity guards. Prevents re-contamination when daemons/plugins keep re-creating bad data you just cleaned up.
trigger: When you clean up contaminated data but it keeps coming back from daemons or background processes. Or when you need a single source of truth for domain/type normalization across multiple codepaths.
---

# PostgreSQL Trigger Data Guards

When you clean up contaminated data (bad domains, junk node types, action_hash blobs) but daemons/plugins keep re-creating it, do not chase with cleanup scripts. Add BEFORE INSERT triggers that auto-correct or auto-deactivate on insert.

## When to Use
- You cleaned bad data but it keeps coming back from daemons/background processes
- Multiple codepaths can insert data and you cannot fix them all at once
- You need a single source of truth for domain/type normalization
- You want defense-in-depth against upstream bugs

## Pattern 1: Domain Normalization Trigger

Maps non-canonical domain names to canonical ones on every INSERT and UPDATE. Unknown domains default to a safe fallback.

```sql
CREATE OR REPLACE FUNCTION fn_normalize_domain() RETURNS trigger AS $$
DECLARE new_domain text;
BEGIN
    new_domain := CASE NEW.domain
        WHEN 'hindsight' THEN 'self_improvement'
        WHEN 'terminal' THEN 'coding'
        WHEN 'web_research' THEN 'knowledge_management'
        WHEN 'tool_usage' THEN 'tool_use'
        WHEN 'project' THEN 'tool_use'
        WHEN '' THEN 'tool_use'
        ELSE NEW.domain
    END;
    -- Fallback: unknown domains -> safe default
    -- CRITICAL: only list your TRUE canonical domains here
    IF new_domain NOT IN ('search','coding','reasoning','tool_use','planning',
                          'self_improvement','agent_memory','knowledge_management',
                          'error_recovery','strategy','software_engineering',
                          'agent_evaluation','debugging') THEN
        new_domain := 'tool_use';
    END IF;
    NEW.domain := new_domain;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS domain_normalize ON cortex_nodes;
CREATE TRIGGER domain_normalize 
BEFORE INSERT OR UPDATE ON cortex_nodes 
FOR EACH ROW EXECUTE FUNCTION fn_normalize_domain();
```

## Pattern 2: Auto-Deactivation Trigger

Auto-sets is_active=false for unwanted node types or text patterns, preventing junk from ever being queryable.

```sql
CREATE OR REPLACE FUNCTION fn_deactivate_junk() RETURNS trigger AS $$
BEGIN
    IF NEW.node_type = 'circuit_breaker' THEN NEW.is_active = false; END IF;
    IF NEW.text LIKE '{"action_hash":%' THEN NEW.is_active = false; END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_deactivate_junk ON cortex_nodes;
CREATE TRIGGER trg_deactivate_junk 
BEFORE INSERT ON cortex_nodes 
FOR EACH ROW EXECUTE FUNCTION fn_deactivate_junk();
```

## Key Rules

1. BEFORE triggers modify data before it is written -- the INSERT sees the modified values
2. Use INSERT OR UPDATE for normalization (domains can change on update)
3. Use INSERT only for deactivation (no need to re-check on update)
4. Always DROP TRIGGER IF EXISTS before CREATE to allow re-runs
5. Test with explicit INSERT + SELECT to verify the trigger actually fires
6. The old trigger may call a DIFFERENT function than what you just created -- always verify both function and trigger action statement

## Critical Pitfalls

### TRIGGER REVERTS MANUAL DATA FIXES (MOST IMPORTANT)
If you run UPDATE to fix domain values (e.g., `tool_usage → tool_use`), but the trigger function's CASE/allowlist still maps to the OLD wrong value, your fix gets silently reverted. Every UPDATE fires the trigger, which sees your corrected value and may re-map it back to the wrong canonical name.

**Symptoms:** You UPDATE 9,000 rows, verify count is correct, then 5 minutes later the old values reappear. Daemon or any other writer triggers the BEFORE UPDATE.

**Root cause:** The trigger's `IF new_domain NOT IN (...)` allowlist contains the wrong domain name as "valid", so it passes through unchecked. Or the CASE maps synonyms to the wrong canonical.

**Fix order — ALWAYS do this:**
1. Read the trigger function: `SELECT prosrc FROM pg_proc WHERE proname='fn_normalize_domain'`
2. Verify every domain in the allowlist matches your ACTUAL canonical set
3. Fix the trigger function FIRST (DROP + CREATE with correct mapping)
4. THEN run your UPDATE to fix existing data
5. Verify no reversion after waiting 30+ seconds

**Example:** We had `tool_usage` in the trigger allowlist (wrong) when our canonical set only has `tool_use`. Every manual `UPDATE SET domain='tool_use'` fired the trigger, which saw `tool_use` was valid and left it — but any daemon write with `tool_usage` also passed the trigger's validation. Result: 9,487 rows kept reverting until we fixed the trigger.

### Wrong Function Name
The old trigger says `EXECUTE FUNCTION normalize_domain_trigger()` but you created `fn_normalize_domain()`. Your new function exists but the trigger still calls the old one. Always verify:

```sql
-- Check what function the trigger calls
SELECT trigger_name, action_statement FROM information_schema.triggers 
WHERE event_object_table = 'your_table';

-- Check your function exists
SELECT prosrc FROM pg_proc WHERE proname = 'your_function_name';
```

### psycopg2 Transaction Abort Cascade
When ONE query fails in psycopg2, ALL subsequent queries on the same cursor fail with "current transaction is aborted, commands ignored until end of transaction block" until you call `conn.rollback()`. Always add rollback() in exception handlers. This is the #1 cause of "works in isolation but fails in batch" bugs.

### LIKE Patterns with JSON Double-Quotes in Python
`text LIKE '{"action_hash":%'` causes SyntaxError in Python because the `"` inside the SQL breaks Python string parsing. This is ESPECIALLY bad in f-strings where `{chr(34)}` gets interpreted as Python expression code, not SQL.

WRONG approaches (all cause SyntaxError):
- `"text LIKE '{\"action_hash\":%'"` -- Python string parsing breaks on nested quotes
- `f"...text LIKE '{' || chr(34) || 'action_hash' ..."` -- f-string interprets `chr(34)` as Python code
- `"text !~ '^\{\"action_hash\":'"` -- quoting nightmares

CORRECT approach -- use psycopg2 parameter binding with a Python variable:
```python
_ah_prefix = '{"action_hash":%'
cur.execute("SELECT ... WHERE text NOT LIKE %s ...", (_ah_prefix,))
```

This is safe, clean, and works in all Python versions. The `%s` is handled by psycopg2, not Python string formatting, so there are no quoting issues.

### Do Not Restart Daemons for Plugin Code Changes
Plugin code changes (distillation/__init__.py, episodic_memory.py, etc.) take effect on the next Hermes session load, NOT on daemon restart. The daemon has its own code and reimports each cycle independently. Killing a working daemon to "apply" plugin patches risks spawning duplicate instances. Only restart the daemon when you are changing daemon code itself (cortex_daemon.py).

If you MUST restart the daemon, use the STOP file protocol from the cortex-daemon-diagnostic skill.
