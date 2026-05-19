# Self-Audit Engine Integration

Session: May 6, 2026 — wired self-audit into learning-brain plugin hooks.

## What was added

The tiered memory system now works alongside the self-audit engine in the learning-brain plugin:

- `pre_tool_call_hook`: PreflightChecker validates args + LoopDetector checks history
- `post_tool_call_hook`: TokenWasteTracker records call + logs waste to error_registry

## Files involved

- `plugins/learning-brain/__init__.py` — hooks wired
- `hermes_cli/subconscious/self_audit_engine.py` — audit engine
- `hermes_cli/subconscious/hermes_harness_enhancer.py` — gap analysis

## Key pitfall

Loop detection uses a sliding window of 3 calls. If 3 identical calls or 3 same-tool failures occur, the hook BLOCKS the call and suggests recovery. This prevents the agent from burning tokens on repeated failures (e.g., cronjob queried 16x in one session).

## Recovery patterns

| Error pattern | Suggested fix |
|---------------|---------------|
| patch old_string not found | Use write_file instead |
| skill_manage frontmatter | Add 'name' field to frontmatter |
| cronjob id error | Use terminal(background=True) or python schedule |
| process not found | Process exited, check ps aux |

## Test result

3 identical cronjob calls → loop detected, recovery suggested:
```
[RESCUE] Loop detected! Break pattern:
  1. Stop repeating the same tool
  2. Switch to a different approach (write_file instead of patch)
  3. Ask user for clarification
  4. Use execute_code for complex multi-step logic
```
