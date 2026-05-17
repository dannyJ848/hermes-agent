---
name: retry-circuit-breaker
version: 1.1
category: meta
triggers:
  - tool call fails
  - repeated failure
  - loop detection
  - parameter omitted
---

# Retry Circuit Breaker

After 2 consecutive failures with the SAME tool and SAME missing/malformed parameter, STOP using that tool. Switch immediately to a proven fallback.

## Rules

1. **2-strike rule**: If a tool fails twice for the same reason (missing param, wrong format, auth error), do NOT call it a third time the same way
2. **Check tool_intelligence first**: Before using any tool for the first time in a session, check proven vs weak:
   - PROVEN (90%+): write_file, read_file, execute_code, terminal, skill_view, web_search
   - WEAK (below 50%): cronjob(5%), patch(44%), skill_manage(50%)
   - Always prefer proven tools for critical paths
3. **Self-correction does NOT propagate**: GLM-5.1 has a known bug where recognizing an error in text output ("I keep forgetting X") does NOT fix the next tool call. The only fix is switching to a different tool entirely
4. **Compound shell commands**: Never chain kill + nohup + background in one terminal() call. Use write_file to make a script, then execute it
5. **SQL in terminal**: Never inline SQL in terminal() or execute_code. Always write_file a /tmp/script.py, then run it

## Proven Fallback Map

| Failing Tool | Fallback |
|---|---|
| cronjob create | write_file + terminal (run python script) |
| skill_manage create | write_file to ~/.hermes/skills/<category>/<name>/SKILL.md directly |
| patch (complex) | write_file (full rewrite) or execute_code with Python |
| inline SQL | write_file /tmp/script.py + terminal python3 /tmp/script.py |
| memory (replace failing) | patch on ~/.hermes/memories/MEMORY.md directly |

## Detection Signals

If you catch yourself writing ANY of these phrases, that IS the loop signal — switch tools NOW:
- "I keep forgetting/omitting [X]"
- "I keep [doing X]"
- "Still missing [X]"
- "Let me be more deliberate" (then do the same thing)

## Why This Exists

GLM-5.1's text reasoning and tool dispatch are decoupled. The model can correctly identify a missing parameter in its text output but the correction does not propagate to the next tool call generation. This was observed in:
- cronjob create: 10+ calls omitting 'schedule' param despite explicitly saying "I keep forgetting schedule"
- skill_manage create: 4 calls omitting 'content' param
- memory replace: 3 calls omitting 'content' param
