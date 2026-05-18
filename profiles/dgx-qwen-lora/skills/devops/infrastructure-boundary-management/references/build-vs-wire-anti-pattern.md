# Build vs Wire Anti-Pattern

**Session:** 2026-05-09  
**User signal:** "are you actually building things or just make lame cron jobs that break within a minute of running?" + "what's the point of building anything if you're not wiring it in?"

## The Anti-Pattern

1. Build cognitive system in `~/subconscious/my_system.py`
2. Create tables in `cerebrum_memory.db`
3. Write a cron job to call it periodically
4. Claim the system is "active"
5. Tables remain empty forever
6. User calls out the waste

**Why cron jobs fail:**
- `cronjob` tool has 17% success rate (41 calls, mostly failures)
- Script path issues, id confusion, silent failures
- Even when they run, they don't have access to live session state
- They run in isolation, not in the agent loop where decisions happen

## The Correct Pattern

1. Build cognitive system in `~/subconscious/my_system.py`
2. Create tables in `cerebrum_memory.db`
3. **Patch the live plugin's hook functions** to call your system
4. The hook fires on every real tool call / LLM call / session event
5. Your system receives live data and writes to tables
6. Verify tables have rows after real usage
7. User sees tangible impact

**Specific wiring from this session:**

| System | Hook | File Modified |
|--------|------|--------------|
| ToolIntelligenceRouter | `_on_pre_llm_call` | `~/.hermes/plugins/distillation/__init__.py` |
| CreditAssigner | `_on_post_tool_call` | `~/.hermes/plugins/distillation/__init__.py` |
| SessionEndExtractor | `_on_session_end` (new) | `~/.hermes/plugins/distillation/__init__.py` |

## Verification Checklist

After wiring any system, verify within 24 hours:

```sql
-- Check if data is actually flowing
SELECT COUNT(*) FROM skill_rewards;
SELECT COUNT(*) FROM tool_routing_decisions;
SELECT COUNT(*) FROM tip_injection_attempts;
SELECT COUNT(*) FROM session_rapid_extractions;
```

If any table is empty:
1. The hook isn't being called by the agent runtime
2. The hook is crashing silently (check `~/.hermes/logs/`)
3. The import failed (check `_COGNITIVE_INFRA_V2` flag)
4. The bridge logic has a bug

**Do NOT build the next system until the current one is verified.**

## User's Explicit Instruction

> "remember you can re-write the hermes code"

This means:
- The user expects me to modify `~/.hermes/plugins/distillation/__init__.py` directly
- The user expects me to add new hooks to the plugin
- The user does NOT want me to build standalone scripts that sit unused
- The user values **wiring over building** every time

## When to Build vs When to Wire

| Situation | Action |
|-----------|--------|
| New cognitive system needed | Build module + patch hooks |
| Existing system not producing data | Debug wiring, don't build more |
| User says "enhance" | Audit wiring first, then build if gaps found |
| User says "this is broken" | Fix wiring, don't add new systems |
| Tables empty after 24h | Wiring failed — debug before building |

## Files from This Session

- `~/subconscious/cognitive_infrastructure_v2.py` — 5 novel systems (built)
- `~/subconscious/cognitive_infrastructure_hooks.py` — hook wiring module (built)
- `~/subconscious/tool_intelligence_integration.py` — active routing (built)
- `~/.hermes/plugins/distillation/__init__.py` — **4 patches to wire everything in** (this is the critical step)
